from collections import defaultdict


def _km_curve(times_events):
    """
    Kaplan-Meier estimator.
    times_events: list of (duration_months, event) where event=True means the endpoint occurred.
    Returns list of {time, survival, at_risk} step points.
    """
    if not times_events:
        return []

    buckets = defaultdict(lambda: {"d": 0, "c": 0})
    for t, event in times_events:
        if event:
            buckets[t]["d"] += 1
        else:
            buckets[t]["c"] += 1

    n        = len(times_events)
    at_risk  = n
    survival = 1.0
    result   = [{"time": 0.0, "survival": 1.0, "at_risk": n}]

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


def _median(curve):
    for pt in curve:
        if pt["survival"] <= 0.5:
            return pt["time"]
    return None


def _km_result(times_events):
    curve = _km_curve(times_events)
    return {"curve": curve, "n": len(times_events), "median": _median(curve)}


# ── OS ────────────────────────────────────────────────────────────────────────

def _os_km(qs):
    """
    OS: from 1st-line start to death_date.
    Censored at last_treatment if still alive.
    """
    rows = qs.values("first_line_start_date", "death_date", "last_treatment")
    times_events = []
    for r in rows:
        start = r["first_line_start_date"]
        if not start:
            continue
        if r["death_date"]:
            end, event = r["death_date"], True
        elif r["last_treatment"]:
            end, event = r["last_treatment"], False
        else:
            continue
        duration = (end - start).days / 30.44
        if duration <= 0:
            continue
        times_events.append((duration, event))
    return _km_result(times_events)


# ── PFS ───────────────────────────────────────────────────────────────────────

def _pfs_km(qs):
    """
    PFS: from 1st-line start to first documented Progressive Disease across any
    therapy line, or death — whichever comes first.
    Censored at last_treatment if no progression/death recorded.
    """
    rows = qs.values(
        "first_line_start_date",
        "first_line_end_date",  "first_line_outcome",
        "second_line_end_date", "second_line_outcome",
        "later_end_date",       "later_outcome",
        "death_date",           "last_treatment",
    )
    times_events = []
    for r in rows:
        start = r["first_line_start_date"]
        if not start:
            continue

        # Collect all PD-event dates across lines
        pd_dates = []
        for end_f, out_f in (
            ("first_line_end_date",  "first_line_outcome"),
            ("second_line_end_date", "second_line_outcome"),
            ("later_end_date",       "later_outcome"),
        ):
            if r[end_f] and (r[out_f] or "") == "Progressive Disease":
                pd_dates.append(r[end_f])

        if r["death_date"]:
            pd_dates.append(r["death_date"])

        if pd_dates:
            end, event = min(pd_dates), True
        else:
            end = r["last_treatment"]
            if not end:
                continue
            event = False

        duration = (end - start).days / 30.44
        if duration <= 0:
            continue
        times_events.append((duration, event))
    return _km_result(times_events)


# ── EFS ───────────────────────────────────────────────────────────────────────

def _efs_km(qs):
    """
    EFS: from 1st-line start to the earliest of:
      - Start of 2nd-line therapy (treatment change = event)
      - PD at 1st line (if no 2nd line)
      - Death
    Censored at 1st-line end if no event and patient alive.
    """
    rows = qs.values(
        "first_line_start_date", "first_line_end_date", "first_line_outcome",
        "second_line_start_date",
        "death_date",
    )
    times_events = []
    for r in rows:
        start = r["first_line_start_date"]
        if not start:
            continue

        candidates = []

        if r["second_line_start_date"]:
            # Needed next line = treatment failure
            candidates.append(r["second_line_start_date"])

        if r["first_line_end_date"] and (r["first_line_outcome"] or "") == "Progressive Disease":
            candidates.append(r["first_line_end_date"])

        if r["death_date"]:
            candidates.append(r["death_date"])

        if candidates:
            end, event = min(candidates), True
        elif r["first_line_end_date"]:
            end, event = r["first_line_end_date"], False
        else:
            continue

        duration = (end - start).days / 30.44
        if duration <= 0:
            continue
        times_events.append((duration, event))
    return _km_result(times_events)


# ── public interface ──────────────────────────────────────────────────────────

def compute(qs):
    return {
        "os":  _os_km(qs),
        "pfs": _pfs_km(qs),
        "efs": _efs_km(qs),
    }
