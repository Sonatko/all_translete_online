@echo off
setlocal
cd /d "%~dp0"
title Stopping Translation Ecosystem...

echo ======================================================================
echo  STOPPING TRANSLATION ECOSYSTEM PROCESSES
echo ======================================================================
echo.

echo [*] Terminating OverTranslate, Audio Translation, Studio and Hub...
taskkill /F /T /IM OverTranslate.exe >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'stage_1_audio|LiveTranslate|stage_3_voice|studio|hub\.py' } | Stop-Process -Force" >nul 2>&1

echo.
echo [OK] All translation ecosystem processes stopped cleanly!
exit /b 0
