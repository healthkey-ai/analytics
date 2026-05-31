from collections import Counter, defaultdict


def _therapy_counts(records, therapy_field, total):
    counts = Counter(r[therapy_field] for r in records if r.get(therapy_field))
    return [
        {"therapy": t, "count": c, "pct": round(c / total * 100, 1) if total else 0}
        for t, c in counts.most_common()
    ]


def _short(name):
    if not name:
        return "—"
    idx = name.find(" (")
    return name[:idx] if idx > 0 else name[:30]


def _build_sequences(records):
    counter = Counter()
    for r in records:
        if not r.get("second_line_therapy"):
            continue
        parts = [_short(r.get("first_line_therapy")), _short(r["second_line_therapy"])]
        if r.get("later_therapy"):
            parts.append(_short(r["later_therapy"]))
        counter[" → ".join(parts)] += 1
    return [{"sequence": seq, "count": cnt} for seq, cnt in counter.most_common(12)]


def compute(records):
    total = len(records)

    line_funnel = []
    for n in [1, 2, 3, 4]:
        count = sum(1 for r in records if (r.get("therapy_lines_count") or 0) >= n)
        line_funnel.append({"line": n, "label": f"≥{n}L", "count": count,
                            "pct": round(count / total * 100, 1) if total else 0})

    exact_dist = []
    for n in [1, 2, 3, 4]:
        count = sum(1 for r in records if r.get("therapy_lines_count") == n)
        if count:
            exact_dist.append({"lines": n, "label": f"{n}L", "count": count,
                               "pct": round(count / total * 100, 1) if total else 0})

    return {
        "first_line":        _therapy_counts(records, "first_line_therapy", total),
        "second_line":       _therapy_counts(records, "second_line_therapy", total),
        "later_line":        _therapy_counts(records, "later_therapy", total),
        "line_funnel":       line_funnel,
        "line_distribution": exact_dist,
        "sequences":         _build_sequences(records),
    }
