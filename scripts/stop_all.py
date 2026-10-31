"""Universal Process Terminator for Translation Ecosystem.
Cleanly and instantly stops all processes belonging to all_translete_online
(LiveTranslate, OverTranslate, Voice Studio, Universal Hub) without collateral damage.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("StopAll")

TARGET_PATTERNS = [
    "all_translete_online",
    "stage_1_audio",
    "stage_2_screen",
    "stage_3_voice",
    "livetranslate",
    "overtranslate",
    "hub.py",
]


def stop_all_processes():
    try:
        import psutil
    except ImportError:
        # Fallback to PowerShell
        ps_script = os.path.join(os.path.dirname(__file__), "stop_all.ps1")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script])
        return

    current_pid = os.getpid()
    to_kill = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pid = proc.info["pid"]
            if pid == current_pid or pid == 0 or pid == 4:
                continue
            name = (proc.info["name"] or "").lower()
            cmd = " ".join(proc.info["cmdline"] or []).lower()

            is_target = False
            if "overtranslate" in name:
                is_target = True
            elif "python" in name or "pythonw" in name:
                if any(p in cmd for p in TARGET_PATTERNS):
                    is_target = True

            if is_target:
                to_kill.append((pid, name, proc))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    for pid, name, proc in to_kill:
        log.info(f"Terminating [{name}] (PID {pid})...")
        try:
            proc.kill()
        except Exception:
            pass
        # Hard kill via taskkill to guarantee Windows frees the handle
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)

    log.info(f"[OK] Cleanly terminated {len(to_kill)} ecosystem processes.")


if __name__ == "__main__":
    stop_all_processes()
