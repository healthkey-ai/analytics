#!/usr/bin/env python3
"""
Seed 100 realistic Multiple Myeloma patients into the CTOMOP dev database.
Person IDs 300-399.

Therapy names are taken verbatim from ~/exact/trials/services/therapies_mapper.py.
Outcome distributions are derived from published clinical trial results for each
specific regimen, then risk-adjusted downward for high-risk cytogenetics.

Outcome weight sources:
  VRd:                  SWOG S0777
  Dara-VRd:             GRIFFIN
  Dara-Rd:              MAIA
  VRd Lite:             SWOG S0777 / real-world (elderly-adapted, slightly worse)
  KRd:                  FORTE
  Isa-VRd:              GMMG-HD7
  Isa-KRd:              GMMG-HD7 / real-world estimates
  CyBorD:               PETHEMA GEM real-world
  Daratumumab mono:     GEN501 / SIRIUS
  Carfilzomib mono:     PX-171-003 / real-world
  Ixazomib (Ninlaro):   TOURMALINE-MM1 (Ird data)
  Pomalidomide mono:    MM-002
  EPd:                  ELOQUENT-3
  KPd:                  real-world
  SVd:                  STORM Part 2
  Ide-cel:              KarMMa
  Cilta-cel:            CARTITUDE-1
  Belantamab Mafodotin: DREAMM-2
  Teclistamab:          MajesTEC-1
  Selinexor (Xpovio):   STORM Part 2 (mono arm)
  Venetoclax mono:      real-world t(11;14)
"""

import random
import json
import psycopg2
from datetime import date, timedelta

DB_URL = (
    "postgresql://ctomop_dev_user:IehVp8TGNcelOymGcjtfL6Up6W63DOf2"
    "@dpg-d7pqr35ckfvc73bm0lc0-a.oregon-postgres.render.com/ctomop_dev"
)

random.seed(42)

# ── helpers ───────────────────────────────────────────────────────────────────

def rand_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def add_months(d, months):
    if d is None:
        return None
    m  = d.month - 1 + months
    y  = d.year + m // 12
    mo = m % 12 + 1
    day = min(d.day, [31,28,31,30,31,30,31,31,30,31,30,31][mo - 1])
    return date(y, mo, day)

# ── name / geo pools ──────────────────────────────────────────────────────────

FIRST_NAMES_M = [
    "James","Robert","John","Michael","William","David","Richard","Thomas",
    "Charles","Christopher","Daniel","Matthew","Anthony","Mark","Donald",
    "Steven","Paul","Andrew","Kenneth","Joshua","George","Kevin","Brian",
    "Timothy","Ronald","Edward","Jason","Jeffrey","Ryan","Gary",
]
FIRST_NAMES_F = [
    "Mary","Patricia","Linda","Barbara","Elizabeth","Jennifer","Maria","Susan",
    "Margaret","Dorothy","Lisa","Nancy","Karen","Betty","Helen","Sandra",
    "Donna","Carol","Ruth","Sharon","Michelle","Laura","Sarah","Kimberly",
    "Deborah","Jessica","Shirley","Cynthia","Angela","Melissa",
]
LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Hall","Allen","King","Wright","Scott","Torres",
    "Nguyen","Hill","Flores","Green","Adams","Nelson","Baker","Rivera",
    "Campbell","Mitchell","Carter","Roberts",
]
# Weighted toward populous states
US_STATES = [
    "AL","AZ","AR","CA","CA","CA","CA","CO","CT","FL","FL","FL","GA","GA",
    "ID","IL","IL","IN","IA","KS","KY","LA","ME","MD","MA","MA","MI","MI",
    "MN","MS","MO","MT","NE","NV","NH","NJ","NJ","NM","NY","NY","NY","NC",
    "NC","OH","OH","OK","OR","PA","PA","RI","SC","TN","TX","TX","TX","TX",
    "UT","VA","VA","WA","WA","WI","WY",
]
ETHNICITIES = [
    "Not Hispanic or Latino","Not Hispanic or Latino","Not Hispanic or Latino",
    "Not Hispanic or Latino","Not Hispanic or Latino","Hispanic or Latino",
    "Unknown",
]

# ── disease parameters ────────────────────────────────────────────────────────

ISS_STAGES = {
    # stage: (population weight, B2M range mg/L, albumin range g/dL)
    "I":   (0.30, (1.5,  3.4),  (3.5, 4.8)),
    "II":  (0.40, (3.5,  5.4),  (2.8, 4.0)),
    "III": (0.30, (5.5, 18.0),  (1.8, 3.2)),
}

# (label, is_high_risk, cytogenic_marker_string)
CYTOGENETICS = [
    ("del(17p)",     True,  "del(17p)"),
    ("t(4;14)",      True,  "t(4;14)"),
    ("t(14;16)",     True,  "t(14;16)"),
    ("1q_amp",       False, "1q21 amplification"),
    ("1q_amp",       False, "1q21 amplification"),
    ("hyperdiploid", False, "hyperdiploidy"),
    ("hyperdiploid", False, "hyperdiploidy"),
    ("standard",     False, ""),
    ("standard",     False, ""),
    ("standard",     False, ""),
]

MOLECULAR_MUTATIONS = [
    [], [], [], [],
    [{"gene":"KRAS","variant":"G12D","origin":"somatic","interpretation":"Pathogenic"}],
    [{"gene":"NRAS","variant":"Q61H","origin":"somatic","interpretation":"Pathogenic"}],
    [{"gene":"BRAF","variant":"V600E","origin":"somatic","interpretation":"Pathogenic"}],
    [{"gene":"TP53","variant":"R248W","origin":"somatic","interpretation":"Pathogenic"}],
]

