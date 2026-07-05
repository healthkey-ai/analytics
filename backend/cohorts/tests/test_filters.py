"""Tests for apply_cohort_filters org and date params."""
import datetime
from unittest.mock import patch, MagicMock

import pytest
from django.http import QueryDict


class _FakeQS:
    """Minimal queryset mock for testing apply_cohort_filters."""

    def __init__(self, rows=None):
        self._rows = rows or []
        self._filters = {}

    def filter(self, *args, **kwargs):
        clone = _FakeQS(self._rows)
        clone._filters = {**self._filters, **kwargs}
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


def _make_request(params: dict):
    """Build a minimal request-like object with QueryDict-backed query_params."""
    qd = QueryDict(mutable=True)
    qd.update(params)
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


def _run_filters(params: dict) -> _FakeQS:
    from cohorts.filters import apply_cohort_filters
    req = _make_request(params)
    return apply_cohort_filters(req)


# ── org filter ────────────────────────────────────────────────────────────────

def test_org_filter_applied():
    result = _run_filters({"org": "Mayo Clinic"})
    assert result._filters.get("organization__name__iexact") == "Mayo Clinic"


def test_org_filter_not_applied_when_absent():
    result = _run_filters({})
    assert "organization__name__iexact" not in result._filters


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
