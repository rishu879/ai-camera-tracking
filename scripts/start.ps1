# Master start script for AI Camera Tracking (Backend + Frontend)
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   ISRO FSOC AI Camera Tracking & Coarse Alignment System" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Detect Wi-Fi LAN IP
$lanIP = "127.0.0.1"
$wifi = Get-NetIPAddress -InterfaceAlias "Wi-Fi" -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.254*" }
if ($wifi) {
    $lanIP = $wifi[0].IPAddress
}

Write-Host ">> Detected Local Network IP: $lanIP" -ForegroundColor Yellow
Write-Host ">> Checking Python Virtual Environment..." -ForegroundColor Gray

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "ERROR: Python environment .venv not found. Run 'python -m venv .venv' and 'pip install -r requirements.txt'" -ForegroundColor Red
    exit 1
}

# Start backend if not already running on port 8000
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $port8000) {
    Write-Host ">> Starting FastAPI Mission Control Backend (Port 8000)..." -ForegroundColor Green
    Start-Process -FilePath $py -ArgumentList "server.py" -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host ">> FastAPI Backend already running on port 8000." -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  MISSION CONTROL CONSOLE READY!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  * Host PC Browser:    http://localhost:8000" -ForegroundColor White
Write-Host "  * Phone / Wi-Fi URL:  http://$($lanIP):8000" -ForegroundColor Yellow
Write-Host "  * Direct Backend:     http://$($lanIP):8000" -ForegroundColor White
Write-Host "  * Health Check:       http://$($lanIP):8000/health" -ForegroundColor White
Write-Host "  * Swagger API Docs:   http://$($lanIP):8000/docs" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Mission Control server on port 8000 (Press Ctrl+C to stop)..." -ForegroundColor Gray
& $py "server.py"
