from metrics.services.treatment_patterns import _median, _overall_counts


class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def values(self, *_fields):
        return self._rows


def _row(first=None, second=None, later=None):
    return {
        "first_line_therapy": first,
        "second_line_therapy": second,
        "later_therapy": later,
    }


# ---------------------------------------------------------------------------
# _overall_counts — dedup per patient across lines
# ---------------------------------------------------------------------------

def test_overall_counts_patient_once_per_therapy():
    rows = [
        _row(first="BR", second="BR"),       # same therapy in two lines → counts once
        _row(first="BR", second="R-CHOP"),
        _row(first="R-CHOP"),
    ]
    result = {r["therapy"]: r for r in _overall_counts(_FakeQS(rows), total=3)}

    assert result["BR"]["count"] == 2
    assert result["R-CHOP"]["count"] == 2
    assert result["BR"]["pct"] == round(2 / 3 * 100, 1)


def test_overall_ignores_none_and_empty():
    rows = [_row(first=None, second="", later=None)]
    assert _overall_counts(_FakeQS(rows), total=1) == []


def test_overall_sorted_by_count_desc():
    rows = [_row(first="A"), _row(first="A"), _row(first="B")]
    result = _overall_counts(_FakeQS(rows), total=3)
    assert [r["therapy"] for r in result] == ["A", "B"]


def test_overall_empty_queryset():
    assert _overall_counts(_FakeQS([]), total=0) == []


# ---------------------------------------------------------------------------
# _median
# ---------------------------------------------------------------------------

def test_median_odd_count():
    assert _median([1, 2, 3]) == 2


def test_median_even_count():
    assert _median([1, 2, 3, 4]) == 2.5


def test_median_single_value():
    assert _median([3]) == 3


def test_median_empty():
    assert _median([]) is None
