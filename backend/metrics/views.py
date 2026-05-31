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
    qs = apply_cohort_filters(request)
    records = list(qs.values())
    count = len(records)

    if count == 0:
        return Response({"cohort": {"count": 0}})

    return Response({
        "cohort":              {"count": count},
        "response_rates":      response_rates.compute(records),
        "treatment_patterns":  treatment_patterns.compute(records),
        "demographics":        demographics.compute(records),
        "staging":             staging.compute(records),
        "labs":                labs.compute(records),
        "treatment_duration":  treatment_duration.compute(records),
    })
