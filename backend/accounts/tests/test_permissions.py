"""Tests for IsPremiumOrStaff permission."""
from unittest.mock import MagicMock, patch
from accounts.permissions import IsPremiumOrStaff


def _make_request(is_premium=False, is_staff=False, is_superuser=False, is_authenticated=True):
    user = MagicMock()
    user.is_authenticated = is_authenticated
    user.is_premium = is_premium
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    request = MagicMock()
    request.user = user
    return request


def test_plain_user_denied():
    with patch("accounts.permissions.has_org_admin_access", return_value=False):
        assert IsPremiumOrStaff().has_permission(_make_request(), None) is False


def test_premium_user_allowed():
    with patch("accounts.permissions.has_org_admin_access", return_value=False):
        assert IsPremiumOrStaff().has_permission(_make_request(is_premium=True), None) is True


def test_staff_user_allowed():
    with patch("accounts.permissions.has_org_admin_access", return_value=False):
        assert IsPremiumOrStaff().has_permission(_make_request(is_staff=True), None) is True


@patch("accounts.permissions.has_org_admin_access", return_value=True)
def test_org_admin_user_allowed(mock_has_org_admin_access):
    assert IsPremiumOrStaff().has_permission(_make_request(), None) is True
    mock_has_org_admin_access.assert_called_once()


def test_superuser_allowed():
    assert IsPremiumOrStaff().has_permission(_make_request(is_superuser=True), None) is True


def test_unauthenticated_denied():
    assert IsPremiumOrStaff().has_permission(_make_request(is_authenticated=False), None) is False
