from metrics.services.survival import os_km, pfs_km
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT, NO_SCT


def _subgroup_km(km_fn, subgroups):
    """
    Run km_fn on each (label, sub_qs) pair; drop subgroups with no observations.
    """
    result = []
    for label, sub_qs in subgroups:
        km = km_fn(sub_qs)
        if km["n"] > 0:
            result.append({"label": label, **km})
    return result


def _stage_subgroups(qs):
    stage_vals = (
        qs.exclude(stage__isnull=True)
        .exclude(stage="")
        .values_list("stage", flat=True)
        .distinct()
        .order_by("stage")
    )
    return [(val, qs.filter(stage=val)) for val in stage_vals]


def _cyto_subgroups(qs):
    # Exclude patients with no cytogenetics workup — they are unevaluable, not Standard Risk
    tested = qs.exclude(cytogenic_markers__isnull=True).exclude(cytogenic_markers="")
    return [
        ("High Risk",     tested.filter(HIGH_RISK_CYTO)),
        ("Standard Risk", tested.exclude(HIGH_RISK_CYTO)),
    ]


def _sct_subgroups(qs):
    return [
        ("SCT",    qs.filter(HAS_SCT)),
        ("No SCT", qs.filter(NO_SCT)),
    ]


def _stratify(qs, subgroups_fn):
    subs = subgroups_fn(qs)
    # Note: fires 2 DB queries per subgroup (os_km + pfs_km each call .values()).
    # For stage: 1 (distinct) + N×2 queries. Acceptable at typical cohort sizes (~5 stages).
    # If latency becomes a concern, fetch all rows in 2 queries and partition in Python.
    return {
        "os":  _subgroup_km(os_km,  subs),
        "pfs": _subgroup_km(pfs_km, subs),
    }


def compute(qs):
    return {
        "by_stage":        _stratify(qs, _stage_subgroups),
        "by_cytogenetics": _stratify(qs, _cyto_subgroups),
        "by_sct":          _stratify(qs, _sct_subgroups),
    }
