import subprocess
import re

output = subprocess.check_output(
    ['powershell', '-NoProfile', '-Command', 
     'Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory | Where-Object { $_.Name -like "*0x00010E57*" -and $_.DedicatedUsage -gt 0 } | Select-Object Name, DedicatedUsage'],
    text=True
)

procs = {}
for line in output.splitlines():
    m = re.search(r'pid_(\d+).*?\s+(\d+)', line)
    if m:
        pid, usage = int(m.group(1)), int(m.group(2))
        procs[pid] = procs.get(pid, 0) + usage

name_map = {}
for p in subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True).splitlines():
    parts = p.strip('"').split('","')
    if len(parts) >= 2 and parts[1].isdigit():
        name_map[int(parts[1])] = parts[0]

sorted_procs = sorted(procs.items(), key=lambda x: x[1], reverse=True)
total_bytes = sum(procs.values())
print(f"=== TOTAL VRAM MEASURED ON RTX 5070: {total_bytes / (1024*1024):.1f} MB ===\n")
for pid, mem in sorted_procs:
    mb = mem / (1024 * 1024)
    pname = name_map.get(pid, "Unknown")
    print(f"{pname:<32} (PID {pid:<5}) : {mb:>6.1f} MB")
