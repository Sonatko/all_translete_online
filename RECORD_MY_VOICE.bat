@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Studio Voice Cloning - Pocket TTS

echo ======================================================================
echo  STUDIO VOICE RECORDING AND CLONING - KYUTAI POCKET-TTS
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" "%~dp0stage_3_voice\scratch\record_pocket_clone.py"

echo.
pause
