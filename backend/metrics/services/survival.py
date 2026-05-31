from collections import defaultdict


def _km_curve(times_events):
    """
    Kaplan-Meier estimator.
    times_events: list of (duration_months, event) where event=True means progression.
    Returns list of {time, survival, at_risk} step points.
    """
    if not times_events:
        return []

    # Aggregate events and censored at each time point
    buckets = defaultdict(lambda: {"d": 0, "c": 0})
    for t, event in times_events:
        if event:
            buckets[t]["d"] += 1
        else:
            buckets[t]["c"] += 1

    n = len(times_events)
    at_risk = n
    survival = 1.0
    result = [{"time": 0.0, "survival": 1.0, "at_risk": n}]

    for t in sorted(buckets):
        d = buckets[t]["d"]
        c = buckets[t]["c"]
        if d > 0:
            survival *= 1 - d / at_risk
            result.append({
                "time":     round(t, 1),
                "survival": round(survival, 4),
                "at_risk":  at_risk - d,
            })
        at_risk -= d + c

    return result


def _median_pfs(curve):
    for pt in curve:
        if pt["survival"] <= 0.5:
            return pt["time"]
    return None


def _line_km(qs, therapy_f, outcome_f, start_f, end_f):
    rows = (
        qs.exclude(**{f"{therapy_f}__isnull": True})
        .exclude(**{f"{therapy_f}__exact": ""})
        .values(outcome_f, start_f, end_f)
    )

    times_events = []
    for r in rows:
        start = r[start_f]
        end = r[end_f]
        if not start or not end:
            continue
        duration = (end - start).days / 30.44
        if duration <= 0:
            continue
        event = (r[outcome_f] or "") == "Progressive Disease"
        times_events.append((duration, event))

    curve = _km_curve(times_events)
    return {
        "curve":      curve,
        "n":          len(times_events),
        "median_pfs": _median_pfs(curve),
    }


def compute(qs):
    return {
        "first_line":  _line_km(qs, "first_line_therapy",  "first_line_outcome",
                                "first_line_start_date",  "first_line_end_date"),
        "second_line": _line_km(qs, "second_line_therapy", "second_line_outcome",
                                "second_line_start_date", "second_line_end_date"),
        "later_line":  _line_km(qs, "later_therapy",       "later_outcome",
                                "later_start_date",       "later_end_date"),
    }
