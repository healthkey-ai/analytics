from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.utils import apply_org_scope
from cohorts.filters import apply_cohort_filters
from metrics.services import (
    response_rates,
    treatment_patterns,
    demographics,
    staging,
    labs,
    treatment_duration,
    survival,
    ttnt,
    switching,
    subgroup_survival,
    pathway_sunburst,
    dor,
    forest_plot,
    cohort_characterization,
    incidence,
    time_to_treatment,
)
from metrics.services.survival import landmark_os_km


MM_ONLY_DISEASES = {"multiple myeloma"}


def _is_mm_request(request) -> bool:
    disease = (request.query_params.get("disease") or "").strip().lower()
    return disease in MM_ONLY_DISEASES


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def metrics(request):
    qs = apply_cohort_filters(request)

    qs, err = apply_org_scope(qs, request.user)
    if err:
        return err

    count = qs.count()
    if count == 0:
        return Response({"cohort": {"count": 0}})

    payload = {
        "cohort":              {"count": count},
        "response_rates":      response_rates.compute(qs),
        "treatment_patterns":  treatment_patterns.compute(qs),
        "demographics":        demographics.compute(qs),
        "staging":             staging.compute(qs),
        "labs":                labs.compute(qs),
        "treatment_duration":  treatment_duration.compute(qs),
        "survival":            survival.compute(qs),
        "ttnt":                ttnt.compute(qs),
        "switching":           switching.compute(qs),
        "pathway_sunburst":          pathway_sunburst.compute(qs),
        "dor":                       dor.compute(qs),
        "cohort_characterization":   cohort_characterization.compute(qs),
        "incidence":                 incidence.compute(qs),
        "time_to_treatment":         time_to_treatment.compute(qs),
        "landmark_survival":         landmark_os_km(qs),
    }

    if _is_mm_request(request):
        payload["subgroup_survival"] = subgroup_survival.compute(qs)
        payload["forest_plot"] = forest_plot.compute(qs)

    return Response(payload)
