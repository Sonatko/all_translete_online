@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Dizcord S2ST Speed Pipeline [Stage 3 Voice]

echo ======================================================================
echo  STAGE 3: REAL-TIME OUTGOING SPEECH TRANSLATOR (SPEED PIPELINE)
echo  Sber GigaAM v3 CTC + Opus-MT CTranslate2 + Piper TTS
echo ======================================================================
echo.

:: 1. Mirror authoritative profile from CONFIG if needed
if exist "%~dp0CONFIG\stage_3_voice\Speed_Gaming.json" (
    copy /Y "%~dp0CONFIG\stage_3_voice\Speed_Gaming.json" "%~dp0stage_3_voice\Dizcord\data\profiles\Speed_Gaming.json" >nul
)
if exist "%~dp0CONFIG\stage_3_voice\app_state.json" (
    copy /Y "%~dp0CONFIG\stage_3_voice\app_state.json" "%~dp0stage_3_voice\Dizcord\data\app_state.json" >nul
)

:: 2. Launch Dizcord GUI
echo Launching Dizcord Speed Pipeline...
cd /d "%~dp0stage_3_voice\Dizcord"
start "" "%~dp0stage_3_voice\Dizcord\.venv\Scripts\pythonw.exe" main.py
if errorlevel 1 (
    echo [ERROR] Failed to start Dizcord.
    pause
    exit /b 1
)
cd /d "%~dp0"

echo.
echo ======================================================================
echo  STAGE 3 VOICE IS ACTIVE!
echo ======================================================================
echo  - Mode: Push-to-Translate (Scenario C)
echo  - Default State (Key UP):   Microphone passes through cleanly (0 ms delay)
echo  - PTT Active (Key DOWN):    Microphone muted, audio translated to English
echo  - Hotkey:                   F8 (Hold to speak English into game/voice chat)
echo  - Target Device:            Topping E2x2 / Virtual Cable / System Output
echo ======================================================================
echo.
ping 127.0.0.1 -n 4 >nul
exit /b 0
