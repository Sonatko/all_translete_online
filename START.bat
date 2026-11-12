@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0stage_3_voice\.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0stage_3_voice\.venv\Scripts\pythonw.exe"
set "HUB_SCRIPT=%~dp0launcher\hub.py"

if not exist "%VENV_PY%" goto need_setup
if not exist "%~dp0stage_2_screen\OverTranslate\current\OverTranslate.exe" goto need_setup
if not exist "%~dp0stage_1_audio\LiveTranslate\audio_capture.py" goto need_setup

"%VENV_PY%" -c "import PyQt6, pyaudiowpatch, ctranslate2, sherpa_onnx, pocket_tts" >nul 2>&1
if errorlevel 1 goto need_setup

:: Fast patch synchronization, locale adaptation and self-healing (~0.3s)
"%VENV_PY%" "%~dp0scripts\bootstrap_ecosystem.py" --quiet
if errorlevel 1 goto need_setup

goto launch_hub

:need_setup
echo ======================================================================
echo  FIRST-TIME SETUP / REPAIR: AUTO-PREPARING ENVIRONMENT
echo ======================================================================
echo.
echo Components missing or environment not initialized.
echo Running automatic bootstrap setup (takes ~1 minute)...
echo.
call "%~dp0scripts\setup.bat"
if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed. Please check your internet connection.
    pause
    exit /b 1
)

:launch_hub
if "%1"=="--debug" (
    echo [INFO] Starting Translation Ecosystem Hub in console debug mode...
    "%VENV_PY%" "%HUB_SCRIPT%"
    if errorlevel 1 pause
    exit /b %errorlevel%
)

start "" "%VENV_PYW%" "%HUB_SCRIPT%"
exit /b 0
