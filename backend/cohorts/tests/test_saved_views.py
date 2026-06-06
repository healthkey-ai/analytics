import json
from unittest.mock import MagicMock, patch

import pytest

from cohorts.models import SavedCohort

SAVED_URL = "/api/cohorts/saved/"


def detail_url(pk):
    return f"/api/cohorts/saved/{pk}/"


def export_url(pk, fmt="csv"):
    return f"/api/cohorts/saved/{pk}/export/?file_format={fmt}"


@pytest.fixture
def user(make_user):
    return make_user(email="owner@example.com")


@pytest.fixture
def other_user(make_user):
    return make_user(email="other@example.com")


@pytest.fixture
def cohort(db, user):
    return SavedCohort.objects.create(
        user=user,
        name="ISS Stage I",
        description="Stage 1 patients",
        filters={"disease": "Multiple Myeloma", "stage": ["ISS Stage I"]},
    )


def _mock_export_qs(rows):
    """Return a mock queryset that satisfies saved_views._serialize_qs()."""
    mock_values = MagicMock()
    mock_values.iterator.return_value = iter(rows)
    mock_qs = MagicMock()
    mock_qs.__getitem__ = MagicMock(return_value=mock_qs)
    mock_qs.values.return_value = mock_values
    return mock_qs


# ── List / Create ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSavedCohortList:
    def test_unauthenticated_returns_403(self, api_client):
        resp = api_client.get(SAVED_URL)
        assert resp.status_code == 403

    def test_list_returns_only_own_cohorts(self, api_client, user, other_user, cohort, db):
        SavedCohort.objects.create(user=other_user, name="Other", description="", filters={})
        api_client.force_authenticate(user=user)
        resp = api_client.get(SAVED_URL)
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["name"] == "ISS Stage I"

    def test_create_cohort_returns_201(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        payload = {"name": "New Cohort", "description": "desc", "filters": {"disease": "Multiple Myeloma"}}
        resp = api_client.post(SAVED_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.data["name"] == "New Cohort"
        assert SavedCohort.objects.filter(user=user, name="New Cohort").exists()

    def test_create_persists_filters_json(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        filters = {"disease": "Breast Cancer", "stage": ["II", "III"]}
        api_client.post(SAVED_URL, {"name": "BC", "description": "", "filters": filters}, format="json")
        saved = SavedCohort.objects.get(user=user, name="BC")
        assert saved.filters == filters

    def test_create_without_name_returns_400(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"filters": {}}, format="json")
        assert resp.status_code == 400

    def test_create_without_filters_returns_400(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"name": "No Filters"}, format="json")
        assert resp.status_code == 400

    def test_create_with_non_dict_filters_returns_400(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"name": "Bad", "filters": "not-a-dict"}, format="json")
        assert resp.status_code == 400


