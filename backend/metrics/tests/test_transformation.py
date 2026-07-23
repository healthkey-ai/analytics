import datetime
from unittest.mock import MagicMock, patch

from metrics.services.transformation import compute

D = datetime.date


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def _row(**overrides):
    row = {
        "transformed_to_dlbcl": None,
        "dlbcl_transformation_date": None,
        "post_transformation_outcome": None,
        "diagnosis_date": None,
        "death_date": None,
        "last_treatment": None,
    }
    row.update(overrides)
    return row


def _months_after(start, months):
    return start + datetime.timedelta(days=int(months * 30.44))


def _transformed(months_to_transform=24, outcome="Complete Response", death_after=None, last_after=None):
    dx = D(2020, 1, 1)
    tx = _months_after(dx, months_to_transform)
    return _row(
        transformed_to_dlbcl=True,
        dlbcl_transformation_date=tx,
        post_transformation_outcome=outcome,
        diagnosis_date=dx,
        death_date=_months_after(tx, death_after) if death_after else None,
        last_treatment=_months_after(tx, last_after) if last_after else None,
    )


# ---------------------------------------------------------------------------
# Counts — how many transformed
# ---------------------------------------------------------------------------

def test_counts_transformed_and_pct():
    rows = [
        _transformed(),
        _transformed(),
        _row(transformed_to_dlbcl=False),
        _row(transformed_to_dlbcl=False),
    ]
    result = compute(_FakeQS(rows))

    assert result["evaluable"] == 4
    assert result["transformed_count"] == 2
    assert result["transformed_pct"] == 50.0


def test_null_flags_are_unknown_not_evaluable():
    """Patients without a documented transformation status are NOT in the
    denominator — like unevaluable cytogenetics, they must not dilute the rate."""
    rows = [
        _transformed(),
        _row(transformed_to_dlbcl=None),
        _row(transformed_to_dlbcl=None),
    ]
    result = compute(_FakeQS(rows))

    assert result["evaluable"] == 1
    assert result["unknown"] == 2
    assert result["transformed_pct"] == 100.0


def test_empty_queryset():
    result = compute(_FakeQS([]))
    assert result["evaluable"] == 0
    assert result["transformed_count"] == 0
    assert result["transformed_pct"] == 0
    assert result["os_post_transformation"]["n"] == 0
    assert result["outcome_distribution"] == []


# ---------------------------------------------------------------------------
# When — time from diagnosis to transformation
# ---------------------------------------------------------------------------

def test_time_to_transformation_median_and_histogram():
    rows = [
        _transformed(months_to_transform=10),
        _transformed(months_to_transform=20),
        _transformed(months_to_transform=30),
        _transformed(months_to_transform=70),
    ]
    result = compute(_FakeQS(rows))
    ttt = result["time_to_transformation"]

    assert ttt["n"] == 4
    assert ttt["median_months"] == 25.0

    hist = {b["label"]: b["count"] for b in ttt["histogram"]}
    assert hist["0–12"] == 1
    assert hist["12–24"] == 1
    assert hist["24–36"] == 1
    assert hist["60+"] == 1


def test_transformation_without_dates_excluded_from_timing():
    rows = [_row(transformed_to_dlbcl=True)]  # flag set, no dates
    result = compute(_FakeQS(rows))

    assert result["transformed_count"] == 1
    assert result["time_to_transformation"]["n"] == 0
    assert result["time_to_transformation"]["median_months"] is None


# ---------------------------------------------------------------------------
# How they did afterward — outcomes + OS
# ---------------------------------------------------------------------------

def test_outcome_distribution_uses_promop_vocabulary_titles():
    """PROMOP stores long-form titles (migration 0115 vocabulary) — the
    distribution must bucket on those, not abbreviations."""
    rows = [
        _transformed(outcome="Complete Response"),
        _transformed(outcome="Complete Response"),
        _transformed(outcome="Partial Response"),
        _transformed(outcome="Progressive Disease"),
        _transformed(outcome="Deceased"),
        _transformed(outcome=None),  # → Unknown
    ]
    result = compute(_FakeQS(rows))
    dist = {o["outcome"]: o for o in result["outcome_distribution"]}

    assert dist["Complete Response"]["count"] == 2
    assert dist["Complete Response"]["pct"] == round(2 / 6 * 100, 1)
    assert dist["Partial Response"]["count"] == 1
    assert dist["Progressive Disease"]["count"] == 1
    assert dist["Deceased"]["count"] == 1
    assert dist["Unknown"]["count"] == 1


def test_unexpected_outcome_string_falls_back_to_unknown():
    rows = [_transformed(outcome="Some Free Text")]
    result = compute(_FakeQS(rows))

    assert result["outcome_distribution"] == [
        {"outcome": "Unknown", "count": 1, "pct": 100.0}
    ]


