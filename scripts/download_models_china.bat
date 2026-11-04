@echo off
chcp 65001 >nul
title Download China Models (ZH to EN)
cd /d "%~dp0.."
set "VENV_PY=%~dp0..\stage_3_voice\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment not found. Please run scripts\setup.bat first.
    pause
    exit /b 1
)

echo ======================================================================
echo  DOWNLOADING CHINESE PIPELINE MODELS (ZH -^> EN) VIA CHINA MIRROR
echo ======================================================================
echo.
"%VENV_PY%" "%~dp0download_models.py" --profile zh_en --china-mirror
echo.
pause

