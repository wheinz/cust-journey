# Customer Journey Tool — Handover Guide

This document explains what the tool does and how it's built. For step-by-step deployment instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)** — a runbook tested on Hetzner/Ubuntu 24.04.

No Django experience assumed.

---

## 1. What the tool does

### Two main features

**Customer Journey Mapping** — A visual tool to model every step a customer takes, from first contact through to leaving. The journey is organized as a hierarchy:

```
Lifecycle Phase (e.g. "1. Onboarding")
  └─ Journey Phase (e.g. "Account Setup")
      └─ Step (e.g. "Verify Email")
          ├─ Action (e.g. "Click verification link")
          └─ Touchpoint (e.g. "Email System")
```

You can mark actions as "drop-off points" to track where customers churn. Each level is clickable — clicking a node loads its detail panel on the right side of the screen.

**KPI Framework** — Tie measurable business indicators to every part of the journey. Each KPI records:
- What level it is (Business KPI → KPI → Metric)
- Who owns it
- Whether it's measured, current vs target values, where data is stored
- Impact × Effort score (for prioritization)
- Which quarter it's planned for

### Pages

| URL | What it does |
|---|---|
| `/journey/` | Sidebar tree of the customer journey + detail panel |
| `/kpi/` | Searchable, filterable table of all KPIs |
| `/kpi/hierarchy/` | Tree view: Business KPIs → KPIs → Metrics |
| `/kpi/prioritize/` | Drag-and-drop 4-quadrant prioritization grid |
| `/kpi/roadmap/` | Drag-and-drop quarterly roadmap |
| `/admin/` | Django's built-in admin panel (raw data editing) |

---

## 2. How it's built — the tech stack

The project uses four technologies. None of them require a JavaScript build step or compilation.

| Layer | Technology | What it does |
|---|---|---|
| Backend | **Django** (Python) | Handles all business logic, database queries, page rendering |
| Page updates | **HTMX** | Loads parts of the page without a full refresh (e.g. clicking a tree node loads the detail panel) |
| UI interactions | **Alpine.js** | Manages small client-side things: opening modals, toggling sections |
| Styling | **Tailwind CSS** | All styling is done via utility classes in the HTML |
| Drag-and-drop | **SortableJS** | Powers the prioritization matrix and roadmap |
| Database | **SQLite** | A single file database — no separate database server needed |

### How the tech works together

- Every interaction that needs data from the server goes through HTMX. For example, clicking a journey node sends an HTMX request to Django, which returns an HTML fragment. HTMX swaps that fragment into the detail panel.
- Alpine.js only handles things that are purely cosmetic: toggling a dropdown, opening a modal — things that don't need a round-trip to the server.
- There is **no REST API** and **no JSON endpoints**. Everything returns HTML.
- All static assets (Tailwind, HTMX, Alpine, SortableJS) are loaded from CDNs. The project itself has zero CSS or JS files.

### Project structure

```
cust_journey/
├── Dockerfile                  # Docker image definition
├── entrypoint.sh               # Container startup script (migrate + gunicorn)
├── Caddyfile                   # Caddy reverse proxy config (auto-HTTPS)
├── docker-compose.yml           # Orchestrates app + Caddy containers
├── .dockerignore               # Files excluded from Docker build
├── pyproject.toml              # Dependencies list
├── .env.example                # Environment variable template
├── backup.sh                   # Database backup script
├── cust_journey/
│   ├── manage.py               # Django command-line tool
│   ├── data/                   # Docker: database stored here (named volume)
│   ├── staticfiles/            # Django admin static files (collected on boot)
│   ├── db.sqlite3              # The database (local dev only)
│   ├── cust_journey/           # Project configuration
│   │   ├── settings.py         # All settings
│   │   ├── urls.py             # URL routing
│   │   └── wsgi.py             # Production server entry point
│   ├── journey/                # Journey mapping app
│   │   ├── models.py           # Database tables (Phase, Step, Action, etc.)
│   │   ├── views.py            # Page logic
│   │   └── urls.py             # URL routing for journey pages
│   ├── kpi/                    # KPI framework app
│   │   ├── models.py           # Database table (KPI)
│   │   ├── views.py            # Page logic
│   │   ├── urls.py             # URL routing for KPI pages
│   │   └── management/commands/import_kpis.py  # CSV import script
│   └── templates/              # All HTML templates
│       ├── base.html           # Base layout (includes all CDN scripts)
│       ├── journey/            # Journey page templates
│       └── kpi/                # KPI page templates
```

---

## 3. Technology deep-dive

### Django (backend framework)

Django is a Python web framework. Key concepts the IT team should know:

