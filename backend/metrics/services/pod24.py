"""
POD24 split: separate patients who progressed within 24 months of first-line
treatment start from those who did not, and compare overall survival.

Clock start is explicitly the first-line treatment start date
(`first_line_start_date`) — this is surfaced in the payload as `clock_start`
so the UI can state it, per the proposal's limitation note.

Progression event date = earliest of:
  - any line end date where that line's outcome was "Progressive Disease"
  - second-line start date (treatment change acts as a progression surrogate,
    consistent with the EFS definition in survival.py)
  - death date

Groups:
  - pod24        — event within 24 months of 1L start
  - no_pod24     — event after 24 months, or no event with >= 24 months follow-up
  - unevaluable  — no 1L start date, or censored before 24 months with no event
"""
from metrics.services.km_utils import km_result, log_rank_p

POD24_MONTHS = 24.0
_DAYS_PER_MONTH = 30.44

_FIELDS = (
    "first_line_start_date",
    "first_line_end_date", "first_line_outcome",
    "second_line_end_date", "second_line_outcome",
    "later_end_date", "later_outcome",
    "second_line_start_date",
    "death_date", "last_treatment",
)


def _event_date(row):
    candidates = []
    for end_f, out_f in (
        ("first_line_end_date", "first_line_outcome"),
        ("second_line_end_date", "second_line_outcome"),
        ("later_end_date", "later_outcome"),
    ):
        if row[end_f] and (row[out_f] or "") == "Progressive Disease":
            candidates.append(row[end_f])
    if row["second_line_start_date"]:
        candidates.append(row["second_line_start_date"])
    if row["death_date"]:
        candidates.append(row["death_date"])
    return min(candidates) if candidates else None


def _classify(row):
    """Return 'pod24' | 'no_pod24' | 'unevaluable' for one patient row."""
    start = row["first_line_start_date"]
    if not start:
        return "unevaluable"

    event = _event_date(row)
    if event:
        months = (event - start).days / _DAYS_PER_MONTH
        return "pod24" if months <= POD24_MONTHS else "no_pod24"

    follow_up_end = row["last_treatment"] or row["death_date"]
    if follow_up_end:
        months = (follow_up_end - start).days / _DAYS_PER_MONTH
        if months >= POD24_MONTHS:
            return "no_pod24"
    return "unevaluable"


def _os_times_events(row):
    """OS from 1L start to death; censored at last_treatment. Mirrors survival._os_times_events."""
    start = row["first_line_start_date"]
    if not start:
        return None
    if row["death_date"]:
        end, event = row["death_date"], True
    elif row["last_treatment"]:
        end, event = row["last_treatment"], False
    else:
        return None
    duration = (end - start).days / _DAYS_PER_MONTH
    if duration <= 0:
        return None
    return (duration, event)


def compute(qs):
    rows = qs.values(*_FIELDS)

    groups = {"pod24": [], "no_pod24": [], "unevaluable": 0}
    for row in rows:
        key = _classify(row)
        if key == "unevaluable":
            groups["unevaluable"] += 1
        else:
            te = _os_times_events(row)
            if te:
                groups[key].append(te)

    pod24_te = groups["pod24"]
    no_pod24_te = groups["no_pod24"]
    evaluable = len(pod24_te) + len(no_pod24_te) + groups["unevaluable"]
    classified = len(pod24_te) + len(no_pod24_te)

    return {
        "clock_start": "first_line_start_date",
        "window_months": POD24_MONTHS,
        "groups": [
            {
                "key": "pod24",
                "label": "POD24",
                "count": len(pod24_te),
                "pct": round(len(pod24_te) / classified * 100, 1) if classified else 0,
            },
            {
                "key": "no_pod24",
                "label": "No POD24",
                "count": len(no_pod24_te),
                "pct": round(len(no_pod24_te) / classified * 100, 1) if classified else 0,
            },
            {
                "key": "unevaluable",
                "label": "Unevaluable (< 24 months follow-up)",
                "count": groups["unevaluable"],
                "pct": round(groups["unevaluable"] / evaluable * 100, 1) if evaluable else 0,
            },
        ],
        "os": [
            {"label": "POD24", **km_result(pod24_te)},
            {"label": "No POD24", **km_result(no_pod24_te)},
        ],
        "os_p": log_rank_p([pod24_te, no_pod24_te]),
    }
