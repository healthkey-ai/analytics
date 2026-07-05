"""
Read-only unmanaged mirrors of PROMOP's shared-DB tables.

PRism and PROMOP share the same PostgreSQL database. These models let PRism
read PROMOP's organisation and trust tables without owning or migrating them.
"""
from django.db import models


class PromopOrganization(models.Model):
    """Mirror of PROMOP's `organization` table."""
    name                          = models.CharField(max_length=200)
    slug                          = models.SlugField(max_length=60, unique=True)
    is_active                     = models.BooleanField(default=True)
    allows_public_aggregated_data = models.BooleanField(default=False)

    class Meta:
        managed  = False
        db_table = "organization"

    def __str__(self):
        return self.name


class PromopOrgTrust(models.Model):
    """
    Mirror of PROMOP's `org_trust` table.

    Each row means: granting_org's patient data is accessible to users of
    trusted_org (org-to-org mode) or to users whose email matches
    trusted_domain (domain mode). Exactly one of trusted_org / trusted_domain
    is set per row (enforced by a DB CHECK constraint in PROMOP).
    """
    granting_org  = models.ForeignKey(
        PromopOrganization, on_delete=models.DO_NOTHING,
        db_column="granting_org_id", related_name="trusts_granted",
    )
    trusted_org   = models.ForeignKey(
        PromopOrganization, on_delete=models.DO_NOTHING,
        db_column="trusted_org_id", related_name="trusted_by",
        null=True, blank=True,
    )
    trusted_domain = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        managed  = False
        db_table = "org_trust"


class PromopPatientGroup(models.Model):
    """Mirror of PROMOP's `patient_group` table for group-based org grants."""
    organization = models.ForeignKey(
        PromopOrganization, on_delete=models.DO_NOTHING,
        db_column="organization_id", related_name="+",
    )

    class Meta:
        managed = False
        db_table = "patient_group"


class PromopGroupAccess(models.Model):
    """Mirror of PROMOP's `group_access` table."""
    identity = models.ForeignKey(
        "accounts.Identity",
        on_delete=models.DO_NOTHING,
        db_column="identity_id",
        related_name="+",
        db_constraint=False,
    )
    org = models.ForeignKey(
        PromopOrganization,
        on_delete=models.DO_NOTHING,
        db_column="org_id",
        related_name="+",
        null=True,
        blank=True,
    )
    group = models.ForeignKey(
        PromopPatientGroup,
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="+",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "group_access"
