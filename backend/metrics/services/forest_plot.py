"""
Forest plot: per-subgroup OS hazard ratios with 95% CI (Peto method).
Each row compares a binary split of the cohort on a clinical variable.

Computed for multiple myeloma cohorts (gated in metrics.views), so the splits
are MM-relevant: cytogenetic risk, R-ISS stage, SCT, age, and MRD status.
"""
from django.db.models import Q

from metrics.services.km_utils import log_rank_hr
from metrics.services.survival import _os_times_events
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT, NO_SCT

_MIN_PER_ARM = 5  # skip row if either arm has fewer than this many OS observations

# Patients with a cytogenetics / stage value recorded (unevaluable patients — no
# workup — must not silently fall into the reference arm).
_CYTO_TESTED = ~Q(cytogenic_markers__isnull=True) & ~Q(cytogenic_markers="")
_STAGED = ~Q(stage__isnull=True) & ~Q(stage="")
_STAGE_LATE = Q(stage__icontains="III")  # R-ISS III (vs I/II)


def _row(subgroup, comparison, reference, te_comp, te_ref):
    if len(te_comp) < _MIN_PER_ARM or len(te_ref) < _MIN_PER_ARM:
        return None
    result = log_rank_hr(te_comp, te_ref)
    if result is None:
        return None
    hr, ci_low, ci_high, p = result
    return {
        "subgroup":     subgroup,
        "comparison":   comparison,
        "reference":    reference,
        "n_comparison": len(te_comp),
        "n_reference":  len(te_ref),
        "hr":           hr,
        "ci_low":       ci_low,
        "ci_high":      ci_high,
        "p_value":      p,
    }


def compute(qs):
    splits = [
        # (subgroup label, comparison label, reference label, comp filter Q, ref filter Q)
        (
            "Cytogenetic Risk", "High Risk", "Standard Risk",
            _CYTO_TESTED & HIGH_RISK_CYTO,
            _CYTO_TESTED & ~HIGH_RISK_CYTO,
        ),
        (
            "R-ISS Stage", "Late (III)", "Early (I/II)",
            _STAGED & _STAGE_LATE,
            _STAGED & ~_STAGE_LATE,
        ),
        (
            "SCT", "SCT", "No SCT",
            HAS_SCT,
            NO_SCT,
        ),
        (
            "Age", "≥65 years", "<65 years",
            Q(patient_age__gte=65),
            Q(patient_age__lt=65),
        ),
        (
            "MRD Status", "MRD Negative", "MRD Positive",
            Q(mrd_status__icontains="negative"),
            Q(mrd_status__icontains="positive"),
        ),
    ]

    rows = []
    for subgroup, comp_label, ref_label, comp_q, ref_q in splits:
        te_comp = _os_times_events(qs.filter(comp_q))
        te_ref  = _os_times_events(qs.filter(ref_q))
        row = _row(subgroup, comp_label, ref_label, te_comp, te_ref)
        if row:
            rows.append(row)

    return rows
