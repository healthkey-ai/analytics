"""Shared utilities for organisation-scoped querysets."""
import logging
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


_NO_ORG_RESPONSE = Response(
    {"detail": "No organisation assigned. Contact your administrator."},
    status=status.HTTP_403_FORBIDDEN,
)


def get_visible_org_names(user) -> list[str]:
    """
    Return the sorted list of org names this user may see aggregate data for.

    Access is granted via three mechanisms:
      - Public orgs: organizations with public_data=True are visible to all
        authenticated users regardless of their own org assignment.
      - Org-to-org trust: OrgTrust(granting_org=X, trusted_org=user's org)
        → user can see org X's patients
      - Domain trust: OrgTrust(granting_org=X, trusted_domain='example.com')
        → users with @example.com email can see org X's patients

    The user's own org is always included (if set).
    Do not call for ROLE_STAFF users — apply_org_scope handles that path
    by returning the queryset unmodified.
    """
    from .promop_models import PromopGroupAccess, PromopOrganization, PromopOrgTrust

    # Public orgs are visible to every authenticated user
    public_names: set[str] = set(
        PromopOrganization.objects.filter(
            allows_public_aggregated_data=True,
            is_active=True,
        )
        .values_list("name", flat=True)
    )

    now = timezone.now()
    email = getattr(user, "email", "") or ""
    access_identity_filter = Q(identity=user)
    if email:
        access_identity_filter |= Q(identity__email__iexact=email)

    active_access = PromopGroupAccess.objects.filter(
        access_identity_filter,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    direct_names = set(
        active_access.filter(org__isnull=False, org__is_active=True)
        .values_list("org__name", flat=True)
    )
    group_org_names = set(
        active_access.filter(group__isnull=False, group__organization__is_active=True)
        .values_list("group__organization__name", flat=True)
    )

    visible: set[str] = public_names | direct_names | group_org_names

    # ── domain trusts ─────────────────────────────────────────────────────────
    if "@" in email:
        user_domain = email.split("@")[1].lower()
        for name in PromopOrgTrust.objects.filter(
            trusted_domain__iexact=user_domain,
            granting_org__is_active=True,
        ).values_list("granting_org__name", flat=True):
            visible.add(name)

    # ── org-to-org trusts ─────────────────────────────────────────────────────
    # Domain access can grant access to an umbrella org; expand after domain
    # resolution and repeat until no newly trusted orgs appear.
    _MAX_TRUST_DEPTH = 10
    for _depth in range(_MAX_TRUST_DEPTH):
        trust_base_names = sorted(name for name in visible if name)
        if not trust_base_names:
            break
        trusted_names = set(
            PromopOrgTrust.objects.filter(
                trusted_org__name__in=trust_base_names,
                trusted_org__is_active=True,
                granting_org__is_active=True,
            ).values_list("granting_org__name", flat=True)
        )
        new_names = trusted_names - visible
        if not new_names:
            break
        visible.update(new_names)
    else:
        logger.warning(
            "get_visible_org_names: org-trust expansion hit depth limit (%d) for user email domain",
            _MAX_TRUST_DEPTH,
        )

    return sorted(visible)


def apply_org_scope(qs, user):
    """
    Restrict *qs* to the organisations the user is allowed to see.

    Returns (scoped_qs, error_response_or_None).
    If error_response is not None, the caller should return it immediately.

    - ROLE_STAFF           → unrestricted
    - Any authenticated user → filtered to get_visible_org_names(user), which
                               always includes public orgs plus the user's own
                               org and any trust-granted orgs.
    """
    if getattr(user, "is_staff", False) is True:
        return qs, None  # staff see everything

    visible = get_visible_org_names(user)
    if not visible:
        return None, _NO_ORG_RESPONSE

    return qs.filter(organization__name__in=visible), None
