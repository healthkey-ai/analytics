"""
Creates the `identity` table if it doesn't already exist.

In production, this table is owned by ctomop which runs first. This migration
is a no-op in that case (CREATE TABLE IF NOT EXISTS). In standalone/dev
environments where ctomop hasn't run yet, it creates the table so analytics
can work independently.
"""
from django.db import migrations, models


CREATE_IDENTITY = """
CREATE TABLE IF NOT EXISTS identity (
    id          bigserial PRIMARY KEY,
    password    varchar(128)  NOT NULL,
    last_login  timestamptz,
    is_superuser boolean NOT NULL DEFAULT false,
    issuer      varchar(255)  NOT NULL,
    sub         varchar(255)  NOT NULL,
    uid         varchar(512)  NOT NULL,
    email       varchar(254)  NOT NULL,
    name        varchar(255)  NOT NULL DEFAULT '',
    is_active   boolean       NOT NULL DEFAULT true,
    is_staff    boolean       NOT NULL DEFAULT false,
    created_at  timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT identity_uid_key UNIQUE (uid)
);
-- Partial unique index so one email maps to at most one local account.
-- CREATE INDEX IF NOT EXISTS is idempotent; safe to run against ctomop's table.
CREATE UNIQUE INDEX IF NOT EXISTS identity_local_email_uidx
    ON identity (lower(email))
    WHERE issuer = 'urn:local';
"""

CREATE_IDENTITY_GROUPS = """
CREATE TABLE IF NOT EXISTS accounts_identity_groups (
    id          bigserial PRIMARY KEY,
    identity_id bigint NOT NULL REFERENCES identity(id) ON DELETE CASCADE,
    group_id    integer NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    CONSTRAINT accounts_identity_groups_identity_id_group_id_key UNIQUE (identity_id, group_id)
);
"""

CREATE_IDENTITY_USER_PERMISSIONS = """
CREATE TABLE IF NOT EXISTS accounts_identity_user_permissions (
    id              bigserial PRIMARY KEY,
    identity_id     bigint NOT NULL REFERENCES identity(id) ON DELETE CASCADE,
    permission_id   integer NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    CONSTRAINT accounts_identity_user_permissions_identity_id_permission_id_key
        UNIQUE (identity_id, permission_id)
);
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunSQL(CREATE_IDENTITY, reverse_sql="DROP TABLE IF EXISTS identity CASCADE;"),
        migrations.RunSQL(CREATE_IDENTITY_GROUPS, reverse_sql="DROP TABLE IF EXISTS accounts_identity_groups;"),
        migrations.RunSQL(CREATE_IDENTITY_USER_PERMISSIONS, reverse_sql="DROP TABLE IF EXISTS accounts_identity_user_permissions;"),
        # Register the unmanaged Identity model in Django's migration state so that
        # lazy FK references (e.g. cohorts.SavedCohort.user) can be resolved.
        # No SQL runs; the table is created above (or already exists via ctomop).
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Identity",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("password", models.CharField(max_length=128, verbose_name="password")),
                        ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                        ("is_superuser", models.BooleanField(default=False)),
                        ("issuer", models.CharField(max_length=255)),
                        ("sub", models.CharField(max_length=255)),
                        ("uid", models.CharField(max_length=512, unique=True)),
                        ("email", models.EmailField(max_length=254)),
                        ("name", models.CharField(blank=True, max_length=255)),
                        ("is_active", models.BooleanField(default=True)),
                        ("is_staff", models.BooleanField(default=False)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("groups", models.ManyToManyField(
                            blank=True,
                            related_name="user_set",
                            related_query_name="user",
                            to="auth.group",
                            verbose_name="groups",
                        )),
                        ("user_permissions", models.ManyToManyField(
                            blank=True,
                            related_name="user_set",
                            related_query_name="user",
                            to="auth.permission",
                            verbose_name="user permissions",
                        )),
                    ],
                    options={
                        "db_table": "identity",
                        "managed": False,
                    },
                ),
            ],
        ),
    ]
