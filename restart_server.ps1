# Wymuszenie restartu serwera
Write-Host "=== RESTART SERWERA SOR ===" -ForegroundColor Green
Write-Host ""

# Zatrzymaj wszystkie procesy Python
Write-Host "Zatrzymywanie procesow Python..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Sprawdz czy port 8000 jest wolny
Write-Host "Sprawdzanie portu 8000..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 8000 nadal zajety. Zatrzymywanie procesow..." -ForegroundColor Red
    $portInUse | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Uruchamianie serwera..." -ForegroundColor Green
Write-Host "Otworz w przegladarce: http://localhost:8000/" -ForegroundColor Cyan
Write-Host "Nacisnij Ctrl+C aby zatrzymac" -ForegroundColor Yellow
Write-Host ""

# Uruchom serwer
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
