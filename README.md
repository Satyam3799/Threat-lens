# Threat Lens

SOC-oriented threat intelligence platform: JWT-authenticated Nmap scans (Celery), PostgreSQL persistence, and optional CVE/Shodan/VirusTotal enrichment.

## Stack

| Component | Role |
|-----------|------|
| FastAPI backend | REST API (`/api/*`), health (`/health`) |
| React (Vite) frontend | SPA served by `serve` |
| PostgreSQL | Scan and user data |
| Redis | Celery broker and result backend |
| Celery worker | Async Nmap scans + intel enrichment |
| Caddy (production) | HTTPS reverse proxy |

---

## Local development (Docker)

1. Copy environment template and set secrets:

   ```bash
   cp .env.example .env
   ```

2. Start the dev stack (Postgres/Redis published on host ports **5433** / **6380**):

   ```bash
   docker compose up -d --build
   ```

3. **Windows:** Nmap from inside Docker Desktop often cannot reach the public internet. Run the worker on the host instead:

   ```powershell
   .\scripts\start-worker.ps1
   ```

4. **Linux in-container worker (optional dev profile):**

   ```bash
   docker compose --profile container-worker up -d --build
   ```

5. Open the UI at `http://localhost:5173` (API at `http://localhost:8000`).

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for troubleshooting scans and queues.

---

## Production deployment (Linux VPS)

Production uses `docker-compose.prod.yml`: internal Postgres/Redis, Celery worker with Nmap, and Caddy for automatic HTTPS.

### Prerequisites

- Linux VPS (Ubuntu 22.04+ recommended) with Docker Engine and Docker Compose v2
- DNS A record pointing your hostname to the VPS public IP
- Ports **80** and **443** open on the firewall

### 1. Configure environment

On the VPS, clone the repository and create `.env` from the template:

```bash
cp .env.example .env
nano .env
```

Set at minimum:

| Variable | Example |
|----------|---------|
| `DOMAIN` | `threatlens.duckdns.org` |
| `ACME_EMAIL` | `you@example.com` |
| `VITE_API_URL` | `https://threatlens.duckdns.org` |
| `CORS_ORIGINS` | `https://threatlens.duckdns.org` |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | strong random password |
| `APP_ENV` | `production` |

`VITE_API_URL` is baked into the frontend at **build** time; it must match the public HTTPS origin (browser calls `https://your-domain/api/...` via Caddy).

### 2. DuckDNS setup (free dynamic DNS)

1. Create an account at [https://www.duckdns.org](https://www.duckdns.org).
2. Add a subdomain (e.g. `threatlens`) → note the full name `threatlens.duckdns.org`.
3. Point the DuckDNS token update URL at your VPS IP (web UI or cron on the server).
4. Set in `.env`:

   ```env
   DOMAIN=threatlens.duckdns.org
   VITE_API_URL=https://threatlens.duckdns.org
   CORS_ORIGINS=https://threatlens.duckdns.org
   ```

5. Wait for DNS to propagate, then verify:

   ```bash
   dig +short threatlens.duckdns.org
   ```

### 3. Production startup

From the repository root on the VPS:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend worker caddy
```

Verify health (replace with your domain):

```bash
curl -s https://threatlens.duckdns.org/health
curl -s https://threatlens.duckdns.org/health/queue
```

### 4. Architecture (production)

```text
Internet :443/:80
        │
     Caddy (TLS)
   ┌────┴────┐
   │         │
 /api/*    /*  → frontend:5173
   │
 backend:8000
   │
 postgres, redis (internal network only)
   │
 worker (Celery + nmap, NET_RAW/NET_ADMIN)
```

### 5. Security notes

- Postgres and Redis are **not** exposed on host ports in production.
- Use a JWT secret of at least **32** characters; production startup fails otherwise.
- Set `ALLOW_PRIVATE_SCAN_TARGETS=false` on public VPS deployments.
- Do not commit `.env` or API keys.
- OpenAPI docs (`/docs`) are disabled when `APP_ENV=production`.

### 6. Updates and maintenance

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Back up the `postgres_data` volume before major upgrades.

---

## Project layout

| Path | Purpose |
|------|---------|
| `backend/Dockerfile` | API and Celery image (includes `nmap`) |
| `frontend/Dockerfile` | Vite production build + static server |
| `docker-compose.yml` | Local development |
| `docker-compose.prod.yml` | VPS production |
| `Caddyfile` | HTTPS reverse proxy rules |
| `.env.example` | Environment template |

---

## License

See repository license file if present.
