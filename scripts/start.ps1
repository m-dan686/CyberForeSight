# Start CyberForeSight Backend and Frontend
$root = Resolve-Path "$PSScriptRoot\.."

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Starting CyberForeSight System...      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Start Backend Server (Port 5000)
Write-Host "[1/2] Launching Backend Server on port 5000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; node server.js" -WindowStyle Normal

# 2. Start Frontend Dev Server (Port 5173 with Vite)
Write-Host "[2/2] Launching Frontend Dev Server..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "`nCyberForeSight is starting!" -ForegroundColor Yellow
Write-Host " - Frontend (Dev):    http://localhost:5173" -ForegroundColor White
Write-Host " - Backend / Prod UI: http://localhost:5000" -ForegroundColor White
Write-Host "`nTo stop all services, run: .\scripts\stop.ps1 or double-click scripts\stop.bat" -ForegroundColor Gray
