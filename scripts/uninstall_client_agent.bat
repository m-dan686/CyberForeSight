@echo off
title CyberForeSight Client Agent Uninstaller
echo ========================================================
echo  Uninstalling CyberForeSight Background Client Agent...
echo ========================================================
echo.

set VBS_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\cyberforesight_agent.vbs

if exist "%VBS_PATH%" (
    del /f /q "%VBS_PATH%"
    echo [OK] Removed from Windows Startup folder.
) else (
    echo [INFO] Agent was not found in Startup folder.
)

:: Terminate any running python agent instances
taskkill /f /im python.exe /fi "WINDOWTITLE eq CyberForeSight*" 2>nul

echo.
echo Agent uninstalled.
timeout /t 3