PREEXISTING = [
    [], [], [],
    [{"condition":"Hypertension","icd10":"I10"}],
    [{"condition":"Type 2 Diabetes Mellitus","icd10":"E11"}],
    [{"condition":"Hypertension","icd10":"I10"},
     {"condition":"Chronic Kidney Disease Stage 2","icd10":"N18.2"}],
    [{"condition":"Atrial Fibrillation","icd10":"I48.91"}],
    [{"condition":"COPD","icd10":"J44.1"}],
    [{"condition":"Osteoporosis","icd10":"M81.0"}],
]

# ── therapy lists — exact names from ~/exact/trials/services/therapies_mapper.py ──
# Each entry: (exact_name, drug_classes_set)
# drug_classes are used only to avoid re-using the same class in consecutive lines.

FIRST_LINE = [
    ("VRd (Bortezomib, Lenalidomide, and Dexamethasone)",                                           {"PI","IMiD"}),
    ("VRd (Bortezomib, Lenalidomide, and Dexamethasone)",                                           {"PI","IMiD"}),
    ("VRd (Bortezomib, Lenalidomide, and Dexamethasone)",                                           {"PI","IMiD"}),
    ("Dara-VRd (Daratumumab, Bortezomib, Lenalidomide, and Dexamethasone)",                         {"PI","IMiD","CD38"}),
    ("Dara-VRd (Daratumumab, Bortezomib, Lenalidomide, and Dexamethasone)",                         {"PI","IMiD","CD38"}),
    ("Dara-Rd (Daratumumab, Lenalidomide, and Dexamethasone)",                                      {"IMiD","CD38"}),
    ("KRd (Carfilzomib, Lenalidomide, and Dexamethasone)",                                          {"PI","IMiD"}),
    ("Isa-VRd (Isatuximab, Bortezomib, Lenalidomide, and Dexamethasone)",                           {"PI","IMiD","CD38"}),
    ("VRd Lite (Bortezomib, Lenalidomide, and Dexamethasone)",                                      {"PI","IMiD"}),
    ("CyBorD (Cyclophosphamide, Bortezomib, and Dexamethasone)",                                    {"PI","Alkylator"}),
]

SECOND_LINE = [
    ("KPd (Carfilzomib, Pomalidomide, and Dexamethasone)",                                          {"PI","IMiD"}),
    ("EPd (Elotuzumab, Pomalidomide, and Dexamethasone)",                                           {"SLAMF7","IMiD"}),
    ("SVd (Selinexor, Bortezomib, and Dexamethasone)",                                              {"XPO1","PI"}),
    ("Daratumumab (Darzalex/Darzalex Faspro) Monotherapy",                                          {"CD38"}),
    ("Daratumumab (Darzalex/Darzalex Faspro) Monotherapy",                                          {"CD38"}),
    ("Carfilzomib (Kyprolis) Monotherapy",                                                          {"PI"}),
    ("Ixazomib (Ninlaro)",                                                                          {"PI"}),
    ("Pomalidomide (Pomalyst) Monotherapy",                                                         {"IMiD"}),
    ("Isatuximab (Sarclisa) Monotherapy",                                                           {"CD38"}),
    ("Venetoclax Monotherapy",                                                                      {"BCL2"}),
    ("Selinexor (Xpovio)",                                                                          {"XPO1"}),
    ("Elotuzumab (Empliciti) Monotherapy",                                                          {"SLAMF7"}),
]

LATER_LINE = [
    ("Ide-cel (Abecma) Monotherapy",                                                                {"CAR-T","BCMA"}),
    ("Ide-cel (Abecma) Monotherapy",                                                                {"CAR-T","BCMA"}),
    ("Cilta-cel (Carvykti) Monotherapy",                                                            {"CAR-T","BCMA"}),
    ("Teclistamab (Tecvayli) Monotherapy",                                                          {"TCE","BCMA"}),
    ("Belantamab Mafodotin (Blenrep) Monotherapy",                                                  {"ADC","BCMA"}),
    ("SVd (Selinexor, Bortezomib, and Dexamethasone)",                                              {"XPO1","PI"}),
    ("EPd (Elotuzumab, Pomalidomide, and Dexamethasone)",                                           {"SLAMF7","IMiD"}),
    ("Selinexor (Xpovio)",                                                                          {"XPO1"}),
    ("Daratumumab (Darzalex/Darzalex Faspro) Monotherapy",                                         {"CD38"}),
    ("Carfilzomib (Kyprolis) Monotherapy",                                                          {"PI"}),
    ("Pomalidomide (Pomalyst) Monotherapy",                                                         {"IMiD"}),
    ("Venetoclax Monotherapy",                                                                      {"BCL2"}),
    ("Cyclophosphamide or Melphalan Monotherapy",                                                   {"Alkylator"}),
]

# ── per-regimen outcome distributions ────────────────────────────────────────
# Keys are the exact therapy name strings used above.
# Weights do not need to sum to 100; random.choices normalises them.

