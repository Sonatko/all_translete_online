import subprocess

script = """
Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory | Select-Object Name, DedicatedUsage, SharedUsage
"""
print(subprocess.check_output(['powershell', '-NoProfile', '-Command', script], text=True))
