import datetime
import pytest
from unittest.mock import patch, MagicMock
from metrics.services.subgroup_survival import _subgroup_km, compute


D = datetime.date


# ---------------------------------------------------------------------------
# Minimal FakeQS supporting the ORM calls made by os_km / pfs_km / stage split
# ---------------------------------------------------------------------------

class _FakeQS:
    def __init__(self, rows):
        self._rows = list(rows)

    # --- queryset methods used by subgroup splitting ---

    def filter(self, *args, **kwargs):
        if not kwargs:  # Q-object call — keep passthrough
            return self
        rows = self._rows
        for key, val in kwargs.items():
            rows = [r for r in rows if r.get(key) == val]
        return _FakeQS(rows)

    def exclude(self, *args, **kwargs):
        if not kwargs:  # Q-object call — keep passthrough
            return self
        rows = self._rows
        for key, val in kwargs.items():
            if key.endswith("__isnull"):
                field = key[: -len("__isnull")]
                rows = [r for r in rows if (r.get(field) is None) != val]
            else:
                rows = [r for r in rows if r.get(key) != val]
        return _FakeQS(rows)

    def values_list(self, field, flat=False):
        return _FakeValuesList([r.get(field) for r in self._rows])

    # --- queryset methods used by os_km / pfs_km ---

    def count(self):
        return len(self._rows)

    def values(self, *_fields):
        return self._rows


class _FakeValuesList(list):
    def distinct(self):
        seen = set()
        result = []
        for v in self:
            if v not in seen and v is not None:
                seen.add(v)
                result.append(v)
        return _FakeValuesList(result)

    def order_by(self, *_fields):
        return _FakeValuesList(sorted(self, key=lambda x: (x is None, x)))


def _os_row(start, end=None, death=None, last_tx=None):
    return {
        "first_line_start_date": start,
        "death_date":            death,
        "last_treatment":        last_tx or end,
        "first_line_end_date":   None,
        "first_line_outcome":    None,
        "second_line_end_date":  None,
        "second_line_outcome":   None,
        "later_end_date":        None,
        "later_outcome":         None,
        "second_line_start_date": None,
    }


# ---------------------------------------------------------------------------
# _subgroup_km
# ---------------------------------------------------------------------------

def test_subgroup_km_drops_empty_subgroups():
    from metrics.services.survival import os_km

    populated = _FakeQS([_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1))])
    empty = _FakeQS([])

    result = _subgroup_km(os_km, [("A", populated), ("B", empty)])

    labels = [r["label"] for r in result]
    assert "A" in labels
    assert "B" not in labels


def test_subgroup_km_attaches_label():
    from metrics.services.survival import os_km

    qs = _FakeQS([_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1))])
    result = _subgroup_km(os_km, [("My Group", qs)])

    assert result[0]["label"] == "My Group"
    assert "curve" in result[0]
    assert "n" in result[0]
    assert "median" in result[0]


# ---------------------------------------------------------------------------
# compute() — structure checks
# ---------------------------------------------------------------------------

def _make_stage_qs(stages):
    """Build a FakeQS where each row has a 'stage' field and minimal survival fields."""
    rows = []
    for stage in stages:
        row = _os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1))
        row["stage"] = stage
        # Provide these so the now-real _FakeQS.exclude logic doesn't filter the rows
        row["cytogenic_markers"] = "del(17p)"
        row["stem_cell_transplant_history"] = "Autologous SCT"
        row["mrd_status"] = None
        rows.append(row)
    return _FakeQS(rows)


def test_compute_returns_expected_top_level_keys():
    qs = _make_stage_qs(["ISS Stage I", "ISS Stage II"])
    result = compute(qs)

    assert set(result.keys()) == {"by_stage", "by_cytogenetics", "by_sct", "by_mrd"}


def test_compute_each_stratification_has_os_and_pfs():
    qs = _make_stage_qs(["ISS Stage I"])
    result = compute(qs)

    for strat in ("by_stage", "by_cytogenetics", "by_sct", "by_mrd"):
        assert "os"  in result[strat], f"{strat} missing 'os'"
        assert "pfs" in result[strat], f"{strat} missing 'pfs'"


