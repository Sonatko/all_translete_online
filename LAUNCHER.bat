@echo off
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Translation Ecosystem Hub

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM - GUI DASHBOARD
echo ======================================================================
echo.

start "" "%~dp0stage_3_voice\Dizcord\.venv\Scripts\pythonw.exe" "%~dp0launcher\hub.py"

exit /b 0