REGIMEN_OUTCOMES = {
    # ── 1st line ──────────────────────────────────────────────────────────────
    # SWOG S0777: ORR 82%, CR 16%, VGPR 34%, PR 32%, SD 10%, PD 8%
    "VRd (Bortezomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          16,
        "Very Good Partial Response": 34,
        "Partial Response":           32,
        "Stable Disease":             10,
        "Progressive Disease":         8,
    },
    # GRIFFIN: ORR 92%, sCR 42%, VGPR 26%, PR 24%, SD 5%, PD 3%
    "Dara-VRd (Daratumumab, Bortezomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          42,
        "Very Good Partial Response": 26,
        "Partial Response":           24,
        "Stable Disease":              5,
        "Progressive Disease":         3,
    },
    # MAIA: ORR 93%, sCR 30%, VGPR 32%, PR 31%, SD 4%, PD 3%
    "Dara-Rd (Daratumumab, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          30,
        "Very Good Partial Response": 32,
        "Partial Response":           31,
        "Stable Disease":              4,
        "Progressive Disease":         3,
    },
    # VRd Lite (elderly-adapted; real-world ~75% ORR, fewer CR)
    "VRd Lite (Bortezomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          12,
        "Very Good Partial Response": 28,
        "Partial Response":           35,
        "Stable Disease":             14,
        "Progressive Disease":        11,
    },
    # FORTE: ORR 90%, CR 26%, VGPR 36%, PR 28%, SD 6%, PD 4%
    "KRd (Carfilzomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          26,
        "Very Good Partial Response": 36,
        "Partial Response":           28,
        "Stable Disease":              6,
        "Progressive Disease":         4,
    },
    # GMMG-HD7: Isa-VRd ORR ~93%, sCR+CR ~40%, VGPR ~32%, PR ~21%, PD ~7%
    "Isa-VRd (Isatuximab, Bortezomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          40,
        "Very Good Partial Response": 32,
        "Partial Response":           21,
        "Stable Disease":              4,
        "Progressive Disease":         3,
    },
    # Isa-KRd: emerging data, similar to Isa-VRd
    "Isa-KRd (Isatuximab, Carfilzomib, Lenalidomide, and Dexamethasone)": {
        "Complete Response":          38,
        "Very Good Partial Response": 30,
        "Partial Response":           22,
        "Stable Disease":              5,
        "Progressive Disease":         5,
    },
    # CyBorD real-world: ORR ~73%, CR 16%, VGPR 28%, PR 29%, SD 14%, PD 13%
    "CyBorD (Cyclophosphamide, Bortezomib, and Dexamethasone)": {
        "Complete Response":          16,
        "Very Good Partial Response": 28,
        "Partial Response":           29,
        "Stable Disease":             14,
        "Progressive Disease":        13,
    },
    # ── 2nd line ──────────────────────────────────────────────────────────────
    # KPd real-world / small trials: ORR ~70%, CR 10%, VGPR 25%, PR 35%, SD 16%, PD 14%
    "KPd (Carfilzomib, Pomalidomide, and Dexamethasone)": {
        "Complete Response":          10,
        "Very Good Partial Response": 25,
        "Partial Response":           35,
        "Stable Disease":             16,
        "Progressive Disease":        14,
    },
    # ELOQUENT-3: EPd ORR 53%, CR 8%, VGPR 18%, PR 27%, SD 25%, PD 22%
    "EPd (Elotuzumab, Pomalidomide, and Dexamethasone)": {
        "Complete Response":           8,
        "Very Good Partial Response":  18,
        "Partial Response":            27,
        "Stable Disease":              25,
        "Progressive Disease":         22,
    },
    # STORM Part 2: SVd ORR 26%, CR 3%, VGPR 3%, PR 20%, MR 10%, SD 28%, PD 36%
    "SVd (Selinexor, Bortezomib, and Dexamethasone)": {
        "Complete Response":           3,
        "Very Good Partial Response":  3,
        "Partial Response":           20,
        "Minimal Response":           10,
        "Stable Disease":             28,
        "Progressive Disease":        36,
    },
    # GEN501/SIRIUS: Dara mono ORR 29-36%, CR 3%, VGPR 9%, PR 24%, SD 28%, PD 36%
    "Daratumumab (Darzalex/Darzalex Faspro) Monotherapy": {
        "Complete Response":           3,
        "Very Good Partial Response":  9,
        "Partial Response":           24,
        "Minimal Response":            8,
        "Stable Disease":             20,
        "Progressive Disease":        36,
    },
    # PX-171-003: Carfilzomib mono ORR 24%, CR 5%, VGPR 10%, PR 9%, SD 30%, PD 46%
    "Carfilzomib (Kyprolis) Monotherapy": {
        "Complete Response":           5,
        "Very Good Partial Response":  10,
        "Partial Response":            9,
        "Minimal Response":           10,
        "Stable Disease":             20,
        "Progressive Disease":        46,
    },
    # TOURMALINE-MM1 (IRd): ORR 78%, CR 12%, VGPR 34%, PR 32%, SD 14%, PD 8%
    # Ixazomib used most often in IRd combination; used as proxy
    "Ixazomib (Ninlaro)": {
        "Complete Response":          12,
        "Very Good Partial Response": 34,
        "Partial Response":           32,
        "Stable Disease":             14,
        "Progressive Disease":         8,
    },
    # MM-002: Pomalidomide mono ORR 18%, CR 1%, VGPR 5%, PR 12%, SD 30%, PD 52%
    "Pomalidomide (Pomalyst) Monotherapy": {
        "Complete Response":           1,
        "Very Good Partial Response":  5,
        "Partial Response":           12,
        "Minimal Response":           12,
        "Stable Disease":             18,
        "Progressive Disease":        52,
    },
    # ICARIA-MM: Isa-Pd ORR 60%, CR 6%, VGPR 24%, PR 30%, SD 19%, PD 21%
    "Isatuximab (Sarclisa) Monotherapy": {
        "Complete Response":           6,
        "Very Good Partial Response":  24,
        "Partial Response":            30,
        "Stable Disease":              19,
        "Progressive Disease":         21,
    },
    # Venetoclax mono (t11;14 enriched): ORR 40%, CR 14%, VGPR 14%, PR 12%, SD 20%, PD 40%
    "Venetoclax Monotherapy": {
        "Complete Response":          14,
        "Very Good Partial Response": 14,
        "Partial Response":           12,
        "Stable Disease":             20,
        "Progressive Disease":        40,
    },
    # Selinexor mono (STORM): ORR 21%, CR 2%, VGPR 2%, PR 17%, MR 12%, SD 28%, PD 39%
    "Selinexor (Xpovio)": {
        "Complete Response":           2,
        "Very Good Partial Response":  2,
        "Partial Response":           17,
        "Minimal Response":           12,
        "Stable Disease":             28,
        "Progressive Disease":        39,
    },
    # Elotuzumab mono phase 1/2: ORR ~10%, mostly PR or less; rarely used alone
    "Elotuzumab (Empliciti) Monotherapy": {
        "Complete Response":           2,
        "Very Good Partial Response":  5,
        "Partial Response":           18,
        "Minimal Response":           12,
        "Stable Disease":             28,
        "Progressive Disease":        35,
    },
    # ── Later line (3L+) ──────────────────────────────────────────────────────
    # KarMMa: ide-cel ORR 73%, sCR+CR 33%, VGPR 18%, PR 22%, SD 6%, PD 16%, MR 5%
    "Ide-cel (Abecma) Monotherapy": {
        "Complete Response":          33,
        "Very Good Partial Response": 18,
        "Partial Response":           22,
        "Minimal Response":            5,
        "Stable Disease":              6,
        "Progressive Disease":        16,
    },
    # CARTITUDE-1: cilta-cel ORR 97.9%, sCR+CR 67%, VGPR 25%, PR 5%, PD 3%
    "Cilta-cel (Carvykti) Monotherapy": {
        "Complete Response":          67,
        "Very Good Partial Response": 25,
        "Partial Response":            5,
        "Progressive Disease":         3,
    },
    # MajesTEC-1: teclistamab ORR 63%, sCR+CR 39%, VGPR 14%, PR 10%, PD 37%
    "Teclistamab (Tecvayli) Monotherapy": {
        "Complete Response":          39,
        "Very Good Partial Response": 14,
        "Partial Response":           10,
        "Progressive Disease":        37,
    },
    # DREAMM-2: belantamab ORR 31%, CR 2%, VGPR 9%, PR 20%, MR 10%, SD 18%, PD 41%
    "Belantamab Mafodotin (Blenrep) Monotherapy": {
        "Complete Response":           2,
        "Very Good Partial Response":  9,
        "Partial Response":           20,
        "Minimal Response":           10,
        "Stable Disease":             18,
        "Progressive Disease":        41,
    },
    # Cyclophosphamide/Melphalan salvage: poor prognosis setting
    "Cyclophosphamide or Melphalan Monotherapy": {
        "Complete Response":           3,
        "Very Good Partial Response":  5,
        "Partial Response":           18,
        "Minimal Response":           14,
        "Stable Disease":             25,
        "Progressive Disease":        35,
    },
}

