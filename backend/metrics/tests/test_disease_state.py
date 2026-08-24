import datetime
from metrics.services.disease_state import compute, _classify, STATE_LABELS

D = datetime.date
TODAY = D(2026, 7, 20)


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def _row(**overrides):
    row = {
        "diagnosis_date": None,
        "first_line_start_date": None,
        "first_line_outcome": None,
        "second_line_therapy": None,
        "second_line_outcome": None,
        "later_therapy": None,
        "later_outcome": None,
        "therapy_lines_count": None,
        "relapse_count": None,
    }
    row.update(overrides)
    return row


def _states_by_key(result):
    return {s["key"]: s for s in result["states"]}


# ---------------------------------------------------------------------------
# _classify — one case per state, plus priority ordering
# ---------------------------------------------------------------------------

def test_newly_diagnosed():
    row = _row(diagnosis_date=TODAY - datetime.timedelta(days=60))
    assert _classify(row, TODAY) == "newly_diagnosed"


def test_watch_and_wait():
    row = _row(diagnosis_date=TODAY - datetime.timedelta(days=400))
    assert _classify(row, TODAY) == "watch_and_wait"


def test_in_remission():
    row = _row(
        diagnosis_date=D(2024, 1, 1),
        first_line_start_date=D(2024, 2, 1),
        first_line_outcome="Complete Response",
        therapy_lines_count=1,
    )
    assert _classify(row, TODAY) == "in_remission"


def test_relapsed_via_multiple_lines():
    row = _row(
        diagnosis_date=D(2023, 1, 1),
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Complete Response",
        therapy_lines_count=2,
    )
    assert _classify(row, TODAY) == "relapsed_refractory"


def test_relapsed_via_relapse_count():
    row = _row(
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Partial Response",
        therapy_lines_count=1,
        relapse_count=1,
    )
    assert _classify(row, TODAY) == "relapsed_refractory"


def test_relapsed_via_progressive_disease_outcome():
    row = _row(
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Progressive Disease",
        therapy_lines_count=1,
    )
    assert _classify(row, TODAY) == "relapsed_refractory"


def test_relapsed_via_second_line_data_with_null_lines_count():
    """2L therapy recorded but therapy_lines_count missing must not land in In Remission."""
    row = _row(
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Complete Response",
        second_line_therapy="Lenalidomide and Rituximab (R2)",
        second_line_outcome="Complete Response",
        therapy_lines_count=None,
    )
    assert _classify(row, TODAY) == "relapsed_refractory"


def test_relapse_takes_priority_over_remission():
    """A patient with a PD outcome in a later line must not land in In Remission."""
    row = _row(
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Complete Response",
        second_line_outcome="Progressive Disease",
        therapy_lines_count=2,
    )
    assert _classify(row, TODAY) == "relapsed_refractory"


def test_treated_without_response_is_other():
    row = _row(
        first_line_start_date=D(2023, 2, 1),
        first_line_outcome="Stable Disease",
        therapy_lines_count=1,
    )
    assert _classify(row, TODAY) == "other"


def test_no_data_is_other():
    assert _classify(_row(), TODAY) == "other"


# ---------------------------------------------------------------------------
# compute — structure and totals
# ---------------------------------------------------------------------------

def test_compute_returns_all_states_and_total():
    qs = _FakeQS([
        _row(diagnosis_date=TODAY - datetime.timedelta(days=30)),
        _row(diagnosis_date=TODAY - datetime.timedelta(days=600)),
        _row(first_line_start_date=D(2024, 1, 1), first_line_outcome="Complete Response",
             therapy_lines_count=1),
        _row(therapy_lines_count=3),
    ])
    result = compute(qs, today=TODAY)

    assert [s["key"] for s in result["states"]] == [k for k, _ in STATE_LABELS]
    assert result["total"] == 4
    states = _states_by_key(result)
    assert states["newly_diagnosed"]["count"] == 1
    assert states["watch_and_wait"]["count"] == 1
    assert states["in_remission"]["count"] == 1
    assert states["relapsed_refractory"]["count"] == 1
    assert states["other"]["count"] == 0
    assert sum(s["count"] for s in result["states"]) == result["total"]


def test_compute_empty_queryset():
    result = compute(_FakeQS([]), today=TODAY)
    assert result["total"] == 0
    assert all(s["count"] == 0 and s["pct"] == 0 for s in result["states"])
