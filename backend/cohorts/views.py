from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from cohorts.stage_utils import normalize_stage_label
from patients.models import PatientInfo


OUTCOME_OPTIONS = [
    "Complete Response",
    "Very Good Partial Response",
    "Partial Response",
    "Minimal Response",
    "Stable Disease",
    "Progressive Disease",
]

MM_FIRST_LINE = [
    "VRd (Bortezomib, Lenalidomide, and Dexamethasone)",
    "Dara-VRd (Daratumumab, Bortezomib, Lenalidomide, and Dexamethasone)",
    "Dara-Rd (Daratumumab, Lenalidomide, and Dexamethasone)",
    "VRd Lite (Bortezomib, Lenalidomide, and Dexamethasone)",
    "KRd (Carfilzomib, Lenalidomide, and Dexamethasone)",
    "Isa-VRd (Isatuximab, Bortezomib, Lenalidomide, and Dexamethasone)",
    "Isa-KRd (Isatuximab, Carfilzomib, Lenalidomide, and Dexamethasone)",
    "CyBorD (Cyclophosphamide, Bortezomib, and Dexamethasone)",
]
MM_SECOND_LINE = [
    "KPd (Carfilzomib, Pomalidomide, and Dexamethasone)",
    "EPd (Elotuzumab, Pomalidomide, and Dexamethasone)",
    "SVd (Selinexor, Bortezomib, and Dexamethasone)",
    "Daratumumab (Darzalex/Darzalex Faspro) Monotherapy",
    "Carfilzomib (Kyprolis) Monotherapy",
    "Ixazomib (Ninlaro)",
    "Pomalidomide (Pomalyst) Monotherapy",
    "Isatuximab (Sarclisa) Monotherapy",
    "Venetoclax Monotherapy",
    "Selinexor (Xpovio)",
    "Elotuzumab (Empliciti) Monotherapy",
]
MM_LATER_LINE = [
    "Ide-cel (Abecma) Monotherapy",
    "Cilta-cel (Carvykti) Monotherapy",
    "Teclistamab (Tecvayli) Monotherapy",
    "Belantamab Mafodotin (Blenrep) Monotherapy",
    "SVd (Selinexor, Bortezomib, and Dexamethasone)",
    "EPd (Elotuzumab, Pomalidomide, and Dexamethasone)",
    "Selinexor (Xpovio)",
    "Daratumumab (Darzalex/Darzalex Faspro) Monotherapy",
    "Carfilzomib (Kyprolis) Monotherapy",
    "Pomalidomide (Pomalyst) Monotherapy",
    "Venetoclax Monotherapy",
    "Cyclophosphamide or Melphalan Monotherapy",
]
MM_REFRACTORY = [
    "IMiD-refractory (lenalidomide/pomalidomide)",
    "PI-refractory (bortezomib/carfilzomib)",
    "Double-refractory (PI + IMiD)",
    "Triple-refractory (PI + IMiD + anti-CD38)",
    "Refractory to prior therapy",
]

BC_FIRST_LINE = [
    "CDK4/6 Inhibitor + Letrozole",
    "CDK4/6 Inhibitor + Fulvestrant",
    "Trastuzumab + Pertuzumab + Taxane",
    "Neoadjuvant Chemotherapy",
    "Adjuvant Chemotherapy",
    "Tamoxifen",
    "Aromatase Inhibitor",
]
BC_SECOND_LINE = [
    "T-DM1 (Trastuzumab emtansine)",
    "Trastuzumab Deruxtecan (T-DXd)",
    "Sacituzumab Govitecan",
    "Fulvestrant",
    "Capecitabine",
    "Vinorelbine",
    "PARP Inhibitor (Olaparib/Talazoparib)",
]
BC_LATER_LINE = [
    "Trastuzumab Deruxtecan (T-DXd)",
    "Sacituzumab Govitecan",
    "Eribulin",
    "Capecitabine",
    "Gemcitabine + Carboplatin",
    "Pembrolizumab + Chemotherapy",
    "Tucatinib + Trastuzumab + Capecitabine",
]

FL_FIRST_LINE = [
    "Bendamustine and Rituximab (BR)",
    "R-CHOP",
    "G-CHOP",
    "R-CVP",
    "Rituximab monotherapy",
    "Obinutuzumab monotherapy",
]
FL_SECOND_LINE = [
    "Bendamustine and Rituximab (BR)",
    "R-CHOP",
    "Rituximab monotherapy",
    "Lenalidomide and Rituximab (R2)",
    "Copanlisib monotherapy",
    "Tazemetostat monotherapy",
    "Mosunetuzumab monotherapy",
    "Axicabtagene ciloleucel monotherapy",
    "Tisagenlecleucel monotherapy",
    "Epcoritamab monotherapy",
    "Obinutuzumab monotherapy",
]
FL_LATER_LINE = [
    "Axicabtagene ciloleucel monotherapy",
    "Tisagenlecleucel monotherapy",
    "Tazemetostat monotherapy",
    "Mosunetuzumab monotherapy",
    "Epcoritamab monotherapy",
    "Copanlisib monotherapy",
    "Bendamustine and Rituximab (BR)",
    "Lenalidomide and Rituximab (R2)",
    "Rituximab monotherapy",
    "Obinutuzumab monotherapy",
]
FL_REFRACTORY = [
    "Refractory to anti-CD20 (rituximab/obinutuzumab)",
    "Double refractory (anti-CD20 + alkylating agent)",
    "POD24 (progression within 24 months of 1L chemoimmunotherapy)",
]

