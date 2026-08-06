"""
Add failed_login_count to the identity table.

In production the column already exists (PROMOP owns the schema).
The Postgres branch uses ADD COLUMN IF NOT EXISTS so it is a no-op there.
The SQLite branch checks PRAGMA table_info so it is safe on existing test DBs.
"""
from django.db import migrations


def add_column(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        cursor = schema_editor.connection.cursor()
        cursor.execute("PRAGMA table_info(identity)")
        columns = [row[1] for row in cursor.fetchall()]
        if "failed_login_count" not in columns:
            schema_editor.execute(
                "ALTER TABLE identity ADD COLUMN failed_login_count integer NOT NULL DEFAULT 0"
            )
    else:
        schema_editor.execute(
            "ALTER TABLE identity ADD COLUMN IF NOT EXISTS failed_login_count integer NOT NULL DEFAULT 0"
        )


def remove_column(apps, schema_editor):
    # Postgres only; SQLite doesn't support DROP COLUMN on older versions and
    # production owns this column via PROMOP anyway.
    if schema_editor.connection.vendor != "sqlite":
        schema_editor.execute(
            "ALTER TABLE identity DROP COLUMN IF EXISTS failed_login_count"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_passwordresettoken"),
    ]

    operations = [
        migrations.RunPython(add_column, reverse_code=remove_column),
    ]
