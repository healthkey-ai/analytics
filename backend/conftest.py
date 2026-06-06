import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    """Factory that creates Identity users. Accepts keyword overrides."""
    from accounts.models import Identity

    def _make(email="user@example.com", password="TestPass123!", name="Test User", **kwargs):
        return Identity.objects.create_user(email=email, password=password, name=name, **kwargs)

    return _make