def test_os_measured_from_transformation_date():
    rows = [_transformed(months_to_transform=24, death_after=18)]
    result = compute(_FakeQS(rows))
    os_res = result["os_post_transformation"]

    assert os_res["n"] == 1
    assert os_res["median"] is not None
    # Event ~18 months after transformation (not from diagnosis)
    event_times = [p["time"] for p in os_res["curve"] if p["time"] > 0]
    assert len(event_times) == 1
    assert abs(event_times[0] - 18.0) < 0.5


def test_os_censored_at_last_treatment_when_alive():
    rows = [_transformed(months_to_transform=24, last_after=12)]
    result = compute(_FakeQS(rows))
    os_res = result["os_post_transformation"]

    assert os_res["n"] == 1
    assert os_res["median"] is None  # censored, no event


def test_os_skips_transformed_without_dates():
    rows = [_row(transformed_to_dlbcl=True)]
    result = compute(_FakeQS(rows))
    assert result["os_post_transformation"]["n"] == 0


def test_death_before_transformation_date_excluded():
    """Contradictory record (derived transformation date postdates death) must
    be excluded, not censored as alive in the KM curve."""
    tx = D(2022, 1, 1)
    row = _row(
        transformed_to_dlbcl=True,
        dlbcl_transformation_date=tx,
        diagnosis_date=D(2020, 1, 1),
        death_date=D(2021, 6, 1),          # before transformation
        last_treatment=D(2023, 1, 1),      # would otherwise censor
    )
    result = compute(_FakeQS([row]))
    assert result["os_post_transformation"]["n"] == 0


def test_transformation_before_diagnosis_excluded_from_timing():
    row = _row(
        transformed_to_dlbcl=True,
        dlbcl_transformation_date=D(2019, 1, 1),
        diagnosis_date=D(2020, 1, 1),  # transformation predates diagnosis
    )
    result = compute(_FakeQS([row]))
    assert result["time_to_transformation"]["n"] == 0


def test_histogram_boundary_at_twelve_months():
    """Bins are [lo, hi): 365 days (~11.99 months) lands in '0–12',
    366 days (~12.02 months) lands in '12–24'."""
    dx = D(2020, 1, 1)
    rows = [
        _row(transformed_to_dlbcl=True, diagnosis_date=dx,
             dlbcl_transformation_date=dx + datetime.timedelta(days=365)),
        _row(transformed_to_dlbcl=True, diagnosis_date=dx,
             dlbcl_transformation_date=dx + datetime.timedelta(days=366)),
    ]
    result = compute(_FakeQS(rows))
    hist = {b["label"]: b["count"] for b in result["time_to_transformation"]["histogram"]}
    assert hist["0–12"] == 1
    assert hist["12–24"] == 1


# ---------------------------------------------------------------------------
# Metrics view wiring — transformed patients have DLBCL as their current
# disease, so the plain cohort disease filter excludes them from this chart.
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


def _run_metrics(api_client, disease):
    """GET /api/metrics/ as staff with all payload services mocked out.
    Returns (response, apply_cohort_filters mock, transformation.compute mock)."""
    user = MagicMock()
    user.is_staff = True
    user.is_authenticated = True
    api_client.force_authenticate(user=user)

    fake_qs = MagicMock()
    fake_qs.count.return_value = 5

    service_mocks = {
        name: MagicMock(compute=MagicMock(return_value={}))
        for name in _PAYLOAD_SERVICES
    }
    with patch.multiple("metrics.views", **service_mocks,
                        landmark_os_km=MagicMock(return_value={})), \
         patch("metrics.views.apply_cohort_filters", return_value=fake_qs) as mock_acf:
        resp = api_client.get(f"{_METRICS_URL}?disease={disease}")
    return resp, mock_acf, service_mocks["transformation"].compute


def test_fl_request_broadens_transformation_queryset(api_client):
    """The view must rebuild the transformation queryset with
    include_transformed=True — otherwise transformed patients (recorded with
    DLBCL as current disease) can never appear in their own chart."""
    resp, mock_acf, t_compute = _run_metrics(api_client, "Follicular+Lymphoma")

    assert resp.status_code == 200
    assert "transformation" in resp.data
    calls = mock_acf.call_args_list
    assert calls[0].kwargs == {}                              # main cohort — unbroadened
    assert calls[1].kwargs == {"include_transformed": True}   # transformation — broadened
    assert t_compute.call_count == 1


def test_non_fl_request_skips_transformation(api_client):
    resp, mock_acf, t_compute = _run_metrics(api_client, "Multiple+Myeloma")

    assert resp.status_code == 200
    assert "transformation" not in resp.data
    t_compute.assert_not_called()
    assert all(c.kwargs == {} for c in mock_acf.call_args_list)
