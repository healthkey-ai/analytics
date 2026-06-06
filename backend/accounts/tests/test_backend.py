import pytest
from accounts.backends import EmailBackend


@pytest.mark.django_db
class TestEmailBackend:
    def test_authenticate_success(self, make_user):
        make_user(email="auth@example.com", password="TestPass123!")
        user = EmailBackend().authenticate(None, username="auth@example.com", password="TestPass123!")
        assert user is not None
        assert user.email == "auth@example.com"

    def test_authenticate_wrong_password_returns_none(self, make_user):
        make_user(email="auth2@example.com", password="TestPass123!")
        user = EmailBackend().authenticate(None, username="auth2@example.com", password="WrongPass!")
        assert user is None

    def test_authenticate_nonexistent_user_returns_none(self, db):
        user = EmailBackend().authenticate(None, username="ghost@example.com", password="TestPass123!")
        assert user is None

    def test_authenticate_case_insensitive_email(self, make_user):
        make_user(email="case@example.com", password="TestPass123!")
        user = EmailBackend().authenticate(None, username="CASE@EXAMPLE.COM", password="TestPass123!")
        assert user is not None

    def test_inactive_user_not_authenticated(self, make_user):
        user = make_user(email="inactive@example.com", password="TestPass123!")
        user.is_active = False
        user.save()
        result = EmailBackend().authenticate(None, username="inactive@example.com", password="TestPass123!")
        assert result is None
