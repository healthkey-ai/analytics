"""Shared utilities for organisation-scoped querysets."""
import logging
from django.db import OperationalError, ProgrammingError
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


def get_admin_org_names(user) -> list[str]:
    """
    Return the sorted list of org names the user may administer.

    Admin access is granted via:
      - is_staff → all active orgs
      - direct org_admin grants
      - OrgTrust rows that match the user's email domain
      - OrgTrust rows that trust an org the user already belongs to

    Public aggregated-data visibility does not confer admin rights.
    """
    from .promop_models import PromopGroupAccess, PromopOrganization, PromopOrgTrust

    user_id = getattr(user, "pk", None)
    if not isinstance(user_id, int):
        user_id = getattr(user, "id", None)
    if not isinstance(user_id, int):
        return []

    try:
        if getattr(user, "is_staff", False):
            return sorted(
                PromopOrganization.objects.filter(is_active=True).values_list("name", flat=True)
            )

        now = timezone.now()
        email = getattr(user, "email", "") or ""
        access_identity_filter = Q(identity_id=user_id)
        if email:
            access_identity_filter |= Q(identity__email__iexact=email)

        active_access = PromopGroupAccess.objects.filter(
            access_identity_filter,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

        admin_names = set(
            active_access.filter(role="org_admin", org__isnull=False, org__is_active=True)
            .values_list("org__name", flat=True)
        )
        direct_names = set(
            active_access.filter(org__isnull=False, org__is_active=True)
            .values_list("org__name", flat=True)
        )
        group_org_names = set(
            active_access.filter(group__isnull=False, group__organization__is_active=True)
            .values_list("group__organization__name", flat=True)
        )
        direct_names |= group_org_names

        trusted_by_org = set(
            PromopOrgTrust.objects.filter(
                trusted_org__name__in=sorted(name for name in direct_names if name),
                trusted_org__is_active=True,
                granting_org__is_active=True,
            ).values_list("granting_org__name", flat=True)
        ) if direct_names else set()

        user_domain = email.split("@")[1].lower() if "@" in email else ""
        trusted_by_domain = set(
            PromopOrgTrust.objects.filter(
                trusted_domain__iexact=user_domain,
                granting_org__is_active=True,
            ).values_list("granting_org__name", flat=True)
        ) if user_domain else set()

        return sorted(admin_names | trusted_by_org | trusted_by_domain)
    except (ProgrammingError, OperationalError):
        return []


def has_org_admin_access(user) -> bool:
    """Return True when the user may administer at least one org."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False):
        return True
    return bool(get_admin_org_names(user))


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
