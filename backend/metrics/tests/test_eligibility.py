"""Tests for the eligibility / feasibility counts service and its wiring
into the metrics endpoint."""
from unittest.mock import MagicMock, patch

from metrics.services.eligibility import compute


def _request():
    return MagicMock()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

def test_compute_returns_funnel_structure():
    base = MagicMock()
    base.count.return_value = 1000
    final = MagicMock()
    final.count.return_value = 250

    with patch("metrics.services.eligibility.apply_org_scope", return_value=(base, None)), \
         patch("metrics.services.eligibility.apply_cohort_filters", return_value=final) as acf:
        result = compute(_request())

    assert result["total"] == 1000
    assert result["eligible"] == 250
    assert result["eligible_pct"] == 25.0
    assert result["steps"][0] == {"key": "all", "label": "All patients", "count": 1000}
    _, kwargs = acf.call_args
    assert kwargs["qs"] is base
    assert isinstance(kwargs["funnel"], list)


def test_compute_returns_none_when_org_scope_denies():
    denial = MagicMock()
    with patch("metrics.services.eligibility.apply_org_scope", return_value=(None, denial)):
        assert compute(_request()) is None


def test_eligible_pct_zero_when_population_empty():
    base = MagicMock()
    base.count.return_value = 0
    final = MagicMock()
    final.count.return_value = 0

    with patch("metrics.services.eligibility.apply_org_scope", return_value=(base, None)), \
         patch("metrics.services.eligibility.apply_cohort_filters", return_value=final):
        result = compute(_request())

    assert result["total"] == 0
    assert result["eligible_pct"] == 0


# ---------------------------------------------------------------------------
# Metrics view wiring
# ---------------------------------------------------------------------------

_METRICS_URL = "/api/metrics/"

_PAYLOAD_SERVICES = [
    "response_rates", "treatment_patterns", "demographics", "staging", "labs",
    "treatment_duration", "survival", "ttnt", "switching", "pathway_sunburst",
    "dor", "cohort_characterization", "incidence", "time_to_treatment",
    "disease_state", "therapy_categories", "pod24", "landmark_response",
    "pathway_outcomes", "subgroup_survival", "forest_plot", "transformation",
    "eligibility",
]


def _staff_client(api_client):
    user = MagicMock()
    user.is_staff = True
    user.is_authenticated = True
    api_client.force_authenticate(user=user)
    return api_client


def test_metrics_includes_eligibility_in_payload(api_client):
    _staff_client(api_client)
    fake_qs = MagicMock()
    fake_qs.count.return_value = 5
    elig_value = {"total": 100, "eligible": 5, "eligible_pct": 5.0, "steps": []}

    service_mocks = {
        name: MagicMock(compute=MagicMock(return_value={}))
        for name in _PAYLOAD_SERVICES
    }
    service_mocks["eligibility"] = MagicMock(compute=MagicMock(return_value=elig_value))
    with patch.multiple("metrics.views", **service_mocks,
                        landmark_os_km=MagicMock(return_value={})), \
         patch("metrics.views.apply_cohort_filters", return_value=fake_qs):
        resp = api_client.get(f"{_METRICS_URL}?disease=Multiple+Myeloma")

    assert resp.status_code == 200
    assert resp.data["eligibility"] == elig_value
    service_mocks["eligibility"].compute.assert_called_once()


def test_metrics_includes_eligibility_when_cohort_empty(api_client):
    """An empty cohort is a valid feasibility answer — the funnel must still
    be returned so the UI can show where the population dropped off."""
    _staff_client(api_client)
    fake_qs = MagicMock()
    fake_qs.count.return_value = 0
    elig_value = {"total": 100, "eligible": 0, "eligible_pct": 0,
                  "steps": [{"key": "all", "label": "All patients", "count": 100}]}

    with patch("metrics.views.apply_cohort_filters", return_value=fake_qs), \
         patch("metrics.views.eligibility") as mock_elig:
        mock_elig.compute.return_value = elig_value
        resp = api_client.get(f"{_METRICS_URL}?disease=Multiple+Myeloma")

    assert resp.status_code == 200
    assert resp.data["cohort"] == {"count": 0}
    assert resp.data["eligibility"] == elig_value
