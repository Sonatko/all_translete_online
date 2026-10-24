import subprocess
import re

# Get LUID of adapters
cmd_luid = """
Get-CimInstance Win32_VideoController | Select-Object Name, PNPDeviceID
"""
print(subprocess.check_output(['powershell', '-NoProfile', '-Command', cmd_luid], text=True))

# Query DXGI adapters LUID via PowerShell DirectX Diagnostic
script = """
Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\*" | 
  Where-Object { $_.DriverDesc } | Select-Object DriverDesc, MatchingDeviceId
"""
print(subprocess.check_output(['powershell', '-NoProfile', '-Command', script], text=True))
