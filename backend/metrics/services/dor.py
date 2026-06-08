from metrics.services.km_utils import km_result

NON_RESPONDING = {"Progressive Disease", "Stable Disease", "SD", "PD"}


def _dor_times_events(qs, line_start_f, line_outcome_f, next_start_f):
    """
    Duration of Response KM for one therapy line.
    Excludes non-responders (PD, SD, null/empty outcome).
    Event = earliest of next_start_f or death_date.
    Censored at last_treatment.
    Returns [(duration_months, event)] list.
    """
    rows = qs.values(line_start_f, line_outcome_f, next_start_f, "death_date", "last_treatment")
    times_events = []
    for r in rows:
        outcome = (r[line_outcome_f] or "").strip()
        if not outcome or outcome in NON_RESPONDING:
            continue

        start = r[line_start_f]
        if not start:
            continue

        candidates = []
        if r[next_start_f]:
            candidates.append(r[next_start_f])
        if r["death_date"]:
            candidates.append(r["death_date"])

        if candidates:
            end, event = min(candidates), True
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


def compute(qs):
    qs1 = qs.exclude(first_line_therapy__isnull=True).exclude(first_line_therapy__exact="")
    qs2 = qs.exclude(second_line_therapy__isnull=True).exclude(second_line_therapy__exact="")

    te_1l = _dor_times_events(
        qs1,
        line_start_f="first_line_start_date",
        line_outcome_f="first_line_outcome",
        next_start_f="second_line_start_date",
    )
    te_2l = _dor_times_events(
        qs2,
        line_start_f="second_line_start_date",
        line_outcome_f="second_line_outcome",
        next_start_f="later_start_date",
    )

    return {
        "first_line":  km_result(te_1l),
        "second_line": km_result(te_2l),
    }
