import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset DRF throttle state between tests.

    DRF rate throttles keep their request history in the process cache, keyed by
    user pk. Test users are rolled back and their pks recycle, so without this the
    export-throttle counts (ChartExportRateThrottle, 10/hour) accumulate across
    every test hitting the endpoint and eventually 429 an unrelated test. Clearing
    the cache per test isolates throttle state; a test exercising throttling within
    itself is unaffected.
    """
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    """Factory that creates Identity users. Pass is_premium=True for export-capable users."""
    from accounts.models import Identity

    def _make(
        email="user@example.com",
        password="TestPass123!",
        name="Test User",
        **kwargs,
    ):
        return Identity.objects.create_user(email=email, password=password, name=name, **kwargs)

    return _make
