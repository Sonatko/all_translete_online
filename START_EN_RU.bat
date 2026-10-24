@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Hub [ENGLISH -> RUSSIAN]

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM [ENGLISH -> RUSSIAN]
echo ======================================================================
echo.

echo [1/3] Checking if Translation Gateway is already online...
curl.exe -s -o NUL -w "%%{http_code}" http://127.0.0.1:8080/health 2>nul | findstr /R "^200$" >nul
if %errorlevel% equ 0 (
    echo [OK] Translation Gateway is already online and ready!
    goto launch_livetranslate
)

echo [2/3] Launching Meta NLLB-200 Server in background (Hidden)...
start "" "%~dp0bin\LiveTranslate\.venv\Scripts\pythonw.exe" "%~dp0bin\nllb_server\server.py"

echo [3/3] Waiting for NLLB-200 Server to initialize on CUDA...
set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=60

:wait_loop
set /a ATTEMPTS+=1
if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo.
    echo [ERROR] Server timed out after %MAX_ATTEMPTS% seconds.
    echo Please check bin\nllb_server\server.log for details.
    pause
    exit /b 1
)

ping 127.0.0.1 -n 2 >nul

curl.exe -s -o NUL -w "%%{http_code}" http://127.0.0.1:8080/health 2>nul | findstr /R "^200$" >nul
if %errorlevel% equ 0 goto server_ready

<nul set /p=.
goto wait_loop

:server_ready
echo.
echo [OK] Translation Gateway is ONLINE and healthy! (HTTP 200 OK)

:launch_livetranslate
echo.
echo ======================================================================
echo  LAUNCHING LIVETRANSLATE SUBTITLE OVERLAY [ENGLISH -> RUSSIAN]
echo ======================================================================
echo  [Mode]         - English Speech -> English (Line 1) + Russian (Line 2)
echo  [F9]           - Master Toggle: Show/Hide Subtitles + Run/Pause Audio
echo  [2x MMB]        - Double click Middle Button (wheel) to toggle Click-through
echo  [MMB Drag]      - Drag subtitle banner with Middle Mouse Button (wheel)
echo ======================================================================
echo.
set "LIVETRANSLATE_SETTINGS_FILE=%~dp0bin\LiveTranslate\user_settings.json"
cd /d "%~dp0bin\LiveTranslate"
start "" start.bat
exit
