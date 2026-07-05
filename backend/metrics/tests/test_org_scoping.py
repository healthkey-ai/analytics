"""Tests for apply_org_scope — org-scoped queryset filtering."""
import pytest
from unittest.mock import MagicMock, patch
from accounts.utils import apply_org_scope as _apply_org_scope


def _make_user(is_staff=False):
    user = MagicMock()
    user.is_staff = is_staff
    return user


def _make_qs():
    qs = MagicMock()
    qs.filter.return_value = qs
    return qs


def test_staff_sees_all_orgs():
    qs = _make_qs()
    user = _make_user(is_staff=True)
    scoped_qs, err = _apply_org_scope(qs, user)
    assert err is None
    qs.filter.assert_not_called()
    assert scoped_qs is qs


@patch('accounts.utils.get_visible_org_names', return_value=['Org A'])
def test_user_scoped_to_visible_orgs(mock_visible):
    qs = _make_qs()
    user = _make_user()
    scoped_qs, err = _apply_org_scope(qs, user)
    assert err is None
    qs.filter.assert_called_once_with(organization__name__in=['Org A'])


@patch('accounts.utils.get_visible_org_names', return_value=[])
def test_user_with_no_visible_orgs_returns_403(mock_visible):
    qs = _make_qs()
    user = _make_user()
    scoped_qs, err = _apply_org_scope(qs, user)
    assert scoped_qs is None
    assert err is not None
    assert err.status_code == 403


@patch('accounts.utils.get_visible_org_names', return_value=['ABC Foundation'])
def test_user_with_public_org_sees_it(mock_visible):
    qs = _make_qs()
    user = _make_user()
    scoped_qs, err = _apply_org_scope(qs, user)
    assert err is None
    qs.filter.assert_called_once_with(organization__name__in=['ABC Foundation'])


@patch('accounts.utils.get_visible_org_names', return_value=['Cancer Center'])
def test_premium_user_scoped_to_visible_orgs(mock_visible):
    qs = _make_qs()
    user = _make_user()
    scoped_qs, err = _apply_org_scope(qs, user)
    assert err is None
    qs.filter.assert_called_once_with(organization__name__in=['Cancer Center'])


@patch('accounts.utils.get_visible_org_names', return_value=['HealthTree Trust', 'Hospital A', 'Hospital B'])
def test_multi_org_trust_scoped_to_all_visible(mock_visible):
    qs = _make_qs()
    user = _make_user()
    scoped_qs, err = _apply_org_scope(qs, user)
    assert err is None
    qs.filter.assert_called_once_with(
        organization__name__in=['HealthTree Trust', 'Hospital A', 'Hospital B']
    )
