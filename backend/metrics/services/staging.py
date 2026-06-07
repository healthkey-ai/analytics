from django.db.models import Count, Q
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT


def compute(qs):
    total = qs.count()
    if not total:
        return {}

    def pct(n):
        return round(n / total * 100, 1) if total else 0

    # ISS stage
    stage_rows = (
        qs.exclude(stage__isnull=True)
        .values('stage').annotate(count=Count('id')).order_by('stage')
    )
    stages = [{"stage": r['stage'], "count": r['count'], "pct": pct(r['count'])}
              for r in stage_rows]

    # ECOG
    ecog_rows = (
        qs.exclude(ecog_performance_status__isnull=True)
        .values('ecog_performance_status').annotate(count=Count('id'))
        .order_by('ecog_performance_status')
    )
    ecog = [{"ecog": r['ecog_performance_status'], "count": r['count'],
             "pct": pct(r['count'])} for r in ecog_rows]

    # All scalar counts in one aggregate() call — replaces 8 separate .count() queries
    agg = qs.aggregate(
        crab_met=Count('id',    filter=Q(meets_crab=True)),
        crab_not=Count('id',    filter=Q(meets_crab=False)),
        del17p=Count('id',      filter=Q(cytogenic_markers__icontains='del(17p)')),
        t414=Count('id',        filter=Q(cytogenic_markers__icontains='t(4;14)')),
        t1416=Count('id',       filter=Q(cytogenic_markers__icontains='t(14;16)')),
        q121=Count('id',        filter=Q(cytogenic_markers__icontains='1q21')),
        hyperdiploid=Count('id',filter=Q(cytogenic_markers__icontains='hyperdiploidy')),
        std_risk=Count('id',    filter=~HIGH_RISK_CYTO & (Q(cytogenic_markers='') | Q(cytogenic_markers__isnull=True))),
        sct_count=Count('id',   filter=HAS_SCT),
    )

    crab_met = agg['crab_met']
    crab_not = agg['crab_not']
    crab = [
        {"label": "CRAB Met",     "count": crab_met, "pct": pct(crab_met)},
        {"label": "CRAB Not Met", "count": crab_not, "pct": pct(crab_not)},
    ] if (crab_met + crab_not) else []

    cyto_groups = [
        ("del(17p)",           True,  agg['del17p']),
        ("t(4;14)",            True,  agg['t414']),
        ("t(14;16)",           True,  agg['t1416']),
        ("1q21 amplification", False, agg['q121']),
        ("Hyperdiploidy",      False, agg['hyperdiploid']),
        ("Standard Risk",      False, agg['std_risk']),
    ]
    cytogenetics = [
        {"marker": label, "count": count, "pct": pct(count), "high_risk": high_risk}
        for label, high_risk, count in cyto_groups if count
    ]

    sct_count = agg['sct_count']

    # Bone lesions
    bone_rows = (
        qs.exclude(bone_lesions__isnull=True)
        .values('bone_lesions').annotate(count=Count('id')).order_by('-count')
    )
    bone_lesions = [{"type": r['bone_lesions'], "count": r['count'],
                     "pct": pct(r['count'])} for r in bone_rows]

    # Refractory status
    refractory_rows = (
        qs.exclude(treatment_refractory_status__isnull=True)
        .values('treatment_refractory_status').annotate(count=Count('id')).order_by('-count')
    )
    refractory = [{"status": r['treatment_refractory_status'], "count": r['count'],
                   "pct": pct(r['count'])} for r in refractory_rows]

    return {
        "stages":            stages,
        "ecog":              ecog,
        "crab":              crab,
        "cytogenetics":      cytogenetics,
        "sct_count":         sct_count,
        "sct_pct":           pct(sct_count),
        "bone_lesions":      bone_lesions,
        "refractory_status": refractory,
    }
