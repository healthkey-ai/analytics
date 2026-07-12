import re


_QUALIFIER_STAGE_RE = re.compile(r"^Stage\s+([1-4])\s+\(qualifier value\)$", re.IGNORECASE)
_CANONICAL_STAGE_RE = re.compile(r"^(?:Stage\s+)?(I{1,3}|IV)([ABC])?$", re.IGNORECASE)
_ROMAN_TO_NUMERIC = {"I": "1", "II": "2", "III": "3", "IV": "4"}
_NUMERIC_TO_ROMAN = {v: k for k, v in _ROMAN_TO_NUMERIC.items()}


def normalize_stage_label(stage: str, disease: str | None = None) -> str:
    """Collapse breast cancer stage variants into a canonical display/filter value."""
    if not stage:
        return stage
    if disease != "Breast Cancer":
        return stage

    value = stage.strip()
    qualifier_match = _QUALIFIER_STAGE_RE.match(value)
    if qualifier_match:
        return f"Stage {_NUMERIC_TO_ROMAN[qualifier_match.group(1)]}"

    canonical_match = _CANONICAL_STAGE_RE.match(value)
    if canonical_match:
        roman = canonical_match.group(1).upper()
        suffix = (canonical_match.group(2) or "").upper()
        return f"Stage {roman}{suffix}"

    return value


def expand_stage_filter_values(stages: list[str], disease: str | None = None) -> list[str]:
    """Expand canonical breast cancer stages to include stored qualifier-style aliases."""
    if disease != "Breast Cancer":
        return stages

    expanded: list[str] = []
    seen: set[str] = set()
    for stage in stages:
        canonical = normalize_stage_label(stage, disease)
        candidates = [canonical]
        match = _CANONICAL_STAGE_RE.match(canonical)
        if match and not match.group(2):
            roman = match.group(1).upper()
            candidates.append(f"Stage {_ROMAN_TO_NUMERIC[roman]} (qualifier value)")
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded
