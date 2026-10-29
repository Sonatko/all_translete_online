# 1-Click Silent Installer for VB-Audio Virtual Cable (for PCs without Topping sound cards)
$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " INSTALLING VB-AUDIO VIRTUAL CABLE (1-CLICK SETUP)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$tempDir = Join-Path $PSScriptRoot "..\stage_3_voice\scratch\vbcable_installer"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

$zipPath = Join-Path $tempDir "vbcable.zip"
$downloadUrl = "https://download.vb-audio.com/Download_VAC/VBCABLE_Driver_Pack43.zip"

Write-Host "[1/3] Downloading VB-Audio Virtual Cable package (1.2 MB)..." -ForegroundColor Yellow
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "[OK] Downloaded successfully." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to download from $downloadUrl : $_" -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Extracting driver package..." -ForegroundColor Yellow
Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
Write-Host "[OK] Extracted." -ForegroundColor Green

$setupExe = Join-Path $tempDir "VBCABLE_Setup_x64.exe"
if (-not (Test-Path $setupExe)) {
    $setupExe = Join-Path $tempDir "VBCABLE_Setup.exe"
}

Write-Host "[3/3] Installing audio driver (Silent Mode)..." -ForegroundColor Yellow
$proc = Start-Process -FilePath $setupExe -ArgumentList "-i -h" -Wait -PassThru
Write-Host "[OK] Installation completed with code: $($proc.ExitCode)" -ForegroundColor Green

Write-Host ""
Write-Host "VB-Audio Virtual Cable is now installed and ready to use!" -ForegroundColor Green
Write-Host "You can now use 'Cable Mode' with 0-effort in CS2 and Discord." -ForegroundColor Cyan
Start-Sleep -Seconds 2
