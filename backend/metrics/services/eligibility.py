"""
Eligibility / feasibility counts (FLF proposal §4 — industry & researchers).

Answers the sizing question: "how many patients fit this profile?" Starting
from the org-scoped population, the funnel records the cumulative patient
count after each cohort-filter group whose filters were applied, ending at
the eligible count. De-identified aggregate counts only.

Unlike other services this takes the request (not a qs): the funnel must
rebuild the queryset stage by stage from the unfiltered population, so it
cannot share the already-filtered cohort queryset. It does share the view's
org-scoped base queryset — org scoping is several queries for non-staff
users, so the view evaluates it once and passes it in.
"""
from cohorts.filters import apply_cohort_filters


def compute(request, base):
    steps = [{"key": "all", "label": "All patients", "count": base.count()}]
    apply_cohort_filters(request, qs=base, funnel=steps)

    total = steps[0]["count"]
    # No filters are applied after the last recorded step, so the last step's
    # count is the final cohort count — no second COUNT query needed.
    eligible = steps[-1]["count"]
    return {
        "total": total,
        "eligible": eligible,
        "eligible_pct": round(eligible / total * 100, 1) if total else 0,
        "steps": steps,
    }
