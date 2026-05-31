#!/usr/bin/env python3
"""
Backfill death_date for the 100 MM patients (person_id 300-399).

Death timing is calibrated against published real-world MM survival data:
  - 5-year OS ~55% with modern frontline therapy (SEER 2015-2021)
  - Post-progression survival (after last therapy) depends on line and outcome
  - High-risk cytogenetics carry ~1.5× mortality hazard

Target: ~50% of patients deceased by study cutoff 2026-05-31.
"""

import random
import psycopg2
from datetime import date, timedelta

DB_URL = (
    "postgresql://ctomop_dev_user:IehVp8TGNcelOymGcjtfL6Up6W63DOf2"
    "@dpg-d7pqr35ckfvc73bm0lc0-a.oregon-postgres.render.com/ctomop_dev"
)

random.seed(99)  # different seed so death dates are independent of treatment choices

CUTOFF = date(2026, 5, 31)


def add_months(d, months):
    if d is None:
        return None
    m   = d.month - 1 + months
    y   = d.year + m // 12
    mo  = m % 12 + 1
    day = min(d.day, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1])
    return date(y, mo, day)


# Months after last-treatment-end until death, by last outcome
POST_TX_MONTHS = {
    "Progressive Disease":        (1,  10),
    "Minimal Response":           (3,  18),
    "Stable Disease":             (4,  24),
    "Partial Response":           (8,  36),
    "Very Good Partial Response": (12, 48),
    "Complete Response":          (18, 60),
}

# Base probability of death by study cutoff, given last line outcome & n_lines
# Rows: last_outcome category (PD/poor, SD/MR, response)
# Cols: 1 line, 2 lines, 3 lines, 4 lines
DEATH_PROB = {
    "bad":      [0.72, 0.88, 0.94, 0.97],   # PD or MR at last line
    "moderate": [0.38, 0.56, 0.70, 0.80],   # SD at last line
    "good":     [0.14, 0.24, 0.36, 0.48],   # PR / VGPR / CR at last line
}

HIGH_RISK_MULTIPLIER = 1.40  # caps at 0.97


def classify_outcome(outcome):
    if outcome in ("Progressive Disease", "Minimal Response"):
        return "bad"
    if outcome in ("Stable Disease",):
        return "moderate"
    return "good"   # CR, VGPR, PR, None


def compute_death_date(row):
    fl_start = row["first_line_start_date"]
    if not fl_start:
        return None

    n_lines = row["therapy_lines_count"] or 1

    # Last line's end date and outcome
    if row["later_end_date"]:
        last_end     = row["later_end_date"]
        last_outcome = row["later_outcome"] or ""
    elif row["second_line_end_date"]:
        last_end     = row["second_line_end_date"]
        last_outcome = row["second_line_outcome"] or ""
    else:
        last_end     = row["first_line_end_date"]
        last_outcome = row["first_line_outcome"] or ""

    if not last_end:
        return None

    high_risk = bool(row["tp53_disruption"]) or (
        row["cytogenic_markers"] and any(
            m in (row["cytogenic_markers"] or "")
            for m in ["del(17p)", "t(4;14)", "t(14;16)"]
        )
    )

    cat   = classify_outcome(last_outcome)
    idx   = min(n_lines - 1, 3)
    prob  = DEATH_PROB[cat][idx]
    if high_risk:
        prob = min(0.97, prob * HIGH_RISK_MULTIPLIER)

    if random.random() > prob:
        return None  # patient is alive at cutoff

    lo, hi = POST_TX_MONTHS.get(last_outcome, (4, 24))
    months_after = random.randint(lo, hi)
    death = add_months(last_end, months_after)

    # Don't project deaths past study cutoff
    if death > CUTOFF:
        return None

    return death


def run():
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()

    cur.execute("""
        SELECT person_id,
               first_line_start_date, first_line_end_date, first_line_outcome,
               second_line_end_date,  second_line_outcome,
               later_end_date,        later_outcome,
               last_treatment, therapy_lines_count,
               tp53_disruption, cytogenic_markers
        FROM patient_info
        WHERE disease_slug = 'MM'
        ORDER BY person_id
    """)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    deaths = 0
    for row in rows:
        dd = compute_death_date(row)
        cur.execute(
            "UPDATE patient_info SET death_date = %s WHERE person_id = %s",
            (dd, row["person_id"])
        )
        if dd:
            deaths += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated {len(rows)} patients — {deaths} deaths ({100*deaths//len(rows)}%)")

    # Quick check
    conn2 = psycopg2.connect(DB_URL)
    cur2  = conn2.cursor()
    cur2.execute("""
        SELECT
            COUNT(*) FILTER (WHERE death_date IS NOT NULL) AS dead,
            COUNT(*) FILTER (WHERE death_date IS NULL)     AS alive,
            MIN(death_date), MAX(death_date),
            ROUND(AVG(EXTRACT(MONTH FROM AGE(death_date, first_line_start_date))
                      + 12 * EXTRACT(YEAR FROM AGE(death_date, first_line_start_date)))
                  FILTER (WHERE death_date IS NOT NULL), 1) AS avg_os_months
        FROM patient_info WHERE disease_slug = 'MM'
    """)
    print(dict(zip([d[0] for d in cur2.description], cur2.fetchone())))
    cur2.close()
    conn2.close()


if __name__ == "__main__":
    run()
