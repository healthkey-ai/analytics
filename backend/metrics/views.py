from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cohorts.filters import apply_cohort_filters
from metrics.services import (
    response_rates,
    treatment_patterns,
    demographics,
    staging,
    labs,
    treatment_duration,
    survival,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def metrics(request):
    qs = apply_cohort_filters(request)
    count = qs.count()

    if count == 0:
        return Response({"cohort": {"count": 0}})

    return Response({
        "cohort":              {"count": count},
        "response_rates":      response_rates.compute(qs),
        "treatment_patterns":  treatment_patterns.compute(qs),
        "demographics":        demographics.compute(qs),
        "staging":             staging.compute(qs),
        "labs":                labs.compute(qs),
        "treatment_duration":  treatment_duration.compute(qs),
        "survival":            survival.compute(qs),
    })
