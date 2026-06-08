import pytest
from metrics.services.km_utils import km_curve, log_rank_p


# ---------------------------------------------------------------------------
# km_curve — confidence interval fields
# ---------------------------------------------------------------------------

def test_km_curve_ci_fields_present():
    te = [(6.0, True), (12.0, True), (24.0, False)]
    curve = km_curve(te)
    assert curve, "curve should not be empty"
    for pt in curve:
        assert "ci_lower" in pt, f"ci_lower missing at t={pt['time']}"
        assert "ci_upper" in pt, f"ci_upper missing at t={pt['time']}"


def test_km_curve_ci_in_unit_interval():
    te = [(6.0, True), (12.0, True), (18.0, False), (24.0, True)]
    curve = km_curve(te)
    for pt in curve:
        assert 0 <= pt["ci_lower"] <= 1, f"ci_lower={pt['ci_lower']} out of [0,1]"
        assert 0 <= pt["ci_upper"] <= 1, f"ci_upper={pt['ci_upper']} out of [0,1]"


def test_km_curve_ci_ordering():
    te = [(6.0, True), (12.0, True), (24.0, False)]
    curve = km_curve(te)
    for pt in curve:
        assert pt["ci_lower"] <= pt["survival"], (
            f"ci_lower={pt['ci_lower']} > survival={pt['survival']}"
        )
        assert pt["survival"] <= pt["ci_upper"], (
            f"survival={pt['survival']} > ci_upper={pt['ci_upper']}"
        )


def test_km_curve_ci_empty_input():
    assert km_curve([]) == []


def test_km_curve_ci_single_event_no_crash():
    """n == d at the single event — Greenwood skip must not crash."""
    te = [(12.0, True)]
    curve = km_curve(te)
    for pt in curve:
        assert "ci_lower" in pt
        assert "ci_upper" in pt
        assert 0 <= pt["ci_lower"] <= 1
        assert 0 <= pt["ci_upper"] <= 1


def test_km_curve_initial_point_ci_ones():
    te = [(6.0, True)]
    curve = km_curve(te)
    assert curve[0]["ci_lower"] == 1.0
    assert curve[0]["ci_upper"] == 1.0


# ---------------------------------------------------------------------------
# log_rank_p
# ---------------------------------------------------------------------------

def test_log_rank_p_single_group_returns_none():
    te = [(6.0, True), (12.0, True), (24.0, False)]
    assert log_rank_p([te]) is None


def test_log_rank_p_no_groups_returns_none():
    assert log_rank_p([]) is None


def test_log_rank_p_all_empty_groups_returns_none():
    assert log_rank_p([[], []]) is None


def test_log_rank_p_one_non_empty_group_returns_none():
    te = [(6.0, True), (12.0, True)]
    assert log_rank_p([te, []]) is None


def test_log_rank_p_identical_groups_high_pvalue():
    """Two identical groups → no difference → large p-value."""
    te = [(6.0, True), (12.0, True), (18.0, False), (24.0, True)]
    p = log_rank_p([te[:], te[:]])
    assert p is not None
    assert p > 0.05, f"Expected high p-value for identical groups, got {p}"


def test_log_rank_p_well_separated_groups_small_pvalue():
    """All early events vs. all late events → strong separation → small p-value."""
    group_a = [(2.0, True), (3.0, True), (4.0, True), (5.0, True)]
    group_b = [(20.0, True), (22.0, True), (24.0, True), (26.0, True)]
    p = log_rank_p([group_a, group_b])
    assert p is not None
    assert p < 0.05, f"Expected small p-value for well-separated groups, got {p}"


def test_log_rank_p_returns_float_or_none():
    te_a = [(6.0, True), (12.0, True)]
    te_b = [(8.0, True), (14.0, False)]
    result = log_rank_p([te_a, te_b])
    assert result is None or (isinstance(result, float) and 0.0 <= result <= 1.0)
