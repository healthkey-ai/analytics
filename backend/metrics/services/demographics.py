from collections import Counter


def compute(records):
    total = len(records)
    if not total:
        return {}

    # Age buckets
    age_buckets = [
        ("< 50",  None, 49),
        ("50–54", 50,   54),
        ("55–59", 55,   59),
        ("60–64", 60,   64),
        ("65–69", 65,   69),
        ("70–74", 70,   74),
        ("75–79", 75,   79),
        ("80+",   80,   None),
    ]
    age_dist = []
    for label, lo, hi in age_buckets:
        count = sum(
            1 for r in records
            if r.get("patient_age") is not None
            and (lo is None or r["patient_age"] >= lo)
            and (hi is None or r["patient_age"] <= hi)
        )
        if count:
            age_dist.append({"bucket": label, "count": count,
                             "pct": round(count / total * 100, 1)})

    # Gender
    gender_map = {"M": "Male", "F": "Female"}
    gender_counts = Counter(r["gender"] for r in records if r.get("gender"))
    gender = [
        {"gender": gender_map.get(g, g), "count": c,
         "pct": round(c / total * 100, 1)}
        for g, c in gender_counts.most_common()
    ]

    # Ethnicity
    ethnicity_counts = Counter(r["ethnicity"] for r in records if r.get("ethnicity"))
    ethnicity = [
        {"ethnicity": e, "count": c, "pct": round(c / total * 100, 1)}
        for e, c in ethnicity_counts.most_common()
    ]

    # Region (top 15)
    region_counts = Counter(r["region"] for r in records if r.get("region"))
    region = [
        {"region": reg, "count": c}
        for reg, c in region_counts.most_common(15)
    ]

    # Smoking
    smoking_counts = Counter(r["smoking_status"] for r in records if r.get("smoking_status"))
    smoking = [
        {"status": s, "count": c, "pct": round(c / total * 100, 1)}
        for s, c in smoking_counts.most_common()
    ]

    return {
        "age_distribution": age_dist,
        "gender":           gender,
        "ethnicity":        ethnicity,
        "region":           region,
        "smoking":          smoking,
    }