- **Model** = A database table defined in Python. `models.py` files define the structure. Running `manage.py migrate` creates/updates the actual database tables.
- **View** = A Python function or class that handles an HTTP request and returns an HTML response.
- **Template** = An HTML file with Django's template syntax (`{% %}`, `{{ }}`) for inserting data.
- **URL routing** = `urls.py` files map URL paths to views.
- **`manage.py`** = The command-line entry point. All operations go through it: `manage.py runserver`, `manage.py migrate`, etc.

### HTMX (partial page updates)

HTMX lets any HTML element make HTTP requests and swap the response into the page. Example from this project:

```html
<!-- Clicking this tree node loads the detail panel -->
<a hx-get="/journey/phase/1/"
   hx-target="#detail-panel"
   hx-swap="innerHTML">
   Onboarding
</a>
```

This means: "When clicked, GET `/journey/phase/1/`, and put the result inside the element with id `detail-panel`."

### SQLite (database)

SQLite stores the entire database as a single file (`db.sqlite3`). No server process, no connection strings, no port configuration. The file lives next to `manage.py`.

**Upsides**: Zero configuration, easy to back up (just copy the file), portable.
**Trade-off**: Only one process can write at a time. This is fine for an internal tool with a small team. If the user base grows beyond ~20 concurrent users, you'd want to switch to PostgreSQL.

---

## 4. How to host it

### 4a. Local development (on a laptop)

Prerequisites: **Python 3.12+** and **uv** (a Python package manager — similar to pip/npm).

```bash
# Install uv (one time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up
git clone <repo-url>
cd cust_journey
cp .env.example .env                    # Create your env file
uv sync                                  # Install dependencies
uv run python cust_journey/manage.py migrate          # Create database tables
uv run python cust_journey/manage.py createsuperuser  # Create admin login
uv run python cust_journey/manage.py runserver        # Start dev server
```

Open http://localhost:8000. To import existing KPI data:

```bash
uv run python cust_journey/manage.py import_kpis cust_journey/kpis_shv_new.csv
```

### 4b. Production hosting (Docker Compose)

The production stack runs in two containers orchestrated by Docker Compose:

```
Internet → Caddy (reverse proxy + auto-HTTPS) → Gunicorn (WSGI) → Django
```

**Caddy** handles all HTTPS automatically — no certificate setup, no renewal cron jobs. **Gunicorn** runs inside the app container.

#### Step-by-step production setup

**1. Get a Linux server** with Docker installed (Ubuntu 22.04+ recommended). Any VPS provider works: DigitalOcean, Hetzner, AWS EC2, or an internal server.

```bash
# Install Docker (one time, on the server)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group membership to take effect
```

**2. Clone the repository:**

```bash
git clone <repo-url> /opt/cust-journey
cd /opt/cust-journey
```

**3. Configure the environment.** Copy the template and edit the values:

```bash
cp .env.example .env
```

Edit `.env` for production:

```
DJANGO_SECRET_KEY=<generate a long random string>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
DOMAIN=your-domain.com
DB_PATH=/app/data/db.sqlite3
```

