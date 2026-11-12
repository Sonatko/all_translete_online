@echo off
setlocal
cd /d "%~dp0"
title Stopping Translation Ecosystem...

echo ======================================================================
echo  STOPPING TRANSLATION ECOSYSTEM PROCESSES
echo ======================================================================
echo.

set "VENV_PY=%~dp0stage_3_voice\.venv\Scripts\python.exe"
if exist "%~dp0python_embeded\python.exe" set "VENV_PY=%~dp0python_embeded\python.exe"

:: 1. Force kill OverTranslate and its updater window
taskkill /F /T /IM OverTranslate.exe >nul 2>&1
taskkill /F /T /IM Update.exe >nul 2>&1

:: 2. Use python psutil terminator if available (fastest, 0.05s)
if exist "%VENV_PY%" (
    "%VENV_PY%" "%~dp0scripts\stop_all.py"
    goto finish
)

:: 3. Fallback to PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_all.ps1"

:finish
echo.
echo ======================================================================
echo  [OK] ALL TRANSLATION ECOSYSTEM PROCESSES STOPPED!
echo ======================================================================
ping 127.0.0.1 -n 2 >nul
exit /b 0
