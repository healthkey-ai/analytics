import csv
import io
import re

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status

from patients.models import PatientInfo
from .filters import apply_cohort_filters
from .models import SavedCohort


class ExportRateThrottle(UserRateThrottle):
    rate = "10/hour"
    scope = "cohort_export"


COHORT_MAX_PER_USER = 10
FILTER_LIST_MAX_VALUES = 10

# Explicit allowlist of exportable fields — add new fields here intentionally.
# PII fields (email, DOB, postal_code, etc.) are never included.
EXPORT_FIELDS = [
    "id",
    # demographics
    "patient_age", "gender", "race", "ethnicity", "country", "region",
    "smoking_status",
    # disease
    "disease", "disease_slug", "stage", "diagnosis_date",
    "condition_clinical_status",
    # performance
    "karnofsky_performance_score", "ecog_performance_status",
    # comorbidities
    "no_other_active_malignancies", "no_pre_existing_conditions",
    "preexisting_conditions", "peripheral_neuropathy_grade",
    # cytogenetics / molecular
    "cytogenic_markers", "genetic_mutations", "tp53_disruption",
    "stem_cell_transplant_history", "plasma_cell_leukemia",
    # MM disease characteristics
    "clonal_plasma_cells", "measurable_disease_imwg", "meets_crab",
    "bone_lesions", "bone_imaging_result", "kappa_flc", "lambda_flc",
    "monoclonal_protein_serum", "monoclonal_protein_urine",
    # labs — CBC
    "hemoglobin_g_dl", "platelet_count", "wbc_count_thousand_per_ul",
    "anc_thousand_per_ul",
    # labs — renal / electrolytes
    "serum_creatinine_mg_dl", "egfr_ml_min_173m2", "serum_calcium_mg_dl",
    # labs — liver / protein
    "albumin_g_dl", "ast_u_l", "alt_u_l", "alkaline_phosphatase_u_l",
    "bilirubin_total_mg_dl",
    # labs — myeloma-specific
    "beta2_microglobulin", "ldh_u_l",
    # breast cancer specific
    "estrogen_receptor_status", "progesterone_receptor_status",
    "her2_status", "tnbc_status", "tumor_stage", "nodes_stage",
    "distant_metastasis_stage",
    # outcomes / follow-up
    "mrd_status",
    # treatment
    "prior_therapy", "therapy_lines_count", "relapse_count",
    "treatment_refractory_status",
    "first_line_therapy", "first_line_start_date", "first_line_end_date",
    "first_line_outcome", "first_line_intent", "first_line_discontinuation_reason",
    "second_line_therapy", "second_line_start_date", "second_line_end_date",
    "second_line_outcome", "second_line_intent",
    "later_therapy", "later_start_date", "later_end_date",
    "later_outcome", "later_intent", "later_therapies",
    "supportive_therapies",
    "created_at", "updated_at",
]

MAX_EXPORT_ROWS = 50_000


class _FakeRequest:
    """Wraps a filters dict so apply_cohort_filters() can read it."""

    def __init__(self, filters: dict):
        self._filters = filters

    @property
    def query_params(self):
        return _DictQueryParams(self._filters)


class _DictQueryParams:
    def __init__(self, d: dict):
        self._d = d

    def get(self, key, default=None):
        val = self._d.get(key)
        if val is None:
            return default
        if isinstance(val, list):
            return val[0] if val else default
        return str(val)

    def getlist(self, key):
        val = self._d.get(key)
        if val is None:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        return [str(val)]

    def __contains__(self, key):
        return key in self._d

    def __getitem__(self, key):
        val = self._d[key]
        if isinstance(val, list):
            return val[0]
        return str(val)


def _serialize_qs(qs):
    rows = []
    for obj in qs.values(*EXPORT_FIELDS).iterator(chunk_size=2000):
        row = {}
        for k, v in obj.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
            else:
                row[k] = v
        rows.append(row)
    return rows


