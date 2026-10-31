# Stop all ecosystem processes cleanly
$targets = @('all_translete_online', 'stage_1_audio', 'stage_2_screen', 'stage_3_voice', 'LiveTranslate', 'OverTranslate', 'hub.py')

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $cmd = $_.CommandLine
    $name = $_.Name
    if ($name -like "*OverTranslate*") { return $true }
    if ($name -match "python|pythonw") {
        foreach ($t in $targets) {
            if ($cmd -like "*$t*") { return $true }
        }
    }
    return $false
} | ForEach-Object {
    Write-Host "Stopping process: $($_.Name) (PID $($_.ProcessId))"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
