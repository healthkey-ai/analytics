"""Tests for apply_cohort_filters org, date, and stage alias params."""
import datetime
from unittest.mock import patch, MagicMock

import pytest
from django.db.models import Q
from django.http import QueryDict


class _FakeQS:
    """Minimal queryset mock for testing apply_cohort_filters."""

    def __init__(self, rows=None):
        self._rows = rows or []
        self._filters = {}
        self._q_args = []

    def filter(self, *args, **kwargs):
        clone = _FakeQS(self._rows)
        clone._filters = {**self._filters, **kwargs}
        clone._q_args = self._q_args + list(args)
        return clone

    def exclude(self, *args, **kwargs):
        return self

    def values_list(self, *fields, flat=False):
        if flat:
            return [r[fields[0]] for r in self._rows]
        return [tuple(r[f] for f in fields) for r in self._rows]

    def values(self, *fields):
        return [{f: r[f] for f in fields} for r in self._rows]

    def distinct(self):
        return self

    def order_by(self, *args):
        return self

    def count(self):
        return len(self._rows)


def _make_request(params: dict):
    """Build a minimal request-like object with QueryDict-backed query_params."""
    qd = QueryDict(mutable=True)
    for key, val in params.items():
        if isinstance(val, list):
            qd.setlist(key, [str(v) for v in val])
        else:
            qd[key] = str(val)
    req = MagicMock()
    req.query_params = qd
    return req


@pytest.fixture(autouse=True)
def patch_patient_qs(monkeypatch):
    """Replace PatientInfo.objects.all() so no DB is needed."""
    fake = _FakeQS()
    with patch("cohorts.filters.PatientInfo") as mock_pi:
        mock_pi.objects.all.return_value = fake
        yield fake


def _run_filters(params: dict, **kwargs) -> _FakeQS:
    from cohorts.filters import apply_cohort_filters
    req = _make_request(params)
    return apply_cohort_filters(req, **kwargs)


# ── org filter ────────────────────────────────────────────────────────────────

def test_org_filter_applied():
    result = _run_filters({"org": "Mayo Clinic"})
    assert result._filters.get("organization__name__iexact") == "Mayo Clinic"


def test_org_filter_not_applied_when_absent():
    result = _run_filters({})
    assert "organization__name__iexact" not in result._filters


# ── demographic filters ──────────────────────────────────────────────────────

def test_gender_filter_accepts_male_label():
    result = _run_filters({"gender": "Male"})
    assert result._filters.get("gender__in") == ["M", "m", "Male", "male", "MALE"]


def test_gender_filter_accepts_female_code():
    result = _run_filters({"gender": "F"})
    assert result._filters.get("gender__in") == ["F", "f", "Female", "female", "FEMALE"]


def test_country_filter_applied_as_multi_value():
    result = _run_filters({"country": ["US", "GB"]})
    assert result._filters.get("country__in") == ["US", "GB"]


def test_country_filter_not_applied_when_absent():
    result = _run_filters({})
    assert "country__in" not in result._filters


# ── disease filter / transformation broadening ───────────────────────────────

def test_disease_filter_is_plain_icontains_by_default():
    result = _run_filters({"disease": "Follicular Lymphoma"})
    assert result._filters.get("disease__icontains") == "Follicular Lymphoma"
    assert result._q_args == []


def test_include_transformed_broadens_disease_filter():
    """Transformed patients have DLBCL as their current disease — the broadened
    filter must OR the disease match with transformed_to_dlbcl=True."""
    result = _run_filters({"disease": "Follicular Lymphoma"}, include_transformed=True)
    assert "disease__icontains" not in result._filters
    assert result._q_args == [
        Q(disease__icontains="Follicular Lymphoma") | Q(transformed_to_dlbcl=True)
    ]


def test_include_transformed_without_disease_adds_no_filter():
    result = _run_filters({}, include_transformed=True)
    assert "disease__icontains" not in result._filters
    assert result._q_args == []


