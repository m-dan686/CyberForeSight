@echo off
title CyberForeSight Launcher
echo ========================================
echo  Starting CyberForeSight System...
echo ========================================

cd /d "%~dp0\.."

echo [1/2] Starting Backend Server (Port 5000)...
start "CyberForeSight-Backend" cmd /k "cd backend && node server.js"

echo [2/2] Starting Frontend Dev Server (Port 5173)...
start "CyberForeSight-Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services launched in separate windows!
echo - Frontend: http://localhost:5173
echo - Backend:  http://localhost:5000
echo.
echo To stop everything, double-click scripts\stop.bat
timeout /t 3 >nul
