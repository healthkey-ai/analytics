from django.db.models import Count, Q


def compute(qs):
    total = qs.count()
    if not total:
        return {}

    def pct(n):
        return round(n / total * 100, 1) if total else 0

    # ISS / disease stage
    stage_rows = (
        qs.exclude(stage__isnull=True)
        .values("stage")
        .annotate(count=Count("id"))
        .order_by("stage")
    )
    stages = [{"stage": r["stage"], "count": r["count"], "pct": pct(r["count"])}
              for r in stage_rows]

    # ECOG
    ecog_rows = (
        qs.exclude(ecog_performance_status__isnull=True)
        .values("ecog_performance_status")
        .annotate(count=Count("id"))
        .order_by("ecog_performance_status")
    )
    ecog = [{"ecog": r["ecog_performance_status"], "count": r["count"],
             "pct": pct(r["count"])} for r in ecog_rows]

    # CRAB (MM)
    crab_met = qs.filter(meets_crab=True).count()
    crab_not = qs.filter(meets_crab=False).count()
    crab = [
        {"label": "CRAB Met",     "count": crab_met, "pct": pct(crab_met)},
        {"label": "CRAB Not Met", "count": crab_not, "pct": pct(crab_not)},
    ] if (crab_met + crab_not) else []

    # Cytogenetic risk
    cyto_groups = [
        ("del(17p)",          True,  "del(17p)"),
        ("t(4;14)",           True,  "t(4;14)"),
        ("t(14;16)",          True,  "t(14;16)"),
        ("1q21 amplification",False, "1q21"),
        ("Hyperdiploidy",     False, "hyperdiploidy"),
        ("Standard Risk",     False, None),
    ]
    any_high_risk = (
        Q(cytogenic_markers__icontains="del(17p)") |
        Q(cytogenic_markers__icontains="t(4;14)") |
        Q(cytogenic_markers__icontains="t(14;16)")
    )
    cytogenetics = []
    for label, high_risk, keyword in cyto_groups:
        if keyword:
            count = qs.filter(cytogenic_markers__icontains=keyword).count()
        else:
            count = qs.exclude(any_high_risk).filter(
                Q(cytogenic_markers="") | Q(cytogenic_markers__isnull=True)
            ).count()
        if count:
            cytogenetics.append({
                "marker": label,
                "count": count,
                "pct": pct(count),
                "high_risk": high_risk,
            })

    # SCT history (MM)
    sct_count = qs.exclude(
        Q(stem_cell_transplant_history__isnull=True) |
        Q(stem_cell_transplant_history=list())
    ).count()

    # Bone lesions (MM)
    bone_rows = (
        qs.exclude(bone_lesions__isnull=True)
        .values("bone_lesions")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    bone_lesions = [{"type": r["bone_lesions"], "count": r["count"],
                     "pct": pct(r["count"])} for r in bone_rows]

    # Refractory status
    refractory_rows = (
        qs.exclude(treatment_refractory_status__isnull=True)
        .values("treatment_refractory_status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    refractory = [{"status": r["treatment_refractory_status"], "count": r["count"],
                   "pct": pct(r["count"])} for r in refractory_rows]

    return {
        "stages": stages,
        "ecog": ecog,
        "crab": crab,
        "cytogenetics": cytogenetics,
        "sct_count": sct_count,
        "sct_pct": pct(sct_count),
        "bone_lesions": bone_lesions,
        "refractory_status": refractory,
    }
