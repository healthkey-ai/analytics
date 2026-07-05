from django.db import migrations


# Backfill is_premium from accounts_userprofile BEFORE dropping the table.
# Any user with role='premium' in UserProfile gets identity.is_premium=True.
# Migration 0005 adds the column with DEFAULT false, so without this step
# all premium users would silently lose access after the table is dropped.
BACKFILL_PREMIUM = """
UPDATE identity
SET is_premium = true
WHERE id IN (
    SELECT user_id FROM accounts_userprofile WHERE role = 'premium'
);
"""

# Copy org assignments from accounts_userprofile into PRomop's group_access
# BEFORE dropping the table. Wrapped in a DO block so it is a no-op when
# PRomop's tables don't exist (e.g., in the test DB).
#
# NOTE: This matches orgs by name across PRism's accounts_organization and
# PRomop's organization table. Verify the name join is correct before deploying:
#   SELECT ao.name, po.name
#   FROM accounts_userprofile up
#   JOIN accounts_organization ao ON ao.id = up.organization_id
#   JOIN organization po ON po.name = ao.name
#   WHERE up.organization_id IS NOT NULL;
BACKFILL_ORG_ACCESS = """
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'group_access'
    ) AND EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'organization'
    ) THEN
        INSERT INTO group_access (identity_id, org_id, role)
        SELECT up.user_id, po.id, 'member'
        FROM accounts_userprofile up
        JOIN accounts_organization ao ON ao.id = up.organization_id
        JOIN organization po ON po.name = ao.name
        WHERE up.organization_id IS NOT NULL
        ON CONFLICT DO NOTHING;
    END IF;
END $$;
"""


class Migration(migrations.Migration):
    """
    Drop the accounts_userprofile table — roles are now managed in PRomop.

    Data is backfilled before the drop:
    - role='premium' rows → identity.is_premium = True
    - organization assignments → group_access rows (when PRomop tables exist)
    """

    dependencies = [
        ("accounts", "0003_organization"),
    ]

    operations = [
        migrations.RunSQL(BACKFILL_PREMIUM, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(BACKFILL_ORG_ACCESS, reverse_sql=migrations.RunSQL.noop),
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
