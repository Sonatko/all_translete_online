@echo off
title Dizcord - optional extras
cd /d "%~dp0"
if not exist "%~dp0runtime\.setup-ok" call "%~dp0setup.bat"
:menu
echo.
echo  Optional extras (installed into this folder):
echo    1) Piper        - reinstall the offline voice engine (installed by setup; more voices go in models\piper)
echo    2) Kokoro       - high quality offline voices (needs model files in models\kokoro)
echo    3) Argos        - offline translation (large download)
echo    4) NVIDIA GPU   - CUDA libraries for faster Whisper on NVIDIA cards (~1 GB)
echo    5) Download Kokoro model files (~340 MB)
echo    0) Exit
echo.
set /p choice=Choose:
if "%choice%"=="1" powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1 -Packages piper-tts
if "%choice%"=="2" powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1 -Packages kokoro-onnx
if "%choice%"=="3" powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1 -Packages argostranslate
if "%choice%"=="4" powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1 -Packages nvidia-cublas-cu12,nvidia-cudnn-cu12==9.*
if "%choice%"=="5" (
  if not exist models\kokoro mkdir models\kokoro
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx -OutFile models\kokoro\kokoro-v1.0.onnx; Invoke-WebRequest https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin -OutFile models\kokoro\voices-v1.0.bin"
)
if "%choice%"=="0" exit /b 0
goto menu
