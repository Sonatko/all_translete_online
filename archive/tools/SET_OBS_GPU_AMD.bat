@echo off
title Switch OBS to AMD iGPU
echo ======================================================================
echo  SWITCHING OBS STUDIO TO AMD RADEON iGPU
echo ======================================================================
echo.
echo [1/2] Configuring DirectX preferences for obs64.exe...
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "C:\Program Files\obs-studio\bin\64bit\obs64.exe" /t REG_SZ /d "GpuPreference=1;" /f
if %errorlevel% equ 0 (
    echo.
    echo [2/2] SUCCESS - OBS Studio assigned to AMD Radeon Graphics
    echo [INFO] Restart OBS Studio to free ~360 MB VRAM on RTX 5070
) else (
    echo.
    echo [ERROR] Failed to update registry
)
echo.
pause
