from collections import Counter


def compute(records):
    total = len(records)
    if not total:
        return {}

    def pct(n):
        return round(n / total * 100, 1) if total else 0

    # ISS / disease stage
    stage_counts = Counter(r["stage"] for r in records if r.get("stage"))
    stages = [{"stage": s, "count": c, "pct": pct(c)}
              for s, c in sorted(stage_counts.items())]

    # ECOG
    ecog_counts = Counter(
        r["ecog_performance_status"] for r in records
        if r.get("ecog_performance_status") is not None
    )
    ecog = [{"ecog": e, "count": c, "pct": pct(c)}
            for e, c in sorted(ecog_counts.items())]

    # CRAB (MM)
    crab_met = sum(1 for r in records if r.get("meets_crab") is True)
    crab_not = sum(1 for r in records if r.get("meets_crab") is False)
    crab = [
        {"label": "CRAB Met",     "count": crab_met, "pct": pct(crab_met)},
        {"label": "CRAB Not Met", "count": crab_not, "pct": pct(crab_not)},
    ] if (crab_met + crab_not) else []

    # Cytogenetics
    HIGH_RISK_KEYWORDS = ("del(17p)", "t(4;14)", "t(14;16)")

    def contains(markers, keyword):
        return bool(markers) and keyword.lower() in markers.lower()

    def is_high_risk(markers):
        return any(contains(markers, kw) for kw in HIGH_RISK_KEYWORDS)

    cyto_groups = [
        ("del(17p)",           True,  "del(17p)"),
        ("t(4;14)",            True,  "t(4;14)"),
        ("t(14;16)",           True,  "t(14;16)"),
        ("1q21 amplification", False, "1q21"),
        ("Hyperdiploidy",      False, "hyperdiploidy"),
        ("Standard Risk",      False, None),
    ]
    cytogenetics = []
    for label, high_risk, keyword in cyto_groups:
        if keyword:
            count = sum(1 for r in records if contains(r.get("cytogenic_markers"), keyword))
        else:
            count = sum(
                1 for r in records
                if not is_high_risk(r.get("cytogenic_markers"))
                and not r.get("cytogenic_markers")
            )
        if count:
            cytogenetics.append({"marker": label, "count": count,
                                  "pct": pct(count), "high_risk": high_risk})

    # SCT history
    def has_sct(val):
        if val is None:
            return False
        if isinstance(val, list):
            return len(val) > 0
        return bool(val)

    sct_count = sum(1 for r in records if has_sct(r.get("stem_cell_transplant_history")))

    # Bone lesions
    bone_counts = Counter(r["bone_lesions"] for r in records if r.get("bone_lesions"))
    bone_lesions = [{"type": t, "count": c, "pct": pct(c)}
                    for t, c in bone_counts.most_common()]

    # Refractory status
    refractory_counts = Counter(
        r["treatment_refractory_status"] for r in records
        if r.get("treatment_refractory_status")
    )
    refractory = [{"status": s, "count": c, "pct": pct(c)}
                  for s, c in refractory_counts.most_common()]

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
