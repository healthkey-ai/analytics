from metrics.services.km_utils import km_curve, km_median, km_result


def _ttnt_km(qs, end_f, next_start_f):
    """
    TTNT Kaplan-Meier for one line transition.
      end_f        – field: end of current line
      next_start_f – field: start of next line (event if present)
    Event = patient started the next therapy line.
    Censored = no next line; time = (death_date or last_treatment) - end_f.
    """
    rows = qs.values(end_f, next_start_f, "death_date", "last_treatment")
    times_events = []
    for r in rows:
        end = r[end_f]
        if not end:
            continue
        next_start = r[next_start_f]
        if next_start:
            duration = (next_start - end).days / 30.44
            event = True
        else:
            censor = r["death_date"] or r["last_treatment"]
            if not censor or censor <= end:
                continue
            duration = (censor - end).days / 30.44
            event = False
        if duration <= 0:
            continue
        times_events.append((duration, event))

    return km_result(times_events)


def compute(qs):
    # Only include patients who actually received the prior line
    qs1 = qs.exclude(first_line_therapy__isnull=True).exclude(first_line_therapy__exact="")
    qs2 = qs.exclude(second_line_therapy__isnull=True).exclude(second_line_therapy__exact="")

    return {
        "line_1_to_2": _ttnt_km(
            qs1,
            end_f="first_line_end_date",
            next_start_f="second_line_start_date",
        ),
        "line_2_to_3": _ttnt_km(
            qs2,
            end_f="second_line_end_date",
            next_start_f="later_start_date",
        ),
    }
