# Changelog

All notable changes to the analytics platform are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned

- **OHDSI Atlas cohort export** — export a saved PRism cohort as an Atlas-compatible Circe JSON definition via `GET /api/cohorts/saved/{id}/export/atlas/`. Enables cohorts defined in PRism's point-and-click UI to be executed in OHDSI tools (PatientLevelPrediction, CohortMethod). Requires a concept mapping layer from PROMOP field values to OMOP vocabulary concept IDs.

---

## [1.0.0] — 2026-07-04

### Summary

Initial tagged release submitted to the Journal of Open Source Software (JOSS).

### Features included in this release

- **Cohort Builder** — 20+ clinical filter dimensions (disease, ISS stage, ECOG, cytogenetics, lines of therapy, regimens, refractory status, MM-specific criteria, lab ranges, diagnosis year) composing via a single `apply_cohort_filters` function.
- **KM Survival Analysis** — Overall Survival (OS), Progression-Free Survival (PFS), and Event-Free Survival (EFS) with 95% Greenwood confidence bands and log-rank p-values via SciPy.
- **Subgroup Survival** — OS/PFS Kaplan-Meier stratified by ISS stage, cytogenetic risk group (High Risk / Standard Risk), SCT status, and MRD status, with landmark survival tables at 6/12/24/36 months.
- **Time to Next Treatment (TTNT)** — KM curves for line 1→2 and line 2→3 transitions.
- **Duration of Response (DOR)** — KM chart for confirmed responders (CR/sCR/VGPR/PR/MR) per IMWG criteria in 1st- and 2nd-line therapy.
- **Treatment Analytics** — Response rate stacked bar charts (CR/VGPR/PR/MR/SD/PD), treatment switching Sankey diagrams, top treatment sequence paths, and treatment duration box plots.
- **Demographics and Staging** — ISS stage, ECOG, cytogenetic marker prevalence, CRAB criteria, age buckets, gender, race, and geographic distribution panels. Laboratory value box plots for nine key analytes.
- **Authentication and Org-Scoped Access** — Email/password login; organization-based data scoping; role-based access control.
- **Saved Cohorts and Export** — Save, load, update, and delete named cohort filter sets (max 10 per user); patient-level CSV/JSON export with PII fields excluded and per-user ownership enforced.
- **Backend test suite** — ~2,400 lines across 19 pytest files covering KM correctness, log-rank p-values, cohort filter composition, org-scoped queryset logic, and authentication flows.
- **Deployment** — Single-command deploy to Render (backend + frontend static); GitHub Actions CI on every push.

---

## 2026-06-08 — KM Enhancements (PR #9)

### Added
- **MRD survival split** — Kaplan-Meier OS/PFS stratified by MRD status in the Subgroup Survival panel. Groups with fewer than 5 patients are suppressed; at most 10 groups shown.
- **95% confidence bands** — Greenwood formula CI bands (dashed, low opacity) on all KM charts: OS/PFS/EFS overview, subgroup survival, and duration of response.
- **Log-rank p-values** — Generalized K-group log-rank test (scipy) displayed as a badge on every subgroup stratification (stage, cytogenetics, SCT, MRD). Returns `null` when fewer than 2 groups are present.
- **Duration of Response (DOR)** — New KM chart for responders (CR/sCR/VGPR/PR/MR) in 1st- and 2nd-line therapy. Event = next treatment start or death; censored at last treatment.
- **Landmark survival table** — Survival probability at 6/12/24/36 months per subgroup, shown below each stratified KM chart. Displays `—` when follow-up is insufficient to reach a landmark.

### Changed
- **Metrics endpoint now requires authentication** — `GET /api/metrics/` returns 403 for unauthenticated callers. The frontend reloads automatically on 401/403 to show the login page.
- **DOR responder definition uses IMWG allowlist** — Only CR, sCR, VGPR, PR, MR count as responders (previously used a PD/SD denylist that would admit unrecognized outcome strings).

### Fixed
- `DurationOfResponse` component crash when backend returns a null line (null guard moved inside `useMemo`).
- `LandmarkTable` previously showed `100.0%` for groups whose maximum follow-up didn't reach a given landmark; now shows `—`.
- `numpy` added as an explicit dependency in `requirements.txt` (was only transitive via scipy).
- `numpy` / `scipy` imports moved to module top level in `km_utils.py`.
- Dead `_subgroup_km` function removed from `subgroup_survival.py`.

### Tests
- 47 backend unit tests covering KM curve correctness, log-rank p-values, MRD subgroup splitting, and DOR responder logic.

---

## 2026-06-06 — Saved Cohorts, Auth & Export (PR #5)

### Added
- **User authentication** — Email/password login and signup backed by the shared `identity` table. Session cookie shared with promop via `SESSION_COOKIE_DOMAIN=.healthkey.ai` and the same `SECRET_KEY`, enabling SSO between the two apps.
- **Saved cohorts** — Authenticated users can save, name, load, update, and delete cohort filter sets. Maximum 10 cohorts per user.
- **CSV/JSON export** — Download patient-level data (all fields except PII) from any saved cohort via `GET /api/cohorts/saved/{id}/export/?format=csv|json`.
- **Cohort dirty tracking** — The UI indicates when a loaded saved cohort has been modified but not re-saved.

### Security
- Export endpoint enforces per-user ownership; users cannot export other users' cohorts.
- Export cardinality limit: filter arrays capped at 10 items to prevent abuse.
- PII fields (`email`, `phone_number`, `date_of_birth`, `postal_code`, `city`, `facility_name`, `person_id`, `organization_id`) excluded from all exports.

---

## 2026-06-03 — TTNT, Switching & Subgroup Survival (PRs #6, #7)

### Added
- **Time to Next Treatment (TTNT)** — KM curves for line 1→2 and line 2→3 transitions.
- **Treatment switching** — Sankey-style breakdown of regimen transitions from 1L and 2L.
- **Subgroup Survival** — OS/PFS KM stratified by ISS stage, cytogenetic risk, and SCT status.
- **MRD status filter** in the cohort panel.
- Race distribution in Patient Demographics.

---

## Earlier

See git log for changes prior to the structured changelog.
