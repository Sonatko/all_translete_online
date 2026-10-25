@echo off
chcp 65001 >nul
title Stopping Translation Ecosystem...

echo ======================================================================
echo  STOPPING ALL TRANSLATION PROCESSES
echo ======================================================================
echo.

echo [1/3] Terminating Screen Translation (OverTranslate)...
taskkill /F /IM OverTranslate.exe >nul 2>&1

echo [2/3] Terminating Audio Translation (NLLB Server and LiveTranslate)...
powershell -NoProfile -Command "Get-Process llama-server, python, pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*all_translete_online*' } | Stop-Process -Force; Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1
taskkill /F /IM llama-server.exe >nul 2>&1
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq NLLB*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo.
echo [3/3] All translation ecosystem processes stopped cleanly!
ping 127.0.0.1 -n 2 >nul
exit /b 0
