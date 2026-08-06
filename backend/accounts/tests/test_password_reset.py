import uuid
from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from accounts.models import Identity, PasswordResetToken


def _make_user(email="test@example.com", password="Str0ngPassw0rd!99", name="Test"):
    return Identity.objects.create_user(email=email, password=password, name=name)


# ── Request endpoint ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_password_reset_request_sends_email(client):
    user = _make_user()
    resp = client.post("/api/auth/password-reset/", {"email": user.email}, content_type="application/json")
    assert resp.status_code == 200
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to
    assert PasswordResetToken.objects.filter(identity=user).exists()


@pytest.mark.django_db
def test_password_reset_request_unknown_email_returns_200(client):
    resp = client.post("/api/auth/password-reset/", {"email": "nobody@example.com"}, content_type="application/json")
    assert resp.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_request_no_email_returns_400(client):
    resp = client.post("/api/auth/password-reset/", {}, content_type="application/json")
    assert resp.status_code == 400


# ── Confirm endpoint ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_password_reset_confirm_happy_path(client):
    user = _make_user()
    token_obj = PasswordResetToken.objects.create(identity=user)
    new_pw = "NewStr0ngPassw0rd!99"
    resp = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": str(token_obj.token), "password": new_pw},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email
    token_obj.refresh_from_db()
    assert token_obj.used_at is not None
    user.refresh_from_db()
    assert user.check_password(new_pw)


@pytest.mark.django_db
def test_password_reset_confirm_expired_token(client):
    user = _make_user()
    token_obj = PasswordResetToken.objects.create(
        identity=user,
        created_at=timezone.now() - timedelta(hours=2),
    )
    resp = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": str(token_obj.token), "password": "NewStr0ngPassw0rd!99"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.django_db
def test_password_reset_confirm_used_token(client):
    user = _make_user()
    token_obj = PasswordResetToken.objects.create(identity=user, used_at=timezone.now())
    resp = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": str(token_obj.token), "password": "NewStr0ngPassw0rd!99"},
        content_type="application/json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(client):
    resp = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": str(uuid.uuid4()), "password": "NewStr0ngPassw0rd!99"},
        content_type="application/json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_weak_password(client):
    user = _make_user()
    token_obj = PasswordResetToken.objects.create(identity=user)
    resp = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": str(token_obj.token), "password": "short"},
        content_type="application/json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_missing_fields(client):
    resp = client.post("/api/auth/password-reset/confirm/", {}, content_type="application/json")
    assert resp.status_code == 400
