@echo off
setlocal
cd /d "%~dp0.."
title Studio Voice Cloning - Pocket-TTS

set "VENV_PY=%~dp0..\stage_3_voice\.venv\Scripts\python.exe"
set "CLONE_SCRIPT=%~dp0..\stage_3_voice\studio\record_voice.py"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment python.exe not found at:
    echo "%VENV_PY%"
    echo Please run scripts\setup.bat first.
    pause
    exit /b 1
)

"%VENV_PY%" -u "%CLONE_SCRIPT%"
if errorlevel 1 (
    echo.
    echo [ERROR] Voice recording process exited with code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
pause
exit /b 0

