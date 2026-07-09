"""Tests for the signup view."""
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from accounts.views import signup_view


@contextmanager
def _noop_atomic():
    yield


def _post(data):
    factory = APIRequestFactory()
    request = factory.post('/api/auth/signup/', data, format='json')
    request.session = MagicMock()
    return signup_view(request)


def _mock_user(email='test@example.com'):
    mock_user = MagicMock()
    mock_user.uid = 'test-uid'
    mock_user.email = email
    mock_user.name = 'Test User'
    mock_user.is_staff = False
    mock_user.is_premium = False
    return mock_user


@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views._create_or_claim_signup_identity')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_succeeds(mock_create_or_claim, mock_validate, mock_get_token, mock_login):
    mock_create_or_claim.return_value = _mock_user()
    response = _post({
        'email': 'test@example.com',
        'password': 'ValidPass123!',
        'name': 'Test User',
    })
    assert response.status_code == 201


@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views._create_or_claim_signup_identity')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_response_includes_role(mock_create_or_claim, mock_validate, mock_get_token, mock_login):
    mock_create_or_claim.return_value = _mock_user()
    response = _post({
        'email': 'test@example.com',
        'password': 'ValidPass123!',
        'name': 'Test User',
    })
    assert response.status_code == 201
    assert response.data['role'] == 'user'
    assert response.data['is_premium'] is False


def test_signup_missing_email_returns_400():
    response = _post({'password': 'ValidPass123!', 'name': 'Test'})
    assert response.status_code == 400


def test_signup_missing_password_returns_400():
    response = _post({'email': 'test@example.com', 'name': 'Test'})
    assert response.status_code == 400
