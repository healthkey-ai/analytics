# Analytics Platform

Real-world evidence analytics for oncology patient cohorts, built on top of [CTOMOP](https://github.com/healthkey-ai/ctomop) (OMOP CDM v6.0).

## Overview

Select a patient cohort using 20+ clinical criteria, then instantly explore outcomes across response rates, treatment patterns, demographics, disease staging, lab values, and more — all derived from structured real-world data in a PostgreSQL OMOP CDM database.

## Features

### Cohort Builder
Filter patients by:
- Disease (Multiple Myeloma, Breast Cancer)
- ISS stage, ECOG performance status
- Age range, gender, ethnicity, geographic region
- Cytogenetic markers (del17p, t(4;14), t(14;16), high-risk flag, TP53 disruption)
- Lines of therapy (min/max), 1L/2L/3L+ regimen and outcome
- Refractory status
- MM-specific: CRAB criteria, bone lesions, prior ASCT, plasma cell leukemia
- Lab ranges: hemoglobin, β2-microglobulin, albumin, creatinine
- Diagnosis year range, smoking status

### Dashboard Panels
- **Response Rates** — stacked bar by therapy and outcome (CR/VGPR/PR/MR/SD/PD), switchable across 1L/2L/3L+, with chart/table toggle and ORR%
- **Treatment Patterns** — 1st-line regimen frequency
- **Lines of Therapy** — funnel (% reaching each line) + distribution donut
- **Patient Demographics** — age buckets, gender donut, ethnicity and geographic distribution
- **Disease Staging** — ISS stage donut, ECOG bar, cytogenetic markers (high-risk highlighted), CRAB criteria, bone lesions, ASCT rate
- **Laboratory Values** — box plots (median/IQR/range) for 9 key lab values
- **Treatment Duration** — median months by therapy+outcome (top 15), time-to-first-treatment distribution
- **Top Treatment Sequences** — most common multi-line therapy paths (e.g. VRd → Daratumumab → Cilta-cel)

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL (OMOP CDM v6.0) via CTOMOP |
| Frontend | React 19 + TypeScript + Vite |
| Styling | Tailwind CSS v4 |
| Charts | Recharts |

## Project Structure

```
analytics/
├── backend/                    # Django + DRF API
│   ├── analytics_project/      # Django project settings and URLs
│   ├── patients/               # Unmanaged PatientInfo model (reads patient_info view)
│   ├── cohorts/                # Cohort filter logic and form settings endpoint
│   └── metrics/                # Analytics computation services
│       └── services/
│           ├── response_rates.py
│           ├── treatment_patterns.py
│           ├── demographics.py
│           ├── staging.py
│           ├── labs.py
│           └── treatment_duration.py
├── frontend/                   # React SPA
│   └── src/
│       ├── components/
│       │   ├── CohortPanel/    # Dark sidebar with collapsible filter sections
│       │   ├── Dashboard/      # Main layout with sticky header
│       │   ├── charts/         # One component per dashboard panel
│       │   └── ui/             # MetricCard wrapper
│       ├── hooks/
│       │   └── useAnalytics.ts # State management + 400ms debounced API calls
│       ├── api/client.ts       # Axios client + filter serialization
│       └── types/index.ts      # Shared TypeScript interfaces
└── seed_mm_patients.py         # Seeds 100 realistic MM patients into CTOMOP
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`.

Key endpoints:
- `GET /api/form-settings/?disease=Multiple+Myeloma` — returns therapy lists, staging options, etc. for the cohort builder
- `GET /api/metrics/?disease=Multiple+Myeloma&[filters...]` — returns all dashboard metrics for the current cohort

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:5173/`. API requests to `/api/*` are proxied to the Django backend at `http://localhost:8000`.

### Seeding Sample Data

To populate 100 realistic Multiple Myeloma patients with clinically plausible treatment histories and outcome distributions:

```bash
python seed_mm_patients.py
```

Outcome probabilities are drawn from published trial data (GRIFFIN, MAIA, KarMMa, CARTITUDE-1, DREAMM-2, etc.) and risk-adjusted for high-risk cytogenetics.

## Database

The backend connects to a CTOMOP PostgreSQL instance and reads from the `patient_info` denormalized view via an unmanaged Django model. Connection settings live in `backend/analytics_project/settings.py`.
