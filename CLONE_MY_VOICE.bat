@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Neural Voice Cloning (XTTS-v2 - My Voice)

echo ======================================================================
echo  КЛОНИРОВАНИЕ ВАШЕГО ГОЛОСА (Topping E2x2 + Behringer XM8500)
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" "%~dp0stage_3_voice\scratch\record_and_clone.py"

echo.
pause
