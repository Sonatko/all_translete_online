# Script to rename Topping E2x2 audio endpoints to short, clean names
$ErrorActionPreference = "Stop"

$capturePath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture"
$renderPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"

$renamed = 0

# 1. Rename Loopback 1/2 -> ИИ Микрофон
Get-ChildItem $capturePath | ForEach-Object {
    $propKey = Join-Path $_.PSPath "Properties"
    if (Test-Path $propKey) {
        $p = Get-ItemProperty $propKey
        $friendly = $p.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
        $custom = $p.'{b3f8fa53-0004-438e-9002-d512e37804a8},6'
        if ($friendly -eq "Loopback 1/2" -or $friendly -like "*Loopback 1/2*" -or $custom -eq "Topping Mic") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "ИИ Микрофон"
            Write-Host "[OK] Renamed -> 'ИИ Микрофон'" -ForegroundColor Green
            $renamed++
        }
    }
}

# 2. Rename Playback 3/4 -> Голос ИИ
# 3. Rename Playback 1/2 -> Наушники
Get-ChildItem $renderPath | ForEach-Object {
    $propKey = Join-Path $_.PSPath "Properties"
    if (Test-Path $propKey) {
        $p = Get-ItemProperty $propKey
        $friendly = $p.'{a45c254e-df1c-4efd-8020-67d146a850e0},2'
        $custom = $p.'{b3f8fa53-0004-438e-9002-d512e37804a8},6'
        if ($friendly -eq "Playback 3/4" -or $friendly -like "*Playback 3/4*" -or $custom -eq "Topping Voice") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "Голос ИИ"
            Write-Host "[OK] Renamed -> 'Голос ИИ'" -ForegroundColor Green
            $renamed++
        }
        if ($friendly -eq "Playback 1/2" -or $friendly -like "*Playback 1/2*" -or $custom -eq "Topping Headphones") {
            Set-ItemProperty -Path $propKey -Name "{b3f8fa53-0004-438e-9002-d512e37804a8},6" -Value "Наушники"
            Write-Host "[OK] Renamed -> 'Наушники'" -ForegroundColor Green
            $renamed++
        }
    }
}

Write-Host "Successfully updated $renamed devices." -ForegroundColor Cyan
Start-Sleep -Seconds 1

