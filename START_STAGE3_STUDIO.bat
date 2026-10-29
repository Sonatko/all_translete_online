@echo off
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Stage 3 Voice Translation Studio

echo ======================================================================
echo  STAGE 3: VOICE TRANSLATION STUDIO - REAL-TIME S2ST (CS2 / DISCORD)
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" -u "%~dp0stage_3_voice\studio\main.py"

echo.
pause
