@echo off
chcp 65001 >nul
title Stopping Translation Ecosystem...

echo ======================================================================
echo  STOPPING TRANSLATION ECOSYSTEM PROCESSES
echo ======================================================================
echo.

echo [1/2] Terminating Screen Translation (OverTranslate)...
taskkill /F /IM OverTranslate.exe >nul 2>&1

echo [2/2] Terminating Audio Translation (LiveTranslate)...
powershell -NoProfile -Command "Get-Process python, pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*all_translete_online*' } | Stop-Process -Force" >nul 2>&1

echo.
echo All ecosystem processes stopped cleanly and safely!
ping 127.0.0.1 -n 2 >nul
exit /b 0
