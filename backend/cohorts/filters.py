import datetime

from django.db.models import Q
from django.utils import timezone
from cohorts.stage_utils import expand_stage_filter_values
from patients.models import PatientInfo
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT, NO_SCT


def apply_cohort_filters(request, include_transformed=False, qs=None, funnel=None) -> "QuerySet[PatientInfo]":
    """
    Build a PatientInfo queryset from GET query parameters.

    All multi-value params use the same key repeated, e.g. stage=ISS+Stage+I&stage=ISS+Stage+II.
    Boolean params accept "true" / "false" strings.

    include_transformed: broaden the disease filter to also match patients with a
    documented FL→DLBCL transformation (transformed_to_dlbcl=True), whose current
    disease is recorded as DLBCL. Used by the transformation analytics — without
    it those patients are filtered out of their own chart.

    qs: base queryset to start from (defaults to PatientInfo.objects.all()).

    funnel: optional list; when provided, a {"key", "label", "count"} step is
    appended after each filter group for which at least one filter was applied.
    Used by the eligibility/feasibility analytics. Requires an explicitly
    org-scoped qs= — otherwise step counts would span every org's patients.
    """
    if funnel is not None and qs is None:
        raise ValueError("funnel= requires an explicitly org-scoped qs= base queryset")

    qs = qs if qs is not None else PatientInfo.objects.all()
    p = request.query_params

    def _step(key, label, applied):
        if funnel is not None and applied:
            funnel.append({"key": key, "label": label, "count": qs.count()})

    def _bool(key):
        v = p.get(key, "").lower()
        if v == "true":
            return True
        if v == "false":
            return False
        return None

    def _list(key):
        return [v for v in p.getlist(key) if v]

    def _int(key, default=None):
        try:
            return int(p[key])
        except (KeyError, ValueError, TypeError):
            return default

    def _float(key, default=None):
        try:
            return float(p[key])
        except (KeyError, ValueError, TypeError):
            return default

    # ── disease & stage ───────────────────────────────────────────────────────
    disease = p.get("disease")
    if disease:
        if include_transformed:
            qs = qs.filter(Q(disease__icontains=disease) | Q(transformed_to_dlbcl=True))
        else:
            qs = qs.filter(disease__icontains=disease)

    stages = _list("stage")
    if stages:
        stages = expand_stage_filter_values(stages, disease)
        qs = qs.filter(stage__in=stages)
    _step("disease_stage", "Disease & stage", bool(disease) or bool(stages))

    # ── demographics ──────────────────────────────────────────────────────────
    applied = False

    age_min = _int("age_min")
    age_max = _int("age_max")
    if age_min is not None:
        qs = qs.filter(patient_age__gte=age_min)
        applied = True
    if age_max is not None:
        qs = qs.filter(patient_age__lte=age_max)
        applied = True

    gender = p.get("gender")
    if gender:
        applied = True
        normalized_gender = gender.strip().lower()
        gender_values = {
            "m": ["M", "m", "Male", "male", "MALE"],
            "male": ["M", "m", "Male", "male", "MALE"],
            "f": ["F", "f", "Female", "female", "FEMALE"],
            "female": ["F", "f", "Female", "female", "FEMALE"],
        }.get(normalized_gender)
        if gender_values:
            qs = qs.filter(gender__in=gender_values)
        else:
            qs = qs.filter(gender__iexact=gender)

    races = _list("race")
    if races:
        qs = qs.filter(race__in=races)
        applied = True

    smoking = _list("smoking_status")
    if smoking:
        qs = qs.filter(smoking_status__in=smoking)
        applied = True

    _step("demographics", "Demographics", applied)

    # ── geography ─────────────────────────────────────────────────────────────
    applied = False

    countries = _list("country")
    if countries:
        qs = qs.filter(country__in=countries)
        applied = True

    regions = _list("region")
    if regions:
        qs = qs.filter(region__in=regions)
        applied = True

    # Note: this filter is meaningful only for staff (and future trusted-org) users.
    # For regular users, apply_org_scope (called in the view layer) enforces row-level
    # org isolation via an exact-match filter regardless of what org= is passed here.
    org = p.get("org")
    if org:
        qs = qs.filter(organization__name__iexact=org)
        applied = True

    _step("geography", "Geography", applied)

    # ── performance status ────────────────────────────────────────────────────
    applied = False

    ecog_vals = [int(v) for v in _list("ecog") if v.isdigit()]
    if ecog_vals:
        qs = qs.filter(ecog_performance_status__in=ecog_vals)
        applied = True

    kps_min = _int("kps_min")
    kps_max = _int("kps_max")
    if kps_min is not None:
        qs = qs.filter(karnofsky_performance_score__gte=kps_min)
        applied = True
    if kps_max is not None:
        qs = qs.filter(karnofsky_performance_score__lte=kps_max)
        applied = True

    _step("performance", "Performance status", applied)

    # ── cytogenetics & risk ───────────────────────────────────────────────────
    applied = False

    cyto_markers = _list("cytogenetic_markers")
    if cyto_markers:
        q = Q()
        for m in cyto_markers:
            q |= Q(cytogenic_markers__icontains=m)
        qs = qs.filter(q)
        applied = True

    high_risk = _bool("high_risk_cytogenetics")
    if high_risk is True:
        qs = qs.filter(HIGH_RISK_CYTO)
        applied = True
    elif high_risk is False:
        qs = qs.exclude(HIGH_RISK_CYTO)
        applied = True

    tp53 = _bool("tp53_disruption")
    if tp53 is not None:
        qs = qs.filter(tp53_disruption=tp53)
        applied = True

    _step("cytogenetics", "Cytogenetics & risk", applied)

    # ── treatment history ─────────────────────────────────────────────────────
    applied = False

    lines_min = _int("therapy_lines_min")
    lines_max = _int("therapy_lines_max")
    if lines_min is not None:
        qs = qs.filter(therapy_lines_count__gte=lines_min)
        applied = True
    if lines_max is not None:
        qs = qs.filter(therapy_lines_count__lte=lines_max)
        applied = True

    fl_therapies = _list("first_line_therapy")
    if fl_therapies:
        qs = qs.filter(first_line_therapy__in=fl_therapies)
        applied = True

    sl_therapies = _list("second_line_therapy")
    if sl_therapies:
        qs = qs.filter(second_line_therapy__in=sl_therapies)
        applied = True

    lt_therapies = _list("later_therapy")
    if lt_therapies:
        qs = qs.filter(later_therapy__in=lt_therapies)
        applied = True

    fl_outcomes = _list("first_line_outcome")
    if fl_outcomes:
        qs = qs.filter(first_line_outcome__in=fl_outcomes)
        applied = True

    sl_outcomes = _list("second_line_outcome")
    if sl_outcomes:
        qs = qs.filter(second_line_outcome__in=sl_outcomes)
        applied = True

    lt_outcomes = _list("later_outcome")
    if lt_outcomes:
        qs = qs.filter(later_outcome__in=lt_outcomes)
        applied = True

    refractory = _list("refractory_status")
    if refractory:
        qs = qs.filter(treatment_refractory_status__in=refractory)
        applied = True

    _step("treatment_history", "Treatment history", applied)

    # ── disease characteristics ───────────────────────────────────────────────
    applied = False

    meets_crab = _bool("meets_crab")
    if meets_crab is not None:
        qs = qs.filter(meets_crab=meets_crab)
        applied = True

    has_bone = _bool("has_bone_lesions")
    if has_bone is True:
        qs = qs.exclude(bone_lesions="No bone lesions").exclude(bone_lesions__isnull=True)
        applied = True
    elif has_bone is False:
        qs = qs.filter(Q(bone_lesions="No bone lesions") | Q(bone_lesions__isnull=True))
        applied = True

    has_sct = _bool("has_sct")
    if has_sct is True:
        qs = qs.filter(HAS_SCT)
        applied = True
    elif has_sct is False:
        qs = qs.filter(NO_SCT)
        applied = True

    pcl = _bool("plasma_cell_leukemia")
    if pcl is not None:
        qs = qs.filter(plasma_cell_leukemia=pcl)
        applied = True

    mrd = _list("mrd_status")
    if mrd:
        qs = qs.filter(mrd_status__in=mrd)
        applied = True

    er_statuses = _list("er_status")
    if er_statuses:
        qs = qs.filter(estrogen_receptor_status__in=er_statuses)
        applied = True

    her2_statuses = _list("her2_status")
    if her2_statuses:
        qs = qs.filter(her2_status__in=her2_statuses)
        applied = True

    tnbc = _bool("tnbc_status")
    if tnbc is not None:
        qs = qs.filter(tnbc_status=tnbc)
        applied = True

    _step("disease_characteristics", "Disease characteristics", applied)

    # ── labs ──────────────────────────────────────────────────────────────────
    applied = False

    hgb_min = _float("hemoglobin_min")
    hgb_max = _float("hemoglobin_max")
    if hgb_min is not None:
        qs = qs.filter(hemoglobin_g_dl__gte=hgb_min)
        applied = True
    if hgb_max is not None:
        qs = qs.filter(hemoglobin_g_dl__lte=hgb_max)
        applied = True

    cr_max = _float("creatinine_max")
    if cr_max is not None:
        qs = qs.filter(serum_creatinine_mg_dl__lte=cr_max)
        applied = True

    b2m_min = _float("b2m_min")
    b2m_max = _float("b2m_max")
    if b2m_min is not None:
        qs = qs.filter(beta2_microglobulin__gte=b2m_min)
        applied = True
    if b2m_max is not None:
        qs = qs.filter(beta2_microglobulin__lte=b2m_max)
        applied = True

    _step("labs", "Labs", applied)

    # ── diagnosis period ──────────────────────────────────────────────────────
    applied = False

    dx_year_min = _int("diagnosis_year_min")
    dx_year_max = _int("diagnosis_year_max")
    if dx_year_min is not None:
        qs = qs.filter(diagnosis_date__year__gte=dx_year_min)
        applied = True
    if dx_year_max is not None:
        qs = qs.filter(diagnosis_date__year__lte=dx_year_max)
        applied = True

    date_window = p.get("date")
    if date_window:
        now = timezone.now().date()
        if date_window == "7d":
            qs = qs.filter(diagnosis_date__gte=now - datetime.timedelta(days=7))
            applied = True
        elif date_window == "30d":
            qs = qs.filter(diagnosis_date__gte=now - datetime.timedelta(days=30))
            applied = True
        elif date_window == "90d":
            qs = qs.filter(diagnosis_date__gte=now - datetime.timedelta(days=90))
            applied = True
        elif date_window == "this_year":
            qs = qs.filter(diagnosis_date__year=now.year)
            applied = True

    _step("diagnosis_period", "Diagnosis period", applied)

    return qs
