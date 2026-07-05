"""
Add is_premium to the identity table and register it in Django's ORM state.

Uses ALTER TABLE … ADD COLUMN IF NOT EXISTS so it is idempotent: safe to run
whether PRomop has already added the column or not, and safe to run multiple
times. PRomop owns the identity table in production; this migration ensures the
column exists in standalone / test environments where PRomop hasn't run yet.

SeparateDatabaseAndState is used so the RunSQL DB operation and the AddField
ORM-state update are kept in sync. Without the state operation, makemigrations
would generate a spurious AddField on every fresh clone.
"""
from django.db import migrations, models

ADD_COLUMN = """
ALTER TABLE identity
    ADD COLUMN IF NOT EXISTS is_premium boolean NOT NULL DEFAULT false;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_remove_userprofile"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(ADD_COLUMN, reverse_sql=migrations.RunSQL.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="Identity",
                    name="is_premium",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
