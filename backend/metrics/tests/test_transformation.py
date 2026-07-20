import datetime
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


def _transformed(months_to_transform=24, outcome="CR", death_after=None, last_after=None):
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

def test_outcome_distribution():
    rows = [
        _transformed(outcome="CR"),
        _transformed(outcome="CR"),
        _transformed(outcome="PD"),
        _transformed(outcome="Deceased"),
        _transformed(outcome=None),  # → Unknown
    ]
    result = compute(_FakeQS(rows))
    dist = {o["outcome"]: o for o in result["outcome_distribution"]}

    assert dist["CR"]["count"] == 2
    assert dist["CR"]["pct"] == 40.0
    assert dist["PD"]["count"] == 1
    assert dist["Deceased"]["count"] == 1
    assert dist["Unknown"]["count"] == 1


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
