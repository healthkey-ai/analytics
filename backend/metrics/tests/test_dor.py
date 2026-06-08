import datetime
import pytest
from metrics.services.dor import compute, _dor_times_events

D = datetime.date


class _FakeQS:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *args, **kwargs):
        return self

    def exclude(self, *args, **kwargs):
        if not kwargs:
            return self
        rows = self._rows
        for key, val in kwargs.items():
            if key.endswith("__isnull"):
                field = key[: -len("__isnull")]
                rows = [r for r in rows if (r.get(field) is None) != val]
            elif key.endswith("__exact"):
                field = key[: -len("__exact")]
                rows = [r for r in rows if r.get(field) != val]
            else:
                rows = [r for r in rows if r.get(key) != val]
        return _FakeQS(rows)

    def values(self, *fields):
        if not fields:
            return self._rows
        return [{f: r.get(f) for f in fields} for r in self._rows]


def _row(
    first_line_therapy=None,
    first_line_start=None,
    first_line_outcome=None,
    second_line_therapy=None,
    second_line_start=None,
    second_line_outcome=None,
    later_start=None,
    death=None,
    last_tx=None,
):
    return {
        "first_line_therapy":    first_line_therapy,
        "first_line_start_date": first_line_start,
        "first_line_outcome":    first_line_outcome,
        "second_line_therapy":   second_line_therapy,
        "second_line_start_date": second_line_start,
        "second_line_outcome":   second_line_outcome,
        "later_start_date":      later_start,
        "death_date":            death,
        "last_treatment":        last_tx,
    }


# ---------------------------------------------------------------------------
# _dor_times_events
# ---------------------------------------------------------------------------

def test_dor_happy_path_responders():
    """Responders with next-line start produce events with correct polarity."""
    rows = [
        _row("RVd", D(2020, 1, 1), "Partial Response",
             second_line_start=D(2021, 6, 1), last_tx=D(2022, 1, 1)),
        _row("RVd", D(2020, 1, 1), "Complete Response",
             second_line_start=D(2022, 1, 1), last_tx=D(2023, 1, 1)),
    ]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 2
    assert all(event for _, event in te), "both rows should be events"


def test_dor_non_responders_excluded():
    """PD, SD, 'PD', 'SD' shorthand all excluded; only PR makes it through."""
    rows = [
        _row("RVd", D(2020, 1, 1), "Progressive Disease",
             second_line_start=D(2021, 1, 1)),
        _row("RVd", D(2020, 1, 1), "Stable Disease",
             second_line_start=D(2021, 1, 1)),
        _row("RVd", D(2020, 1, 1), "SD",
             second_line_start=D(2021, 1, 1)),
        _row("RVd", D(2020, 1, 1), "PD",
             second_line_start=D(2021, 1, 1)),
        _row("RVd", D(2020, 1, 1), "Partial Response",
             second_line_start=D(2021, 6, 1), last_tx=D(2022, 1, 1)),
    ]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 1, "only the PR row should be included"


def test_dor_null_outcome_excluded():
    """Null outcome treated as non-response and excluded."""
    rows = [_row("RVd", D(2020, 1, 1), None,
                 second_line_start=D(2021, 6, 1), last_tx=D(2022, 1, 1))]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 0


def test_dor_missing_start_date_skipped():
    """Row without a start date must be silently skipped."""
    rows = [_row("RVd", None, "Partial Response",
                 second_line_start=D(2021, 6, 1))]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 0


def test_dor_death_used_as_event():
    """When no next line, death_date is used as an event (not censor)."""
    rows = [_row("RVd", D(2020, 1, 1), "Complete Response",
                 death=D(2022, 6, 1))]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 1
    duration, event = te[0]
    assert event is True
    assert duration > 0


def test_dor_censored_at_last_treatment():
    """Patient alive, no next line → censored at last_treatment."""
    rows = [_row("RVd", D(2020, 1, 1), "Very Good Partial Response",
                 last_tx=D(2023, 1, 1))]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 1
    _, event = te[0]
    assert event is False


def test_dor_next_line_before_death_is_event():
    """Next-line start is earlier than death → next line is the event."""
    rows = [_row("RVd", D(2020, 1, 1), "Partial Response",
                 second_line_start=D(2021, 6, 1),
                 death=D(2023, 1, 1),
                 last_tx=D(2023, 1, 1))]
    qs = _FakeQS(rows)
    te = _dor_times_events(qs, "first_line_start_date", "first_line_outcome",
                           "second_line_start_date")
    assert len(te) == 1
    duration, event = te[0]
    expected = (D(2021, 6, 1) - D(2020, 1, 1)).days / 30.44
    assert event is True
    assert abs(duration - expected) < 0.01


# ---------------------------------------------------------------------------
# compute()
# ---------------------------------------------------------------------------

def test_dor_empty_queryset_returns_n_zero():
    """Empty queryset → both lines have n=0, no crash."""
    qs = _FakeQS([])
    result = compute(qs)
    assert result["first_line"]["n"] == 0
    assert result["second_line"]["n"] == 0


def test_dor_compute_returns_expected_structure():
    rows = [
        _row("RVd", D(2020, 1, 1), "Partial Response",
             second_line_therapy="DRd",
             second_line_start=D(2021, 6, 1),
             last_tx=D(2022, 1, 1)),
    ]
    qs = _FakeQS(rows)
    result = compute(qs)

    assert "first_line"  in result
    assert "second_line" in result
    for key in ("curve", "n", "median"):
        assert key in result["first_line"],  f"first_line missing '{key}'"
        assert key in result["second_line"], f"second_line missing '{key}'"