# ── Detail / Update / Delete ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestSavedCohortDetail:
    def test_get_own_cohort(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.get(detail_url(cohort.pk))
        assert resp.status_code == 200
        assert resp.data["name"] == "ISS Stage I"
        assert resp.data["filters"]["disease"] == "Multiple Myeloma"

    def test_get_other_users_cohort_returns_404(self, api_client, other_user, cohort):
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(detail_url(cohort.pk))
        assert resp.status_code == 404

    def test_update_name(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.put(detail_url(cohort.pk), {"name": "Renamed Cohort"}, format="json")
        assert resp.status_code == 200
        assert resp.data["name"] == "Renamed Cohort"
        cohort.refresh_from_db()
        assert cohort.name == "Renamed Cohort"

    def test_update_filters(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        new_filters = {"disease": "Breast Cancer"}
        resp = api_client.put(detail_url(cohort.pk), {"filters": new_filters}, format="json")
        assert resp.status_code == 200
        cohort.refresh_from_db()
        assert cohort.filters == new_filters

    def test_update_description(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.put(detail_url(cohort.pk), {"description": "Updated notes"}, format="json")
        assert resp.status_code == 200
        cohort.refresh_from_db()
        assert cohort.description == "Updated notes"

    def test_update_other_users_cohort_returns_404(self, api_client, other_user, cohort):
        api_client.force_authenticate(user=other_user)
        resp = api_client.put(detail_url(cohort.pk), {"name": "Hijacked"}, format="json")
        assert resp.status_code == 404
        cohort.refresh_from_db()
        assert cohort.name == "ISS Stage I"

    def test_delete_own_cohort(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.delete(detail_url(cohort.pk))
        assert resp.status_code == 204
        assert not SavedCohort.objects.filter(pk=cohort.pk).exists()

    def test_delete_other_users_cohort_returns_404(self, api_client, other_user, cohort):
        api_client.force_authenticate(user=other_user)
        resp = api_client.delete(detail_url(cohort.pk))
        assert resp.status_code == 404
        assert SavedCohort.objects.filter(pk=cohort.pk).exists()

    def test_unauthenticated_returns_403(self, api_client, cohort):
        resp = api_client.get(detail_url(cohort.pk))
        assert resp.status_code == 403


# ── Export ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSavedCohortExport:
    _SAMPLE_ROWS = [{"id": 1, "patient_age": 65, "gender": "M", "disease": "Multiple Myeloma"}]

    def test_csv_export_returns_csv_content_type(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        mock_qs = _mock_export_qs(self._SAMPLE_ROWS)
        with patch("cohorts.saved_views.apply_cohort_filters", return_value=mock_qs):
            resp = api_client.get(export_url(cohort.pk, "csv"))
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]

    def test_csv_export_has_attachment_header(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        mock_qs = _mock_export_qs(self._SAMPLE_ROWS)
        with patch("cohorts.saved_views.apply_cohort_filters", return_value=mock_qs):
            resp = api_client.get(export_url(cohort.pk, "csv"))
        assert "attachment" in resp["Content-Disposition"]
        assert "ISS_Stage_I" in resp["Content-Disposition"]

    def test_csv_export_contains_header_row(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        mock_qs = _mock_export_qs(self._SAMPLE_ROWS)
        with patch("cohorts.saved_views.apply_cohort_filters", return_value=mock_qs):
            resp = api_client.get(export_url(cohort.pk, "csv"))
        content = b"".join(resp.streaming_content).decode()
        assert "id" in content
        assert "patient_age" in content

    def test_json_export_returns_list(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        mock_qs = _mock_export_qs(self._SAMPLE_ROWS)
        with patch("cohorts.saved_views.apply_cohort_filters", return_value=mock_qs):
            resp = api_client.get(export_url(cohort.pk, "json"))
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert isinstance(data, list)
        assert data[0]["patient_age"] == 65

    def test_export_empty_cohort_returns_empty_csv(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        mock_qs = _mock_export_qs([])
        with patch("cohorts.saved_views.apply_cohort_filters", return_value=mock_qs):
            resp = api_client.get(export_url(cohort.pk, "csv"))
        assert resp.status_code == 200

    def test_export_other_users_cohort_returns_404(self, api_client, other_user, cohort):
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(export_url(cohort.pk, "csv"))
        assert resp.status_code == 404

    def test_export_unauthenticated_returns_403(self, api_client, cohort):
        resp = api_client.get(export_url(cohort.pk, "csv"))
        assert resp.status_code == 403


# ── Filter cardinality ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFilterCardinality:
    def test_create_with_list_at_limit_returns_201(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        filters = {"stage": ["I", "II", "III", "IV", "A", "B", "C", "D", "E", "F"]}  # 10
        resp = api_client.post(SAVED_URL, {"name": "OK", "filters": filters}, format="json")
        assert resp.status_code == 201

    def test_create_with_list_exceeding_limit_returns_400(self, api_client, user, db):
        api_client.force_authenticate(user=user)
        filters = {"stage": ["I", "II", "III", "IV", "A", "B", "C", "D", "E", "F", "G"]}  # 11
        resp = api_client.post(SAVED_URL, {"name": "Too many", "filters": filters}, format="json")
        assert resp.status_code == 400
        assert "stage" in resp.data["detail"]

    def test_update_with_list_exceeding_limit_returns_400(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.put(detail_url(cohort.pk), {"filters": {"stage": ["a"] * 11}}, format="json")
        assert resp.status_code == 400

    def test_update_with_list_at_limit_returns_200(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        resp = api_client.put(detail_url(cohort.pk), {"filters": {"stage": ["a"] * 10}}, format="json")
        assert resp.status_code == 200


# ── Cohort cap ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCohortCap:
    def test_eleventh_cohort_is_rejected(self, api_client, user, db):
        for i in range(10):
            SavedCohort.objects.create(user=user, name=f"Cohort {i}", filters={})
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"name": "One too many", "filters": {}}, format="json")
        assert resp.status_code == 400
        assert "limit" in resp.data["detail"].lower()

    def test_tenth_cohort_succeeds(self, api_client, user, db):
        for i in range(9):
            SavedCohort.objects.create(user=user, name=f"Cohort {i}", filters={})
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"name": "Tenth", "filters": {"disease": "MM"}}, format="json")
        assert resp.status_code == 201

    def test_cap_is_per_user(self, api_client, user, other_user, db):
        for i in range(10):
            SavedCohort.objects.create(user=other_user, name=f"Cohort {i}", filters={})
        api_client.force_authenticate(user=user)
        resp = api_client.post(SAVED_URL, {"name": "My first", "filters": {}}, format="json")
        assert resp.status_code == 201


# ── Export throttle ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestExportThrottle:
    def test_throttled_export_returns_429(self, api_client, user, cohort):
        api_client.force_authenticate(user=user)
        with patch("cohorts.saved_views.ExportRateThrottle.allow_request", return_value=False), \
             patch("cohorts.saved_views.ExportRateThrottle.wait", return_value=3600):
            resp = api_client.get(export_url(cohort.pk, "csv"))
        assert resp.status_code == 429
