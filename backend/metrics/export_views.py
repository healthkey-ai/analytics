"""
Chart-level patient export endpoint.

GET /metrics/export/?chart=<key>&file_format=csv

Returns patient-level data (one row per patient) with columns relevant to
the requested chart.  Access is restricted to premium or staff users and
rate-limited to 10 requests per hour.
"""
import csv
import io

from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import IsPremiumOrStaff
from accounts.utils import apply_org_scope
from cohorts.filters import apply_cohort_filters
from cohorts.saved_views import EXPORT_FIELDS
from patients.models import PatientInfo

MAX_EXPORT_ROWS = 50_000
MAX_JSON_ROWS   = 5_000


class ChartExportRateThrottle(UserRateThrottle):
    rate = "10/hour"
    scope = "chart_export"


# ---------------------------------------------------------------------------
# Field lists — each value must be a subset of EXPORT_FIELDS in saved_views.py
# (PII fields like postal_code and date_of_birth are never included).
# ---------------------------------------------------------------------------

CHART_EXPORT_FIELDS = {
    "survival": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "first_line_outcome",
    ],
    "subgroup_survival": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "cytogenic_markers", "stem_cell_transplant_history",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "first_line_outcome",
    ],
    "response_rates": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "first_line_therapy", "first_line_outcome",
        "second_line_therapy", "second_line_outcome",
        "later_therapy", "later_outcome",
    ],
    "treatment_patterns": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "therapy_lines_count", "relapse_count",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "first_line_outcome",
        "second_line_therapy", "second_line_start_date", "second_line_end_date",
        "second_line_outcome",
        "later_therapy", "later_start_date", "later_end_date",
        "later_outcome", "later_therapies",
    ],
    "demographics": [
        "id", "patient_age", "gender", "race", "ethnicity",
        "country", "region", "smoking_status", "disease",
        "diagnosis_date",
    ],
    "staging": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "ecog_performance_status",
        "cytogenic_markers", "stem_cell_transplant_history",
        "clonal_plasma_cells", "meets_crab",
        "bone_lesions", "bone_imaging_result", "plasma_cell_leukemia",
    ],
    "labs": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "hemoglobin_g_dl", "platelet_count",
        "wbc_count_thousand_per_ul", "anc_thousand_per_ul",
        "serum_creatinine_mg_dl", "egfr_ml_min_173m2",
        "serum_calcium_mg_dl", "albumin_g_dl",
        "ast_u_l", "alt_u_l", "alkaline_phosphatase_u_l",
        "bilirubin_total_mg_dl", "beta2_microglobulin", "ldh_u_l",
        "monoclonal_protein_serum", "monoclonal_protein_urine",
    ],
    "ttnt": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "second_line_therapy", "second_line_start_date", "second_line_end_date",
        "later_therapy", "later_start_date", "later_end_date",
    ],
    "dor": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_therapy", "first_line_outcome",
        "first_line_start_date", "first_line_end_date",
        "second_line_therapy", "second_line_outcome",
        "second_line_start_date", "second_line_end_date",
    ],
    "treatment_duration": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "second_line_therapy", "second_line_start_date", "second_line_end_date",
        "later_therapy", "later_start_date", "later_end_date",
    ],
    "switching": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "therapy_lines_count",
        "first_line_therapy", "second_line_therapy",
        "later_therapy", "later_therapies",
    ],
    "pathway_sunburst": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "therapy_lines_count",
        "first_line_therapy", "second_line_therapy",
        "later_therapy", "later_therapies",
    ],
    "incidence": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date", "first_line_start_date",
    ],
    "time_to_treatment": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date", "first_line_start_date",
    ],
    "disease_state": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date", "therapy_lines_count", "relapse_count",
        "first_line_start_date", "condition_clinical_status",
    ],
    # All EXPORT_FIELDS for eligibility / cohort_characterization (already includes id)
    "eligibility": list(EXPORT_FIELDS),
    "cohort_characterization": list(EXPORT_FIELDS),
    "pod24": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_start_date", "first_line_end_date", "first_line_outcome",
    ],
    "landmark_response": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_start_date", "first_line_end_date", "first_line_outcome",
    ],
    "pathway_outcomes": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date",
        "first_line_therapy", "first_line_start_date", "first_line_outcome",
        "second_line_therapy", "second_line_start_date", "second_line_outcome",
    ],
    "transformation": [
        "id", "patient_age", "gender", "disease",
        "diagnosis_date", "condition_clinical_status",
        "first_line_therapy", "first_line_start_date", "first_line_outcome",
    ],
    "forest_plot": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "cytogenic_markers", "stem_cell_transplant_history",
        "first_line_therapy", "first_line_outcome",
    ],
    "landmark_survival": [
        "id", "patient_age", "gender", "disease", "stage",
        "diagnosis_date",
        "first_line_therapy", "first_line_start_date", "first_line_end_date",
        "first_line_outcome",
    ],
}


def _csv_stream(qs, fields, max_rows=MAX_EXPORT_ROWS):
    """Yield CSV rows one at a time to avoid loading the full dataset into memory."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    yield buf.getvalue()
    for obj in qs[:max_rows].values(*fields).iterator(chunk_size=2000):
        buf.seek(0)
        buf.truncate()
        row = {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in obj.items()}
        writer.writerow(row)
        yield buf.getvalue()


@api_view(["GET"])
@permission_classes([IsPremiumOrStaff])
@throttle_classes([ChartExportRateThrottle])
def chart_export(request):
    chart = request.query_params.get("chart", "").strip()
    if not chart or chart not in CHART_EXPORT_FIELDS:
        return Response(
            {"detail": f"Unknown chart '{chart}'."},
            status=400,
        )

    file_format = request.query_params.get("file_format", "csv").strip().lower()
    if file_format not in ("csv", "json"):
        return Response(
            {"detail": "file_format must be 'csv' or 'json'."},
            status=400,
        )

    # Apply org scope first so cohort filters operate on a pre-scoped queryset,
    # preventing a user-supplied org= param from touching rows outside their org.
    qs = PatientInfo.objects.all()
    qs, err = apply_org_scope(qs, request.user)
    if err:
        return err
    qs = apply_cohort_filters(request, qs=qs)

    fields = CHART_EXPORT_FIELDS[chart]

    if file_format == "json":
        rows = []
        for obj in qs[:MAX_JSON_ROWS].values(*fields).iterator(chunk_size=2000):
            row = {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in obj.items()}
            rows.append(row)
        return JsonResponse({"rows": rows})

    # CSV — stream row-by-row
    response = StreamingHttpResponse(
        _csv_stream(qs, fields),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f'attachment; filename="chart-{chart}.csv"'
    return response
