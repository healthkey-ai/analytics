from collections import defaultdict
from django.db.models import Count


OUTCOME_ORDER = [
    "Complete Response",
    "Very Good Partial Response",
    "Partial Response",
    "Minimal Response",
    "Stable Disease",
    "Progressive Disease",
]
RESPONDING = {"Complete Response", "Very Good Partial Response", "Partial Response"}


def _therapy_response_table(qs, therapy_field, outcome_field):
    rows = (
        qs.exclude(**{f"{therapy_field}__isnull": True})
        .exclude(**{f"{therapy_field}__exact": ""})
        .values(therapy_field, outcome_field)
        .annotate(n=Count("id"))
        .order_by(therapy_field, outcome_field)
    )

    grouped = defaultdict(lambda: defaultdict(int))
    for r in rows:
        therapy = r[therapy_field] or "Unknown"
        outcome = r[outcome_field] or "Unknown"
        grouped[therapy][outcome] += r["n"]

    result = []
    for therapy, outcomes in grouped.items():
        total = sum(outcomes.values())
        responding = sum(v for k, v in outcomes.items() if k in RESPONDING)
        result.append({
            "therapy": therapy,
            "outcomes": {o: outcomes.get(o, 0) for o in OUTCOME_ORDER if outcomes.get(o)},
            "total": total,
            "orr_pct": round(responding / total * 100, 1) if total else 0,
        })

    result.sort(key=lambda x: -x["total"])
    return result


def compute(qs):
    return {
        "first_line": _therapy_response_table(qs, "first_line_therapy", "first_line_outcome"),
        "second_line": _therapy_response_table(qs, "second_line_therapy", "second_line_outcome"),
        "later_line": _therapy_response_table(qs, "later_therapy", "later_outcome"),
    }
