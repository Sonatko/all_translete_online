@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Hub [Online/Active]

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM
echo ======================================================================
echo.

:: ---------------------------------------------------------------------
:: 1. Translation Gateway (Meta NLLB-200 Server on CUDA)
:: ---------------------------------------------------------------------
echo [1/3] Checking if Translation Gateway is already online...
curl.exe -s -o NUL -w "%%{http_code}" http://127.0.0.1:8080/health 2>nul | findstr /R "^200$" >nul
if %errorlevel% equ 0 (
    echo [OK] Translation Gateway is already online and ready!
    goto launch_audio
)

echo [1/3] Launching Meta NLLB-200 Server in background (Hidden)...
start "" "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\pythonw.exe" "%~dp0stage_1_audio\nllb_server\server.py"

echo Waiting for NLLB-200 Server to initialize on CUDA...
set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=60

:wait_loop
set /a ATTEMPTS+=1
if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo.
    echo [ERROR] Server timed out after %MAX_ATTEMPTS% seconds.
    echo Please check stage_1_audio\nllb_server\server.log for details.
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

:: ---------------------------------------------------------------------
:: 2. LiveTranslate Subtitle Overlay (Stage 1 Audio)
:: ---------------------------------------------------------------------
:launch_audio
echo.
echo [2/3] Launching LiveTranslate Subtitle Overlay...
set "LIVETRANSLATE_SETTINGS_FILE=%~dp0stage_1_audio\LiveTranslate\user_settings.json"
cd /d "%~dp0stage_1_audio\LiveTranslate"
start "" start.bat
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: 3. OverTranslate In-Place Screen Translator (Stage 2 Screen)
:: ---------------------------------------------------------------------
echo [3/3] Launching OverTranslate (Screen OCR ^& QuickLookup)...
taskkill /F /IM OverTranslate.exe >nul 2>&1
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
ping 127.0.0.1 -n 3 >nul
start "" OverTranslate.exe
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: Dashboard & Hotkeys
:: ---------------------------------------------------------------------
echo.
echo ======================================================================
echo  TRANSLATION ECOSYSTEM IS ONLINE AND READY!
echo ======================================================================
echo  [Stage 1: Audio Subtitles - LiveTranslate]
echo  - F9:           Master Toggle (Subtitles Show/Hide + Audio Run/Pause)
echo  - 2x MMB:       Double Middle Click to toggle Click-through (Lock/Unlock)
echo  - MMB Drag:     Drag subtitle banner with Middle Mouse Button (wheel)
echo.
echo  [Stage 2: Screen OCR ^& Text - OverTranslate]
echo  - Ctrl+Alt+A:   Screen OCR In-Place Translation (Drag bounding box)
echo  - Ctrl+C+C:     Instant QuickLookup ^& Context Breakdown (Double Copy)
echo  - Ctrl+Alt+W:   Show / Hide OverTranslate Main Window
echo ======================================================================
echo  To stop all services cleanly, run STOP.bat
echo ======================================================================
echo.
echo Closing launcher window in 4 seconds...
ping 127.0.0.1 -n 5 >nul
exit /b 0
