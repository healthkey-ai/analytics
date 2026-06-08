from metrics.services.survival import _os_times_events, _pfs_times_events
from metrics.services.km_utils import km_result, log_rank_p
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


_MRD_MIN_N = 5
_MRD_MAX_GROUPS = 10


def _mrd_subgroups(qs):
    # Only include patients with a recorded MRD assessment
    assessed = qs.exclude(mrd_status__isnull=True).exclude(mrd_status="")
    values = (
        assessed.values_list("mrd_status", flat=True)
        .distinct()
        .order_by("mrd_status")[: _MRD_MAX_GROUPS]
    )
    subgroups = []
    for val in values:
        sub = assessed.filter(mrd_status=val)
        if sub.count() >= _MRD_MIN_N:
            subgroups.append((val, sub))
    return subgroups


def _stratify(qs, subgroups_fn):
    subs = subgroups_fn(qs)

    os_lines      = []
    pfs_lines     = []
    os_te_groups  = []
    pfs_te_groups = []

    for label, sub_qs in subs:
        os_te  = _os_times_events(sub_qs)
        pfs_te = _pfs_times_events(sub_qs)

        if os_te:
            os_km_r = km_result(os_te)
            if os_km_r["n"] > 0:
                os_lines.append({"label": label, **os_km_r})
                os_te_groups.append(os_te)

        if pfs_te:
            pfs_km_r = km_result(pfs_te)
            if pfs_km_r["n"] > 0:
                pfs_lines.append({"label": label, **pfs_km_r})
                pfs_te_groups.append(pfs_te)

    return {
        "os":    os_lines,
        "pfs":   pfs_lines,
        "os_p":  log_rank_p(os_te_groups),
        "pfs_p": log_rank_p(pfs_te_groups),
    }


def compute(qs):
    return {
        "by_stage":        _stratify(qs, _stage_subgroups),
        "by_cytogenetics": _stratify(qs, _cyto_subgroups),
        "by_sct":          _stratify(qs, _sct_subgroups),
        "by_mrd":          _stratify(qs, _mrd_subgroups),
    }
