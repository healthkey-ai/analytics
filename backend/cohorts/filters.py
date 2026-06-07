from django.db.models import Q
from patients.models import PatientInfo
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT, NO_SCT


def apply_cohort_filters(request) -> "QuerySet[PatientInfo]":
    """
    Build a PatientInfo queryset from GET query parameters.

    All multi-value params use the same key repeated, e.g. stage=ISS+Stage+I&stage=ISS+Stage+II.
    Boolean params accept "true" / "false" strings.
    """
    qs = PatientInfo.objects.all()
    p = request.query_params

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

    # ── disease ───────────────────────────────────────────────────────────────
    disease = p.get("disease")
    if disease:
        qs = qs.filter(disease=disease)

    # ── ISS / TNM stage ───────────────────────────────────────────────────────
    stages = _list("stage")
    if stages:
        qs = qs.filter(stage__in=stages)

    # ── age ───────────────────────────────────────────────────────────────────
    age_min = _int("age_min")
    age_max = _int("age_max")
    if age_min is not None:
        qs = qs.filter(patient_age__gte=age_min)
    if age_max is not None:
        qs = qs.filter(patient_age__lte=age_max)

    # ── gender ────────────────────────────────────────────────────────────────
    gender = p.get("gender")
    if gender:
        qs = qs.filter(gender=gender)

    # ── race ──────────────────────────────────────────────────────────────────
    races = _list("race")
    if races:
        qs = qs.filter(race__in=races)

    # ── geography ─────────────────────────────────────────────────────────────
    regions = _list("region")
    if regions:
        qs = qs.filter(region__in=regions)

    # ── ECOG / KPS ────────────────────────────────────────────────────────────
    ecog_vals = [int(v) for v in _list("ecog") if v.isdigit()]
    if ecog_vals:
        qs = qs.filter(ecog_performance_status__in=ecog_vals)

    kps_min = _int("kps_min")
    kps_max = _int("kps_max")
    if kps_min is not None:
        qs = qs.filter(karnofsky_performance_score__gte=kps_min)
    if kps_max is not None:
        qs = qs.filter(karnofsky_performance_score__lte=kps_max)

    # ── cytogenetics ──────────────────────────────────────────────────────────
    cyto_markers = _list("cytogenetic_markers")
    if cyto_markers:
        q = Q()
        for m in cyto_markers:
            q |= Q(cytogenic_markers__icontains=m)
        qs = qs.filter(q)

    high_risk = _bool("high_risk_cytogenetics")
    if high_risk is True:
        qs = qs.filter(HIGH_RISK_CYTO)
    elif high_risk is False:
        qs = qs.exclude(HIGH_RISK_CYTO)

    tp53 = _bool("tp53_disruption")
    if tp53 is not None:
        qs = qs.filter(tp53_disruption=tp53)

    # ── treatment lines ───────────────────────────────────────────────────────
    lines_min = _int("therapy_lines_min")
    lines_max = _int("therapy_lines_max")
    if lines_min is not None:
        qs = qs.filter(therapy_lines_count__gte=lines_min)
    if lines_max is not None:
        qs = qs.filter(therapy_lines_count__lte=lines_max)

    # ── specific therapies ────────────────────────────────────────────────────
    fl_therapies = _list("first_line_therapy")
    if fl_therapies:
        qs = qs.filter(first_line_therapy__in=fl_therapies)

    sl_therapies = _list("second_line_therapy")
    if sl_therapies:
        qs = qs.filter(second_line_therapy__in=sl_therapies)

    lt_therapies = _list("later_therapy")
    if lt_therapies:
        qs = qs.filter(later_therapy__in=lt_therapies)

    # ── treatment outcomes ────────────────────────────────────────────────────
    fl_outcomes = _list("first_line_outcome")
    if fl_outcomes:
        qs = qs.filter(first_line_outcome__in=fl_outcomes)

    sl_outcomes = _list("second_line_outcome")
    if sl_outcomes:
        qs = qs.filter(second_line_outcome__in=sl_outcomes)

    lt_outcomes = _list("later_outcome")
    if lt_outcomes:
        qs = qs.filter(later_outcome__in=lt_outcomes)

    # ── refractory status ─────────────────────────────────────────────────────
    refractory = _list("refractory_status")
    if refractory:
        qs = qs.filter(treatment_refractory_status__in=refractory)

    # ── disease characteristics (MM) ─────────────────────────────────────────
    meets_crab = _bool("meets_crab")
    if meets_crab is not None:
        qs = qs.filter(meets_crab=meets_crab)

    has_bone = _bool("has_bone_lesions")
    if has_bone is True:
        qs = qs.exclude(bone_lesions="No bone lesions").exclude(bone_lesions__isnull=True)
    elif has_bone is False:
        qs = qs.filter(Q(bone_lesions="No bone lesions") | Q(bone_lesions__isnull=True))

    has_sct = _bool("has_sct")
    if has_sct is True:
        qs = qs.filter(HAS_SCT)
    elif has_sct is False:
        qs = qs.filter(NO_SCT)

    pcl = _bool("plasma_cell_leukemia")
    if pcl is not None:
        qs = qs.filter(plasma_cell_leukemia=pcl)

    # ── lab ranges ────────────────────────────────────────────────────────────
    hgb_min = _float("hemoglobin_min")
    hgb_max = _float("hemoglobin_max")
    if hgb_min is not None:
        qs = qs.filter(hemoglobin_g_dl__gte=hgb_min)
    if hgb_max is not None:
        qs = qs.filter(hemoglobin_g_dl__lte=hgb_max)

    cr_max = _float("creatinine_max")
    if cr_max is not None:
        qs = qs.filter(serum_creatinine_mg_dl__lte=cr_max)

    b2m_min = _float("b2m_min")
    b2m_max = _float("b2m_max")
    if b2m_min is not None:
        qs = qs.filter(beta2_microglobulin__gte=b2m_min)
    if b2m_max is not None:
        qs = qs.filter(beta2_microglobulin__lte=b2m_max)

    # ── diagnosis year ────────────────────────────────────────────────────────
    dx_year_min = _int("diagnosis_year_min")
    dx_year_max = _int("diagnosis_year_max")
    if dx_year_min is not None:
        qs = qs.filter(diagnosis_date__year__gte=dx_year_min)
    if dx_year_max is not None:
        qs = qs.filter(diagnosis_date__year__lte=dx_year_max)

    # ── MRD status ────────────────────────────────────────────────────────────
    mrd = _list("mrd_status")
    if mrd:
        qs = qs.filter(mrd_status__in=mrd)

    # ── lifestyle ─────────────────────────────────────────────────────────────
    smoking = _list("smoking_status")
    if smoking:
        qs = qs.filter(smoking_status__in=smoking)

    # ── breast cancer specific ────────────────────────────────────────────────
    er_statuses = _list("er_status")
    if er_statuses:
        qs = qs.filter(estrogen_receptor_status__in=er_statuses)

    her2_statuses = _list("her2_status")
    if her2_statuses:
        qs = qs.filter(her2_status__in=her2_statuses)

    tnbc = _bool("tnbc_status")
    if tnbc is not None:
        qs = qs.filter(tnbc_status=tnbc)

    return qs
