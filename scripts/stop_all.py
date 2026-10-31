"""Universal Process Terminator for Translation Ecosystem.
Cleanly and instantly stops all processes belonging to all_translete_online
(LiveTranslate, OverTranslate, Voice Studio, Universal Hub) and flushes ghost tray icons.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
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


def refresh_windows_tray():
    """Flush and erase phantom/ghost notification icons from Windows Tray and Overflow Window."""
    try:
        user32 = ctypes.windll.user32

        def _scan_toolbar(h_wnd):
            if not h_wnd:
                return
            rect = wintypes.RECT()
            user32.GetClientRect(h_wnd, ctypes.byref(rect))
            for x in range(0, rect.right, 4):
                for y in range(0, rect.bottom, 4):
                    lparam = (y << 16) | (x & 0xFFFF)
                    user32.SendMessageW(h_wnd, 0x0200, 0, lparam)  # WM_MOUSEMOVE

        # 1. Main taskbar tray
        h_tray = user32.FindWindowW("Shell_TrayWnd", None)
        h_notify = user32.FindWindowExW(h_tray, 0, "TrayNotifyWnd", None)
        h_sys_pager = user32.FindWindowExW(h_notify, 0, "SysPager", None)
        h_toolbar = user32.FindWindowExW(h_sys_pager, 0, "ToolbarWindow32", None)
        _scan_toolbar(h_toolbar)

        # 2. Notification overflow popup window
        h_overflow = user32.FindWindowW("NotifyIconOverflowWindow", None)
        h_overflow_toolbar = user32.FindWindowExW(h_overflow, 0, "ToolbarWindow32", None)
        _scan_toolbar(h_overflow_toolbar)
        log.info("[OK] Windows Notification Area refreshed (ghost icons cleared).")
    except Exception as e:
        log.debug("Tray refresh skipped: %s", e)


def stop_all_processes():
    try:
        import psutil
    except ImportError:
        ps_script = os.path.join(os.path.dirname(__file__), "stop_all.ps1")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script])
        refresh_windows_tray()
        sys.exit(0)

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
            if "overtranslate" in name or ("update.exe" in name and "overtranslate" in cmd):
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
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        except Exception:
            pass

    log.info(f"[OK] Cleanly terminated {len(to_kill)} ecosystem processes.")
    refresh_windows_tray()
    sys.exit(0)


if __name__ == "__main__":
    stop_all_processes()
