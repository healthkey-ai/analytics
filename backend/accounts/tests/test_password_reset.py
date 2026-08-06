"""Tests for the password-reset email-link flow."""
import pytest
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from accounts.models import Identity


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def local_user(db):
    user = Identity.objects.create_user(
        email="user@example.com",
        password="ValidPass123!",
        name="Test User",
    )
    return user


# ---------------------------------------------------------------------------
# request_password_reset
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   APP_BASE_URL="http://localhost:5173")
def test_request_reset_known_email_returns_200(client, local_user):
    resp = client.post("/api/auth/password-reset/", {"email": local_user.email}, format="json")
    assert resp.status_code == 200
    assert "reset link" in resp.data["detail"]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   APP_BASE_URL="http://localhost:5173")
def test_request_reset_unknown_email_returns_200(client, db):
    """Should not reveal whether the account exists."""
    resp = client.post("/api/auth/password-reset/", {"email": "nobody@example.com"}, format="json")
    assert resp.status_code == 200
    assert "reset link" in resp.data["detail"]


@pytest.mark.django_db
def test_request_reset_missing_email_returns_400(client, db):
    resp = client.post("/api/auth/password-reset/", {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   APP_BASE_URL="http://localhost:5173")
def test_request_reset_sends_email(client, local_user):
    from django.core import mail
    client.post("/api/auth/password-reset/", {"email": local_user.email}, format="json")
    assert len(mail.outbox) == 1
    assert local_user.email in mail.outbox[0].to
    assert "reset-password" in mail.outbox[0].body


# ---------------------------------------------------------------------------
# reset_password (confirm)
# ---------------------------------------------------------------------------

def _make_link_params(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


@pytest.mark.django_db
def test_reset_password_valid_token(client, local_user):
    uid, token = _make_link_params(local_user)
    resp = client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": uid, "token": token, "new_password": "NewValidPass456!"},
        format="json",
    )
    assert resp.status_code == 200
    local_user.refresh_from_db()
    assert local_user.check_password("NewValidPass456!")


@pytest.mark.django_db
def test_reset_password_invalid_token(client, local_user):
    uid, _ = _make_link_params(local_user)
    resp = client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": uid, "token": "bad-token", "new_password": "NewValidPass456!"},
        format="json",
    )
    assert resp.status_code == 400
    assert "expired" in resp.data["detail"].lower() or "invalid" in resp.data["detail"].lower()


@pytest.mark.django_db
def test_reset_password_invalid_uid(client, local_user):
    _, token = _make_link_params(local_user)
    resp = client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": "not-a-real-uid", "token": token, "new_password": "NewValidPass456!"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_reset_password_weak_password(client, local_user):
    uid, token = _make_link_params(local_user)
    resp = client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": uid, "token": token, "new_password": "short"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_reset_password_token_invalidated_after_use(client, local_user):
    uid, token = _make_link_params(local_user)
    # First use — should succeed
    client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": uid, "token": token, "new_password": "NewValidPass456!"},
        format="json",
    )
    # Second use — token should now be invalid (password hash changed)
    resp = client.post(
        "/api/auth/password-reset-confirm/",
        {"uid": uid, "token": token, "new_password": "AnotherPass789!"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_reset_password_missing_fields(client, local_user):
    resp = client.post("/api/auth/password-reset-confirm/", {}, format="json")
    assert resp.status_code == 400
