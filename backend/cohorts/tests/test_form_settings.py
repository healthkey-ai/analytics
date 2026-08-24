"""Tests for the form_settings endpoint.

Covers: disease_counts aggregation, diseases sort order, Breast Cancer FHIR
normalisation, org= scoping, and the auth/visibility guard.

PatientInfo is managed=False and not available in the test DB, so all DB
calls on that model are intercepted by _patch_pi.
"""
from unittest.mock import MagicMock, patch

import pytest

FORM_SETTINGS_URL = "/api/form-settings/"


@pytest.fixture(autouse=True)
def disable_form_settings_throttling(monkeypatch):
    from cohorts.views import form_settings
    monkeypatch.setattr(form_settings.cls, "throttle_classes", [])


class _ChainableList(list):
    """A list that supports the .distinct() queryset chain."""

    def distinct(self):
        return self


class _FakePatientQS:
    """Minimal queryset that satisfies the PatientInfo chains used in form_settings.

    Query chains the view makes:
      1. PatientInfo.objects.filter(...).filter(...).exclude(...).values_list(field, flat=True).distinct()
         → used for regions and races
      2. PatientInfo.objects.exclude(...).filter(...).values("disease").annotate(cnt=Count("id"))
         → used for disease_counts; __iter__ yields {"disease": ..., "cnt": ...} rows
    """

    def __init__(self, disease_rows=None, regions=None, races=None, stages=None):
        self._disease_rows = disease_rows or []
        self._regions = regions or []
        self._races = races or []
        self._stages = stages or []

    def filter(self, *args, **kwargs):
        return self

    def exclude(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def order_by(self, *args):
        return self

    def values_list(self, *fields, flat=False):
        field = fields[0] if fields else None
        if field == "region":
            return _ChainableList(self._regions)
        if field == "race":
            return _ChainableList(self._races)
        if field == "stage":
            return _ChainableList(self._stages)
        return _ChainableList([])

    def values(self, *fields):
        return self

    def annotate(self, **kwargs):
        # Return the disease_rows list; the view iterates over it directly.
        return self._disease_rows

    def __iter__(self):
        return iter(self._disease_rows)


def _patch_pi(disease_rows, regions=None, races=None, stages=None):
    """Return a context manager that patches PatientInfo in cohorts.views."""
    fake = _FakePatientQS(disease_rows, regions or [], races or [], stages or [])
    mock_pi = MagicMock()
    mock_pi.objects.filter.return_value = fake
    mock_pi.objects.exclude.return_value = fake
    return patch("cohorts.views.PatientInfo", mock_pi)


def _mock_user(email="reviewer@example.com"):
    user = MagicMock()
    user.is_authenticated = True
    user.is_staff = False
    user.email = email
    return user


# ── Disease counts ─────────────────────────────────────────────────────────────

class TestFormSettingsDiseaseCounts:
    """disease_counts aggregation, sorting, and FHIR normalisation."""

    def test_returns_disease_counts_dict(self, api_client):
        rows = [
            {"disease": "Multiple Myeloma", "cnt": 50},
            {"disease": "Breast Cancer", "cnt": 20},
        ]
        with _patch_pi(rows):
            resp = api_client.get(FORM_SETTINGS_URL)
        assert resp.status_code == 200
        assert resp.data["disease_counts"]["Multiple Myeloma"] == 50
        assert resp.data["disease_counts"]["Breast Cancer"] == 20

    def test_diseases_list_sorted_by_count_descending(self, api_client):
        rows = [
            {"disease": "Breast Cancer", "cnt": 100},
            {"disease": "Multiple Myeloma", "cnt": 40},
        ]
        with _patch_pi(rows):
            resp = api_client.get(FORM_SETTINGS_URL)
        assert resp.data["diseases"] == ["Breast Cancer", "Multiple Myeloma"]

    def test_fhir_breast_cancer_variants_merge_into_one_canonical_key(self, api_client):
        """'ER|ERBB2 Breast cancer', 'Invasive breast cancer', etc. all → 'Breast Cancer'."""
        rows = [
            {"disease": "Breast Cancer", "cnt": 60},
            {"disease": "ER|ERBB2 Breast cancer", "cnt": 15},
            {"disease": "Invasive breast cancer", "cnt": 10},
        ]
        with _patch_pi(rows):
            resp = api_client.get(FORM_SETTINGS_URL)
        counts = resp.data["disease_counts"]
        assert counts.get("Breast Cancer") == 85
        assert "ER|ERBB2 Breast cancer" not in counts
        assert "Invasive breast cancer" not in counts

    def test_case_variants_merge_into_canonical_disease_name(self, api_client):
        """'Follicular Lymphoma' and 'Follicular lymphoma' → one canonical entry."""
        rows = [
            {"disease": "Follicular Lymphoma", "cnt": 711},
            {"disease": "Follicular lymphoma", "cnt": 270},
        ]
        with _patch_pi(rows):
            resp = api_client.get(FORM_SETTINGS_URL)
        counts = resp.data["disease_counts"]
        assert counts.get("Follicular Lymphoma") == 981
        assert "Follicular lymphoma" not in counts
        assert resp.data["diseases"] == ["Follicular Lymphoma"]

    def test_empty_patient_table_returns_empty_counts_and_diseases(self, api_client):
        with _patch_pi([]):
            resp = api_client.get(FORM_SETTINGS_URL)
        assert resp.status_code == 200
        assert resp.data["disease_counts"] == {}
        assert resp.data["diseases"] == []

    def test_response_includes_required_form_fields(self, api_client):
        with _patch_pi([]):
            resp = api_client.get(FORM_SETTINGS_URL)
        for field in ("diseases", "disease_counts", "stages", "outcome_options",
                      "regions", "race_options"):
            assert field in resp.data, f"Missing field in response: {field}"

    def test_stage_options_use_actual_db_values_when_present(self, api_client):
        rows = [{"disease": "Breast Cancer", "cnt": 20}]
        with _patch_pi(rows, stages=["Stage IIA", "Stage 2 (qualifier value)", "IIIB"]):
            resp = api_client.get(FORM_SETTINGS_URL + "?disease=Breast+Cancer")
        assert resp.status_code == 200
        assert resp.data["stages"] == ["Stage II", "Stage IIA", "Stage IIIB"]

    def test_single_disease_count_equals_total_patients(self, api_client):
        rows = [{"disease": "Multiple Myeloma", "cnt": 123}]
        with _patch_pi(rows):
            resp = api_client.get(FORM_SETTINGS_URL)
        assert resp.data["disease_counts"]["Multiple Myeloma"] == 123
        assert resp.data["diseases"] == ["Multiple Myeloma"]


# ── Org scoping and auth guard ─────────────────────────────────────────────────

class TestFormSettingsOrgAuth:
    """org= parameter requires authentication and org visibility."""

    def test_unauthenticated_request_with_org_returns_401(self, api_client):
        resp = api_client.get(FORM_SETTINGS_URL + "?org=Acme+Hospital")
        assert resp.status_code == 401

    def test_no_org_param_does_not_require_auth(self, api_client):
        """AllowAny behaviour is preserved when org= is absent."""
        with _patch_pi([]):
            resp = api_client.get(FORM_SETTINGS_URL)
        assert resp.status_code == 200

    def test_authenticated_user_for_invisible_org_returns_403(self, api_client):
        api_client.force_authenticate(user=_mock_user())
        with patch("accounts.utils.get_visible_org_names", return_value=["Other Org"]):
            resp = api_client.get(FORM_SETTINGS_URL + "?org=Acme+Hospital")
        assert resp.status_code == 403

    def test_authenticated_user_for_visible_org_returns_200(self, api_client):
        api_client.force_authenticate(user=_mock_user())
        rows = [{"disease": "Multiple Myeloma", "cnt": 30}]
        with patch("accounts.utils.get_visible_org_names", return_value=["Acme Hospital"]):
            with _patch_pi(rows):
                resp = api_client.get(FORM_SETTINGS_URL + "?org=Acme+Hospital")
        assert resp.status_code == 200
        assert resp.data["disease_counts"]["Multiple Myeloma"] == 30

    def test_org_with_no_patients_returns_empty_counts(self, api_client):
        api_client.force_authenticate(user=_mock_user())
        with patch("accounts.utils.get_visible_org_names", return_value=["Ghost Org"]):
            with _patch_pi([]):
                resp = api_client.get(FORM_SETTINGS_URL + "?org=Ghost+Org")
        assert resp.status_code == 200
        assert resp.data["disease_counts"] == {}

    def test_org_scoped_counts_are_independent_of_global_counts(self, api_client):
        """Counts returned when org= is set reflect only that org's patients."""
        api_client.force_authenticate(user=_mock_user())
        org_rows = [{"disease": "Breast Cancer", "cnt": 7}]
        with patch("accounts.utils.get_visible_org_names", return_value=["Small Clinic"]):
            with _patch_pi(org_rows):
                resp = api_client.get(FORM_SETTINGS_URL + "?org=Small+Clinic")
        assert resp.data["disease_counts"] == {"Breast Cancer": 7}
        assert resp.data["diseases"] == ["Breast Cancer"]
