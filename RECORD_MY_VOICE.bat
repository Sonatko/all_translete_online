@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Studio Voice Cloning (Kyutai Pocket-TTS)

echo ======================================================================
echo  СТУДИЙНАЯ ЗАПИСЬ И КЛОНИРОВАНИЕ ГОЛОСА (KYUTAI POCKET-TTS)
echo ======================================================================
echo.

"%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe" "%~dp0stage_3_voice\scratch\record_pocket_clone.py"

echo.
pause
