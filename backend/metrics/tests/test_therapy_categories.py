from metrics.services.therapy_categories import compute, categories_for


class _FakeQS:
    def __init__(self, rows):
        # rows: list of dicts keyed by therapy field
        self._rows = rows

    def exclude(self, *args, **kwargs):
        rows = self._rows
        for key, val in kwargs.items():
            if key.endswith("__isnull"):
                field = key[: -len("__isnull")]
                rows = [r for r in rows if (r.get(field) is None) != val]
            elif key.endswith("__exact"):
                field = key[: -len("__exact")]
                rows = [r for r in rows if r.get(field) != val]
        return _FakeQS(rows)

    def values_list(self, field, flat=False):
        return [r.get(field) for r in self._rows]


# ---------------------------------------------------------------------------
# categories_for — mapping correctness, including multi-membership
# ---------------------------------------------------------------------------

def test_rchop_is_chemo_and_monoclonal():
    cats = categories_for("R-CHOP")
    assert "Chemotherapy-containing" in cats
    assert "Monoclonal antibody" in cats


def test_br_is_chemo_and_monoclonal():
    cats = categories_for("Bendamustine and Rituximab (BR)")
    assert "Chemotherapy-containing" in cats
    assert "Monoclonal antibody" in cats


def test_r2_is_imid_and_monoclonal():
    cats = categories_for("Lenalidomide and Rituximab (R2)")
    assert "Immunomodulatory (IMiD)" in cats
    assert "Monoclonal antibody" in cats


def test_bispecific():
    assert categories_for("Mosunetuzumab monotherapy") == ["Bispecific antibody"]
    assert categories_for("Epcoritamab monotherapy") == ["Bispecific antibody"]


def test_car_t():
    assert categories_for("Axicabtagene ciloleucel monotherapy") == ["CAR-T"]
    assert categories_for("Cilta-cel (Carvykti) Monotherapy") == ["CAR-T"]


def test_targeted_small_molecule():
    assert categories_for("Tazemetostat monotherapy") == ["Targeted / small-molecule"]
    assert categories_for("Copanlisib monotherapy") == ["Targeted / small-molecule"]


def test_rituximab_monotherapy_is_mab_only():
    assert categories_for("Rituximab monotherapy") == ["Monoclonal antibody"]


def test_unknown_regimen_has_no_categories():
    assert categories_for("Some Novel Agent") == []


def test_none_and_empty_have_no_categories():
    assert categories_for(None) == []
    assert categories_for("") == []


# ---------------------------------------------------------------------------
# compute — per-line structure, counts, empty queryset
# ---------------------------------------------------------------------------

def test_compute_counts_categories_per_line():
    rows = [
        {"first_line_therapy": "R-CHOP"},
        {"first_line_therapy": "Bendamustine and Rituximab (BR)"},
        {"first_line_therapy": None},
        {"first_line_therapy": ""},
    ]
    result = compute(_FakeQS(rows))

    first = {c["category"]: c for c in result["first_line"]}
    # 2 evaluable 1L regimens; both are chemo-containing and mAb
    assert first["Chemotherapy-containing"]["count"] == 2
    assert first["Chemotherapy-containing"]["pct"] == 100.0
    assert first["Monoclonal antibody"]["count"] == 2
    assert result["second_line"] == []
    assert result["later_line"] == []


def test_compute_uses_correct_field_per_line():
    rows = [{"second_line_therapy": "Mosunetuzumab monotherapy"}]
    result = compute(_FakeQS(rows))

    assert result["first_line"] == []
    second = {c["category"]: c for c in result["second_line"]}
    assert second["Bispecific antibody"]["count"] == 1


def test_compute_empty_queryset():
    result = compute(_FakeQS([]))
    assert result == {"first_line": [], "second_line": [], "later_line": []}


# ---------------------------------------------------------------------------
# Coverage: every regimen offered in the filter panel must map to a category
# ---------------------------------------------------------------------------

def test_every_therapy_map_regimen_has_a_category():
    from cohorts.views import THERAPY_MAP

    uncategorized = [
        (disease, regimen)
        for disease, cfg in THERAPY_MAP.items()
        for key in ("first_line_therapies", "second_line_therapies", "later_line_therapies")
        for regimen in cfg.get(key, [])
        if not categories_for(regimen)
    ]
    assert uncategorized == []
