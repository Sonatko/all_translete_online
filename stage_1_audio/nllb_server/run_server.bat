@echo off
chcp 65001 >nul
title NLLB-200 1.3B Translation Server (CUDA)
cd /d "%~dp0"
start "" /B "..\LiveTranslate\.venv\Scripts\pythonw.exe" server.py