def _csv_stream(qs):
    """Yield CSV rows one at a time so we never hold the full dataset in memory."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    yield buf.getvalue()
    for obj in qs.values(*EXPORT_FIELDS).iterator(chunk_size=2000):
        buf.seek(0)
        buf.truncate()
        row = {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in obj.items()}
        writer.writerow(row)
        yield buf.getvalue()


def _validate_filter_cardinality(filters: dict) -> str | None:
    """Return an error message if any list-valued filter exceeds the max cardinality."""
    for key, val in filters.items():
        if isinstance(val, list) and len(val) > FILTER_LIST_MAX_VALUES:
            return (
                f"Filter '{key}' has {len(val)} values; maximum is {FILTER_LIST_MAX_VALUES}."
            )
    return None


def _safe_filename(name: str) -> str:
    """Strip characters that could break Content-Disposition headers."""
    cleaned = re.sub(r"[^\w\-. ]", "_", name).replace(" ", "_")[:64]
    return cleaned.encode("ascii", "replace").decode("ascii")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def saved_cohort_list(request):
    if request.method == "GET":
        cohorts = SavedCohort.objects.filter(user=request.user)
        data = [_cohort_data(c) for c in cohorts]
        return Response(data)

    # POST — create
    if SavedCohort.objects.filter(user=request.user).count() >= COHORT_MAX_PER_USER:
        return Response(
            {"detail": f"Cohort limit reached ({COHORT_MAX_PER_USER} max). Delete an existing cohort to save a new one."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    name = request.data.get("name", "").strip()
    if not name:
        return Response({"detail": "name is required."}, status=status.HTTP_400_BAD_REQUEST)
    filters = request.data.get("filters")
    if not isinstance(filters, dict):
        return Response({"detail": "filters must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)
    error = _validate_filter_cardinality(filters)
    if error:
        return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
    cohort = SavedCohort.objects.create(
        user=request.user,
        name=name,
        description=request.data.get("description", ""),
        filters=filters,
    )
    return Response(_cohort_data(cohort), status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def saved_cohort_detail(request, pk):
    try:
        cohort = SavedCohort.objects.get(pk=pk, user=request.user)
    except SavedCohort.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(_cohort_data(cohort))

    if request.method == "PUT":
        if "name" in request.data:
            name = request.data["name"].strip() if isinstance(request.data["name"], str) else ""
            if not name:
                return Response({"detail": "name cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            cohort.name = name
        if "description" in request.data:
            cohort.description = request.data["description"]
        if "filters" in request.data:
            if not isinstance(request.data["filters"], dict):
                return Response({"detail": "filters must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)
            error = _validate_filter_cardinality(request.data["filters"])
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
            cohort.filters = request.data["filters"]
        cohort.save()
        return Response(_cohort_data(cohort))

    # DELETE
    cohort.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ExportRateThrottle])
def saved_cohort_export(request, pk):
    try:
        cohort = SavedCohort.objects.get(pk=pk, user=request.user)
    except SavedCohort.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    fake_req = _FakeRequest(cohort.filters)
    qs = apply_cohort_filters(fake_req)
    fmt = request.query_params.get("file_format", "csv")
    safe_name = _safe_filename(cohort.name)

    if fmt == "json":
        rows = _serialize_qs(qs[:MAX_EXPORT_ROWS])
        return JsonResponse(rows, safe=False)

    # CSV — stream row-by-row to avoid loading 50k rows into memory
    filename = f"cohort-{safe_name}.csv"
    response = StreamingHttpResponse(_csv_stream(qs[:MAX_EXPORT_ROWS]), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _cohort_data(cohort: SavedCohort) -> dict:
    return {
        "id": cohort.pk,
        "name": cohort.name,
        "description": cohort.description,
        "filters": cohort.filters,
        "created_at": cohort.created_at.isoformat(),
        "updated_at": cohort.updated_at.isoformat(),
    }
