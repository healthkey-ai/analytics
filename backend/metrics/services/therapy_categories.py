"""
Therapy-category grouping: map free-text regimens to therapy categories and
count patients per category, per line of therapy.

Categories are matched by case-insensitive substring. A regimen can belong to
more than one category (e.g. R-CHOP is both chemotherapy-containing and an
anti-CD20 monoclonal antibody regimen) — membership is additive, so category
counts for a line need not sum to the number of patients on that line.
"""

# Ordered (category, keywords) — first match per category wins, but every
# category is tested so multi-membership is preserved.
CATEGORY_RULES = [
    ("Bispecific antibody", ["mosunetuzumab", "epcoritamab", "glofitamab", "teclistamab"]),
    ("CAR-T", ["axicabtagene", "tisagenlecleucel", "ide-cel", "cilta-cel"]),
    (
        "Chemotherapy-containing",
        [
            "chop", "cvp", "bendamustine", "cyclophosphamide", "melphalan",
            "taxane", "capecitabine", "gemcitabine", "carboplatin",
            "vinorelbine", "eribulin", "chemotherapy",
        ],
    ),
    ("Immunomodulatory (IMiD)", ["lenalidomide", "pomalidomide", "(r2)"]),
    (
        "Monoclonal antibody",
        [
            "rituximab", "obinutuzumab", "daratumumab", "isatuximab",
            "trastuzumab", "pertuzumab", "elotuzumab",
            # Abbreviated combos whose anti-CD20 component is implied:
            # R-CHOP, R-CVP (rituximab), G-CHOP (obinutuzumab)
            "r-chop", "r-cvp", "g-chop",
        ],
    ),
    (
        "Targeted / small-molecule",
        [
            "tazemetostat", "copanlisib", "venetoclax", "selinexor", "parp",
            "bortezomib", "carfilzomib", "ixazomib", "cdk4/6",
        ],
    ),
    ("Endocrine", ["tamoxifen", "letrozole", "aromatase", "fulvestrant"]),
]

LINE_FIELDS = [
    ("first_line", "first_line_therapy"),
    ("second_line", "second_line_therapy"),
    ("later_line", "later_therapy"),
]


def categories_for(regimen):
    """Return all category names a regimen string belongs to."""
    text = (regimen or "").lower()
    return [name for name, keywords in CATEGORY_RULES if any(k in text for k in keywords)]


def _line_categories(qs, therapy_field):
    rows = qs.exclude(**{f"{therapy_field}__isnull": True}).exclude(
        **{f"{therapy_field}__exact": ""}
    ).values_list(therapy_field, flat=True)

    regimens = list(rows)
    total = len(regimens)
    counts = {name: 0 for name, _ in CATEGORY_RULES}
    for regimen in regimens:
        for category in categories_for(regimen):
            counts[category] += 1

    return [
        {
            "category": name,
            "count": counts[name],
            "pct": round(counts[name] / total * 100, 1) if total else 0,
        }
        for name, _ in CATEGORY_RULES
        if counts[name]
    ]


def compute(qs):
    return {line: _line_categories(qs, field) for line, field in LINE_FIELDS}
