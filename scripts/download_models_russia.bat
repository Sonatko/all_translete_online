@echo off
chcp 65001 >nul
title Download Russian Models (RU to EN)
cd /d "%~dp0.."
set "VENV_PY=%~dp0..\stage_3_voice\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo ======================================================================
    echo  FIRST-TIME RUN DETECTED: AUTO-CONFIGURING ENVIRONMENT FIRST
    echo ======================================================================
    echo.
    call "%~dp0setup.bat"
    if errorlevel 1 (
        echo [ERROR] Environment setup failed. Please check your network connection.
        pause
        exit /b 1
    )
)

echo ======================================================================
echo  DOWNLOADING RUSSIAN PIPELINE MODELS (RU -^> EN)
echo ======================================================================
echo.
"%VENV_PY%" "%~dp0download_models.py" --profile ru_en
echo.
pause
