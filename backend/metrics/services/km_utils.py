import math
from collections import defaultdict


def km_curve(times_events):
    """
    Kaplan-Meier estimator.
    times_events: list of (duration_months, event) where event=True means the endpoint occurred.
    Returns list of {time, survival, at_risk, ci_lower, ci_upper} step points.
    CI is computed via Greenwood's formula (plain linear / Wald interval on S).
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

    n         = len(times_events)
    at_risk   = n
    survival  = 1.0
    greenwood = 0.0  # running Greenwood variance sum: sum d/(n*(n-d))
    result    = [{"time": 0.0, "survival": 1.0, "at_risk": n,
                  "ci_lower": 1.0, "ci_upper": 1.0}]

    for t in sorted(buckets):
        d = buckets[t]["d"]
        c = buckets[t]["c"]
        if d > 0 and at_risk > 0:
            survival *= 1 - d / at_risk
            # Skip Greenwood update when n == d to avoid division by zero
            if at_risk != d:
                greenwood += d / (at_risk * (at_risk - d))
            se = survival * math.sqrt(greenwood)
            result.append({
                "time":     t,
                "survival": round(survival, 4),
                "at_risk":  at_risk,  # at_risk before events, per KM convention
                "ci_lower": round(max(0.0, survival - 1.96 * se), 4),
                "ci_upper": round(min(1.0, survival + 1.96 * se), 4),
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


def log_rank_p(groups_te):
    """
    Generalized K-group log-rank test.
    groups_te: list of [(duration_months, event)] lists, one per group.
    Returns p-value (float, 4 dp) or None if not computable (< 2 non-empty groups,
    no events, or singular covariance matrix).
    """
    import numpy as np
    from scipy import stats

    # Keep only non-empty groups
    groups = [te for te in groups_te if te]
    K = len(groups)
    if K < 2:
        return None

    # Collect all event times (only actual events, de-duplicated)
    event_times = sorted({round(dur, 1) for te in groups for dur, ev in te if ev})
    if not event_times:
        return None

    O = np.zeros(K)
    E = np.zeros(K)
    V = np.zeros((K, K))

    for t in event_times:
        n_k = np.array([
            sum(1 for dur, _ in te if round(dur, 1) >= t)
            for te in groups
        ], dtype=float)
        d_k = np.array([
            sum(1 for dur, ev in te if round(dur, 1) == t and ev)
            for te in groups
        ], dtype=float)

        n = n_k.sum()
        d = d_k.sum()

        if n <= 1 or d == 0:
            continue

        O += d_k
        E += n_k * d / n

        factor = d * (n - d) / (n * n * (n - 1))
        for k in range(K):
            for l in range(K):
                if k == l:
                    V[k, l] += n_k[k] * (n - n_k[k]) * factor
                else:
                    V[k, l] += -n_k[k] * n_k[l] * factor

    Z = (O - E)[: K - 1]
    V_red = V[: K - 1, : K - 1]

    try:
        stat = float(Z @ np.linalg.inv(V_red) @ Z)
        if stat < 0:
            return None
        return round(float(stats.chi2.sf(stat, df=K - 1)), 4)
    except (np.linalg.LinAlgError, ValueError):
        return None