FALLBACK_OUTCOMES = {
    "Complete Response":          10,
    "Very Good Partial Response": 18,
    "Partial Response":           27,
    "Minimal Response":           12,
    "Stable Disease":             18,
    "Progressive Disease":        15,
}

# ── outcome utilities ─────────────────────────────────────────────────────────

def _risk_adjust(weights: dict, high_risk: bool) -> dict:
    """For high-risk cytogenetics: double PD/MR, halve CR/VGPR."""
    if not high_risk:
        return weights
    out = {}
    for outcome, w in weights.items():
        if outcome in ("Progressive Disease", "Minimal Response"):
            out[outcome] = w * 2
        elif outcome in ("Complete Response", "Very Good Partial Response"):
            out[outcome] = max(1, w // 2)
        else:
            out[outcome] = w
    return out

def pick_outcome(therapy_name: str, high_risk: bool) -> str:
    weights  = REGIMEN_OUTCOMES.get(therapy_name, FALLBACK_OUTCOMES)
    weights  = _risk_adjust(weights, high_risk)
    return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

# Response → plausible treatment duration in months
RESPONSE_DURATION = {
    "Complete Response":          (14, 36),
    "Very Good Partial Response": (10, 24),
    "Partial Response":           ( 6, 16),
    "Minimal Response":           ( 3,  8),
    "Stable Disease":             ( 4, 12),
    "Progressive Disease":        ( 2,  6),
}

def treatment_duration(outcome: str) -> int:
    lo, hi = RESPONSE_DURATION[outcome]
    return random.randint(lo, hi)

# ── SCT ───────────────────────────────────────────────────────────────────────

def build_sct(age, fl_end, fl_outcome):
    """ASCT for transplant-eligible (≤75) patients with ≥PR on 1L (~55%)."""
    if age > 75:
        return []
    if fl_outcome not in ("Complete Response","Very Good Partial Response","Partial Response"):
        return []
    if random.random() > 0.55:
        return []
    sct_date = add_months(fl_end, random.randint(2, 5))
    entries = [{"type":"Autologous Stem Cell Transplant (ASCT)",
                "date": str(sct_date),
                "outcome":"Successful engraftment"}]
    if random.random() < 0.10:   # tandem ASCT
        entries.append({"type":"Second Autologous Stem Cell Transplant (ASCT)",
                        "date": str(add_months(sct_date, 3)),
                        "outcome":"Successful engraftment"})
    return entries

# ── treatment sequence utilities ──────────────────────────────────────────────

def pick_next_line(pool, prior_classes):
    """Prefer regimens that introduce a drug class not yet used."""
    preferred = [(n, c) for n, c in pool if not (c & prior_classes)]
    return random.choice(preferred if preferred else pool)

def derive_refractory_status(lines):
    """
    lines: list of (therapy_name, drug_classes_set, outcome)
    A drug class is refractory if the patient progressed or had minimal response on it.
    """
    refractory = set()
    for _, classes, outcome in lines:
        if outcome in ("Progressive Disease", "Minimal Response"):
            refractory |= classes

    has_pi   = "PI"   in refractory
    has_imid = "IMiD" in refractory
    has_cd38 = "CD38" in refractory

    if has_pi and has_imid and has_cd38:
        return "Triple-refractory (PI + IMiD + anti-CD38)"
    if has_pi and has_imid:
        return "Double-refractory (PI + IMiD)"
    if has_imid:
        return "IMiD-refractory (lenalidomide/pomalidomide)"
    if has_pi:
        return "PI-refractory (bortezomib/carfilzomib)"
    if refractory:
        return "Refractory to prior therapy"
    return None

# ── patient builder ───────────────────────────────────────────────────────────

def build_patient(i):
    pid    = 300 + i
    gender = "M" if random.random() < 0.60 else "F"
    fn     = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
    ln     = random.choice(LAST_NAMES)
    age    = random.randint(50, 82)
    birth_year = 2026 - age
    ethnicity  = random.choice(ETHNICITIES)
    state      = random.choice(US_STATES)
    ecog       = random.choices([0,1,2,3], weights=[30,40,22,8])[0]
    kps        = max(10, 100 - ecog * 20 + random.randint(-10, 10))

    # ISS stage
    stage_key = random.choices(
        list(ISS_STAGES.keys()),
        weights=[v[0] for v in ISS_STAGES.values()]
    )[0]
    _, b2m_range, alb_range = ISS_STAGES[stage_key]
    b2m     = round(random.uniform(*b2m_range), 2)
    albumin = round(random.uniform(*alb_range), 1)

    # Cytogenetics
    cyto_label, high_risk, cytogenic_markers = random.choice(CYTOGENETICS)
    mutations    = random.choice(MOLECULAR_MUTATIONS)
    tp53_disrupt = (cyto_label == "del(17p)")

    # CRAB criteria
    crab_prob = {"I": 0.15, "II": 0.40, "III": 0.72}[stage_key]
    if high_risk:
        crab_prob = min(0.90, crab_prob * 1.3)
    has_anemia        = random.random() < (crab_prob + 0.15)
    has_renal         = random.random() < crab_prob
    has_hypercalcemia = random.random() < (crab_prob * 0.45)
    bone_lesion_opts  = (
        ["Multiple lytic lesions","Multiple lytic lesions","Diffuse osteoporosis",
         "Single lytic lesion","Pathologic fracture"]
        if crab_prob > 0.35
        else ["Multiple lytic lesions","Diffuse osteoporosis","Single lytic lesion",
              "No bone lesions","No bone lesions"]
    )
    bone_lesions = random.choice(bone_lesion_opts)
    has_bone     = (bone_lesions != "No bone lesions")
    meets_crab   = has_anemia or has_renal or has_hypercalcemia or has_bone

    # Labs
    hemoglobin = round(random.uniform(7.0, 11.5) if has_anemia else random.uniform(10.5, 14.5), 1)
    creatinine = round(random.uniform(1.5, 5.0)  if has_renal  else random.uniform(0.6,  1.4), 2)
    calcium    = round(random.uniform(10.5, 14.0) if has_hypercalcemia else random.uniform(8.5, 10.3), 1)
    egfr       = max(10, int(110 / (creatinine ** 1.15)))
    m_prot_s   = round(random.uniform(0.5, 7.5), 1)
    m_prot_u   = round(random.uniform(0, 3.0), 1) if random.random() < 0.4 else 0.0
    kappa_flc  = random.randint(4, 280)
    lambda_flc = random.randint(2, 90)
    if random.random() < 0.5:
        kappa_flc, lambda_flc = lambda_flc, kappa_flc
    clonal_pc  = random.randint(10, 90)
    ldh        = (random.randint(200, 650) if (high_risk or stage_key == "III")
                  else random.randint(110, 260))
    plt        = random.randint(60, 380)
    wbc        = round(random.uniform(2.5, 11.0), 1)
    anc        = round(random.uniform(1.0,  8.0), 1)
    ast        = random.randint(14, 60)
    alt        = random.randint(10, 55)
    alp        = random.randint(40, 200)
    bilirubin  = round(random.uniform(0.3, 1.8), 1)

    dx_date = rand_date(2017, 2022)

    # ── Number of treatment lines ────────────────────────────────────────────
    # High-risk / ISS III patients progress through more lines
    line_weights = ([20, 30, 30, 20] if (high_risk or stage_key == "III")
                    else [32, 35, 23, 10])
    n_lines = random.choices([1, 2, 3, 4], weights=line_weights)[0]

    # ── 1st line ─────────────────────────────────────────────────────────────
    fl_name, fl_classes = random.choice(FIRST_LINE)
    fl_outcome  = pick_outcome(fl_name, high_risk)
    fl_months   = treatment_duration(fl_outcome)
    fl_start    = add_months(dx_date, random.randint(1, 3))
    fl_end      = add_months(fl_start, fl_months)
    fl_intent   = ("Curative"
                   if age <= 75 and fl_outcome in ("Complete Response","Very Good Partial Response")
                   else "Treatment")

    # SCT between 1L and 2L for eligible patients with good response
    sct_history = build_sct(age, fl_end, fl_outcome)
    post_fl_date = (date.fromisoformat(sct_history[-1]["date"]) + timedelta(days=90)
                    if sct_history else fl_end)

    all_lines     = [(fl_name, fl_classes, fl_outcome)]
    prior_classes = set(fl_classes)

    # ── 2nd line ─────────────────────────────────────────────────────────────
    sl_name = sl_start = sl_end = sl_outcome = None
    if n_lines >= 2:
        sl_name, sl_classes = pick_next_line(SECOND_LINE, prior_classes)
        sl_outcome  = pick_outcome(sl_name, high_risk)
        sl_months   = treatment_duration(sl_outcome)
        sl_start    = add_months(post_fl_date, random.randint(1, 5))
        sl_end      = add_months(sl_start, sl_months)
        prior_classes |= sl_classes
        all_lines.append((sl_name, sl_classes, sl_outcome))

    # ── 3rd line ─────────────────────────────────────────────────────────────
    lt_name = lt_start = lt_end = lt_outcome = None
    later_therapies_json = []
    if n_lines >= 3:
        lt_name, lt_classes = pick_next_line(LATER_LINE, prior_classes)
        lt_outcome  = pick_outcome(lt_name, high_risk)
        lt_months   = treatment_duration(lt_outcome)
        lt_start    = add_months(sl_end, random.randint(1, 4))
        lt_end      = add_months(lt_start, lt_months)
        prior_classes |= lt_classes
        all_lines.append((lt_name, lt_classes, lt_outcome))

        # 4th line stored in later_therapies JSON array
        if n_lines == 4:
            lt4_name, lt4_classes = pick_next_line(LATER_LINE, prior_classes)
            lt4_outcome = pick_outcome(lt4_name, high_risk)
            lt4_months  = treatment_duration(lt4_outcome)
            lt4_start   = add_months(lt_end, random.randint(1, 4))
            lt4_end     = add_months(lt4_start, lt4_months)
            later_therapies_json = [{
                "therapy":    lt4_name,
                "start_date": str(lt4_start),
                "end_date":   str(lt4_end),
                "outcome":    lt4_outcome,
                "intent":     "Disease Control",
            }]
            all_lines.append((lt4_name, lt4_classes, lt4_outcome))

    last_tx = (date.fromisoformat(later_therapies_json[-1]["end_date"])
               if later_therapies_json
               else (lt_end or sl_end or fl_end))

    refractory_status = derive_refractory_status(all_lines)

    prior_therapy_label = {
        1: "None",
        2: "One line",
        3: "Two lines",
        4: "More than two lines",
    }[n_lines]

    # Supportive therapy (bisphosphonates for bone disease are standard in MM)
    supportive = None
    supp_start = None
    if has_bone or random.random() < 0.55:
        supportive = random.choice(["Zoledronic Acid (Zometa)", "Denosumab (Xgeva)", "Pamidronate"])
        supp_start = add_months(fl_start, 1)

    preexisting = random.choice(PREEXISTING)
    smoking     = random.choices(["Never","Former","Current"], weights=[45, 42, 13])[0]

    return {
        "person_id":   pid,
        "given_name":  fn,
        "family_name": ln,
        "birth_year":  birth_year,
        "patient_age": age,
        "gender":      gender,
        "ethnicity":   ethnicity,
        "country":     "US",
        "region":      state,
        "postal_code": f"{random.randint(10000, 99999)}",
        "disease":       "Multiple Myeloma",
        "disease_slug":  "MM",
        "stage":         f"ISS Stage {stage_key}",
        "diagnosis_date": dx_date,
        "karnofsky_performance_score": kps,
        "ecog_performance_status":     ecog,
        "no_other_active_malignancies": True,
        "no_pre_existing_conditions":   len(preexisting) == 0,
        "preexisting_conditions":       json.dumps(preexisting),
        "peripheral_neuropathy_grade":
            random.choices([0,1,2,3], weights=[50,25,15,10])[0],
        "cytogenic_markers":           cytogenic_markers,
        "genetic_mutations":           json.dumps(mutations),
        "tp53_disruption":             tp53_disrupt,
        "stem_cell_transplant_history": json.dumps(sct_history),
        "plasma_cell_leukemia":        random.random() < 0.03,
        "clonal_plasma_cells":         clonal_pc,
        "measurable_disease_imwg":     True,
        "meets_crab":                  meets_crab,
        "bone_lesions":                bone_lesions,
        "bone_imaging_result":         has_bone,
        "hemoglobin_g_dl":             hemoglobin,
        "hemoglobin_level":            hemoglobin,
        "hemoglobin_level_units":      "g/dL",
        "platelet_count":              plt,
        "platelet_count_thousand_per_ul": round(plt / 1000, 1),
        "wbc_count_thousand_per_ul":   wbc,
        "white_blood_cell_count":      wbc,
        "anc_thousand_per_ul":         anc,
        "absolute_neutrophile_count":  anc,
        "serum_calcium_mg_dl":         calcium,
        "serum_calcium_level":         calcium,
        "serum_calcium_level_units":   "mg/dL",
        "serum_creatinine_mg_dl":      creatinine,
        "serum_creatinine_level":      creatinine,
        "serum_creatinine_level_units": "mg/dL",
        "creatinine_clearance_ml_min":  egfr,
        "estimated_glomerular_filtration_rate": egfr,
        "egfr_ml_min_173m2":           egfr,
        "renal_adequacy_status":       creatinine <= 2.0,
        "albumin_g_dl":                albumin,
        "albumin_level":               albumin,
        "albumin_level_units":         "g/dL",
        "beta2_microglobulin":         b2m,
        "serum_beta2_microglobulin_level": b2m,
        "monoclonal_protein_serum":    m_prot_s,
        "monoclonal_protein_urine":    m_prot_u,
        "kappa_flc":                   kappa_flc,
        "lambda_flc":                  lambda_flc,
        "lactate_dehydrogenase_level": ldh,
        "ldh_u_l":                     ldh,
        "liver_enzyme_levels_ast":     ast,
        "ast_u_l":                     ast,
        "liver_enzyme_levels_alt":     alt,
        "alt_u_l":                     alt,
        "liver_enzyme_levels_alp":     alp,
        "alkaline_phosphatase_u_l":    alp,
        "serum_bilirubin_level_total":  bilirubin,
        "bilirubin_total_mg_dl":        bilirubin,
        "serum_bilirubin_level_total_units": "mg/dL",
        "prior_therapy":               prior_therapy_label,
        "therapy_lines_count":         n_lines,
        "relapse_count":               max(0, n_lines - 1),
        "treatment_refractory_status": refractory_status,
        "last_treatment":              last_tx,
        "first_line_therapy":          fl_name,
        "first_line_start_date":       fl_start,
        "first_line_end_date":         fl_end,
        "first_line_date":             fl_start,
        "first_line_outcome":          fl_outcome,
        "first_line_intent":           fl_intent,
        "second_line_therapy":         sl_name,
        "second_line_start_date":      sl_start,
        "second_line_end_date":        sl_end,
        "second_line_date":            sl_start,
        "second_line_outcome":         sl_outcome,
        "later_therapy":               lt_name,
        "later_start_date":            lt_start,
        "later_end_date":              lt_end,
        "later_date":                  lt_start,
        "later_outcome":               lt_outcome,
        "later_therapies":             json.dumps(later_therapies_json),
        "supportive_therapies":        supportive,
        "supportive_therapy_start_date": supp_start,
        "pulmonary_function_test_result":    random.random() < 0.72,
        "consent_capability":                True,
        "caregiver_availability_status":     random.random() < 0.70,
        "contraceptive_use":                 gender == "F" and age < 55 and random.random() < 0.35,
        "no_pregnancy_or_lactation_status":  True,
        "pregnancy_test_result":             False,
        "no_mental_health_disorder_status":  random.random() < 0.85,
        "no_concomitant_medication_status":  random.random() < 0.55,
        "no_tobacco_use_status":             smoking != "Current",
        "no_substance_use_status":           random.random() < 0.90,
        "no_geographic_exposure_risk":       True,
        "no_hiv_status":                     True,
        "no_hepatitis_b_status":             True,
        "no_hepatitis_c_status":             True,
        "no_active_infection_status":        random.random() < 0.88,
        "smoking_status":                    smoking,
    }

# ── database insert ───────────────────────────────────────────────────────────

INSERT_PERSON = """
    INSERT INTO person (person_id, year_of_birth, given_name, family_name)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (person_id) DO NOTHING
"""

INSERT_PATIENT = """
    INSERT INTO patient_info (
        person_id, patient_age, gender, ethnicity, country, region, postal_code,
        disease, disease_slug, stage, diagnosis_date,
        karnofsky_performance_score, ecog_performance_status,
        no_other_active_malignancies, no_pre_existing_conditions, preexisting_conditions,
        peripheral_neuropathy_grade,
        cytogenic_markers, genetic_mutations, tp53_disruption,
        stem_cell_transplant_history, plasma_cell_leukemia,
        clonal_plasma_cells, measurable_disease_imwg,
        meets_crab, bone_lesions, bone_imaging_result,
        hemoglobin_g_dl, hemoglobin_level, hemoglobin_level_units,
        platelet_count, platelet_count_thousand_per_ul,
        wbc_count_thousand_per_ul, white_blood_cell_count,
        anc_thousand_per_ul, absolute_neutrophile_count,
        serum_calcium_mg_dl, serum_calcium_level, serum_calcium_level_units,
        serum_creatinine_mg_dl, serum_creatinine_level, serum_creatinine_level_units,
        creatinine_clearance_ml_min, estimated_glomerular_filtration_rate, egfr_ml_min_173m2,
        renal_adequacy_status,
        albumin_g_dl, albumin_level, albumin_level_units,
        beta2_microglobulin, serum_beta2_microglobulin_level,
        monoclonal_protein_serum, monoclonal_protein_urine,
        kappa_flc, lambda_flc,
        lactate_dehydrogenase_level, ldh_u_l,
        liver_enzyme_levels_ast, ast_u_l,
        liver_enzyme_levels_alt, alt_u_l,
        liver_enzyme_levels_alp, alkaline_phosphatase_u_l,
        serum_bilirubin_level_total, bilirubin_total_mg_dl, serum_bilirubin_level_total_units,
        prior_therapy, therapy_lines_count, relapse_count,
        treatment_refractory_status, last_treatment,
        first_line_therapy, first_line_start_date, first_line_end_date,
        first_line_date, first_line_outcome, first_line_intent,
        second_line_therapy, second_line_start_date, second_line_end_date,
        second_line_date, second_line_outcome,
        later_therapy, later_start_date, later_end_date,
        later_date, later_outcome, later_therapies,
        supportive_therapies, supportive_therapy_start_date,
        pulmonary_function_test_result, consent_capability,
        caregiver_availability_status, contraceptive_use,
        no_pregnancy_or_lactation_status, pregnancy_test_result,
        no_mental_health_disorder_status, no_concomitant_medication_status,
        no_tobacco_use_status, no_substance_use_status,
        no_geographic_exposure_risk, no_hiv_status,
        no_hepatitis_b_status, no_hepatitis_c_status, no_active_infection_status,
        smoking_status,
        created_at, updated_at
    ) VALUES (
        %(person_id)s, %(patient_age)s, %(gender)s, %(ethnicity)s,
        %(country)s, %(region)s, %(postal_code)s,
        %(disease)s, %(disease_slug)s, %(stage)s, %(diagnosis_date)s,
        %(karnofsky_performance_score)s, %(ecog_performance_status)s,
        %(no_other_active_malignancies)s, %(no_pre_existing_conditions)s,
        %(preexisting_conditions)s, %(peripheral_neuropathy_grade)s,
        %(cytogenic_markers)s, %(genetic_mutations)s, %(tp53_disruption)s,
        %(stem_cell_transplant_history)s, %(plasma_cell_leukemia)s,
        %(clonal_plasma_cells)s, %(measurable_disease_imwg)s,
        %(meets_crab)s, %(bone_lesions)s, %(bone_imaging_result)s,
        %(hemoglobin_g_dl)s, %(hemoglobin_level)s, %(hemoglobin_level_units)s,
        %(platelet_count)s, %(platelet_count_thousand_per_ul)s,
        %(wbc_count_thousand_per_ul)s, %(white_blood_cell_count)s,
        %(anc_thousand_per_ul)s, %(absolute_neutrophile_count)s,
        %(serum_calcium_mg_dl)s, %(serum_calcium_level)s, %(serum_calcium_level_units)s,
        %(serum_creatinine_mg_dl)s, %(serum_creatinine_level)s,
        %(serum_creatinine_level_units)s,
        %(creatinine_clearance_ml_min)s, %(estimated_glomerular_filtration_rate)s,
        %(egfr_ml_min_173m2)s, %(renal_adequacy_status)s,
        %(albumin_g_dl)s, %(albumin_level)s, %(albumin_level_units)s,
        %(beta2_microglobulin)s, %(serum_beta2_microglobulin_level)s,
        %(monoclonal_protein_serum)s, %(monoclonal_protein_urine)s,
        %(kappa_flc)s, %(lambda_flc)s,
        %(lactate_dehydrogenase_level)s, %(ldh_u_l)s,
        %(liver_enzyme_levels_ast)s, %(ast_u_l)s,
        %(liver_enzyme_levels_alt)s, %(alt_u_l)s,
        %(liver_enzyme_levels_alp)s, %(alkaline_phosphatase_u_l)s,
        %(serum_bilirubin_level_total)s, %(bilirubin_total_mg_dl)s,
        %(serum_bilirubin_level_total_units)s,
        %(prior_therapy)s, %(therapy_lines_count)s, %(relapse_count)s,
        %(treatment_refractory_status)s, %(last_treatment)s,
        %(first_line_therapy)s, %(first_line_start_date)s, %(first_line_end_date)s,
        %(first_line_date)s, %(first_line_outcome)s, %(first_line_intent)s,
        %(second_line_therapy)s, %(second_line_start_date)s, %(second_line_end_date)s,
        %(second_line_date)s, %(second_line_outcome)s,
        %(later_therapy)s, %(later_start_date)s, %(later_end_date)s,
        %(later_date)s, %(later_outcome)s, %(later_therapies)s,
        %(supportive_therapies)s, %(supportive_therapy_start_date)s,
        %(pulmonary_function_test_result)s, %(consent_capability)s,
        %(caregiver_availability_status)s, %(contraceptive_use)s,
        %(no_pregnancy_or_lactation_status)s, %(pregnancy_test_result)s,
        %(no_mental_health_disorder_status)s, %(no_concomitant_medication_status)s,
        %(no_tobacco_use_status)s, %(no_substance_use_status)s,
        %(no_geographic_exposure_risk)s, %(no_hiv_status)s,
        %(no_hepatitis_b_status)s, %(no_hepatitis_c_status)s,
        %(no_active_infection_status)s, %(smoking_status)s,
        NOW(), NOW()
    )
    ON CONFLICT (person_id) DO NOTHING
"""

def insert_patients(patients):
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    for idx, p in enumerate(patients, 1):
        cur.execute(INSERT_PERSON, (p["person_id"], p["birth_year"], p["given_name"], p["family_name"]))
        cur.execute(INSERT_PATIENT, p)
        if idx % 10 == 0:
            conn.commit()
            print(f"  {idx}/100 inserted...")
    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone — {len(patients)} MM patients inserted (person_ids 300–399).")

# ── verification ──────────────────────────────────────────────────────────────

def verify():
    import subprocess
    queries = [
        ("Stage distribution",
         "SELECT stage, COUNT(*) FROM patient_info WHERE disease='Multiple Myeloma' "
         "GROUP BY stage ORDER BY stage;"),
        ("1L therapy → outcome",
         "SELECT first_line_therapy, first_line_outcome, COUNT(*) "
         "FROM patient_info WHERE disease='Multiple Myeloma' "
         "GROUP BY first_line_therapy, first_line_outcome "
         "ORDER BY first_line_therapy, count DESC;"),
        ("2L therapy → outcome",
         "SELECT second_line_therapy, second_line_outcome, COUNT(*) "
         "FROM patient_info WHERE disease='Multiple Myeloma' "
         "AND second_line_therapy IS NOT NULL "
         "GROUP BY second_line_therapy, second_line_outcome "
         "ORDER BY second_line_therapy, count DESC;"),
        ("3L+ therapy → outcome",
         "SELECT later_therapy, later_outcome, COUNT(*) "
         "FROM patient_info WHERE disease='Multiple Myeloma' "
         "AND later_therapy IS NOT NULL "
         "GROUP BY later_therapy, later_outcome "
         "ORDER BY later_therapy, count DESC;"),
        ("Therapy lines distribution",
         "SELECT therapy_lines_count, COUNT(*) FROM patient_info "
         "WHERE disease='Multiple Myeloma' "
         "GROUP BY therapy_lines_count ORDER BY therapy_lines_count;"),
        ("Refractory status",
         "SELECT treatment_refractory_status, COUNT(*) FROM patient_info "
         "WHERE disease='Multiple Myeloma' AND treatment_refractory_status IS NOT NULL "
         "GROUP BY treatment_refractory_status ORDER BY count DESC;"),
    ]
    for title, sql in queries:
        print(f"\n── {title} ──")
        r = subprocess.run(["psql", DB_URL, "-c", sql], capture_output=True, text=True)
        print(r.stdout)


if __name__ == "__main__":
    print("Generating 100 Multiple Myeloma patients...")
    patients = [build_patient(i) for i in range(100)]
    print("Inserting into database...")
    insert_patients(patients)
    verify()
