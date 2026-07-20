import datetime
from metrics.services.landmark_response import compute, LANDMARK_MONTHS

D = datetime.date


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def _row(**overrides):
    row = {
        "first_line_start_date": None,
        "first_line_end_date": None,
        "first_line_outcome": None,
        "death_date": None,
        "last_treatment": None,
    }
    row.update(overrides)
    return row


def _months_after(start, months):
    return start + datetime.timedelta(days=int(months * 30.44))


def _landmarks_by_month(result):
    return {e["months"]: e for e in result["landmarks"]}


def test_cr_within_window_counts():
    start = D(2022, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, 6),
        first_line_outcome="Complete Response",
    )
    result = compute(_FakeQS([row]))
    lm = _landmarks_by_month(result)

    # CR at 6 months counts at every landmark >= 6 months
    assert all(entry["cr_count"] == 1 for entry in result["landmarks"])
    assert all(entry["evaluable"] == 1 for entry in result["landmarks"])
    assert lm[30]["pct"] == 100.0


def test_cr_after_12_but_before_30_months():
    start = D(2022, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, 20),
        first_line_outcome="Complete Response",
    )
    lm = _landmarks_by_month(compute(_FakeQS([row])))

    assert lm[12]["cr_count"] == 0
    assert lm[24]["cr_count"] == 1
    assert lm[30]["cr_count"] == 1
    assert lm[36]["cr_count"] == 1


def test_non_cr_outcome_never_counts():
    start = D(2022, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, 6),
        first_line_outcome="Partial Response",
    )
    result = compute(_FakeQS([row]))
    assert all(e["cr_count"] == 0 for e in result["landmarks"])
    # Still evaluable (end date known)
    assert all(e["evaluable"] == 1 for e in result["landmarks"])


def test_unevaluable_without_end_date_or_follow_up():
    start = D(2022, 1, 1)
    row = _row(first_line_start_date=start)  # no end, no follow-up
    result = compute(_FakeQS([row]))
    assert all(e["evaluable"] == 0 for e in result["landmarks"])
    assert all(e["pct"] == 0 for e in result["landmarks"])


def test_evaluable_via_long_follow_up_without_end_date():
    start = D(2022, 1, 1)
    row = _row(
        first_line_start_date=start,
        last_treatment=_months_after(start, 40),
    )
    lm = _landmarks_by_month(compute(_FakeQS([row])))
    assert all(e["evaluable"] == 1 for e in lm.values())


def test_short_follow_up_only_evaluable_at_early_landmarks():
    start = D(2022, 1, 1)
    row = _row(
        first_line_start_date=start,
        last_treatment=_months_after(start, 15),
    )
    lm = _landmarks_by_month(compute(_FakeQS([row])))
    assert lm[12]["evaluable"] == 1
    assert lm[24]["evaluable"] == 0
    assert lm[30]["evaluable"] == 0


def test_missing_start_date_skipped():
    row = _row(first_line_end_date=D(2023, 1, 1), first_line_outcome="Complete Response")
    result = compute(_FakeQS([row]))
    assert all(e["evaluable"] == 0 for e in result["landmarks"])


def test_structure_and_clock_start():
    result = compute(_FakeQS([]))
    assert result["clock_start"] == "first_line_start_date"
    assert [e["months"] for e in result["landmarks"]] == LANDMARK_MONTHS
