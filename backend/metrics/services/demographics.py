from django.db.models import Count


def compute(qs):
    total = qs.count()
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
        sub = qs
        if lo is not None:
            sub = sub.filter(patient_age__gte=lo)
        if hi is not None:
            sub = sub.filter(patient_age__lte=hi)
        count = sub.count()
        if count:
            age_dist.append({"bucket": label, "count": count,
                             "pct": round(count / total * 100, 1)})

    # Gender
    gender_rows = (
        qs.exclude(gender__isnull=True)
        .values("gender")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    gender_map = {"M": "Male", "F": "Female"}
    gender = [
        {"gender": gender_map.get(r["gender"], r["gender"]),
         "count": r["count"],
         "pct": round(r["count"] / total * 100, 1)}
        for r in gender_rows
    ]

    # Ethnicity
    ethnicity_rows = (
        qs.exclude(ethnicity__isnull=True)
        .values("ethnicity")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    ethnicity = [
        {"ethnicity": r["ethnicity"], "count": r["count"],
         "pct": round(r["count"] / total * 100, 1)}
        for r in ethnicity_rows
    ]

    # Region (top 15)
    region_rows = (
        qs.exclude(region__isnull=True)
        .values("region")
        .annotate(count=Count("id"))
        .order_by("-count")[:15]
    )
    region = [{"region": r["region"], "count": r["count"]} for r in region_rows]

    # Smoking
    smoking_rows = (
        qs.exclude(smoking_status__isnull=True)
        .values("smoking_status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    smoking = [{"status": r["smoking_status"], "count": r["count"],
                "pct": round(r["count"] / total * 100, 1)} for r in smoking_rows]

    return {
        "age_distribution": age_dist,
        "gender": gender,
        "ethnicity": ethnicity,
        "region": region,
        "smoking": smoking,
    }
