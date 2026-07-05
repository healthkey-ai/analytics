# Contributing to PRism

Thank you for your interest in contributing. This document covers how to set up your development environment, run tests, and submit changes.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (or a PROMOP-compatible instance)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # then fill in DATABASE_URL
python manage.py runserver
```

Tests:
```bash
cd backend
pytest --ds=analytics_project.test_settings -q
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Tests:
```bash
cd frontend
npm test -- --run
```

## Branch Workflow

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes, adding tests for any new logic.
3. Run both test suites before opening a PR — the CI will catch failures, but it's faster to fix locally.
4. Open a pull request against `main`. Include a brief description of the change and link any relevant issues.

## Code Conventions

- **Backend**: Follow existing patterns in `backend/metrics/services/`. New analytics services accept a queryset and return a plain Python dict. Never call `PatientInfo.objects.all()` inside a service — accept the queryset from the view layer.
- **Shared clinical Q objects**: Import `HIGH_RISK_CYTO`, `HAS_SCT`, `NO_SCT` from `metrics.services.clinical_filters` — never redefine them inline.
- **KM estimator**: Use `km_result` from `metrics.services.km_utils` — never reimplement.
- **Frontend**: New chart components use `NonNullable<MetricsResponse['field']>` for props and wrap `mergeKMCurves` in `useMemo`.
- **Tests**: Every new feature needs tests before the PR is merged. Use the `_FakeQS` mock pattern for backend service tests.

## Clinical Correctness

When working with cytogenetics subgroups, always exclude patients with no cytogenetics workup before splitting into risk groups. Patients with `cytogenic_markers` null or empty are unevaluable — they must not fall into "Standard Risk".

## Commit Messages

Use the imperative mood in the subject line (`Add KM confidence bands`, not `Added KM confidence bands`). Keep the subject under 72 characters.

## Reporting Bugs

Open a GitHub issue with:
- Steps to reproduce
- Expected vs. actual behaviour
- Browser/OS/Python version if relevant

## Security Issues

Please do not report security vulnerabilities in public GitHub issues. Email `security@healthkey.ai` instead.
