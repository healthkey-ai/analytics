# Prism

[![Tests](https://github.com/healthkey-ai/prism/actions/workflows/test.yml/badge.svg)](https://github.com/healthkey-ai/prism/actions/workflows/test.yml)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.XXXXX/status.svg)](https://doi.org/10.21105/joss.XXXXX)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Real-world evidence analytics for oncology patient cohorts, built on top of [PROMOP](https://github.com/healthkey-ai/promop) (OMOP CDM 5.4).

## Overview

Select a patient cohort using 20+ clinical criteria, then instantly explore outcomes across response rates, treatment patterns, demographics, disease staging, lab values, and more — all derived from structured real-world data in a PostgreSQL OMOP CDM database.

## Features

### Cohort Builder
Filter patients by:
- Disease (Multiple Myeloma, Breast Cancer, Follicular Lymphoma)
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
| Database | PostgreSQL (OMOP CDM 5.4) via PROMOP |
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
└── seed_mm_patients.py         # Seeds 100 realistic MM patients into PROMOP
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

The recommended way to populate a PROMOP database with synthetic oncology patients is via PROMOP's built-in FHIR pipeline. See the [PROMOP quickstart guide](https://github.com/healthkey-ai/promop/blob/dev/docs/quickstart.md) for full instructions. In short:

```bash
# Generate a synthetic FHIR bundle
python manage.py generate_fhir_bundle --patients 100 --disease MM

# Import the bundle into the PROMOP database
python manage.py import_fhir_bundle bundle.json
```

Alternatively, the repository includes a standalone seed script for 100 Multiple Myeloma patients with clinically plausible treatment histories and outcome distributions drawn from published trial data (GRIFFIN, MAIA, KarMMa, CARTITUDE-1, DREAMM-2, etc.), risk-adjusted for high-risk cytogenetics:

```bash
DATABASE_URL="postgresql://..." python seed_mm_patients.py
```

## Deploying to Render

**Root Directory:** `backend`

**Build Command:**
```
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```
gunicorn analytics_project.wsgi:application --bind 0.0.0.0:$PORT
```

**Environment variables:**
| Variable | Value |
|---|---|
| `DEBUG` | `false` |
| `SECRET_KEY` | *(generate a random secret)* |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend.onrender.com` |

## Database

The backend connects to a PROMOP PostgreSQL instance and reads from the `patient_info` denormalized view via an unmanaged Django model. Connection settings live in `backend/analytics_project/settings.py`.

## Citing Prism

If you use Prism in research, please cite:

> Blum, A. (2026). Prism: An Open-Source Real-World Evidence Analytics Platform for Oncology Patient Cohorts. *Journal of Open Source Software*. https://doi.org/10.21105/joss.XXXXX
