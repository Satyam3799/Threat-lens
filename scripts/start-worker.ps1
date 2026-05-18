# Run Celery worker on the HOST (required for Nmap on Windows Docker Desktop).
# Docker's worker container often cannot reach external targets (all ports show filtered).
#
# Prerequisites:
#   docker compose up -d
#   .\venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   nmap installed on Windows PATH

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-Path "$Root\.env") {
    Get-Content "$Root\.env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

# Match docker-compose postgres/redis published ports (not in-container hostnames).
$pgUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { 'postgres' }
$pgPass = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { 'postgres' }
$pgDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { 'threat_lens' }
$pgHostPort = if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { '5433' }
$env:DATABASE_URL = "postgresql+psycopg2://${pgUser}:${pgPass}@localhost:${pgHostPort}/${pgDb}"
$redisPort = if ($env:REDIS_PORT) { $env:REDIS_PORT } else { '6380' }
$env:REDIS_URL = "redis://localhost:${redisPort}/0"
$env:CELERY_BROKER_URL = $env:REDIS_URL
$env:CELERY_RESULT_BACKEND = "redis://localhost:${redisPort}/1"
$env:POSTGRES_SSLMODE = 'disable'
$env:PYTHONPATH = $Root
$env:ENABLE_INTEL_ENRICHMENT = if ($env:ENABLE_INTEL_ENRICHMENT) { $env:ENABLE_INTEL_ENRICHMENT } else { 'true' }
$env:ALLOW_PRIVATE_SCAN_TARGETS = if ($env:ALLOW_PRIVATE_SCAN_TARGETS) { $env:ALLOW_PRIVATE_SCAN_TARGETS } else { 'true' }

Write-Host "Worker connecting to:" -ForegroundColor Cyan
Write-Host "  DATABASE_URL=$($env:DATABASE_URL)"
Write-Host "  REDIS_URL=$($env:REDIS_URL)"
Write-Host ""
Write-Host "Starting Celery worker (Ctrl+C to stop)..." -ForegroundColor Green

& "$Root\venv\Scripts\python.exe" -m celery -A backend.worker.celery_app.celery_app worker --loglevel=INFO --pool=solo
