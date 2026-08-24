#!/usr/bin/env python3
"""Atomically replace the canonical FL/MM/BC patient cohorts in production.

Set SOURCE_DATABASE_URL to staging and TARGET_DATABASE_URL to production.  The
script preserves patient-record IDs, refreshes the corresponding person rows,
and copies record revisions.  It deliberately leaves identities, organizations,
and every non-target disease untouched.
"""

import os
from collections import Counter

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values


SOURCE_URL = os.environ["SOURCE_DATABASE_URL"]
TARGET_URL = os.environ["TARGET_DATABASE_URL"]
DISEASE_SLUGS = (
    "follicular-lymphoma",
    "multiple-myeloma",
    "malignant-tumor-of-breast",
)


def columns(conn, table):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = %s
               ORDER BY ordinal_position""",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def rows(conn, sql, params=()):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def insert_rows(cur, table, field_names, values, page_size=100):
    if not values:
        return
    quoted_fields = ", ".join(f'"{field}"' for field in field_names)
    execute_values(
        cur,
        f'INSERT INTO "{table}" ({quoted_fields}) VALUES %s',
        [row_values(row, field_names) for row in values],
        page_size=page_size,
    )


def row_values(row, field_names):
    return tuple(
        Json(value) if isinstance(value, (dict, list)) else value
        for value in (row[field] for field in field_names)
    )


def main():
    source = psycopg2.connect(SOURCE_URL)
    target = psycopg2.connect(TARGET_URL)
    try:
        source_patient_columns = columns(source, "patient_record")
        target_patient_columns = columns(target, "patient_record")
        patient_columns = [field for field in source_patient_columns if field in target_patient_columns]
        required_patient_columns = {"id", "person_id", "disease_slug", "organization_id", "death_date"}
        if not required_patient_columns.issubset(patient_columns):
            raise RuntimeError("production is missing required patient_record columns")
        skipped_patient_columns = sorted(set(source_patient_columns) - set(patient_columns))
        if skipped_patient_columns:
            print("not present in production; skipped:", skipped_patient_columns)

        patient_rows = rows(
            source,
            "SELECT * FROM patient_record WHERE disease_slug = ANY(%s) ORDER BY id",
            (list(DISEASE_SLUGS),),
        )
        patient_ids = [row["id"] for row in patient_rows]
        person_ids = [row["person_id"] for row in patient_rows]
        person_columns = [
            field for field in columns(source, "person") if field in columns(target, "person")
        ]
        revision_columns = [
            field for field in columns(source, "record_revision")
            if field in columns(target, "record_revision")
        ]
        if "person_id" not in person_columns or "patient_record_id" not in revision_columns:
            raise RuntimeError("production is missing required person or revision columns")
        person_rows = rows(source, "SELECT * FROM person WHERE person_id = ANY(%s)", (person_ids,))
        revision_rows = rows(
            source,
            "SELECT * FROM record_revision WHERE patient_record_id = ANY(%s) ORDER BY id",
            (patient_ids,),
        )

        expected = Counter(row["disease_slug"] for row in patient_rows)
        print("source cohorts:", dict(expected), "revisions:", len(revision_rows))

        with target:
            with target.cursor() as cur:
                cur.execute("SET CONSTRAINTS ALL DEFERRED")
                cur.execute(
                    """SELECT COUNT(*) FROM patient_record
                       WHERE id = ANY(%s) AND NOT (disease_slug = ANY(%s))""",
                    (patient_ids, list(DISEASE_SLUGS)),
                )
                if cur.fetchone()[0]:
                    raise RuntimeError("source IDs collide with non-target production patients")

                cur.execute(
                    """DELETE FROM record_revision
                       WHERE patient_record_id IN (
                           SELECT id FROM patient_record WHERE disease_slug = ANY(%s)
                       )""",
                    (list(DISEASE_SLUGS),),
                )
                cur.execute("DELETE FROM patient_record WHERE disease_slug = ANY(%s)", (list(DISEASE_SLUGS),))

                # Existing people can belong to a retained account; upsert the
                # demographic record instead of deleting the person row.
                if person_rows:
                    fields = person_columns
                    quoted_fields = ", ".join(f'"{field}"' for field in fields)
                    assignments = ", ".join(
                        f'"{field}" = EXCLUDED."{field}"'
                        for field in fields if field != "person_id"
                    )
                    execute_values(
                        cur,
                        f'INSERT INTO person ({quoted_fields}) VALUES %s '
                        f'ON CONFLICT (person_id) DO UPDATE SET {assignments}',
                        [row_values(row, fields) for row in person_rows],
                        page_size=500,
                    )

                insert_rows(cur, "patient_record", patient_columns, patient_rows)
                insert_rows(
                    cur,
                    "record_revision",
                    [field for field in revision_columns if field != "id"],
                    revision_rows,
                )

                # Preserve future auto-increment inserts after retaining source IDs.
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence('patient_record', 'id'), "
                    "GREATEST(COALESCE((SELECT MAX(id) FROM patient_record), 1), 1), true)"
                )
                cur.execute(
                    """SELECT disease_slug, COUNT(*) FROM patient_record
                       WHERE disease_slug = ANY(%s) GROUP BY disease_slug""",
                    (list(DISEASE_SLUGS),),
                )
                actual = dict(cur.fetchall())
                if actual != dict(expected):
                    raise RuntimeError(f"post-copy counts differ: expected {dict(expected)}, got {actual}")

        print("production copy complete:", dict(expected), "revisions:", len(revision_rows))
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
