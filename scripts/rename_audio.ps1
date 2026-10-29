# Script to rename Topping E2x2 audio endpoints to short, clean names
$ErrorActionPreference = "Stop"

$capturePath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture"
$renderPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"

$renamed = 0

# 1. Rename Loopback 1/2 -> Topping Mic
Get-ChildItem $capturePath | ForEach-Object {
    $propKey = Join-Path $_.PSPath "Properties"
    if (Test-Path $propKey) {
        $p = Get-ItemProperty $propKey
        $friendly = $p.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
        if ($friendly -eq "Loopback 1/2" -or $friendly -like "*Loopback 1/2*") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "Topping Mic"
            Write-Host "[OK] Renamed '$friendly' -> 'Topping Mic'" -ForegroundColor Green
            $renamed++
        }
    }
}

# 2. Rename Playback 3/4 -> Topping Voice
# 3. Rename Playback 1/2 -> Topping Headphones
Get-ChildItem $renderPath | ForEach-Object {
    $propKey = Join-Path $_.PSPath "Properties"
    if (Test-Path $propKey) {
        $p = Get-ItemProperty $propKey
        $friendly = $p.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
        if ($friendly -eq "Playback 3/4" -or $friendly -like "*Playback 3/4*") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "Topping Voice"
            Write-Host "[OK] Renamed '$friendly' -> 'Topping Voice'" -ForegroundColor Green
            $renamed++
        }
        if ($friendly -eq "Playback 1/2" -or $friendly -like "*Playback 1/2*") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "Topping Headphones"
            Write-Host "[OK] Renamed '$friendly' -> 'Topping Headphones'" -ForegroundColor Green
            $renamed++
        }
    }
}

Write-Host "Successfully updated $renamed devices." -ForegroundColor Cyan
Start-Sleep -Seconds 1
