import pytest
from metrics.services.switching import _switching_flows


class _FakeQS:
    """Minimal queryset mock for testing switching computation logic."""

    def __init__(self, rows):
        self._rows = rows

    def exclude(self, **_):
        return self

    def values(self, *_fields):
        return self._rows


def qs(rows):
    return _FakeQS(rows)


# ---------------------------------------------------------------------------
# _switching_flows
# ---------------------------------------------------------------------------

def test_basic_percentages():
    rows = [
        {"from_reg": "VRd", "to_reg": "DPd"},
        {"from_reg": "VRd", "to_reg": "DPd"},
        {"from_reg": "VRd", "to_reg": "KRd"},
    ]
    result = _switching_flows(qs(rows), "from_reg", "to_reg")

    assert len(result) == 1
    row = result[0]
    assert row["from_regimen"] == "VRd"
    assert row["n_switched"] == 3

    by_dest = {s["to_regimen"]: s for s in row["switches"]}
    assert by_dest["DPd"]["n"] == 2
    assert by_dest["DPd"]["pct"] == pytest.approx(66.7, abs=0.1)
    assert by_dest["KRd"]["n"] == 1
    assert by_dest["KRd"]["pct"] == pytest.approx(33.3, abs=0.1)


def test_percentages_sum_to_100():
    rows = [{"f": "A", "t": chr(ord("X") + i)} for i in range(7)]
    result = _switching_flows(qs(rows), "f", "t", min_from_n=1)

    assert len(result) == 1
    total_pct = sum(s["pct"] for s in result[0]["switches"])
    assert total_pct == pytest.approx(100.0, abs=0.2)


def test_min_from_n_filters_small_groups():
    rows = [
        {"f": "Big", "t": "X"},
        {"f": "Big", "t": "Y"},
        {"f": "Small", "t": "X"},  # only 1 patient — should be excluded with default min_from_n=2
    ]
    result = _switching_flows(qs(rows), "f", "t")

    froms = [r["from_regimen"] for r in result]
    assert "Big" in froms
    assert "Small" not in froms


def test_sorted_by_total_switchers_descending():
    rows = (
        [{"f": "A", "t": "X"}, {"f": "A", "t": "Y"}]          # 2 switchers
        + [{"f": "B", "t": "X"}] * 5                             # 5 switchers
    )
    result = _switching_flows(qs(rows), "f", "t", min_from_n=1)

    assert result[0]["from_regimen"] == "B"
    assert result[1]["from_regimen"] == "A"


def test_switches_sorted_by_n_descending():
    rows = [
        {"f": "VRd", "t": "rare"},
        {"f": "VRd", "t": "common"},
        {"f": "VRd", "t": "common"},
        {"f": "VRd", "t": "common"},
    ]
    result = _switching_flows(qs(rows), "f", "t")

    assert result[0]["switches"][0]["to_regimen"] == "common"


def test_empty_queryset():
    assert _switching_flows(qs([]), "f", "t") == []
