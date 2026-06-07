from collections import defaultdict


def km_curve(times_events):
    """
    Kaplan-Meier estimator.
    times_events: list of (duration_months, event) where event=True means the endpoint occurred.
    Returns list of {time, survival, at_risk} step points.
    """
    if not times_events:
        return []

    buckets = defaultdict(lambda: {"d": 0, "c": 0})
    for t, event in times_events:
        t_key = round(t, 1)  # bucket at display precision so same-month events merge
        if event:
            buckets[t_key]["d"] += 1
        else:
            buckets[t_key]["c"] += 1

    n        = len(times_events)
    at_risk  = n
    survival = 1.0
    result   = [{"time": 0.0, "survival": 1.0, "at_risk": n}]

    for t in sorted(buckets):
        d = buckets[t]["d"]
        c = buckets[t]["c"]
        if d > 0 and at_risk > 0:
            survival *= 1 - d / at_risk
            result.append({
                "time":     t,
                "survival": round(survival, 4),
                "at_risk":  at_risk,  # at_risk before events, per KM convention
            })
        at_risk -= d + c

    return result


def km_median(curve):
    for pt in curve:
        if pt["survival"] <= 0.5:
            return pt["time"]
    return None


def km_result(times_events):
    curve = km_curve(times_events)
    return {"curve": curve, "n": len(times_events), "median": km_median(curve)}
