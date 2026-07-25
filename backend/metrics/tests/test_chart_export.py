"""
Tests for GET /api/export/?chart=<key>&file_format=csv|json

JSON is supported via direct API access but is not offered in the UI.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from django.urls import reverse

from cohorts.saved_views import EXPORT_FIELDS as _SAFE_EXPORT_FIELDS
from metrics.export_views import CHART_EXPORT_FIELDS as _CHART_FIELDS

# Validate at import time that no chart key exposes fields outside the PII allowlist.
_SAFE_SET = set(_SAFE_EXPORT_FIELDS)
for _chart_key, _chart_fields in _CHART_FIELDS.items():
    _unsafe = set(_chart_fields) - _SAFE_SET
    assert not _unsafe, (
        f"CHART_EXPORT_FIELDS['{_chart_key}'] contains fields not in EXPORT_FIELDS "
        f"allowlist: {_unsafe}. Add to EXPORT_FIELDS only after privacy review."
    )

EXPORT_URL = reverse("chart_export")


def _export_url(chart, fmt="csv"):
    return f"{EXPORT_URL}?chart={chart}&file_format={fmt}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_qs_for_export(rows):
    """
    Return a mock queryset that satisfies chart_export's usage pattern:
    qs[:MAX_EXPORT_ROWS].values(*fields).iterator(chunk_size=...)
    and also _csv_stream's qs.values(*fields).iterator(chunk_size=...) call.
    """
    mock_iterator = MagicMock()
    mock_iterator.return_value = iter(rows)

    mock_values = MagicMock()
    mock_values.iterator = mock_iterator

    mock_sliced = MagicMock()
    mock_sliced.values.return_value = mock_values

    mock_qs = MagicMock()
    # Support slicing: qs[:N] returns mock_sliced
    mock_qs.__getitem__ = MagicMock(return_value=mock_sliced)
    # Support _csv_stream's direct qs.values(*fields) call
    mock_qs.values.return_value = mock_values

    return mock_qs


def _patch_apply_cohort_filters(mock_qs):
    return patch("metrics.export_views.apply_cohort_filters", return_value=mock_qs)


def _patch_apply_org_scope(mock_qs):
    return patch(
        "metrics.export_views.apply_org_scope",
        side_effect=lambda qs, user: (qs, None),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user(make_user):
    return make_user(email="staff@example.com", is_staff=True)


@pytest.fixture
def premium_user(make_user):
    return make_user(email="premium@example.com", is_premium=True)


@pytest.fixture
def plain_user(make_user):
    return make_user(email="plain@example.com")


# ---------------------------------------------------------------------------
# Auth / permission tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChartExportPermissions:
    def test_unauthenticated_returns_403(self, api_client):
        resp = api_client.get(_export_url("demographics"))
        assert resp.status_code == 403

    def test_plain_user_denied(self, api_client, plain_user):
        api_client.force_authenticate(user=plain_user)
        resp = api_client.get(_export_url("demographics"))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChartExportValidation:
    def test_unknown_chart_returns_400(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{EXPORT_URL}?chart=garbage")
        assert resp.status_code == 400
        assert "Unknown chart" in resp.data["detail"]

    def test_missing_chart_param_returns_400(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(EXPORT_URL)
        assert resp.status_code == 400

    def test_invalid_file_format_returns_400(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(f"{EXPORT_URL}?chart=demographics&file_format=xml")
        assert resp.status_code == 400
        assert "file_format" in resp.data["detail"]


# ---------------------------------------------------------------------------
# CSV export tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChartExportCSV:
    _SAMPLE_ROWS = [
        {
            "id": "pat-001",
            "patient_age": 65,
            "gender": "M",
            "race": "White",
            "ethnicity": "Non-Hispanic",
            "country": "US",
            "region": "Southeast",
            "smoking_status": "Never",
            "disease": "Multiple Myeloma",
            "diagnosis_date": "2020-01-15",
        }
    ]

    def test_valid_chart_returns_csv_with_headers(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export(self._SAMPLE_ROWS)
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "csv"))
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]

        # Collect streaming content and decode
        content = b"".join(resp.streaming_content).decode()
        first_line = content.splitlines()[0]

        # All demographics fields should appear in the header row (id must be first)
        assert first_line.startswith("id,"), f"Expected 'id' as first column, got: {first_line}"
        for col in ("id", "patient_age", "gender", "race", "ethnicity", "country", "region", "smoking_status", "disease", "diagnosis_date"):
            assert col in first_line, f"Expected column '{col}' in header: {first_line}"

    def test_csv_has_content_disposition_attachment(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export(self._SAMPLE_ROWS)
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "csv"))
        assert "attachment" in resp["Content-Disposition"]
        assert "demographics" in resp["Content-Disposition"]

    def test_empty_cohort_returns_header_only_csv(self, api_client, staff_user):
        """An empty queryset should produce a CSV with only the header row (no crash)."""
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export([])
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "csv"))
        assert resp.status_code == 200
        content = b"".join(resp.streaming_content).decode()
        lines = [l for l in content.splitlines() if l.strip()]
        # Only the header row
        assert len(lines) == 1
        assert "patient_age" in lines[0]

    def test_default_format_is_csv(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export([])
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(f"{EXPORT_URL}?chart=demographics")
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]


# ---------------------------------------------------------------------------
# JSON export tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChartExportJSON:
    _SAMPLE_ROWS = [
        {
            "id": "pat-002",
            "patient_age": 72,
            "gender": "F",
            "race": "Asian",
            "ethnicity": "Non-Hispanic",
            "country": "US",
            "region": "West",
            "smoking_status": "Former",
            "disease": "Follicular Lymphoma",
            "diagnosis_date": "2019-06-01",
        }
    ]

    def test_valid_chart_returns_json(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export(self._SAMPLE_ROWS)
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "json"))
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert "rows" in data
        assert isinstance(data["rows"], list)

    def test_json_rows_contain_expected_fields(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export(self._SAMPLE_ROWS)
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "json"))
        data = json.loads(resp.content)
        assert len(data["rows"]) == 1
        row = data["rows"][0]
        assert row["patient_age"] == 72
        assert row["disease"] == "Follicular Lymphoma"

    def test_empty_cohort_returns_empty_rows_json(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export([])
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "json"))
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["rows"] == []

    def test_premium_user_can_access_json_export(self, api_client, premium_user):
        api_client.force_authenticate(user=premium_user)
        mock_qs = _mock_qs_for_export(self._SAMPLE_ROWS)
        with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
            resp = api_client.get(_export_url("demographics", "json"))
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Smoke test — each chart key should return 200
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChartExportAllCharts:
    """Verify every chart key in CHART_EXPORT_FIELDS is accepted."""

    def test_all_chart_keys_return_200(self, api_client, staff_user):
        from unittest.mock import patch
        from metrics.export_views import CHART_EXPORT_FIELDS, ChartExportRateThrottle

        api_client.force_authenticate(user=staff_user)
        mock_qs = _mock_qs_for_export([])

        # Disable rate limiting so all chart keys can be tested in a single run
        with patch.object(ChartExportRateThrottle, "allow_request", return_value=True):
            for chart_key in CHART_EXPORT_FIELDS:
                with _patch_apply_cohort_filters(mock_qs), _patch_apply_org_scope(mock_qs):
                    resp = api_client.get(_export_url(chart_key, "csv"))
                assert resp.status_code == 200, (
                    f"chart='{chart_key}' returned {resp.status_code}"
                )
