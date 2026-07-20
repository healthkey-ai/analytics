import datetime
from metrics.services.pod24 import compute, _classify, POD24_MONTHS

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
        "second_line_end_date": None,
        "second_line_outcome": None,
        "later_end_date": None,
        "later_outcome": None,
        "second_line_start_date": None,
        "death_date": None,
        "last_treatment": None,
    }
    row.update(overrides)
    return row


def _months_after(start, months):
    return start + datetime.timedelta(days=int(months * 30.44))


# ---------------------------------------------------------------------------
# _classify — group boundaries
# ---------------------------------------------------------------------------

def test_pd_within_24_months_is_pod24():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, 12),
        first_line_outcome="Progressive Disease",
    )
    assert _classify(row) == "pod24"


def test_pd_exactly_at_24_months_is_pod24():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, POD24_MONTHS),
        first_line_outcome="Progressive Disease",
    )
    assert _classify(row) == "pod24"


def test_pd_after_24_months_is_no_pod24():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_end_date=_months_after(start, 30),
        first_line_outcome="Progressive Disease",
    )
    assert _classify(row) == "no_pod24"


def test_second_line_start_counts_as_progression():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        second_line_start_date=_months_after(start, 18),
    )
    assert _classify(row) == "pod24"


def test_death_within_window_is_pod24():
    start = D(2023, 1, 1)
    row = _row(first_line_start_date=start, death_date=_months_after(start, 10))
    assert _classify(row) == "pod24"


def test_no_event_with_sufficient_follow_up_is_no_pod24():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_outcome="Complete Response",
        last_treatment=_months_after(start, 36),
    )
    assert _classify(row) == "no_pod24"


def test_censored_before_24_months_is_unevaluable():
    start = D(2023, 1, 1)
    row = _row(
        first_line_start_date=start,
        first_line_outcome="Complete Response",
        last_treatment=_months_after(start, 12),
    )
    assert _classify(row) == "unevaluable"


def test_missing_first_line_start_is_unevaluable():
    assert _classify(_row(death_date=D(2024, 1, 1))) == "unevaluable"


# ---------------------------------------------------------------------------
# compute — structure, counts, KM output
# ---------------------------------------------------------------------------

def test_compute_structure_and_counts():
    start = D(2022, 1, 1)
    rows = [
        # 2 POD24
        _row(first_line_start_date=start,
             first_line_end_date=_months_after(start, 12),
             first_line_outcome="Progressive Disease",
             death_date=_months_after(start, 30)),
        _row(first_line_start_date=start,
             second_line_start_date=_months_after(start, 20),
             death_date=_months_after(start, 40)),
        # 1 no POD24
        _row(first_line_start_date=start,
             first_line_outcome="Complete Response",
             last_treatment=_months_after(start, 48)),
        # 1 unevaluable
        _row(first_line_start_date=start,
             last_treatment=_months_after(start, 6)),
    ]
    result = compute(_FakeQS(rows))

    assert result["clock_start"] == "first_line_start_date"
    assert result["window_months"] == POD24_MONTHS

    groups = {g["key"]: g for g in result["groups"]}
    assert groups["pod24"]["count"] == 2
    assert groups["no_pod24"]["count"] == 1
    assert groups["unevaluable"]["count"] == 1
    # POD24 / no-POD24 pcts are of the classified (evaluable) patients
    assert groups["pod24"]["pct"] == round(2 / 3 * 100, 1)

    assert [line["label"] for line in result["os"]] == ["POD24", "No POD24"]
    assert result["os"][0]["n"] == 2
    assert result["os"][1]["n"] == 1
    for line in result["os"]:
        assert {"curve", "n", "median"} <= set(line)


def test_compute_empty_queryset():
    result = compute(_FakeQS([]))
    groups = {g["key"]: g for g in result["groups"]}
    assert all(g["count"] == 0 for g in groups.values())
    assert all(line["n"] == 0 and line["curve"] == [] for line in result["os"])
    assert result["os_p"] is None
