"""Tests for the signup view — org optional, domain-restricted orgs enforced."""
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from accounts.views import signup_view
from accounts.models import UserProfile


@contextmanager
def _noop_atomic():
    yield


def _post(data):
    factory = APIRequestFactory()
    request = factory.post('/api/auth/signup/', data, format='json')
    request.session = MagicMock()
    return signup_view(request)


def _mock_user(email='test@example.com', org='ABC Foundation'):
    mock_user = MagicMock()
    mock_user.uid = 'test-uid'
    mock_user.email = email
    mock_user.name = 'Test User'
    mock_user.is_staff = False
    mock_profile = MagicMock()
    mock_profile.role = UserProfile.ROLE_USER
    mock_profile.organization = org
    mock_user.profile = mock_profile
    return mock_user


# ---------------------------------------------------------------------------
# Org optional
# ---------------------------------------------------------------------------

@patch('accounts.views.UserProfile.objects.create')
@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views.Identity.objects.create_user')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_without_org_succeeds(
    mock_create_user, mock_validate, mock_get_token, mock_login, mock_profile_create
):
    mock_create_user.return_value = _mock_user(org='')

    response = _post({
        'email': 'test@example.com',
        'password': 'ValidPass123!',
        'name': 'Test User',
    })

    assert response.status_code == 201
    mock_profile_create.assert_called_once_with(
        user=mock_create_user.return_value, organization='', role=UserProfile.ROLE_USER
    )


@patch('accounts.views.UserProfile.objects.create')
@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views.Identity.objects.create_user')
@patch('accounts.views.Organization.objects.get')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_correct_domain_succeeds(
    mock_org_get, mock_create_user, mock_validate, mock_get_token, mock_login, mock_profile_create
):
    mock_org = MagicMock()
    mock_org.allowed_email_domain = 'hospital.org'
    mock_org_get.return_value = mock_org
    mock_create_user.return_value = _mock_user(email='doc@hospital.org', org='City Hospital')

    response = _post({
        'email': 'doc@hospital.org',
        'password': 'ValidPass123!',
        'name': 'Dr Smith',
        'organization': 'City Hospital',
    })

    assert response.status_code == 201


@patch('accounts.views.UserProfile.objects.create')
@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views.Identity.objects.create_user')
@patch('accounts.views.Organization.objects.get')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_open_org_any_email_succeeds(
    mock_org_get, mock_create_user, mock_validate, mock_get_token, mock_login, mock_profile_create
):
    mock_org = MagicMock()
    mock_org.allowed_email_domain = ''  # open org like ABC Foundation
    mock_org_get.return_value = mock_org
    mock_create_user.return_value = _mock_user(email='anyone@gmail.com', org='ABC Foundation')

    response = _post({
        'email': 'anyone@gmail.com',
        'password': 'ValidPass123!',
        'name': 'Anyone',
        'organization': 'ABC Foundation',
    })

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Profile created with correct org
# ---------------------------------------------------------------------------

@patch('accounts.views.UserProfile.objects.create')
@patch('accounts.views.login')
@patch('accounts.views.get_token')
@patch('accounts.views.validate_password')
@patch('accounts.views.Identity.objects.create_user')
@patch('accounts.views.Organization.objects.get')
@patch('accounts.views.transaction.atomic', _noop_atomic)
def test_signup_response_includes_role_and_org(
    mock_org_get, mock_create_user, mock_validate, mock_get_token, mock_login, mock_profile_create
):
    mock_org = MagicMock()
    mock_org.allowed_email_domain = ''
    mock_org_get.return_value = mock_org
    mock_create_user.return_value = _mock_user(org='ABC Foundation')

    response = _post({
        'email': 'test@example.com',
        'password': 'ValidPass123!',
        'name': 'Test User',
        'organization': 'ABC Foundation',
    })

    assert response.status_code == 201
    assert response.data['role'] == 'user'
    assert response.data['organization'] == 'ABC Foundation'