def test_compute_subgroup_entries_have_required_fields():
    qs = _make_stage_qs(["ISS Stage I", "ISS Stage II"])
    result = compute(qs)

    for strat in ("by_stage", "by_cytogenetics", "by_sct", "by_mrd"):
        for entry in result[strat]["os"]:
            assert "label"  in entry, f"{strat} entry missing 'label'"
            assert "n"      in entry, f"{strat} entry missing 'n'"
            assert "curve"  in entry, f"{strat} entry missing 'curve'"
            assert "median" in entry, f"{strat} entry missing 'median'"


# ---------------------------------------------------------------------------
# MRD subgroup tests
# ---------------------------------------------------------------------------

def _make_mrd_qs(mrd_values):
    rows = []
    for mrd in mrd_values:
        row = _os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1))
        row["mrd_status"] = mrd
        row["stage"] = None
        row["cytogenic_markers"] = None
        row["stem_cell_transplant_history"] = None
        rows.append(row)
    return _FakeQS(rows)


def test_mrd_subgroups_split_by_distinct_values():
    from metrics.services.subgroup_survival import _mrd_subgroups, _MRD_MIN_N

    # Provide enough rows to clear the min-n threshold
    qs = _make_mrd_qs(["MRD Negative"] * _MRD_MIN_N + ["MRD Positive"] * _MRD_MIN_N)
    subgroups = _mrd_subgroups(qs)

    labels = [label for label, _ in subgroups]
    assert "MRD Negative" in labels
    assert "MRD Positive" in labels


def test_mrd_subgroups_excludes_null_and_empty():
    from metrics.services.subgroup_survival import _mrd_subgroups

    rows = [
        {**_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1)), "mrd_status": None},
        {**_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1)), "mrd_status": ""},
        {**_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1)), "mrd_status": "MRD Negative"},
    ]
    qs = _FakeQS(rows)
    subgroups = _mrd_subgroups(qs)

    labels = [label for label, _ in subgroups]
    assert None not in labels
    assert "" not in labels


def test_mrd_subgroups_empty_when_no_assessments():
    from metrics.services.subgroup_survival import _mrd_subgroups

    rows = [
        {**_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1)), "mrd_status": None},
        {**_os_row(D(2020, 1, 1), last_tx=D(2022, 1, 1)), "mrd_status": None},
    ]
    qs = _FakeQS(rows)
    subgroups = _mrd_subgroups(qs)

    assert subgroups == []


def test_mrd_subgroups_drops_groups_below_min_n():
    from metrics.services.subgroup_survival import _mrd_subgroups, _MRD_MIN_N

    # Only "MRD Negative" meets the threshold; "MRD Positive" has too few rows
    qs = _make_mrd_qs(["MRD Negative"] * _MRD_MIN_N + ["MRD Positive"] * (_MRD_MIN_N - 1))
    subgroups = _mrd_subgroups(qs)

    labels = [label for label, _ in subgroups]
    assert "MRD Negative" in labels
    assert "MRD Positive" not in labels


def test_by_mrd_in_compute_output():
    from metrics.services.subgroup_survival import _MRD_MIN_N

    qs = _make_mrd_qs(["MRD Negative"] * _MRD_MIN_N + ["MRD Positive"] * _MRD_MIN_N)
    result = compute(qs)

    assert "by_mrd" in result
    assert "os"  in result["by_mrd"]
    assert "pfs" in result["by_mrd"]


# ---------------------------------------------------------------------------
# p-value fields (Feature 1 — log-rank)
# ---------------------------------------------------------------------------

def test_stratification_has_p_value_fields():
    qs = _make_stage_qs(["ISS Stage I", "ISS Stage II"])
    result = compute(qs)

    for strat in ("by_stage", "by_cytogenetics", "by_sct", "by_mrd"):
        assert "os_p"  in result[strat], f"{strat} missing 'os_p'"
        assert "pfs_p" in result[strat], f"{strat} missing 'pfs_p'"


def test_p_value_none_for_single_subgroup():
    """Only one stage present → log-rank requires ≥ 2 groups → os_p must be None."""
    qs = _make_stage_qs(["ISS Stage I"])
    result = compute(qs)
    assert result["by_stage"]["os_p"] is None


def test_p_value_is_float_or_none():
    qs = _make_stage_qs(["ISS Stage I", "ISS Stage II"])
    result = compute(qs)
    p = result["by_stage"]["os_p"]
    assert p is None or (isinstance(p, float) and 0.0 <= p <= 1.0)
