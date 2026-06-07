from collections import defaultdict


def _switching_flows(qs, from_f, to_f, min_from_n=2):
    """
    For each regimen in from_f, compute the distribution of next regimens in to_f.
    Only include from-regimens with at least min_from_n patients who switched.
    Returns rows sorted by total switchers descending.
    """
    rows = qs.exclude(**{f"{from_f}__isnull": True}) \
             .exclude(**{f"{from_f}__exact": ""}) \
             .exclude(**{f"{to_f}__isnull": True}) \
             .exclude(**{f"{to_f}__exact": ""}) \
             .values(from_f, to_f)

    # count[from][to] = n
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        counts[r[from_f]][r[to_f]] += 1

    result = []
    for from_reg, to_map in counts.items():
        total = sum(to_map.values())
        if total < min_from_n:
            continue
        switches = sorted(
            [{"to_regimen": to, "n": n, "pct": round(100 * n / total, 1)}
             for to, n in to_map.items()],
            key=lambda x: -x["n"],
        )
        result.append({
            "from_regimen": from_reg,
            "n_switched": total,
            "switches": switches,
        })

    return sorted(result, key=lambda x: -x["n_switched"])


def compute(qs):
    return {
        "from_1l": _switching_flows(qs, "first_line_therapy", "second_line_therapy"),
        "from_2l": _switching_flows(qs, "second_line_therapy", "later_therapy"),
    }
