import pytest

LOGIN_URL = "/api/auth/login/"
SIGNUP_URL = "/api/auth/signup/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/user/"


@pytest.mark.django_db
class TestSignupView:
    def test_success_creates_user_and_returns_data(self, api_client):
        resp = api_client.post(SIGNUP_URL, {"email": "alice@example.com", "password": "StrongPass123!", "name": "Alice"})
        assert resp.status_code == 201
        assert resp.data["email"] == "alice@example.com"
        assert resp.data["name"] == "Alice"

    def test_weak_password_rejected(self, api_client):
        resp = api_client.post(SIGNUP_URL, {"email": "alice@example.com", "password": "short"})
        assert resp.status_code == 400
        assert "detail" in resp.data

    def test_numeric_password_rejected(self, api_client):
        resp = api_client.post(SIGNUP_URL, {"email": "alice@example.com", "password": "123456789012"})
        assert resp.status_code == 400

    def test_duplicate_email_rejected(self, api_client, make_user):
        make_user(email="dup@example.com")
        resp = api_client.post(SIGNUP_URL, {"email": "dup@example.com", "password": "StrongPass123!"})
        assert resp.status_code == 400

    def test_missing_email_rejected(self, api_client):
        resp = api_client.post(SIGNUP_URL, {"password": "StrongPass123!"})
        assert resp.status_code == 400

    def test_missing_password_rejected(self, api_client):
        resp = api_client.post(SIGNUP_URL, {"email": "alice@example.com"})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def test_success_returns_user_data(self, api_client, make_user):
        make_user(email="login@example.com", password="TestPass123!")
        resp = api_client.post(LOGIN_URL, {"email": "login@example.com", "password": "TestPass123!"})
        assert resp.status_code == 200
        assert resp.data["email"] == "login@example.com"

    def test_wrong_password_returns_401(self, api_client, make_user):
        make_user(email="login2@example.com", password="TestPass123!")
        resp = api_client.post(LOGIN_URL, {"email": "login2@example.com", "password": "WrongPass999!"})
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, api_client):
        resp = api_client.post(LOGIN_URL, {"email": "ghost@example.com", "password": "TestPass123!"})
        assert resp.status_code == 401

    def test_email_case_insensitive(self, api_client, make_user):
        make_user(email="case@example.com", password="TestPass123!")
        resp = api_client.post(LOGIN_URL, {"email": "CASE@EXAMPLE.COM", "password": "TestPass123!"})
        assert resp.status_code == 200


@pytest.mark.django_db
class TestLogoutView:
    def test_authenticated_logout_succeeds(self, api_client, make_user):
        user = make_user()
        api_client.force_authenticate(user=user)
        resp = api_client.post(LOGOUT_URL)
        assert resp.status_code == 200

    def test_unauthenticated_logout_also_succeeds(self, api_client):
        # Logout is AllowAny — calling it unauthenticated is a no-op, not an error
        resp = api_client.post(LOGOUT_URL)
        assert resp.status_code == 200


@pytest.mark.django_db
class TestMeView:
    def test_authenticated_returns_user_data(self, api_client, make_user):
        user = make_user(email="me@example.com", name="Me User")
        api_client.force_authenticate(user=user)
        resp = api_client.get(ME_URL)
        assert resp.status_code == 200
        assert resp.data["email"] == "me@example.com"
        assert resp.data["name"] == "Me User"
        assert "uid" in resp.data
        assert "is_staff" in resp.data

    def test_unauthenticated_returns_403(self, api_client):
        resp = api_client.get(ME_URL)
        assert resp.status_code == 403
