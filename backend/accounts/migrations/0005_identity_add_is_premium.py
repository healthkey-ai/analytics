"""
Add is_premium to the identity table.

Uses ALTER TABLE … ADD COLUMN IF NOT EXISTS so it is idempotent: safe to run
whether PRomop has already added the column or not, and safe to run multiple
times. PRomop owns the identity table in production; this migration ensures the
column exists in standalone / test environments where PRomop hasn't run yet.
"""
from django.db import migrations

ADD_COLUMN = """
ALTER TABLE identity
    ADD COLUMN IF NOT EXISTS is_premium boolean NOT NULL DEFAULT false;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_remove_userprofile"),
    ]

    operations = [
        migrations.RunSQL(ADD_COLUMN, reverse_sql=migrations.RunSQL.noop),
    ]
