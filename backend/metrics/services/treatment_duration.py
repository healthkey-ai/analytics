from collections import Counter
from django.db import connection


def _duration_table(qs, therapy_f, outcome_f, start_f, end_f):
    subq_sql, params = qs.values('id').query.sql_with_params()

    # DATE - DATE in Postgres returns integer days; divide by 30.44 for months
    sql = f"""
        SELECT
            "{therapy_f}",
            COALESCE("{outcome_f}", 'Unknown') AS outcome,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ("{end_f}" - "{start_f}") / 30.44
            ) AS median_months,
            AVG(("{end_f}" - "{start_f}") / 30.44) AS mean_months,
            COUNT(*) AS cnt
        FROM patient_record
        WHERE id IN ({subq_sql})
          AND "{therapy_f}" IS NOT NULL AND "{therapy_f}" != ''
          AND "{start_f}" IS NOT NULL AND "{end_f}" IS NOT NULL
          AND "{end_f}" > "{start_f}"
        GROUP BY "{therapy_f}", COALESCE("{outcome_f}", 'Unknown')
        ORDER BY cnt DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    return [
        {
            "therapy":       row[0],
            "outcome":       row[1],
            "median_months": round(float(row[2]), 1) if row[2] is not None else 0,
            "mean_months":   round(float(row[3]), 1) if row[3] is not None else 0,
            "count":         row[4],
        }
        for row in rows
    ]


def _ttft_distribution(qs):
    subq_sql, params = qs.values('id').query.sql_with_params()

    sql = f"""
        SELECT
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY (first_line_start_date - diagnosis_date)
            ) AS median_days,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 0   AND 30  THEN 1 ELSE 0 END) AS b0_30,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 31  AND 60  THEN 1 ELSE 0 END) AS b31_60,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 61  AND 90  THEN 1 ELSE 0 END) AS b61_90,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 91  AND 180 THEN 1 ELSE 0 END) AS b91_180,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 181 AND 365 THEN 1 ELSE 0 END) AS b6_12m,
            SUM(CASE WHEN (first_line_start_date - diagnosis_date) BETWEEN 366 AND 730 THEN 1 ELSE 0 END) AS b12m
        FROM patient_record
        WHERE id IN ({subq_sql})
          AND diagnosis_date IS NOT NULL
          AND first_line_start_date IS NOT NULL
          AND (first_line_start_date - diagnosis_date) BETWEEN 0 AND 730
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()

    if not row or row[0] is None:
        return {"median_days": None, "distribution": []}

    labels = ["0–30d", "31–60d", "61–90d", "91–180d", "6–12m", ">12m"]
    dist = [
        {"bucket": label, "count": int(count)}
        for label, count in zip(labels, row[1:]) if count
    ]
    return {"median_days": round(float(row[0]), 0), "distribution": dist}


def compute(qs):
    return {
        "first_line":  _duration_table(qs, "first_line_therapy",  "first_line_outcome",
                                       "first_line_start_date",   "first_line_end_date"),
        "second_line": _duration_table(qs, "second_line_therapy", "second_line_outcome",
                                       "second_line_start_date",  "second_line_end_date"),
        "later_line":  _duration_table(qs, "later_therapy",       "later_outcome",
                                       "later_start_date",        "later_end_date"),
        "time_to_first_treatment": _ttft_distribution(qs),
    }
