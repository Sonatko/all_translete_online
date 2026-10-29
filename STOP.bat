@echo off
chcp 65001 >nul
title Stopping Translation Ecosystem...

echo ======================================================================
echo  STOPPING TRANSLATION ECOSYSTEM PROCESSES
echo ======================================================================
echo.

echo [1/3] Terminating Screen Translation (OverTranslate)...
taskkill /F /IM OverTranslate.exe >nul 2>&1

echo [2/3] Terminating Audio Translation (LiveTranslate)...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*stage_1_audio*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo [3/3] Terminating Voice Pipeline and Hub Launcher...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*stage_3_voice*' -or $_.CommandLine -like '*studio*' -or $_.CommandLine -like '*hub.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo.
echo All ecosystem processes stopped cleanly and safely!
ping 127.0.0.1 -n 2 >nul
exit /b 0
