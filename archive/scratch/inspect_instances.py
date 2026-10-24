import subprocess

script = """
Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory | Select-Object -First 10 -Property Name, DedicatedUsage
"""
print(subprocess.check_output(['powershell', '-NoProfile', '-Command', script], text=True))
