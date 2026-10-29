@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0stage_3_voice\Dizcord\.venv\Scripts\pythonw.exe"
set "HUB_SCRIPT=%~dp0launcher\hub.py"

if not exist "%VENV_PY%" (
    echo [ERROR] Python Virtual Environment not found:
    echo "%VENV_PY%"
    pause
    exit /b 1
)

if "%1"=="--debug" (
    echo [INFO] Starting Translation Ecosystem Hub in console debug mode...
    "%VENV_PY%" "%HUB_SCRIPT%"
    if errorlevel 1 pause
    exit /b %errorlevel%
)

start "" "%VENV_PYW%" "%HUB_SCRIPT%"
exit /b 0
