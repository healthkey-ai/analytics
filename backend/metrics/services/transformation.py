"""
Transformation to aggressive lymphoma (FL → DLBCL).

Answers, for a follicular lymphoma cohort:
  - How many patients transformed (count + share of evaluable cohort)
  - When — months from diagnosis to documented transformation (median + histogram)
  - How they did afterward — post-transformation outcome distribution and
    overall survival measured from the transformation date

Transformation is a soft call: not every patient is biopsied, so this is shown
only where a transformation is documented (`transformed_to_dlbcl` is not null
= evaluable). The UI must state that caveat (per the FLF proposal).

Data fields (PROMOP #226): transformed_to_dlbcl, dlbcl_transformation_date,
post_transformation_outcome (vocab: CR / PR / SD / PD / Deceased / Unknown).
"""
from metrics.services.km_utils import km_result

_DAYS_PER_MONTH = 30.44

# Histogram buckets in months from diagnosis to transformation
_BINS = [(0, 12), (12, 24), (24, 36), (36, 60), (60, None)]

OUTCOME_ORDER = ["CR", "PR", "SD", "PD", "Deceased", "Unknown"]


def _histogram(months_list):
    out = []
    for lo, hi in _BINS:
        label = f"{lo}–{hi}" if hi is not None else f"{lo}+"
        count = sum(
            1 for m in months_list
            if lo <= m and (hi is None or m < hi)
        )
        out.append({"label": label, "count": count, "lo": lo, "hi": hi})
    return out


def _median(sorted_vals):
    n = len(sorted_vals)
    if not n:
        return None
    mid = n // 2
    if n % 2:
        return round(sorted_vals[mid], 1)
    return round((sorted_vals[mid - 1] + sorted_vals[mid]) / 2, 1)


def compute(qs):
    rows = qs.values(
        "transformed_to_dlbcl",
        "dlbcl_transformation_date",
        "post_transformation_outcome",
        "diagnosis_date",
        "death_date",
        "last_treatment",
    )

    evaluable = 0
    transformed = []
    unknown = 0
    for row in rows:
        flag = row["transformed_to_dlbcl"]
        if flag is None:
            unknown += 1
            continue
        evaluable += 1
        if flag:
            transformed.append(row)

    # When — months from diagnosis to transformation
    months_list = sorted(
        (r["dlbcl_transformation_date"] - r["diagnosis_date"]).days / _DAYS_PER_MONTH
        for r in transformed
        if r["dlbcl_transformation_date"] and r["diagnosis_date"]
        and r["dlbcl_transformation_date"] >= r["diagnosis_date"]
    )
    time_to_transformation = {
        "n": len(months_list),
        "median_months": _median(months_list),
        "histogram": _histogram(months_list),
    }

    # How they did afterward — outcome distribution
    outcome_counts = {o: 0 for o in OUTCOME_ORDER}
    outcome_recorded = 0
    for r in transformed:
        outcome = r["post_transformation_outcome"] or "Unknown"
        if outcome not in outcome_counts:
            outcome = "Unknown"
        outcome_counts[outcome] += 1
        outcome_recorded += 1
    outcome_distribution = [
        {
            "outcome": o,
            "count": outcome_counts[o],
            "pct": round(outcome_counts[o] / outcome_recorded * 100, 1)
            if outcome_recorded else 0,
        }
        for o in OUTCOME_ORDER
        if outcome_counts[o]
    ]

    # OS from transformation date to death; censored at last_treatment
    times_events = []
    for r in transformed:
        start = r["dlbcl_transformation_date"]
        if not start:
            continue
        if r["death_date"] and r["death_date"] >= start:
            end, event = r["death_date"], True
        elif r["last_treatment"] and r["last_treatment"] >= start:
            end, event = r["last_treatment"], False
        else:
            continue
        duration = (end - start).days / _DAYS_PER_MONTH
        if duration <= 0:
            continue
        times_events.append((duration, event))

    return {
        "evaluable": evaluable,
        "unknown": unknown,
        "transformed_count": len(transformed),
        "transformed_pct": round(len(transformed) / evaluable * 100, 1) if evaluable else 0,
        "time_to_transformation": time_to_transformation,
        "outcome_distribution": outcome_distribution,
        "os_post_transformation": km_result(times_events),
    }
