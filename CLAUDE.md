# CLAUDE.md — LLM Instructions for PRism

This file tells LLMs (Claude, Copilot, etc.) how to work on this codebase consistently.

---

## Model Selection

**Sonnet** is the default for day-to-day work:
- Bug fixes and small enhancements
- New dashboard metrics following established patterns
- Frontend component changes
- Test additions and updates
- Documentation updates

**Opus** for work that requires broad codebase knowledge:
- Architecture changes (new service layers, data model changes, API design)
- Broad refactors touching many files across the codebase
- Bugs or investigations that require understanding the full system to diagnose
- Any change where getting the context wrong across files would cause a correctness problem

Switch with `/model claude-opus-4-8` or toggle `/fast`.

---

## Project Overview

**PRism** is a read-only oncology analytics platform that:
- Mirrors clinical patient records into a PostgreSQL read model (`PatientInfo`, `managed=False`)
- Exposes a DRF REST API consumed by a React TypeScript frontend
- Computes survival curves (KM), treatment patterns, TTNT, and subgroup statistics
- Deploys to Render (backend + frontend static)

**Key tech:**
- Backend: Django 5.x, Django REST Framework, PostgreSQL, pytest
- Frontend: React 19, TypeScript, Tailwind CSS, Recharts
- No Django migrations (read-only mirror tables with `managed=False`)

---

## Stack File Map

| Concern | File(s) |
|---|---|
| Read model | `backend/patients/models.py` — `PatientInfo` (`managed=False`) |
| Cohort filtering | `backend/cohorts/filters.py` — `apply_cohort_filters` |
| Shared clinical Q objects | `backend/metrics/services/clinical_filters.py` — `HIGH_RISK_CYTO`, `HAS_SCT`, `NO_SCT` |
| KM estimator | `backend/metrics/services/km_utils.py` — `km_curve`, `km_median`, `km_result` |
| Survival services | `backend/metrics/services/survival.py` — `os_km`, `pfs_km`, `efs_km` |
| Subgroup survival | `backend/metrics/services/subgroup_survival.py` — stratified KM by stage/cyto/SCT |
| TTNT service | `backend/metrics/services/ttnt.py` |
| Treatment switching | `backend/metrics/services/switching.py` |
| Staging/aggregates | `backend/metrics/services/staging.py` |
| Metrics API view | `backend/metrics/views.py` — `metrics()` endpoint |
| Cohort API | `backend/cohorts/views.py`, `backend/cohorts/saved_views.py` |
| Auth | `backend/accounts/` — Identity model, JWT views |
| TypeScript types | `frontend/src/types/index.ts` — `MetricsResponse`, `SurvivalLine`, etc. |
| KM chart utility | `frontend/src/utils/kmChartUtils.ts` — `mergeKMCurves` |
| Chart components | `frontend/src/components/charts/` |
| Dashboard | `frontend/src/components/Dashboard/index.tsx` |
| API client | `frontend/src/api/client.ts` |
| Backend tests | `backend/metrics/tests/`, `backend/accounts/tests/`, `backend/cohorts/tests/` |
| Frontend tests | `frontend/src/components/**/__tests__/*.test.tsx` |

---

## Rule: Tests for Every New Feature

**Every new feature must have tests written and run before the work is considered complete.**

- Write tests immediately after implementing the feature — not as a follow-up.
- The feature is not done until the tests pass.
- Run both suites before every push.

### Backend Tests (pytest)

Tests live alongside the service they test in `backend/metrics/tests/`, `backend/cohorts/tests/`, etc.

Use the `_FakeQS` mock pattern for service functions that accept a queryset — avoids a live DB:

```python
class _FakeQS:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args, **kwargs):    # must accept Q objects as positional args
        return self

    def exclude(self, *args, **kwargs):  # same
        return self

    def values_list(self, *fields, flat=False):
        if flat:
            return [r[fields[0]] for r in self._rows]
        return [tuple(r[f] for f in fields) for r in self._rows]

    def values(self, *fields):
        return [{f: r[f] for f in fields} for r in self._rows]

    def distinct(self):
        return self

    def order_by(self, *args):
        return self
```

What to test for a new service function:
- Happy path: correct input → expected KM/aggregate output
- Empty queryset → graceful empty result (no crash)
- Single-patient edge cases
- Clinical correctness of any subgroup splits (e.g., patients with no cytogenetics data must not land in "Standard Risk")

### Running Tests

```bash
# Backend — run from backend/ directory
cd backend
pytest --ds=analytics_project.test_settings -q

# Frontend — run from frontend/ directory
cd frontend && npm test -- --run
```

### Run Tests Before Every Push

**Always run both test suites before pushing to any branch.** Do not push if any test is failing.

```bash
# One-liner from repo root:
cd backend && pytest --ds=analytics_project.test_settings -q \
  && cd ../frontend && npm test -- --run
```

