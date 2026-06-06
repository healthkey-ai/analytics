import csv
import io

from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from patients.models import PatientInfo
from .filters import apply_cohort_filters
from .models import SavedCohort


# Fields excluded from export (PII)
PII_FIELDS = {
    "email", "phone_number", "date_of_birth", "postal_code",
    "city", "facility_name", "person_id", "organization_id",
}

# All non-PII PatientInfo field names
EXPORT_FIELDS = [
    f.name for f in PatientInfo._meta.get_fields()
    if hasattr(f, "column") and f.name not in PII_FIELDS
]


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
    for obj in qs.values(*EXPORT_FIELDS):
        row = {}
        for k, v in obj.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
            else:
                row[k] = v
        rows.append(row)
    return rows


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def saved_cohort_list(request):
    if request.method == "GET":
        cohorts = SavedCohort.objects.filter(user=request.user)
        data = [_cohort_data(c) for c in cohorts]
        return Response(data)

    # POST — create
    name = request.data.get("name", "").strip()
    if not name:
        return Response({"detail": "name is required."}, status=status.HTTP_400_BAD_REQUEST)
    filters = request.data.get("filters")
    if not isinstance(filters, dict):
        return Response({"detail": "filters must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)
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
            cohort.name = request.data["name"]
        if "description" in request.data:
            cohort.description = request.data["description"]
        if "filters" in request.data:
            cohort.filters = request.data["filters"]
        cohort.save()
        return Response(_cohort_data(cohort))

    # DELETE
    cohort.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def saved_cohort_export(request, pk):
    try:
        cohort = SavedCohort.objects.get(pk=pk, user=request.user)
    except SavedCohort.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    fake_req = _FakeRequest(cohort.filters)
    qs = apply_cohort_filters(fake_req)
    fmt = request.query_params.get("format", "csv")

    if fmt == "json":
        rows = _serialize_qs(qs)
        return JsonResponse(rows, safe=False)

    # CSV
    rows = _serialize_qs(qs)
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("")

    filename = f"cohort-{cohort.name.replace(' ', '_')}.csv"
    response = HttpResponse(buf.getvalue(), content_type="text/csv")
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