# ── eligibility funnel ───────────────────────────────────────────────────────

def test_funnel_records_only_applied_groups_in_order(patch_patient_qs):
    patch_patient_qs._rows = [{}] * 10
    steps = []
    _run_filters({"disease": "Follicular Lymphoma", "country": ["US"]}, funnel=steps)
    assert [(s["key"], s["label"], s["count"]) for s in steps] == [
        ("disease_stage", "Disease & stage", 10),
        ("geography", "Geography", 10),
    ]


def test_funnel_records_all_groups_when_all_filters_applied(patch_patient_qs):
    patch_patient_qs._rows = [{}] * 5
    steps = []
    _run_filters(
        {
            "disease": "Multiple Myeloma",
            "stage": ["ISS Stage II"],
            "age_min": 18,
            "country": ["US"],
            "ecog": ["1"],
            "high_risk_cytogenetics": "true",
            "therapy_lines_min": 1,
            "meets_crab": "true",
            "hemoglobin_min": 10,
            "date": "this_year",
        },
        funnel=steps,
    )
    assert [s["key"] for s in steps] == [
        "disease_stage", "demographics", "geography", "performance",
        "cytogenetics", "treatment_history", "disease_characteristics",
        "labs", "diagnosis_period",
    ]


def test_funnel_records_nothing_when_no_filters():
    steps = []
    _run_filters({}, funnel=steps)
    assert steps == []


def test_base_queryset_param_is_used():
    custom = _FakeQS(rows=[{}] * 3)
    from cohorts.filters import apply_cohort_filters
    req = _make_request({})
    assert apply_cohort_filters(req, qs=custom) is custom


# ── stage filters ────────────────────────────────────────────────────────────

def test_breast_cancer_stage_filter_expands_qualifier_aliases():
    result = _run_filters({"disease": "Breast Cancer", "stage": ["II"]})
    assert result._filters.get("stage__in") == ["Stage II", "Stage 2 (qualifier value)"]


def test_non_breast_stage_filter_is_not_rewritten():
    result = _run_filters({"disease": "Multiple Myeloma", "stage": ["ISS Stage II"]})
    assert result._filters.get("stage__in") == ["ISS Stage II"]


# ── date filter ───────────────────────────────────────────────────────────────

FIXED_TODAY = datetime.date(2026, 6, 30)


@pytest.fixture()
def frozen_today(monkeypatch):
    """Freeze timezone.now().date() to FIXED_TODAY."""
    from django.utils import timezone
    import datetime as dt
    mock_now = MagicMock()
    mock_now.return_value.date.return_value = FIXED_TODAY
    monkeypatch.setattr(timezone, "now", mock_now)


def test_date_7d(frozen_today):
    result = _run_filters({"date": "7d"})
    expected = FIXED_TODAY - datetime.timedelta(days=7)
    assert result._filters.get("diagnosis_date__gte") == expected


def test_date_30d(frozen_today):
    result = _run_filters({"date": "30d"})
    expected = FIXED_TODAY - datetime.timedelta(days=30)
    assert result._filters.get("diagnosis_date__gte") == expected


def test_date_90d(frozen_today):
    result = _run_filters({"date": "90d"})
    expected = FIXED_TODAY - datetime.timedelta(days=90)
    assert result._filters.get("diagnosis_date__gte") == expected


def test_date_this_year(frozen_today):
    result = _run_filters({"date": "this_year"})
    assert result._filters.get("diagnosis_date__year") == FIXED_TODAY.year


def test_date_unknown_value_ignored(frozen_today):
    result = _run_filters({"date": "last_century"})
    assert "diagnosis_date__gte" not in result._filters
    assert "diagnosis_date__year" not in result._filters


def test_date_absent_no_filter():
    result = _run_filters({})
    assert "diagnosis_date__gte" not in result._filters
    assert "diagnosis_date__year" not in result._filters
