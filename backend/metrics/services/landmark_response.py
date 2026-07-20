"""
Landmark response rates (CR30 & configurable landmarks).

For each landmark M months, report the proportion of evaluable first-line
patients who achieved a complete response within M months of starting
first-line therapy.

  - CR by M        — 1L outcome is a complete response AND the 1L end date is
                     within M months of the 1L start date.
  - Evaluable at M — 1L start date known AND (1L end date known OR follow-up
                     (last_treatment / death) reaches at least M months).

Clock start is explicitly the first-line treatment start date, surfaced in the
payload as `clock_start` per the proposal's limitation note.
"""

CR_OUTCOMES = {"Complete Response", "sCR"}
LANDMARK_MONTHS = [12, 24, 30, 36]
_DAYS_PER_MONTH = 30.44


def compute(qs, landmarks=None):
    landmarks = landmarks or LANDMARK_MONTHS
    rows = qs.values(
        "first_line_start_date",
        "first_line_end_date",
        "first_line_outcome",
        "death_date",
        "last_treatment",
    )

    results = [{"months": m, "cr_count": 0, "evaluable": 0} for m in landmarks]

    for row in rows:
        start = row["first_line_start_date"]
        if not start:
            continue
        end = row["first_line_end_date"]
        follow_up = row["last_treatment"] or row["death_date"]
        is_cr = (row["first_line_outcome"] or "") in CR_OUTCOMES

        for entry in results:
            months = entry["months"]
            days = months * _DAYS_PER_MONTH
            evaluable = (end is not None) or (
                follow_up is not None and (follow_up - start).days >= days
            )
            if not evaluable:
                continue
            entry["evaluable"] += 1
            if is_cr and end and (end - start).days <= days:
                entry["cr_count"] += 1

    for entry in results:
        entry["pct"] = (
            round(entry["cr_count"] / entry["evaluable"] * 100, 1)
            if entry["evaluable"]
            else 0
        )

    return {"clock_start": "first_line_start_date", "landmarks": results}