To generate a secret key: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`

> **Cloudflare users**: If your domain is behind Cloudflare's proxy, set `DOMAIN=your-domain.com` as normal. Caddy will obtain a Let's Encrypt certificate for the origin server even through the proxy. Cloudflare handles edge TLS; Caddy handles origin TLS.

**4. Start the application:**

```bash
docker compose up -d
```

That's it. The first boot runs database migrations automatically. Caddy provisions a Let's Encrypt certificate on the first HTTPS request.

**5. Create an admin user:**

```bash
docker compose exec app uv run python cust_journey/manage.py createsuperuser
```

#### The files that make this work

| File | What it does |
|---|---|
| `Dockerfile` | Builds the Python image. Uses `uv` to install dependencies, copies the project code. |
| `entrypoint.sh` | Runs on every container start: applies database migrations, collects Django admin static files, then starts Gunicorn. |
| `Caddyfile` | Single reverse-proxy rule. Caddy reads `DOMAIN` from the environment — if it's a real domain, HTTPS is auto-provisioned. |
| `docker-compose.yml` | Defines two services (`app` + `caddy`), mounts the database volume (`db_data`) and the backups directory for persistence. |
| `.dockerignore` | Excludes files from the Docker build context (virtualenvs, git, local DB, backups). |

#### How persistence works

- **Database**: stored in a Docker named volume (`db_data`), mounted at `/app/data` inside the container. Survives container rebuilds and restarts.
- **Backups**: the `./backups` directory on the host is bind-mounted into the container, so the backup script works as normal.
- **Caddy certificates**: stored in a Docker named volume (`caddy_data`), so certificates survive restarts and don't need re-issuing.

### 4c. Local development with Docker

You can also use Docker Compose for local development — no Python or uv needed on your machine:

```bash
cp .env.example .env   # defaults are already set for local dev
docker compose up -d
```

Open http://localhost:8000 (Caddy runs on port 80, proxying to the app on 8000 internally).

---

## 5. Production hardening checklist

Most items are handled automatically by the Docker setup. Before going live:

| Item | What to do | Status with Docker setup |
|---|---|---|
| **SECRET_KEY** | Change to a generated random key in `.env` | You must do this |
| **DEBUG** | Set to `False` in `.env` | You must do this |
| **HTTPS** | Set `DOMAIN` to your real domain in `.env` | Caddy handles it automatically |
| **Static files** | Collected on boot by `entrypoint.sh` | Whitenoise serves them from the app |
| **Database backup** | Schedule the backup script via cron on the host | See ops section below |
| **Database migration** | Consider PostgreSQL if >20 concurrent users | SQLite fine for small teams |

---

## 6. Day-to-day operations

All commands are run from the project directory (`/opt/cust-journey`).

| Task | Command |
|---|---|
| Start the app | `docker compose up -d` |
| Stop the app | `docker compose down` |
| Restart the app | `docker compose restart` |
| Rebuild after code changes | `docker compose up -d --build` |
| View logs (all services) | `docker compose logs` |
| View logs (app only) | `docker compose logs app` |
| Follow live logs | `docker compose logs -f` |
| Check running status | `docker compose ps` |
| Create an admin user | `docker compose exec app uv run python cust_journey/manage.py createsuperuser` |
| Import KPI data from CSV | `docker compose exec app uv run python cust_journey/manage.py import_kpis cust_journey/kpis_shv_new.csv` |
| Run a database backup | `docker compose exec app /app/backup.sh` |
| Schedule daily backups | `(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/cust-journey && docker compose exec -T app /app/backup.sh") \| crontab -` |

### Restoring from a backup

```bash
# 1. Find the backup file
ls /opt/cust-journey/backups/

# 2. Copy it into the Docker volume
docker compose cp backups/backup-YYYY-MM-DD.sqlite3 app:/app/data/db.sqlite3

# 3. Restart
docker compose restart
```

### Upgrading the application

```bash
cd /opt/cust-journey
git pull
docker compose up -d --build
```

The entrypoint runs migrations automatically — no manual steps needed.

---

## 7. The database in detail

### Tables

The database has 6 tables:

| Table | What it stores | Key fields |
|---|---|---|
| `journey_phase` | Top-level lifecycle phases | `name`, `order` |
| `journey_journeyphase` | Sub-phases within a lifecycle phase | `name`, `order`, links to `phase` |
| `journey_step` | Individual steps | `name`, `order`, links to `journey_phase` |
| `journey_action` | Atomic actions within a step | `name`, `is_drop_off` flag |
| `journey_touchpoint` | Interaction touchpoints | `name`, links to `step` |
| `kpi_kpi` | All KPIs, metrics, and business KPIs | ~30 fields covering identity, ownership, measurement, prioritization |

The KPI table uses Django's concrete inheritance: all three levels (Business KPI, KPI, Metric) live in the same table, distinguished by the `level` field.

---

## 8. Architecture decisions (for context)

| Decision | Why |
|---|---|
| SQLite over PostgreSQL | Zero setup, portable, safe with single-writer for an internal tool |
| No JS build pipeline | Removes npm/Node dependency; all assets are CDN-loaded |
| HTMX over React/Vue | Server-side rendering means simpler code, no API layer, no state sync |
| No REST API | The tool is a user-facing web app, not a data platform |
| `uv` over pip | Faster, deterministic, lockfile support |

---

## 9. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| "502 Bad Gateway" | App container crashed | `docker compose logs app` to see the error, then `docker compose restart` |
| Pages load but styling is broken | CDN blocked by firewall | Allow `cdn.tailwindcss.com`, `unpkg.com`, `cdn.jsdelivr.net` |
| "400 Bad Request" | Domain not in `ALLOWED_HOSTS` | Add domain to `.env` and `docker compose restart` |
| "DisallowedHost" in logs | Wrong/missing `ALLOWED_HOSTS` | Same as above |
| Caddy won't get certificate | Port 80/443 not reachable from internet | Check firewall: `sudo ufw allow 80/tcp && sudo ufw allow 443/tcp` |
| "Database is locked" | Another write is in progress | Normal for SQLite, resolves in milliseconds |
| Container keeps restarting | Error in entrypoint.sh | `docker compose logs app` to see the error |

---

## 10. Getting help

- **Docker Compose docs**: https://docs.docker.com/compose/
- **Caddy docs**: https://caddyserver.com/docs/
- **Django documentation**: https://docs.djangoproject.com/en/6.0/
- **HTMX documentation**: https://htmx.org/docs/
- **Gunicorn**: https://docs.gunicorn.org/

---

*Last updated: Handover meeting preparation*
