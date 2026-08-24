"""Tests for forest_plot service and the log_rank_hr utility."""
import pytest
from metrics.services.km_utils import log_rank_hr
from metrics.services.forest_plot import compute


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args, **kwargs):
        return self

    def exclude(self, *args, **kwargs):
        return self

    def values(self, *fields):
        return [{f: r.get(f) for f in fields} for r in self._rows]

    def values_list(self, *fields, flat=False):
        if flat:
            return [r.get(fields[0]) for r in self._rows]
        return [tuple(r.get(f) for f in fields) for r in self._rows]

    def distinct(self):
        return self

    def order_by(self, *args):
        return self


# ── log_rank_hr unit tests ────────────────────────────────────────────────────

def test_hr_identical_groups_near_one():
    """Two groups with the same survival → HR ≈ 1.0."""
    te = [(float(i), True) for i in range(1, 21)]
    hr, ci_low, ci_high, p = log_rank_hr(te, te)
    assert 0.5 < hr < 2.0
    assert ci_low < hr < ci_high


def test_hr_better_survival_group1():
    """Group 1 all survive twice as long → HR < 1 (better for group 1)."""
    te1 = [(float(i * 2), True) for i in range(1, 21)]   # longer survival
    te2 = [(float(i),     True) for i in range(1, 21)]   # shorter survival
    hr, ci_low, ci_high, p = log_rank_hr(te1, te2)
    assert hr < 1.0
    assert ci_high < 1.5


def test_hr_worse_survival_group1():
    """Group 1 all die sooner → HR > 1."""
    te1 = [(float(i),     True) for i in range(1, 21)]
    te2 = [(float(i * 2), True) for i in range(1, 21)]
    hr, ci_low, ci_high, p = log_rank_hr(te1, te2)
    assert hr > 1.0


def test_hr_no_events_returns_none():
    te1 = [(10.0, False), (12.0, False)]
    te2 = [(8.0,  False), (9.0,  False)]
    assert log_rank_hr(te1, te2) is None


def test_hr_empty_arm_returns_none():
    te = [(float(i), True) for i in range(1, 10)]
    assert log_rank_hr(te, []) is None
    assert log_rank_hr([], te) is None


def test_hr_ci_brackets_hr():
    te1 = [(float(i * 2), True) for i in range(1, 15)]
    te2 = [(float(i),     True) for i in range(1, 15)]
    hr, ci_low, ci_high, p = log_rank_hr(te1, te2)
    assert ci_low < hr < ci_high


def test_hr_p_value_range():
    te1 = [(float(i * 3), True) for i in range(1, 20)]
    te2 = [(float(i),     True) for i in range(1, 20)]
    _, _, _, p = log_rank_hr(te1, te2)
    assert 0.0 <= p <= 1.0


# ── compute smoke tests ───────────────────────────────────────────────────────

def _make_os_row(start_days, death_days=None, last_days=None):
    from datetime import date
    base = date(2020, 1, 1)
    from datetime import timedelta
    start = base + timedelta(days=start_days)
    death = (base + timedelta(days=death_days)) if death_days else None
    last  = (base + timedelta(days=last_days))  if last_days  else None
    return {
        "first_line_start_date": start,
        "death_date":            death,
        "last_treatment":        last,
        # MM subgroup fields the forest plot now splits on
        "cytogenic_markers":            "del(17p)",
        "stem_cell_transplant_history": ["autologous SCT"],
        "stage":                        "R-ISS III",
        "patient_age":                  67,
        "mrd_status":                   "MRD negative",
    }


def test_compute_empty_returns_empty():
    qs = _FakeQS([])
    assert compute(qs) == []


def test_compute_too_few_patients_returns_empty():
    """Fewer than _MIN_PER_ARM patients per arm → no rows."""
    rows = [_make_os_row(0, death_days=200) for _ in range(3)]
    qs = _FakeQS(rows)
    assert compute(qs) == []


def test_compute_reports_mm_subgroups():
    """With enough patients and OS events, compute yields MM-relevant subgroup
    rows (cytogenetics / R-ISS stage / SCT / age / MRD), not breast-cancer ones.

    _FakeQS ignores the split predicates, so both arms see the same rows — the
    HR is ≈1 but computable, which is all this smoke test needs to confirm the
    splits are wired and labelled correctly.
    """
    rows = [_make_os_row(0, death_days=200 + i * 10) for i in range(10)]
    result = compute(_FakeQS(rows))
    subgroups = {r["subgroup"] for r in result}
    assert subgroups == {"Cytogenetic Risk", "R-ISS Stage", "SCT", "Age", "MRD Status"}
    for r in result:
        assert r["ci_low"] <= r["hr"] <= r["ci_high"]
        assert 0.0 <= r["p_value"] <= 1.0
