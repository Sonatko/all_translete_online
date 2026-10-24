@echo off
title Switch OBS to NVIDIA RTX 5070
echo ======================================================================
echo  SWITCHING OBS STUDIO TO NVIDIA GEFORCE RTX 5070
echo ======================================================================
echo.
echo [1/2] Configuring DirectX preferences for obs64.exe...
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "C:\Program Files\obs-studio\bin\64bit\obs64.exe" /t REG_SZ /d "GpuPreference=2;" /f
if %errorlevel% equ 0 (
    echo.
    echo [2/2] SUCCESS - OBS Studio returned to NVIDIA GeForce RTX 5070
    echo [INFO] Restart OBS Studio for maximum 2K 144Hz NVENC gaming recording
) else (
    echo.
    echo [ERROR] Failed to update registry
)
echo.
pause
