"""Tests for IsPremiumOrStaff permission."""
from unittest.mock import MagicMock
from accounts.permissions import IsPremiumOrStaff


def _make_request(is_premium=False, is_staff=False, is_authenticated=True):
    user = MagicMock()
    user.is_authenticated = is_authenticated
    user.is_premium = is_premium
    user.is_staff = is_staff
    request = MagicMock()
    request.user = user
    return request


def test_plain_user_denied():
    assert IsPremiumOrStaff().has_permission(_make_request(), None) is False


def test_premium_user_allowed():
    assert IsPremiumOrStaff().has_permission(_make_request(is_premium=True), None) is True


def test_staff_user_allowed():
    assert IsPremiumOrStaff().has_permission(_make_request(is_staff=True), None) is True


def test_unauthenticated_denied():
    assert IsPremiumOrStaff().has_permission(_make_request(is_authenticated=False), None) is False
