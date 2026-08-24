"""
Outcomes by treatment pathway: pick the most common first-line -> second-line
pathway combinations and compute overall survival for each, so two pathways
(e.g. BR -> BR vs BR -> R2) can be compared side by side.

Reliable only where each pathway has enough patients — combos below MIN_N are
dropped, and the UI shows each pathway's n.
"""
from metrics.services.km_utils import km_result

# The deterministic MM demo cohort has 100 patients distributed across many
# clinically plausible regimens.  Its most common exact 1L -> 2L combination
# has eight patients, so a threshold of ten makes this analysis impossible to
# render even when every patient has complete follow-up.  Five remains large
# enough to suppress one-off pathways while keeping the comparison available
# for the intended synthetic cohort.
MIN_N = 5
MAX_PATHWAYS = 5
_DAYS_PER_MONTH = 30.44

_FIELDS = (
    "first_line_therapy",
    "second_line_therapy",
    "first_line_start_date",
    "death_date",
    "last_treatment",
)


def _short(name):
    if not name:
        return "—"
    idx = name.find(" (")
    return name[:idx] if idx > 0 else name[:30]


def _os_times_events(row):
    """OS from 1L start to death; censored at last_treatment. Mirrors survival._os_times_events."""
    start = row["first_line_start_date"]
    if not start:
        return None
    if row["death_date"]:
        end, event = row["death_date"], True
    elif row["last_treatment"]:
        end, event = row["last_treatment"], False
    else:
        return None
    duration = (end - start).days / _DAYS_PER_MONTH
    if duration <= 0:
        return None
    return (duration, event)


def compute(qs):
    rows = qs.values(*_FIELDS)

    combos = {}
    for row in rows:
        first, second = row["first_line_therapy"], row["second_line_therapy"]
        if not first or not second:
            continue
        combos.setdefault((first, second), []).append(row)

    # Rank by patient count, keep the top combos with enough patients
    ranked = sorted(combos.items(), key=lambda kv: -len(kv[1]))
    pathways = []
    for (first, second), combo_rows in ranked:
        if len(combo_rows) < MIN_N or len(pathways) >= MAX_PATHWAYS:
            continue
        te = [t for t in (_os_times_events(r) for r in combo_rows) if t]
        pathways.append({
            "label": f"{_short(first)} → {_short(second)}",
            "n": len(combo_rows),
            "os": km_result(te),
        })

    return {"min_n": MIN_N, "pathways": pathways}