THERAPY_MAP = {
    "Multiple Myeloma": {
        "first_line_therapies": MM_FIRST_LINE,
        "second_line_therapies": MM_SECOND_LINE,
        "later_line_therapies": MM_LATER_LINE,
        "refractory_statuses": MM_REFRACTORY,
        "stages": ["ISS Stage I", "ISS Stage II", "ISS Stage III"],
        "cytogenetic_markers": [
            "del(17p)", "t(4;14)", "t(14;16)", "1q21 amplification", "hyperdiploidy",
        ],
        "extra_filters": {
            "mm_specific": True,
            "has_sct_filter": True,
            "crab_filter": True,
        },
    },
    "Breast Cancer": {
        "first_line_therapies": BC_FIRST_LINE,
        "second_line_therapies": BC_SECOND_LINE,
        "later_line_therapies": BC_LATER_LINE,
        "refractory_statuses": [],
        "stages": ["I", "II", "IIA", "IIB", "III", "IIIA", "IIIB", "IIIC", "IV"],
        "cytogenetic_markers": [],
        "extra_filters": {
            "bc_specific": True,
            "er_pr_her2": True,
        },
    },
    "Follicular Lymphoma": {
        "first_line_therapies": FL_FIRST_LINE,
        "second_line_therapies": FL_SECOND_LINE,
        "later_line_therapies": FL_LATER_LINE,
        "refractory_statuses": FL_REFRACTORY,
        "stages": ["I", "IB", "II", "III", "IIIB", "IV", "IVB"],
        "cytogenetic_markers": ["t(14;18)", "del(1p36)", "TP53 mutation", "MYC rearrangement"],
        "extra_filters": {},
    },
}


@api_view(["GET"])
@permission_classes([AllowAny])
def form_settings(request):
    """Return dropdown options for the cohort filter panel."""
    disease = request.query_params.get("disease", "Multiple Myeloma")
    org = request.query_params.get("org", None)

    # Org-scoped queries expose per-org patient counts — require auth and visibility
    if org:
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        from accounts.utils import get_visible_org_names
        if org not in get_visible_org_names(request.user):
            return Response({"detail": "Organisation not found."}, status=status.HTTP_403_FORBIDDEN)

    disease_config = THERAPY_MAP.get(disease, THERAPY_MAP["Multiple Myeloma"])

    def _normalize_disease(name):
        """Collapse FHIR coding artifacts (e.g. 'ER|ERBB2 Breast cancer') and
        case variants (e.g. 'Follicular lymphoma') into canonical names."""
        if "breast cancer" in name.lower():
            return "Breast Cancer"
        canonical = {d.lower(): d for d in THERAPY_MAP}
        return canonical.get(name.strip().lower(), name)

    # Pull distinct values actually present in the DB for this disease (scoped to org)
    qs = PatientInfo.objects.filter(disease__icontains=disease)
    if org:
        qs = qs.filter(organization__name__iexact=org)
    regions = sorted(
        qs.exclude(region__isnull=True).values_list("region", flat=True).distinct()
    )
    countries = sorted(
        qs.exclude(country__isnull=True).values_list("country", flat=True).distinct()
    )
    races = sorted(
        qs.exclude(race__isnull=True).values_list("race", flat=True).distinct()
    )
    raw_stages = (
        qs.exclude(stage__isnull=True)
          .exclude(stage="")
          .values_list("stage", flat=True)
          .distinct()
    )
    stages = sorted({normalize_stage_label(stage, disease) for stage in raw_stages if stage})

    # Compute patient counts per normalized disease name (scoped to org if provided)
    base_qs = PatientInfo.objects.exclude(disease__isnull=True)
    if org:
        base_qs = base_qs.filter(organization__name__iexact=org)

    disease_counts: dict[str, int] = {}
    for row in base_qs.values("disease").annotate(cnt=Count("id")):
        normalized = _normalize_disease(row["disease"])
        disease_counts[normalized] = disease_counts.get(normalized, 0) + row["cnt"]

    # Sort diseases by patient count descending
    diseases = sorted(disease_counts.keys(), key=lambda d: -disease_counts[d])

    response_payload = {
        "diseases": diseases,
        "disease_counts": disease_counts,
        **disease_config,
        "outcome_options": OUTCOME_OPTIONS,
        "countries": countries,
        "regions": regions,
        "race_options": races,
        "ecog_values": [0, 1, 2, 3],
        "smoking_options": ["Never", "Former", "Current"],
        "therapy_line_options": [1, 2, 3, 4],
        "mrd_status_options": ["MRD Negative", "MRD Positive", "Not Assessed"],
    }
    if stages:
        response_payload["stages"] = stages

    return Response(response_payload)
