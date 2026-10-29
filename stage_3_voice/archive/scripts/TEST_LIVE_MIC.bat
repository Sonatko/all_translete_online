@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Live Microphone Voice Translation Test

echo ======================================================================
echo  INTERACTIVE LIVE MICROPHONE S2ST TEST (Topping E2x2 + Behringer)
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" "%~dp0stage_3_voice\scratch\test_evening_live_mic.py"

echo.
pause

