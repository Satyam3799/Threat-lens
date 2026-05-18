# Start API stack (no in-container worker — use start-worker.ps1 in another terminal).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
docker compose up -d --build
Write-Host ""
Write-Host "Stack started. Open http://localhost:5173" -ForegroundColor Green
Write-Host "Then in a NEW terminal run:  .\scripts\start-worker.ps1" -ForegroundColor Cyan
Write-Host "(Requires Nmap on Windows PATH)" -ForegroundColor Cyan
