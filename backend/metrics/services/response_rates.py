from collections import defaultdict


OUTCOME_ORDER = [
    "Complete Response",
    "Very Good Partial Response",
    "Partial Response",
    "Minimal Response",
    "Stable Disease",
    "Progressive Disease",
]
RESPONDING = {"Complete Response", "Very Good Partial Response", "Partial Response"}


def _therapy_response_table(records, therapy_field, outcome_field):
    grouped = defaultdict(lambda: defaultdict(int))
    for r in records:
        therapy = r.get(therapy_field)
        if not therapy:
            continue
        outcome = r.get(outcome_field) or "Unknown"
        grouped[therapy][outcome] += 1

    result = []
    for therapy, outcomes in grouped.items():
        total = sum(outcomes.values())
        responding = sum(v for k, v in outcomes.items() if k in RESPONDING)
        result.append({
            "therapy": therapy,
            "outcomes": {o: outcomes[o] for o in OUTCOME_ORDER if outcomes.get(o)},
            "total": total,
            "orr_pct": round(responding / total * 100, 1) if total else 0,
        })

    result.sort(key=lambda x: -x["total"])
    return result


def compute(records):
    return {
        "first_line":  _therapy_response_table(records, "first_line_therapy",  "first_line_outcome"),
        "second_line": _therapy_response_table(records, "second_line_therapy", "second_line_outcome"),
        "later_line":  _therapy_response_table(records, "later_therapy",       "later_outcome"),
    }