---

## Rule: DRY — Shared Utilities Must Be Used

### Backend: Clinical Q Objects

`HIGH_RISK_CYTO`, `HAS_SCT`, and `NO_SCT` are defined **once** in `backend/metrics/services/clinical_filters.py`. Import from there — never redefine inline:

```python
from metrics.services.clinical_filters import HIGH_RISK_CYTO, HAS_SCT, NO_SCT
```

### Backend: KM Estimator

`km_curve`, `km_median`, `km_result` live in `backend/metrics/services/km_utils.py`. Import from there — never reimplement:

```python
from metrics.services.km_utils import km_curve, km_median, km_result
```

### Frontend: KM Chart Data

`mergeKMCurves` lives in `frontend/src/utils/kmChartUtils.ts`. Import from there — never copy-paste into chart components:

```typescript
import { mergeKMCurves } from '../../utils/kmChartUtils'
```

---

## Rule: Adding a New Analytics Metric

When adding a new metric to the dashboard, touch **all** layers:

### 1. Backend Service (`backend/metrics/services/`)

Create a new file or add to an existing one. Use `km_result` from `km_utils` for KM-based metrics. Import shared Q objects from `clinical_filters`.

### 2. Backend View (`backend/metrics/views.py`)

Import and call the new service inside the `metrics()` view, add the result to the response dict.

### 3. TypeScript Types (`frontend/src/types/index.ts`)

Add the new field as **optional** (`?`) to `MetricsResponse`. Use `NonNullable<MetricsResponse['field_name']>` in the chart component's Props type so the component receives the non-optional form.

### 4. Chart Component (`frontend/src/components/charts/`)

Create a new chart component. For KM curves, use `mergeKMCurves` and wrap expensive `chartData` computation in `useMemo`. Use `type MyData = NonNullable<MetricsResponse['my_field']>` for the Props interface.

### 5. Dashboard (`frontend/src/components/Dashboard/index.tsx`)

Import the new chart component, add a `<MetricCard>` wrapping it. Pass the relevant slice of `metrics` data.

### 6. Tests

Backend: add tests in `backend/metrics/tests/test_<feature>.py` using `_FakeQS`.
Frontend: add tests in `frontend/src/components/charts/__tests__/<Feature>.test.tsx` if non-trivial logic exists.

---

## Clinical Correctness Rules

These prevent silent data errors that look like valid results:

**Cytogenetics subgroups**: Always exclude patients with no cytogenetics workup before splitting into High/Standard Risk. Patients with `cytogenic_markers` null or empty are unevaluable — they must NOT fall into Standard Risk.

```python
tested = qs.exclude(cytogenic_markers__isnull=True).exclude(cytogenic_markers="")
high_risk = tested.filter(HIGH_RISK_CYTO)
standard_risk = tested.exclude(HIGH_RISK_CYTO)
```

**KM time bucketing**: Round event times to 1 decimal place (`round(t, 1)`) **before** using as a bucket key. Float arithmetic on `days / 30.44` otherwise produces distinct keys for times that should merge, causing duplicate time points in the output curve.

**KM at_risk convention**: `at_risk` in each output point records the count **before** events at that time step, per KM convention. The `at_risk > 0` guard prevents division by zero.

---

## Frontend Patterns

**Optional API fields**: When a `MetricsResponse` field is optional (`?`), components must not accept `T | undefined` in their props. Use `NonNullable<>` at the boundary:

```typescript
type TTNTData = NonNullable<MetricsResponse['ttnt']>
interface Props { data: TTNTData }
```

**KM chart data**: Always wrap `mergeKMCurves(...)` in `useMemo` when the result is used in render — it touches every data point on every render otherwise:

```typescript
const chartData = useMemo(
  () => mergeKMCurves(lines.map((l, i) => ({ key: `g${i}`, curve: l.curve }))),
  [lines]
)
```

**Dynamic subgroup keys**: Use `g0`, `g1`, ... keys for subgroups with a dynamic count. Resolve back to human-readable labels in the Recharts `Tooltip` formatter via `lines[idx]?.label`.

---

## DB / Model Conventions

- `PatientInfo` uses `managed=False` — there are no Django migrations for it. Schema changes are applied directly to the database.
- Service functions receive a queryset (`qs`) and apply `.filter()` / `.exclude()` / `.values_list()` / `.values()` against it. Never do `PatientInfo.objects.all()` inside a service — accept the queryset from the view layer so cohort filters compose correctly.
- The `patient_info` table is a read-only mirror. Never write to it from the analytics app.

---

## Deployment

- Backend and frontend static files deploy to Render.
- `start.sh` runs on every deploy.
- `DEBUG=false` in production — `SSL` is required when `DATABASE_URL` points to a non-localhost host.
- `frontend/dist/` is in `.gitignore` — build artifacts are not committed.
