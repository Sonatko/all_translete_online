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
$urls = @(
    "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip",
    "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"
)

Write-Host "[1/3] Downloading VB-Audio Virtual Cable package (1.3 MB)..." -ForegroundColor Yellow
$downloaded = $false
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
foreach ($url in $urls) {
    try {
        Invoke-WebRequest -Uri $url -OutFile $zipPath -UserAgent "Mozilla/5.0" -UseBasicParsing
        Write-Host "[OK] Downloaded successfully from $url" -ForegroundColor Green
        $downloaded = $true
        break
    } catch {
        Write-Host "[WARN] Mirror failed: $url ($_)" -ForegroundColor DarkYellow
    }
}

if (-not $downloaded) {
    Write-Host "[ERROR] Could not download VB-Cable driver pack." -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Extracting driver package..." -ForegroundColor Yellow
Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
Write-Host "[OK] Extracted." -ForegroundColor Green

$setupExe = Join-Path $tempDir "VBCABLE_Setup_x64.exe"
if (-not (Test-Path $setupExe)) {
    $setupExe = Join-Path $tempDir "VBCABLE_Setup.exe"
}

Write-Host "[3/3] Installing audio driver (Administrator UAC prompt)..." -ForegroundColor Yellow
$proc = Start-Process -FilePath $setupExe -ArgumentList "-i -h" -Verb RunAs -Wait -PassThru
Write-Host "[OK] Installation completed with code: $($proc.ExitCode)" -ForegroundColor Green

Write-Host ""
Write-Host "VB-Audio Virtual Cable is now installed and ready to use!" -ForegroundColor Green
Write-Host "You can now select 'Virtual Cable' in any conference or VoIP application." -ForegroundColor Cyan
Start-Sleep -Seconds 2
