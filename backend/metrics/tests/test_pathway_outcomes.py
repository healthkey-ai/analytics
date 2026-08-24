import datetime
from metrics.services import pathway_outcomes
from metrics.services.pathway_outcomes import compute

D = datetime.date


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def _row(first, second, start=D(2020, 1, 1), death=None, last=None):
    return {
        "first_line_therapy": first,
        "second_line_therapy": second,
        "first_line_start_date": start,
        "death_date": death,
        "last_treatment": last,
    }


def _combo_rows(first, second, n):
    return [
        _row(first, second, death=D(2022, 1, 1))
        for _ in range(n)
    ]


def test_groups_by_1l_2l_combo():
    rows = (
        _combo_rows("Bendamustine and Rituximab (BR)", "R-CHOP", 12)
        + _combo_rows("R-CHOP", "Lenalidomide and Rituximab (R2)", 11)
    )
    result = compute(_FakeQS(rows))

    labels = [p["label"] for p in result["pathways"]]
    assert labels == ["Bendamustine and Rituximab → R-CHOP", "R-CHOP → Lenalidomide and Rituximab"]
    assert result["pathways"][0]["n"] == 12
    assert result["pathways"][1]["n"] == 11


def test_drops_combos_below_min_n():
    rows = (
        _combo_rows("A", "B", pathway_outcomes.MIN_N)
        + _combo_rows("C", "D", pathway_outcomes.MIN_N - 1)
    )
    result = compute(_FakeQS(rows))

    assert [p["label"] for p in result["pathways"]] == ["A → B"]


def test_includes_a_small_but_comparable_pathway():
    """The MM seed cohort's common pathways are typically 5–8 patients."""
    rows = _combo_rows("VRd", "Daratumumab", 5)

    result = compute(_FakeQS(rows))

    assert [p["label"] for p in result["pathways"]] == ["VRd → Daratumumab"]


def test_caps_at_max_pathways():
    rows = []
    for i in range(pathway_outcomes.MAX_PATHWAYS + 2):
        rows += _combo_rows(f"Regimen{i}", "Second", pathway_outcomes.MIN_N)
    result = compute(_FakeQS(rows))

    assert len(result["pathways"]) == pathway_outcomes.MAX_PATHWAYS


def test_skips_rows_missing_either_line():
    rows = _combo_rows("A", "B", pathway_outcomes.MIN_N)
    rows += [
        _row(None, "B"),
        _row("A", None),
        _row("", "B"),
    ]
    result = compute(_FakeQS(rows))
    assert len(result["pathways"]) == 1
    assert result["pathways"][0]["n"] == pathway_outcomes.MIN_N


def test_os_structure_per_pathway():
    rows = _combo_rows("A", "B", pathway_outcomes.MIN_N)
    result = compute(_FakeQS(rows))

    os = result["pathways"][0]["os"]
    assert {"curve", "n", "median"} <= set(os)
    assert os["n"] == pathway_outcomes.MIN_N
    assert os["median"] is not None  # all died at 24 months


def test_empty_queryset():
    result = compute(_FakeQS([]))
    assert result["pathways"] == []
    assert result["min_n"] == pathway_outcomes.MIN_N
