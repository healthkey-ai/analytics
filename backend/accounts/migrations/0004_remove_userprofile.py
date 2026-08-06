from django.db import migrations


# Ensure the column exists before backfilling — 0005 uses ADD COLUMN IF NOT
# EXISTS too, so whichever migration runs first wins and the other is a no-op.
ADD_IS_PREMIUM = """
ALTER TABLE identity
    ADD COLUMN IF NOT EXISTS is_premium boolean NOT NULL DEFAULT false;
"""

# Backfill is_premium from accounts_userprofile BEFORE dropping the table.
# Any user with role='premium' in UserProfile gets identity.is_premium=True.
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
# UserProfile.organization is a CharField (text), not a FK, so we join
# directly on the name rather than through accounts_organization.
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
        INSERT INTO group_access (identity_id, org_id, role, granted_at)
        SELECT up.user_id, po.id, 'member', NOW()
        FROM accounts_userprofile up
        JOIN organization po ON po.name = up.organization
        WHERE up.organization IS NOT NULL AND up.organization <> ''
        ON CONFLICT DO NOTHING;
    END IF;
END $$;
"""


def backfill_profile_data(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(ADD_IS_PREMIUM)
    schema_editor.execute(BACKFILL_PREMIUM)
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(BACKFILL_ORG_ACCESS)


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
        migrations.RunPython(backfill_profile_data, reverse_code=migrations.RunPython.noop),
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
