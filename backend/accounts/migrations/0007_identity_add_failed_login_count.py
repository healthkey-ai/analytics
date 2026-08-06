"""
Sync identity columns that PROMOP added after PRism's initial migration.

In production these columns already exist (PROMOP owns the schema).
ADD COLUMN IF NOT EXISTS / PRAGMA checks make every branch a safe no-op.

Source of truth: /Users/adam/promop/patient_portal/models.py Identity model.
"""
from django.db import migrations

_SQLITE_COLUMNS = [
    ("failed_login_count",   "integer NOT NULL DEFAULT 0"),
    ("must_change_password", "bool NOT NULL DEFAULT 0"),
    ("locked_until",         "datetime"),
]

_PG_COLUMNS = [
    ("failed_login_count",   "integer NOT NULL DEFAULT 0"),
    ("must_change_password", "boolean NOT NULL DEFAULT false"),
    ("locked_until",         "timestamptz"),
]


def add_columns(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        cursor = schema_editor.connection.cursor()
        cursor.execute("PRAGMA table_info(identity)")
        existing = {row[1] for row in cursor.fetchall()}
        for col, defn in _SQLITE_COLUMNS:
            if col not in existing:
                schema_editor.execute(f"ALTER TABLE identity ADD COLUMN {col} {defn}")
    else:
        for col, defn in _PG_COLUMNS:
            schema_editor.execute(
                f"ALTER TABLE identity ADD COLUMN IF NOT EXISTS {col} {defn}"
            )


def remove_columns(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        for col, _ in _PG_COLUMNS:
            schema_editor.execute(
                f"ALTER TABLE identity DROP COLUMN IF EXISTS {col}"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_passwordresettoken"),
    ]

    operations = [
        migrations.RunPython(add_columns, reverse_code=remove_columns),
    ]
