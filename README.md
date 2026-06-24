# cust-journey

A Django web application for mapping, measuring, and prioritizing the customer journey.

## Overview

**Journey Mapping** — Model the customer lifecycle as a hierarchical tree of Phases → Journey Phases → Steps → Actions, with touchpoint tagging and drop-off tracking.

**KPI Framework** — Tie measurable indicators back to journey nodes with a three-level hierarchy (Business KPI / KPI / Metric), impact × effort prioritization, and quarterly roadmapping.

## Setup

**Prerequisites:** Python ≥ 3.12, [uv](https://docs.astral.sh/uv/)

```bash
git clone <repo-url>
cd cust_journey

cp .env.example .env
uv sync
uv run python cust_journey/manage.py migrate
uv run python cust_journey/manage.py createsuperuser
uv run python cust_journey/manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) to start mapping.

## Pages

| URL | Page |
|-----|------|
| `/` | Redirects to Journey Viewer |
| `/journey/` | **Journey Viewer** — sidebar tree of phases/steps + detail panel with linked KPIs |
| `/kpi/` | **KPI Framework** — filterable, searchable table |
| `/kpi/hierarchy/` | **KPI Hierarchy** — tree view (Business KPIs → KPIs → Metrics) |
| `/kpi/prioritize/` | **Prioritization Matrix** — drag-and-drop 4-quadrant impact × effort grid |
| `/kpi/roadmap/` | **Implementation Roadmap** — drag-and-drop quarterly columns |
| `/admin/` | Django admin |

## Prioritization Matrix

KPIs are scored on two dimensions:

| | High Impact | Low Impact |
|---|---|---|
| **Low Effort** | Quick Wins | Maybe Later |
| **High Effort** | Make Plan | Deprioritize |

Drag KPIs between quadrants to reassign scores. Drag within a quadrant to reorder. Filters persist through drag-and-drop actions.

## Tech Stack

- **Django** 6.0 — backend
- **HTMX** 2.0 — AJAX, partial page updates, no full-page reloads
- **Alpine.js** 3.14 — client-side UI state (modals, collapse, toggles)
- **Tailwind CSS** — utility-first styling (CDN, no build step)
- **SortableJS** 1.15 — drag-and-drop for prioritization and roadmap
- **SQLite** — zero-config database

No JavaScript build pipeline. No REST API. Everything returns HTML fragments.

## Project Structure

```
cust_journey/
├── pyproject.toml          # Dependencies (uv)
├── .env.example            # Environment template
└── cust_journey/
    ├── manage.py
    ├── cust_journey/       # Django project config (settings, urls)
    ├── journey/            # Customer Journey Mapping app (Phase, Step, Action, Touchpoint)
    ├── kpi/                # KPI Framework app (KPI, prioritization, roadmap)
    └── templates/          # Full pages + HTMX partials
        ├── base.html       # Layout, CDN scripts, modal container
        ├── journey/        # Journey templates + partials
        └── kpi/            # KPI templates + drag-and-drop partials
```
