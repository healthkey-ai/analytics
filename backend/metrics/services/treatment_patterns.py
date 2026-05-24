from django.db.models import Count


def _therapy_counts(qs, therapy_field):
    total = qs.count()
    rows = (
        qs.exclude(**{f"{therapy_field}__isnull": True})
        .exclude(**{f"{therapy_field}__exact": ""})
        .values(therapy_field)
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [
        {
            "therapy": r[therapy_field],
            "count": r["count"],
            "pct": round(r["count"] / total * 100, 1) if total else 0,
        }
        for r in rows
    ]


def compute(qs):
    total = qs.count()

    # Treatment line funnel
    line_dist = []
    for n in [1, 2, 3, 4]:
        count = qs.filter(therapy_lines_count__gte=n).count()
        line_dist.append({
            "line": n,
            "label": f"≥{n}L",
            "count": count,
            "pct": round(count / total * 100, 1) if total else 0,
        })

    # Exact line count distribution
    exact_dist = []
    for n in [1, 2, 3, 4]:
        count = qs.filter(therapy_lines_count=n).count()
        if count:
            exact_dist.append({
                "lines": n,
                "label": f"{n}L",
                "count": count,
                "pct": round(count / total * 100, 1) if total else 0,
            })

    # Top treatment sequences (1L → 2L → 3L)
    sequences = _build_sequences(qs)

    return {
        "first_line": _therapy_counts(qs, "first_line_therapy"),
        "second_line": _therapy_counts(qs, "second_line_therapy"),
        "later_line": _therapy_counts(qs, "later_therapy"),
        "line_funnel": line_dist,
        "line_distribution": exact_dist,
        "sequences": sequences,
    }


def _short(name):
    """Extract short name from long therapy string (text before first space-paren)."""
    if not name:
        return "—"
    idx = name.find(" (")
    return name[:idx] if idx > 0 else name[:30]


def _build_sequences(qs):
    from collections import Counter
    counter = Counter()
    for p in qs.exclude(second_line_therapy__isnull=True).values(
        "first_line_therapy", "second_line_therapy", "later_therapy"
    ):
        parts = [_short(p["first_line_therapy"]), _short(p["second_line_therapy"])]
        if p["later_therapy"]:
            parts.append(_short(p["later_therapy"]))
        counter[" → ".join(parts)] += 1

    return [
        {"sequence": seq, "count": cnt}
        for seq, cnt in counter.most_common(12)
    ]
