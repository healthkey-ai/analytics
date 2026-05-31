import statistics
from collections import defaultdict


def _duration_months(start, end):
    if not start or not end:
        return None
    delta = (end - start).days
    return round(delta / 30.44, 1) if delta > 0 else None


def _duration_table(records, therapy_f, outcome_f, start_f, end_f):
    grouped = defaultdict(lambda: defaultdict(list))
    for r in records:
        therapy = r.get(therapy_f)
        if not therapy:
            continue
        dur = _duration_months(r.get(start_f), r.get(end_f))
        if dur is not None:
            outcome = r.get(outcome_f) or "Unknown"
            grouped[therapy][outcome].append(dur)

    result = []
    for therapy, outcomes in grouped.items():
        for outcome, durations in outcomes.items():
            result.append({
                "therapy":       therapy,
                "outcome":       outcome,
                "median_months": round(statistics.median(durations), 1),
                "mean_months":   round(statistics.mean(durations), 1),
                "count":         len(durations),
            })

    result.sort(key=lambda x: (-x["count"], x["therapy"]))
    return result


def _ttft_distribution(records):
    days_list = []
    for r in records:
        dx = r.get("diagnosis_date")
        fl = r.get("first_line_start_date")
        if not dx or not fl:
            continue
        d = (fl - dx).days
        if 0 <= d <= 730:
            days_list.append(d)

    if not days_list:
        return {"median_days": None, "distribution": []}

    buckets = [
        (0,   30,  "0–30d"),
        (31,  60,  "31–60d"),
        (61,  90,  "61–90d"),
        (91,  180, "91–180d"),
        (181, 365, "6–12m"),
        (366, 730, ">12m"),
    ]
    dist = [
        {"bucket": label, "count": sum(1 for d in days_list if lo <= d <= hi)}
        for lo, hi, label in buckets
        if sum(1 for d in days_list if lo <= d <= hi)
    ]

    return {
        "median_days": round(statistics.median(days_list), 0),
        "distribution": dist,
    }


def compute(records):
    return {
        "first_line":  _duration_table(records, "first_line_therapy",  "first_line_outcome",
                                       "first_line_start_date",  "first_line_end_date"),
        "second_line": _duration_table(records, "second_line_therapy", "second_line_outcome",
                                       "second_line_start_date", "second_line_end_date"),
        "later_line":  _duration_table(records, "later_therapy",       "later_outcome",
                                       "later_start_date",       "later_end_date"),
        "time_to_first_treatment": _ttft_distribution(records),
    }
