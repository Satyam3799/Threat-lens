# Threat Lens Runbook

## Docker (recommended — one command)

Copy the example env and set a strong JWT secret (optional overrides):

```powershell
copy .env.example .env
```

Start the API stack (PostgreSQL, Redis, API, frontend):

```powershell
docker compose up --build
```

**Windows:** Nmap scans do not work from a Docker worker (ports show as filtered). Open a **second terminal** and run the worker on your host:

```powershell
.\scripts\start-worker.ps1
```

Install [Nmap](https://nmap.org/download.html) on Windows and ensure `nmap` is on your PATH.

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Docker services use internal hostnames (`postgres`, `redis`). The frontend is built with `VITE_API_URL=http://localhost:8000` so the browser reaches the published API port.

## Local Services (non-Docker)

Start PostgreSQL with the database configured in `.env`.

Start Redis before running scans:

```powershell
redis-server
```

Start the FastAPI API:

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the Celery worker in a separate terminal:

```powershell
.\venv\Scripts\Activate.ps1
celery -A backend.worker.celery_app.celery_app worker --loglevel=INFO --pool=solo
```

Start the frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Health Checks

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/health/queue
```

`/health/queue` must return `ok` before scan creation will enqueue jobs.

## Security Controls

Scan APIs require JWT authentication.

Rate limits are controlled through `.env`:

```text
SCAN_CREATE_RATE_LIMIT=5/minute
AUTH_LOGIN_RATE_LIMIT=10/minute
AUTH_REGISTER_RATE_LIMIT=3/minute
DEFAULT_RATE_LIMIT=120/minute
```

Concurrency limits are also controlled through `.env`:

```text
MAX_GLOBAL_ACTIVE_SCANS=4
MAX_USER_ACTIVE_SCANS=1
```

Private target scanning should stay disabled in shared or production environments:

```text
ALLOW_PRIVATE_SCAN_TARGETS=false
```

For local development only, it can be set to `true`.

## Threat intelligence (optional)

Set API keys and feature flags in `.env`. Intel lookups never fail scans; failures return empty or null data.

```text
SHODAN_API_KEY=
VT_API_KEY=
NVD_API_KEY=
ENABLE_INTEL_ENRICHMENT=false
FULL_PORT_SCAN_ENABLED=false
INTEL_HTTP_TIMEOUT_SECONDS=12
INTEL_ENDPOINT_RATE_LIMIT=20/minute
```

When `ENABLE_INTEL_ENRICHMENT=true`, completed scans persist CVE/Shodan/VirusTotal enrichment under `open_ports_enriched`. Intel HTTP routes (`/api/intel/*`, `GET /api/scan/{id}/enriched`) use per-user JWT rate limiting (`INTEL_ENDPOINT_RATE_LIMIT`).

## Architecture Notes

The API creates authenticated queued scan records and publishes Celery jobs to Redis.

The Celery worker owns Nmap execution and updates the PostgreSQL scan lifecycle:

`queued -> running -> completed`

or:

`queued -> running -> failed`

Nmap is executed with an argument array and `shell=False`; targets are normalized and validated before queueing.
