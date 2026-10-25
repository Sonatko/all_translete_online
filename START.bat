@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Ecosystem [START ALL]

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM
echo ======================================================================
echo.

echo [1/3] Checking Translation Gateway (Meta NLLB-200 1.3B)...
curl.exe -s -o NUL -w "%%{http_code}" http://127.0.0.1:8080/health 2>nul | findstr /R "^200$" >nul
if %errorlevel% equ 0 (
    echo   [OK] Translation Gateway is already online on port 8080!
    goto launch_apps
)

echo   [-] Starting NLLB-200 1.3B Server in background (Hidden)...
start "" "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\pythonw.exe" "%~dp0stage_1_audio\nllb_server\server.py"

set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=45

:wait_loop
set /a ATTEMPTS+=1
if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo.
    echo   [ERROR] NLLB Server timed out after %MAX_ATTEMPTS% seconds.
    echo   Please check stage_1_audio\nllb_server\server.log for details.
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
echo   [OK] Translation Gateway is ONLINE and healthy! (HTTP 200 OK)

:launch_apps
echo.
echo [2/3] Launching Screen OCR and Text Translator (OverTranslate)...
tasklist /FI "IMAGENAME eq OverTranslate.exe" 2>nul | findstr /I "OverTranslate.exe" >nul
if %errorlevel% equ 0 (
    echo   [OK] OverTranslate is already running!
) else (
    cd /d "%~dp0stage_2_screen\OverTranslate\current"
    start "" OverTranslate.exe
    cd /d "%~dp0"
    echo   [OK] OverTranslate launched!
)

echo.
echo [3/3] Launching Real-Time Audio Subtitles (LiveTranslate)...
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | findstr /I "pythonw.exe" >nul
cd /d "%~dp0stage_1_audio\LiveTranslate"
start "" start.bat
cd /d "%~dp0"
echo   [OK] LiveTranslate subtitle overlay launched!

echo.
echo ======================================================================
echo  ALL TRANSLATION ENGINES ARE ACTIVE!
echo ======================================================================
echo   [F9]             : Toggle Audio Subtitles (Show/Hide + Run/Pause)
echo   [Ctrl + Alt + A] : Screen OCR In-Place Translation (Games, Images)
echo   [Ctrl + C + C]   : Instant AI / Dictionary Word Lookup Card
echo   [STOP_ALL.bat]   : Close all translation processes cleanly
echo ======================================================================
echo.
timeout /t 3 >nul
exit /b 0
