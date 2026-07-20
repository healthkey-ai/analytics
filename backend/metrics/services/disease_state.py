"""
Disease-state snapshot: derive a mutually exclusive disease state per patient.

There is no explicit disease-state field on patient_info, so states are derived
heuristically from treatment and outcome fields, in priority order:

1. Relapsed/Refractory — received 2+ lines, has a recorded relapse, or had
   Progressive Disease as any line outcome.
2. In Remission — treated, best 1L outcome is a response (CR/VGPR/PR), and no
   later line.
3. Watch & Wait — diagnosed > 6 months ago, never started first-line therapy.
4. Newly Diagnosed — diagnosed within the last 6 months, never started
   first-line therapy.
5. Other/Unknown — insufficient data to classify.

Because these are derived, the UI must state the derivation rules.
"""
import datetime

RESPONSE_OUTCOMES = {"Complete Response", "Very Good Partial Response", "Partial Response"}
NEWLY_DIAGNOSED_MONTHS = 6
_DAYS_PER_MONTH = 30.44

STATE_LABELS = [
    ("newly_diagnosed", "Newly Diagnosed"),
    ("watch_and_wait", "Watch & Wait"),
    ("in_remission", "In Remission"),
    ("relapsed_refractory", "Relapsed / Refractory"),
    ("other", "Other / Unknown"),
]


def _classify(row, today):
    first_outcome = row["first_line_outcome"] or ""
    later_outcomes = (row["second_line_outcome"] or "", row["later_outcome"] or "")
    lines = row["therapy_lines_count"] or 0
    relapses = row["relapse_count"] or 0

    if (
        lines >= 2
        or relapses > 0
        or "Progressive Disease" in (first_outcome, *later_outcomes)
    ):
        return "relapsed_refractory"

    if row["first_line_start_date"]:
        if first_outcome in RESPONSE_OUTCOMES:
            return "in_remission"
        return "other"

    if row["diagnosis_date"]:
        months_since_dx = (today - row["diagnosis_date"]).days / _DAYS_PER_MONTH
        if months_since_dx <= NEWLY_DIAGNOSED_MONTHS:
            return "newly_diagnosed"
        return "watch_and_wait"

    return "other"


def compute(qs, today=None):
    today = today or datetime.date.today()
    rows = qs.values(
        "diagnosis_date",
        "first_line_start_date",
        "first_line_outcome",
        "second_line_outcome",
        "later_outcome",
        "therapy_lines_count",
        "relapse_count",
    )

    total = 0
    counts = {key: 0 for key, _ in STATE_LABELS}
    for row in rows:
        counts[_classify(row, today)] += 1
        total += 1

    return {
        "states": [
            {
                "key": key,
                "label": label,
                "count": counts[key],
                "pct": round(counts[key] / total * 100, 1) if total else 0,
            }
            for key, label in STATE_LABELS
        ],
        "total": total,
    }
