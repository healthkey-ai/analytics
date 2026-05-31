from django.db.models import Count, Case, When, Value, CharField


AGE_BUCKET_ORDER = ['< 50', '50–54', '55–59', '60–64', '65–69', '70–74', '75–79', '80+']


def compute(qs):
    total = qs.count()
    if not total:
        return {}

    # Age — one query using CASE WHEN in the DB instead of 8 range queries
    age_rows = (
        qs.exclude(patient_age__isnull=True)
        .annotate(bucket=Case(
            When(patient_age__lt=50, then=Value('< 50')),
            When(patient_age__lt=55, then=Value('50–54')),
            When(patient_age__lt=60, then=Value('55–59')),
            When(patient_age__lt=65, then=Value('60–64')),
            When(patient_age__lt=70, then=Value('65–69')),
            When(patient_age__lt=75, then=Value('70–74')),
            When(patient_age__lt=80, then=Value('75–79')),
            default=Value('80+'),
            output_field=CharField(),
        ))
        .values('bucket')
        .annotate(count=Count('id'))
    )
    age_dict = {r['bucket']: r['count'] for r in age_rows}
    age_dist = [
        {"bucket": b, "count": age_dict[b], "pct": round(age_dict[b] / total * 100, 1)}
        for b in AGE_BUCKET_ORDER if b in age_dict
    ]

    # Gender
    gender_map = {"M": "Male", "F": "Female"}
    gender_rows = (
        qs.exclude(gender__isnull=True)
        .values('gender').annotate(count=Count('id')).order_by('-count')
    )
    gender = [
        {"gender": gender_map.get(r['gender'], r['gender']), "count": r['count'],
         "pct": round(r['count'] / total * 100, 1)}
        for r in gender_rows
    ]

    # Race
    race_rows = (
        qs.exclude(race__isnull=True)
        .values('race').annotate(count=Count('id')).order_by('-count')
    )
    race = [
        {"race": r['race'], "count": r['count'],
         "pct": round(r['count'] / total * 100, 1)}
        for r in race_rows
    ]

    # Ethnicity
    ethnicity_rows = (
        qs.exclude(ethnicity__isnull=True)
        .values('ethnicity').annotate(count=Count('id')).order_by('-count')
    )
    ethnicity = [
        {"ethnicity": r['ethnicity'], "count": r['count'],
         "pct": round(r['count'] / total * 100, 1)}
        for r in ethnicity_rows
    ]

    # Region (top 15)
    region_rows = (
        qs.exclude(region__isnull=True)
        .values('region').annotate(count=Count('id')).order_by('-count')[:15]
    )
    region = [{"region": r['region'], "count": r['count']} for r in region_rows]

    # Smoking
    smoking_rows = (
        qs.exclude(smoking_status__isnull=True)
        .values('smoking_status').annotate(count=Count('id')).order_by('-count')
    )
    smoking = [
        {"status": r['smoking_status'], "count": r['count'],
         "pct": round(r['count'] / total * 100, 1)}
        for r in smoking_rows
    ]

    return {
        "age_distribution": age_dist,
        "gender":           gender,
        "race":             race,
        "ethnicity":        ethnicity,
        "region":           region,
        "smoking":          smoking,
    }
