@echo off
title CyberForeSight Stopper
echo ========================================
echo  Stopping CyberForeSight Services...
echo ========================================

echo Freeing Port 5000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

echo Freeing Port 5173 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

echo.
echo All CyberForeSight services stopped.
timeout /t 2 >nul
