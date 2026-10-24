@echo off
title Flush Windows DWM Cache
echo ======================================================================
echo  FLUSH WINDOWS DWM TEXTURE CACHE - ADMINISTRATOR
echo ======================================================================
echo.

net session >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Running with Administrator privileges
    echo [INFO] Restarting Desktop Window Manager - dwm.exe...
    taskkill /F /IM dwm.exe
    echo.
    echo [OK] DWM flushed successfully. Screen briefly refreshed.
    ping 127.0.0.1 -n 3 >nul
    exit /b 0
) else (
    echo [INFO] Elevating permissions via Windows UAC...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/c taskkill /F /IM dwm.exe' -Verb RunAs"
    echo [INFO] If UAC prompt appeared, click YES.
    ping 127.0.0.1 -n 3 >nul
    exit /b 0
)
