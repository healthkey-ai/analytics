from rest_framework.decorators import api_view
from rest_framework.response import Response

from cohorts.filters import apply_cohort_filters
from metrics.services import (
    response_rates,
    treatment_patterns,
    demographics,
    staging,
    labs,
    treatment_duration,
)


@api_view(["GET"])
def metrics(request):
    """
    Return all analytics metrics for the given cohort filters.
    Accepts the same query params as the cohort filter panel.
    """
    qs = apply_cohort_filters(request)
    count = qs.count()

    if count == 0:
        return Response({"cohort": {"count": 0}})

    return Response({
        "cohort": {"count": count},
        "response_rates":      response_rates.compute(qs),
        "treatment_patterns":  treatment_patterns.compute(qs),
        "demographics":        demographics.compute(qs),
        "staging":             staging.compute(qs),
        "labs":                labs.compute(qs),
        "treatment_duration":  treatment_duration.compute(qs),
    })
