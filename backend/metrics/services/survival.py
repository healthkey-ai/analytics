from metrics.services.km_utils import km_result as _km_result


# ── OS ────────────────────────────────────────────────────────────────────────

def _os_times_events(qs):
    """
    OS: from 1st-line start to death_date.
    Censored at last_treatment if still alive.
    Returns raw [(duration_months, event)] list.
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
    return times_events


def os_km(qs):
    return _km_result(_os_times_events(qs))


# ── PFS ───────────────────────────────────────────────────────────────────────

def _pfs_times_events(qs):
    """
    PFS: from 1st-line start to first documented Progressive Disease across any
    therapy line, or death — whichever comes first.
    Censored at last_treatment if no progression/death recorded.
    Returns raw [(duration_months, event)] list.
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
    return times_events


def pfs_km(qs):
    return _km_result(_pfs_times_events(qs))


# ── EFS ───────────────────────────────────────────────────────────────────────

def efs_km(qs):
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
        "os":  os_km(qs),
        "pfs": pfs_km(qs),
        "efs": efs_km(qs),
    }
