@echo off
title CyberForeSight Client Agent Installer
echo ========================================================
echo  CyberForeSight Background Client Agent Setup
echo ========================================================
echo.
echo Installing background startup task on this machine...
echo.

set SCRIPT_PATH=%~dp0..\collectors\client_agent.py
set VBS_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\cyberforesight_agent.vbs

:: Create silent background VBS launcher in Windows Startup folder
(
echo Set WshShell = CreateObject("WScript.Shell"^)
echo WshShell.Run "python """ ^& "%SCRIPT_PATH%" ^& """", 0, False
) > "%VBS_PATH%"

echo [SUCCESS] CyberForeSight Silent Agent is now installed in your Startup folder!
echo Location: %VBS_PATH%
echo.
echo Starting the agent in background now...
cscript //nologo "%VBS_PATH%"

echo.
echo ========================================================
echo  Done! This device will now automatically report its
echo  hostname, CPU, and RAM to the server whenever it is
echo  connected to the network (No browser needed).
echo ========================================================
timeout /t 4
