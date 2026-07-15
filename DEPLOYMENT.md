# Deployment Runbook

Step-by-step guide tested on Hetzner (Ubuntu 24.04). Adapt paths and domains as needed.

## 1. Prerequisites

On the target server:

```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
docker compose version
```

The server needs ports **80** (HTTP) and **443** (HTTPS) open to the internet. If using a firewall:

```bash
ufw allow 80/tcp
ufw allow 443/tcp
```

## 2. Deploy

```bash
# Clone into /opt (or wherever you prefer)
git clone https://github.com/wheinz/cust-journey.git /opt/cust-journey
cd /opt/cust-journey
```

### 2a. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`. Two scenarios:

**IP-only (no domain):**

```env
DJANGO_SECRET_KEY=<output of: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=91.99.170.239
DJANGO_CSRF_TRUSTED_ORIGINS=http://91.99.170.239
DOMAIN=:80
DB_PATH=/app/data/db.sqlite3
```

**With a domain (HTTPS auto-provisioned by Caddy):**

```env
DJANGO_SECRET_KEY=<output of: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
DOMAIN=your-domain.com
DB_PATH=/app/data/db.sqlite3
```

> **Note on Cloudflare**: If your domain uses Cloudflare's proxy (orange cloud), Cloudflare handles HTTPS at the edge. In that case point the DNS A record at the server IP, set `DOMAIN=your-domain.com` in `.env`, and Caddy will still get a Let's Encrypt cert for the origin. If you prefer Cloudflare-only TLS with no origin cert, use the IP-only config above with a Cloudflare DNS A record pointed at the server.

### 2b. Start

```bash
docker compose up -d
```

The first boot runs database migrations and collects static files automatically. Wait ~20 seconds, then verify:

```bash
docker compose ps
# Both app-1 and caddy-1 should show "Up"
```

### 2c. Create an admin user

```bash
docker compose exec app uv run python cust_journey/manage.py createsuperuser
```

Or set a password on an existing user:

```bash
docker compose exec app uv run python cust_journey/manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='admin')
u.set_password('your-password')
u.save()
"
```

## 3. `.env` reference

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Random 50-char string | Generate with `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | Yes | `False` | Must be `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Yes | `example.com,1.2.3.4` | Comma-separated, no spaces |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Yes | `https://example.com` | Comma-separated, full URL with scheme |
| `DOMAIN` | Yes | `example.com` or `:80` | Caddy uses this to provision TLS. Use `:80` for plain HTTP (no domain or IP-only) |
| `DB_PATH` | Yes | `/app/data/db.sqlite3` | Where SQLite lives inside the container. Mounted to `db_data` volume |

## 4. Migrate an existing database

If you have a `db.sqlite3` from a previous deployment:

```bash
# Copy it into the running container's volume
docker compose cp /path/to/old/db.sqlite3 app:/app/data/db.sqlite3

# Restart the app (entrypoint runs migrate automatically)
docker compose restart app

# Verify
docker compose logs app --tail 10
```

## 5. Upgrading the application

```bash
cd /opt/cust-journey
git pull
docker compose up -d --build
```

The entrypoint runs `migrate` and `collectstatic` on every boot, so no manual steps needed.

## 6. Day-to-day operations

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Restart | `docker compose restart` |
| Rebuild + restart | `docker compose up -d --build` |
| View logs | `docker compose logs app` |
| Follow logs | `docker compose logs -f app` |
| Check status | `docker compose ps` |
| Run a Django command | `docker compose exec app uv run python cust_journey/manage.py <command>` |
| Import KPI CSV | `docker compose exec app uv run python cust_journey/manage.py import_kpis cust_journey/kpis_shv_new.csv` |

### Backups

```bash
# Manual backup
docker compose exec app /app/backup.sh

# Schedule daily at 2am via cron on the host
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/cust-journey && docker compose exec -T app /app/backup.sh") | crontab -
```

Backups land in `./backups/` on the host (bind-mounted into the container) and are auto-pruned after 7 days.

### Restore from backup

```bash
docker compose cp backups/backup-YYYY-MM-DD.sqlite3 app:/app/data/db.sqlite3
docker compose restart app
```

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| `docker compose up` fails | `docker compose logs app` — common cause: missing or malformed `.env` |
| `ModuleNotFoundError: No module named 'cust_journey.wsgi'` | `entrypoint.sh` must export `PYTHONPATH=/app/cust_journey` before gunicorn |
| "400 Bad Request" | Domain/IP not in `DJANGO_ALLOWED_HOSTS` in `.env`. Restart after editing. |
| Caddy won't get a certificate | Port 80 must be reachable from the internet. Check firewall and DNS. |
| Caddy won't start | If `DOMAIN=` is empty or invalid, Caddy may fail. Use `DOMAIN=:80` for IP-only setups. |
| "Database is locked" | Normal SQLite behavior under concurrent writes. Resolves in milliseconds. |
| Users created but can't log in | Passwords are hashed. If you copied a DB, the hashes are valid. Use `set_password()` if needed. |

## 8. Architecture

```
Port 80/443
    │
    ▼
┌──────────────┐      ┌──────────────────┐
│   Caddy      │ ───► │  Django/Gunicorn │
│  (reverse    │      │   (port 8000,    │
│   proxy,     │      │   internal only) │
│   auto-TLS)  │      │                  │
└──────────────┘      └────────┬─────────┘
                               │
                        ┌──────▼──────┐
                        │   SQLite    │
                        │  (Docker    │
                        │   volume:   │
                        │   db_data)  │
                        └─────────────┘
```

Persistent data lives in two places:
- **`db_data` volume** — the SQLite database (`/app/data/db.sqlite3` inside the container)
- **`caddy_data` volume** — TLS certificates (survive container rebuilds)
- **`./backups/` on host** — database backups (bind-mounted into the container)
