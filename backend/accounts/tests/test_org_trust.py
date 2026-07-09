"""Tests for get_visible_org_names — PROMOP org trust resolution."""
import pytest
from unittest.mock import MagicMock, patch
from accounts.utils import get_visible_org_names


def _make_user(email='user@example.com'):
    user = MagicMock()
    user.email = email
    return user


def _promop_org(name, org_id=1):
    org = MagicMock()
    org.id = org_id
    org.name = name
    return org


@pytest.fixture(autouse=True)
def mock_group_access():
    with patch('accounts.promop_models.PromopGroupAccess') as MockAccess:
        active = MockAccess.objects.filter.return_value.filter.return_value
        active.filter.return_value.values_list.return_value = []
        yield MockAccess


# ── no group access / no org ──────────────────────────────────────────────────

@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_no_group_access_returns_empty(MockOrg, MockTrust):
    MockOrg.objects.filter.return_value.values_list.return_value = []
    MockTrust.objects.filter.return_value.values_list.return_value = []
    user = _make_user()
    assert get_visible_org_names(user) == []


@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_no_org_returns_empty(MockOrg, MockTrust):
    MockOrg.objects.filter.return_value.values_list.return_value = []
    MockTrust.objects.filter.return_value.values_list.return_value = []
    user = _make_user()
    assert get_visible_org_names(user) == []


# ── org-to-org trusts ─────────────────────────────────────────────────────────

@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_org_to_org_trust_includes_granting_orgs(MockOrg, MockTrust, mock_group_access):
    MockOrg.DoesNotExist = Exception
    active = mock_group_access.objects.filter.return_value.filter.return_value

    def access_filter(**kwargs):
        qs = MagicMock()
        if kwargs.get('org__isnull') is False:
            qs.values_list.return_value = ['HealthTree Trust']
        else:
            qs.values_list.return_value = []
        return qs

    active.filter.side_effect = access_filter

    def trust_filter(**kwargs):
        qs = MagicMock()
        if 'trusted_org__name__in' in kwargs:
            qs.values_list.return_value = ['Hospital A', 'Hospital B']
        else:
            qs.values_list.return_value = []
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='user@healthtree.org')
    result = get_visible_org_names(user)
    assert 'HealthTree Trust' in result
    assert 'Hospital A' in result
    assert 'Hospital B' in result
    assert result == sorted(result)  # always sorted


@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_no_trusts_returns_own_org_only(MockOrg, MockTrust, mock_group_access):
    MockOrg.DoesNotExist = Exception
    active = mock_group_access.objects.filter.return_value.filter.return_value

    def access_filter(**kwargs):
        qs = MagicMock()
        if kwargs.get('org__isnull') is False:
            qs.values_list.return_value = ['Acme Cancer Center']
        else:
            qs.values_list.return_value = []
        return qs

    active.filter.side_effect = access_filter

    def trust_filter(**kwargs):
        qs = MagicMock()
        qs.values_list.return_value = []
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='doc@acme.org')
    result = get_visible_org_names(user)
    assert result == ['Acme Cancer Center']


# ── domain trusts ─────────────────────────────────────────────────────────────

@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_domain_trust_includes_granting_org(MockOrg, MockTrust):
    own = _promop_org('HealthTree Trust')
    MockOrg.objects.get.return_value = own
    MockOrg.DoesNotExist = Exception

    def trust_filter(**kwargs):
        qs = MagicMock()
        if 'trusted_org__name__in' in kwargs:
            qs.values_list.return_value = []
        else:
            # domain trust hit: @healthtree.org → Hospital C
            qs.values_list.return_value = ['Hospital C']
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='analyst@healthtree.org')
    result = get_visible_org_names(user)
    assert 'Hospital C' in result


@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_domain_trusted_umbrella_org_expands_org_to_org_trusts(MockOrg, MockTrust):
    MockOrg.objects.filter.return_value.values_list.return_value = []

    def trust_filter(**kwargs):
        qs = MagicMock()
        if kwargs.get('trusted_domain__iexact') == 'healthtree.org':
            qs.values_list.return_value = ['HealthTree Trust']
        elif kwargs.get('trusted_org__name__in') == ['HealthTree Trust']:
            qs.values_list.return_value = ['ABC Foundation', 'BBC Foundation']
        elif kwargs.get('trusted_org__name__in') == ['ABC Foundation', 'BBC Foundation', 'HealthTree Trust']:
            qs.values_list.return_value = ['ABC Foundation', 'BBC Foundation']
        else:
            qs.values_list.return_value = []
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    result = get_visible_org_names(_make_user(email='analyst@healthtree.org'))

    assert result == ['ABC Foundation', 'BBC Foundation', 'HealthTree Trust']


@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_no_email_skips_domain_trust(MockOrg, MockTrust):
    own = _promop_org('Clinic X')
    MockOrg.objects.get.return_value = own
    MockOrg.DoesNotExist = Exception

    call_count = {'domain': 0}

    def trust_filter(**kwargs):
        qs = MagicMock()
        if 'trusted_domain__iexact' in kwargs:
            call_count['domain'] += 1
        qs.values_list.return_value = []
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='')
    get_visible_org_names(user)
    assert call_count['domain'] == 0  # domain path skipped when no email


@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_promop_direct_org_grant_expands_trusted_orgs(MockOrg, MockTrust, mock_group_access):
    active = mock_group_access.objects.filter.return_value.filter.return_value

    def access_filter(**kwargs):
        qs = MagicMock()
        if kwargs.get('org__isnull') is False:
            qs.values_list.return_value = ['HealthTree Trust']
        else:
            qs.values_list.return_value = []
        return qs

    active.filter.side_effect = access_filter

    def trust_filter(**kwargs):
        qs = MagicMock()
        if kwargs.get('trusted_org__name__in') == ['HealthTree Trust']:
            qs.values_list.return_value = ['ABC Foundation', 'BBC Foundation']
        else:
            qs.values_list.return_value = []
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='adam@cancerbot.org')
    result = get_visible_org_names(user)

    assert result == ['ABC Foundation', 'BBC Foundation', 'HealthTree Trust']


# ── deduplication ─────────────────────────────────────────────────────────────

@patch('accounts.promop_models.PromopOrgTrust')
@patch('accounts.promop_models.PromopOrganization')
def test_same_org_via_org_and_domain_trust_not_duplicated(MockOrg, MockTrust):
    """If an org grants access via both org-to-org AND domain trust, it appears once."""
    own = _promop_org('HealthTree Trust')
    MockOrg.objects.get.return_value = own
    MockOrg.DoesNotExist = Exception

    def trust_filter(**kwargs):
        qs = MagicMock()
        qs.values_list.return_value = ['Hospital A']  # both paths return the same org
        return qs

    MockTrust.objects.filter.side_effect = trust_filter

    user = _make_user(email='user@healthtree.org')
    result = get_visible_org_names(user)
    assert result.count('Hospital A') == 1
