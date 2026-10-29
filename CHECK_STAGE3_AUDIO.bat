@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Stage 3 Audio Environment Diagnostics

echo ======================================================================
echo  RUNNING STAGE 3 AUDIO HEALTH CHECK
echo  Checking Topping E2x2, Equalizer APO, and Speed Pipeline...
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" "%~dp0tools\diagnostics\check_evening_audio_env.py"

echo.
pause
