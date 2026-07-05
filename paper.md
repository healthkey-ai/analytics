---
title: 'Prism: An Open-Source Real-World Evidence Analytics Platform for Oncology Patient Cohorts'
tags:
  - Python
  - Django
  - React
  - oncology
  - real-world evidence
  - OMOP CDM
  - survival analysis
  - Kaplan-Meier
authors:
  - name: Adam Blum
    orcid: 0009-0009-4985-7615
    affiliation: 1
affiliations:
  - name: HealthKey AI
    index: 1
date: 4 July 2026
bibliography: paper.bib
---

# Summary

Prism is an open-source web application for interactive real-world evidence (RWE) analytics on oncology patient cohorts. It connects to a PostgreSQL database following the PROMOP schema—an oncology-focused extension of the Observational Medical Outcomes Partnership (OMOP) Common Data Model (CDM) v5.4 [@garza2020]—and provides a point-and-click cohort builder paired with a suite of survival, treatment pattern, and demographic analytics. Analytical computations run server-side in Python, delivering pre-aggregated JSON to a React/TypeScript frontend optimized for clinical researchers without programming experience.

Built on Django 5 and Django REST Framework, Prism exposes a REST API that accepts cohort filter parameters and returns metrics computed against the live patient dataset. A debounced frontend ensures analytics update within milliseconds of each filter change without overwhelming the backend.

# Statement of Need

Real-world evidence derived from electronic health records and registries is increasingly used to inform drug development, regulatory submissions, and clinical practice guidelines [@sherman2016; @blonde2022]. However, generating RWE analyses typically requires either custom programming expertise or access to expensive commercial platforms. Oncology researchers working with institutional registries often lack both.

Existing open-source OMOP analytics tools such as ATLAS [@hripcsak2015] focus primarily on observational study design and population-level cohort characterization. Prism complements these tools by providing a purpose-built analytics layer for oncology RWE, with disease-specific survival analyses, treatment sequence visualization, and subgroup stratification designed for clinical investigators rather than data engineers.

Prism is self-hostable, requires no proprietary software, and exposes a documented REST API, enabling institutions to deploy it against their own OMOP-structured registry data.

# Features

**Cohort Builder.** A collapsible sidebar presents 20+ clinical filter dimensions: disease, ISS stage, ECOG performance status, cytogenetic markers (del17p, t(4;14), t(14;16), TP53 disruption), lines of therapy, regimen and outcome at each line, refractory status, MM-specific criteria (CRAB, bone lesions, ASCT history, plasma cell leukemia), lab value ranges (hemoglobin, β2-microglobulin, albumin, creatinine), and diagnosis year. Filters compose via SQL `WHERE` clauses through a single `apply_cohort_filters` function, making the logic easy to audit and extend.

**Survival Analysis.** Kaplan-Meier estimators [@kaplan1958] compute overall survival (OS), progression-free survival (PFS), and event-free survival (EFS) from first-line treatment start to death or censoring. All curves include 95% confidence bands via the Greenwood formula [@greenwood1926] and log-rank p-values [@mantel1966] via SciPy [@virtanen2020]. Subgroup stratification by ISS stage, cytogenetic risk group, SCT status, and MRD status produces stratified KM panels with landmark survival tables at 6, 12, 24, and 36 months.

**Treatment Analytics.** Response rate stacked bar charts display CR/VGPR/PR/MR/SD/PD distributions by therapy and line. Treatment switching Sankey diagrams visualize regimen transitions across lines. Time to Next Treatment (TTNT) KM curves quantify transition kinetics between lines 1→2 and 2→3. Duration of Response (DOR) charts apply to confirmed responders (CR/sCR/VGPR/PR/MR) per IMWG criteria.

**Demographics and Staging.** Panels present ISS stage distribution, ECOG bar chart, cytogenetic marker prevalence (high-risk highlighted), CRAB criteria rates, age buckets, gender, race, and geographic distribution. Laboratory value box plots (median, IQR, range) cover nine key analytes.

**Access Control and Export.** Role-based access control scopes each user's view to their organization's data. Authenticated users can save, load, and share named cohort filter sets. Patient-level CSV/JSON export omits PII fields and enforces per-user cohort ownership.

# Testing

The backend test suite (pytest, ~2,400 lines across 18 files) covers KM curve correctness, log-rank p-value computation, cohort filter composition, org-scoped queryset logic, and authentication flows. A `_FakeQS` mock pattern allows service functions to be tested without a live database. Frontend component tests use Vitest. Both suites are run via GitHub Actions on every push.

# Availability

Prism is available at [https://github.com/healthkey-ai/prism](https://github.com/healthkey-ai/prism) under the Apache 2.0 license. A live demonstration instance running on synthetic data from fictional oncology foundations is available at [https://prism-dev.onrender.com](https://prism-dev.onrender.com). Installation instructions and deployment guides are provided in the repository README.

# Acknowledgements

Prism builds on the OMOP Common Data Model v5.4 as implemented in PROMOP [@promop]. Survival analysis uses the SciPy scientific computing library [@virtanen2020]. Outcome probability distributions used for synthetic data generation were drawn from published clinical trial reports including GRIFFIN, MAIA, KarMMa, CARTITUDE-1, and DREAMM-2.

# References
