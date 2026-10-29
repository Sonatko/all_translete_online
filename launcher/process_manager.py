"""Process Lifecycle Manager for Translation Ecosystem.
Detects running states of Stage 1, Stage 2, and Stage 3, and handles clean execution.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict

import psutil

log = logging.getLogger("Launcher.Process")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / ".venv" / "Scripts" / "python.exe"
PYTHONW_EXE = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / ".venv" / "Scripts" / "pythonw.exe"
PYTHONW_STAGE1 = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / ".venv" / "Scripts" / "pythonw.exe"


class EcosystemProcessManager:
    """Monitors and controls the lifecycle of all stages."""

    @staticmethod
    def get_stage_status() -> Dict[str, bool]:
        """Check whether each stage is currently running (ultra-fast filtered scan ~1.5ms)."""
        status = {
            "stage_1": False,
            "stage_2": False,
            "stage_3": False,
        }
        try:
            # Query name first (fast C-level call). Avoid expensive cmdline queries for system processes.
            for p in psutil.process_iter(["name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    if "overtranslate" in name:
                        status["stage_2"] = True
                        continue

                    if "python" in name:
                        cmdline = " ".join(p.cmdline() or []).lower()
                        if "hub.py" in cmdline:
                            continue
                        if "stage_1_audio" in cmdline or "livetranslate" in cmdline:
                            status["stage_1"] = True
                        elif "stage_3_voice" in cmdline or "studio" in cmdline:
                            status["stage_3"] = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log.warning("Process scan error: %s", e)
        return status

    @classmethod
    def start_stage_1(cls) -> bool:
        """Launch Stage 1 LiveTranslate."""
        try:
            app_dir = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate"
            env = dict(os.environ)
            env["LIVETRANSLATE_SETTINGS_FILE"] = str(app_dir / "user_settings.json")
            py = str(PYTHONW_STAGE1) if PYTHONW_STAGE1.is_file() else str(PYTHONW_EXE)
            subprocess.Popen([py, "main.py"], cwd=str(app_dir), env=env)
            return True
        except Exception as e:
            log.error("Failed to start Stage 1: %s", e)
            return False

    @classmethod
    def start_stage_2(cls) -> bool:
        """Launch Stage 2 OverTranslate."""
        try:
            exe = PROJECT_ROOT / "stage_2_screen" / "OverTranslate" / "current" / "OverTranslate.exe"
            if not exe.is_file():
                log.error("OverTranslate executable not found at %s", exe)
                return False
            subprocess.Popen([str(exe)], cwd=str(exe.parent))
            return True
        except Exception as e:
            log.error("Failed to start Stage 2: %s", e)
            return False

    @classmethod
    def start_stage_3(cls) -> bool:
        """Launch Stage 3 Voice Translation Studio."""
        try:
            app_dir = PROJECT_ROOT / "stage_3_voice" / "studio"
            py = str(PYTHONW_EXE) if PYTHONW_EXE.is_file() else sys.executable
            subprocess.Popen([py, "main.py"], cwd=str(app_dir))
            return True
        except Exception as e:
            log.error("Failed to start Stage 3: %s", e)
            return False

    @classmethod
    def start_all(cls) -> None:
        """Start all three stages in sequence."""
        cls.start_stage_1()
        cls.start_stage_2()
        cls.start_stage_3()

    @classmethod
    def stop_all(cls) -> None:
        """Terminate all ecosystem stages cleanly in ~5ms without spawning batch subshells."""
        current_pid = os.getpid()
        for p in psutil.process_iter(["name"]):
            try:
                if p.pid == current_pid:
                    continue
                name = (p.info.get("name") or "").lower()
                if "overtranslate" in name:
                    p.kill()
                    continue
                if "python" in name:
                    cmdline = " ".join(p.cmdline() or []).lower()
                    if "hub.py" in cmdline:
                        continue
                    if "stage_1_audio" in cmdline or "livetranslate" in cmdline or "stage_3_voice" in cmdline or "studio" in cmdline:
                        p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

