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
    disease_state,
    therapy_categories,
    pod24,
    landmark_response,
    pathway_outcomes,
    transformation,
    eligibility,
)
from metrics.services.survival import landmark_os_km


MM_ONLY_DISEASES = {"multiple myeloma"}
FL_ONLY_DISEASES = {"follicular lymphoma"}


def _is_mm_request(request) -> bool:
    disease = (request.query_params.get("disease") or "").strip().lower()
    return disease in MM_ONLY_DISEASES


def _is_fl_request(request) -> bool:
    disease = (request.query_params.get("disease") or "").strip().lower()
    return disease in FL_ONLY_DISEASES


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def metrics(request):
    qs = apply_cohort_filters(request)

    qs, err = apply_org_scope(qs, request.user)
    if err:
        return err

    count = qs.count()
    if count == 0:
        # Eligibility is still useful on an empty cohort — the funnel shows
        # where the population dropped off.
        return Response({"cohort": {"count": 0}, "eligibility": eligibility.compute(request)})

    payload = {
        "cohort":              {"count": count},
        "eligibility":         eligibility.compute(request),
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
        "disease_state":             disease_state.compute(qs),
        "therapy_categories":        therapy_categories.compute(qs),
        "pod24":                     pod24.compute(qs),
        "landmark_response":         landmark_response.compute(qs),
        "pathway_outcomes":          pathway_outcomes.compute(qs),
    }

    if _is_mm_request(request):
        payload["subgroup_survival"] = subgroup_survival.compute(qs)
        payload["forest_plot"] = forest_plot.compute(qs)

    if _is_fl_request(request):
        # Transformed patients are recorded with DLBCL as their current disease,
        # so the cohort qs above excludes them — rebuild with them re-included
        # or the transformation chart can never see them.
        t_qs = apply_cohort_filters(request, include_transformed=True)
        t_qs, err = apply_org_scope(t_qs, request.user)
        if err:
            return err
        payload["transformation"] = transformation.compute(t_qs)

    return Response(payload)
