import datetime
import pytest
from metrics.services.ttnt import _ttnt_km


D = datetime.date


class _FakeQS:
    """Minimal queryset mock for testing TTNT computation logic."""

    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def qs(rows):
    return _FakeQS(rows)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def row(end, next_start=None, death=None, last_tx=None):
    return {
        "end_f":         end,
        "next_start_f":  next_start,
        "death_date":    death,
        "last_treatment": last_tx,
    }


def run(rows):
    return _ttnt_km(qs(rows), end_f="end_f", next_start_f="next_start_f")


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_event_patients_counted():
    r = run([row(D(2020, 1, 1), next_start=D(2020, 7, 1))])
    assert r["n"] == 1
    # Single event drops survival to 0.0, which is ≤ 0.5, so median is the event time (~6 mo)
    assert r["median"] == pytest.approx(6.0, abs=0.1)


def test_censored_patients_counted():
    r = run([row(D(2020, 1, 1), last_tx=D(2021, 1, 1))])
    assert r["n"] == 1
    assert r["curve"][-1]["survival"] == pytest.approx(1.0)  # censored, no drop


def test_missing_end_date_skipped():
    r = run([row(None, next_start=D(2020, 6, 1))])
    assert r["n"] == 0


def test_censor_before_end_skipped():
    # last_treatment before end_f — invalid, should be dropped
    r = run([row(D(2020, 6, 1), last_tx=D(2020, 1, 1))])
    assert r["n"] == 0


def test_zero_duration_skipped():
    # same start and next_start date — zero duration, should be dropped
    r = run([row(D(2020, 1, 1), next_start=D(2020, 1, 1))])
    assert r["n"] == 0


def test_median_reached_with_enough_events():
    # 4 patients with events — KM drops below 0.5 by the 3rd event
    rows = [
        row(D(2020, 1, 1), next_start=D(2020, 4, 1)),   # ~3 mo
        row(D(2020, 1, 1), next_start=D(2020, 7, 1)),   # ~6 mo
        row(D(2020, 1, 1), next_start=D(2020, 10, 1)),  # ~9 mo
        row(D(2020, 1, 1), next_start=D(2021, 1, 1)),   # ~12 mo
    ]
    r = run(rows)
    assert r["n"] == 4
    assert r["median"] is not None
    assert r["median"] < 12


def test_death_date_used_as_censor_when_no_last_tx():
    r = run([row(D(2020, 1, 1), death=D(2021, 6, 1))])
    assert r["n"] == 1
    assert r["curve"][-1]["survival"] == pytest.approx(1.0)


def test_death_date_preferred_over_last_tx_for_censor():
    # Both present — death_date takes priority (earlier = more conservative censor)
    r_death = run([row(D(2020, 1, 1), death=D(2020, 6, 1), last_tx=D(2021, 6, 1))])
    r_last  = run([row(D(2020, 1, 1), last_tx=D(2020, 6, 1))])
    # Duration should be the same — death_date was used
    assert r_death["curve"][-1] == r_last["curve"][-1]
