import statistics


LAB_FIELDS = [
    ("hemoglobin",        "hemoglobin_g_dl",       "g/dL",   "Hemoglobin"),
    ("beta2_microglobulin","beta2_microglobulin",   "mg/L",   "β2-Microglobulin"),
    ("albumin",           "albumin_g_dl",           "g/dL",   "Albumin"),
    ("creatinine",        "serum_creatinine_mg_dl", "mg/dL",  "Creatinine"),
    ("ldh",               "ldh_u_l",                "U/L",    "LDH"),
    ("m_protein",         "monoclonal_protein_serum","g/dL",  "M-Protein (Serum)"),
    ("calcium",           "serum_calcium_mg_dl",    "mg/dL",  "Calcium"),
    ("kappa_flc",         "kappa_flc",              "mg/L",   "Kappa FLC"),
    ("lambda_flc",        "lambda_flc",             "mg/L",   "Lambda FLC"),
]


def _stats(values):
    vals = sorted(float(v) for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    median = statistics.median(vals)
    q1 = vals[int(n * 0.25)]
    q3 = vals[int(n * 0.75)]
    return {
        "median": round(median, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "min": round(vals[0], 2),
        "max": round(vals[-1], 2),
        "n": n,
    }


def compute(qs):
    result = {}
    ids = list(qs.values_list("id", flat=True))
    if not ids:
        return result

    # Fetch all relevant columns in one query
    records = list(qs.values(*[f for _, f, _, _ in LAB_FIELDS]))

    for key, field, unit, label in LAB_FIELDS:
        values = [r[field] for r in records if r[field] is not None]
        stats = _stats(values)
        if stats:
            result[key] = {**stats, "unit": unit, "label": label}

    return result
