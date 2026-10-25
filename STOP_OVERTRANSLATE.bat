@echo off
chcp 65001 >nul
title Stopping OverTranslate...
echo ======================================================================
echo  STOPPING OVERTRANSLATE (SCREEN AND OCR TRANSLATOR)
echo ======================================================================
echo.
echo Stopping OverTranslate process...
taskkill /F /IM OverTranslate.exe >nul 2>&1
powershell -NoProfile -Command "Get-Process OverTranslate -ErrorAction SilentlyContinue | Stop-Process -Force" >nul 2>&1
echo.
echo [OK] OverTranslate stopped cleanly!
ping 127.0.0.1 -n 2 >nul
exit /b 0
