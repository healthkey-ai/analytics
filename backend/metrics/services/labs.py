from django.db import connection


LAB_FIELDS = [
    ("hemoglobin",         "hemoglobin_g_dl",        "g/dL",  "Hemoglobin"),
    ("beta2_microglobulin","beta2_microglobulin",     "mg/L",  "β2-Microglobulin"),
    ("albumin",            "albumin_g_dl",            "g/dL",  "Albumin"),
    ("creatinine",         "serum_creatinine_mg_dl",  "mg/dL", "Creatinine"),
    ("ldh",                "ldh_u_l",                 "U/L",   "LDH"),
    ("m_protein",          "monoclonal_protein_serum","g/dL",  "M-Protein (Serum)"),
    ("calcium",            "serum_calcium_mg_dl",     "mg/dL", "Calcium"),
    ("kappa_flc",          "kappa_flc",               "mg/L",  "Kappa FLC"),
    ("lambda_flc",         "lambda_flc",              "mg/L",  "Lambda FLC"),
]


def compute(qs):
    subq_sql, params = qs.values('id').query.sql_with_params()

    # All 9 lab fields in one query using Postgres PERCENTILE_CONT
    selects = []
    for key, field, _, _ in LAB_FIELDS:
        f = f'"{field}"'
        selects += [
            f"PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY {f}) AS {key}_median",
            f"PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {f}) AS {key}_q1",
            f"PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {f}) AS {key}_q3",
            f"MIN({f})   AS {key}_min",
            f"MAX({f})   AS {key}_max",
            f"COUNT({f}) AS {key}_n",
        ]

    sql = f"SELECT {', '.join(selects)} FROM patient_record WHERE id IN ({subq_sql})"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cols = [col[0] for col in cursor.description]

    data = dict(zip(cols, row))
    result = {}
    for key, _, unit, label in LAB_FIELDS:
        n = data.get(f'{key}_n')
        if n:
            result[key] = {
                "median": round(float(data[f'{key}_median']), 2),
                "q1":     round(float(data[f'{key}_q1']),     2),
                "q3":     round(float(data[f'{key}_q3']),     2),
                "min":    round(float(data[f'{key}_min']),    2),
                "max":    round(float(data[f'{key}_max']),    2),
                "n":      int(n),
                "unit":   unit,
                "label":  label,
            }
    return result
