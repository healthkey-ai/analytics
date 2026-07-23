"""
Eligibility / feasibility counts (FLF proposal §4 — industry & researchers).

Answers the sizing question: "how many patients fit this profile?" Starting
from the org-scoped population, the funnel records the cumulative patient
count after each cohort-filter group that actually narrowed the population,
ending at the eligible count. De-identified aggregate counts only.

Unlike other services this takes the request (not a qs): the funnel must
rebuild the queryset stage by stage from the unfiltered population, so it
cannot share the already-filtered cohort queryset.
"""
from accounts.utils import apply_org_scope
from cohorts.filters import apply_cohort_filters
from patients.models import PatientInfo


def compute(request):
    base, err = apply_org_scope(PatientInfo.objects.all(), request.user)
    if err is not None:
        return None

    steps = [{"key": "all", "label": "All patients", "count": base.count()}]
    final_qs = apply_cohort_filters(request, qs=base, funnel=steps)

    total = steps[0]["count"]
    eligible = final_qs.count()
    return {
        "total": total,
        "eligible": eligible,
        "eligible_pct": round(eligible / total * 100, 1) if total else 0,
        "steps": steps,
    }
