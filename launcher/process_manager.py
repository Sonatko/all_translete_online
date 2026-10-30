"""Process Lifecycle Manager for Translation Ecosystem.
Detects running states of Stage 1, Stage 2, and Stage 3, and handles clean execution.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Dict, Optional

import psutil

log = logging.getLogger("Launcher.Process")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / ".venv" / "Scripts" / "python.exe"
PYTHONW_EXE = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / ".venv" / "Scripts" / "pythonw.exe"
PYTHONW_STAGE1 = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / ".venv" / "Scripts" / "pythonw.exe"

_CPU_HARDWARE_INFO: Optional[Dict[str, Any]] = None


def get_cpu_hardware_info() -> Dict[str, Any]:
    """Retrieve tangible CPU processor details (model, physical cores, logical threads)."""
    global _CPU_HARDWARE_INFO
    if _CPU_HARDWARE_INFO is None:
        cpu_name = platform.processor()
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            cpu_name = cpu_name.strip()
        except Exception:
            pass
        phys = psutil.cpu_count(logical=False) or 8
        logi = psutil.cpu_count(logical=True) or 16
        _CPU_HARDWARE_INFO = {
            "name": cpu_name,
            "physical_cores": phys,
            "logical_cores": logi,
            "summary": f"{cpu_name} ({phys} Cores / {logi} Threads)",
        }
    return _CPU_HARDWARE_INFO


class EcosystemProcessManager:
    """Monitors and controls the lifecycle of all stages."""

    @classmethod
    def get_stage_status(cls) -> Dict[str, Any]:
        """Check whether each stage is currently running and collect live resource telemetry."""
        cpu_info = get_cpu_hardware_info()
        status = {
            "stage_1": {"running": False, "pid": None, "ram_mb": 0.0, "cpu_pct": 0.0, "breakdown": []},
            "stage_2": {"running": False, "pid": None, "ram_mb": 0.0, "cpu_pct": 0.0, "breakdown": []},
            "stage_3": {"running": False, "pid": None, "ram_mb": 0.0, "cpu_pct": 0.0, "breakdown": []},
            "cpu_hardware": cpu_info,
            "total_ram_mb": 0.0,
            "total_cpu_pct": 0.0,
            "running_count": 0,
        }
        try:
            for p in psutil.process_iter(["name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    matched = None
                    if "overtranslate" in name:
                        matched = "stage_2"
                    elif "python" in name:
                        cmdline = " ".join(p.cmdline() or []).lower()
                        if "hub.py" in cmdline:
                            continue
                        if "stage_1_audio" in cmdline or "livetranslate" in cmdline:
                            matched = "stage_1"
                        elif "stage_3_voice" in cmdline or "studio" in cmdline:
                            matched = "stage_3"

                    if matched and not status[matched]["running"]:
                        # Collect full process tree telemetry (parent wrapper + spawned worker/inference processes)
                        tree = [p]
                        try:
                            tree.extend(p.children(recursive=True))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                        total_mem_bytes = 0
                        total_cpu_val = 0.0
                        breakdown = []
                        for proc in tree:
                            try:
                                proc_mem = proc.memory_info().rss
                                total_mem_bytes += proc_mem
                                total_cpu_val += proc.cpu_percent(interval=None)
                                p_mb = round(proc_mem / (1024.0 * 1024.0), 1)
                                cmd_str = " ".join(proc.cmdline() or []).lower()
                                threads_cnt = proc.num_threads()
                                if "spawn_main" in cmd_str:
                                    comp_name = "SenseVoice INT8 ASR (Распознавание)"
                                    allocated_t = 4
                                elif p_mb > 1000:
                                    comp_name = "Tencent HY-MT1.5 (Нейроперевод)"
                                    allocated_t = 2
                                elif "overtranslate" in cmd_str or "overtranslate" in (proc.name() or "").lower():
                                    comp_name = "OverTranslate OCR"
                                    allocated_t = 4
                                elif "studio" in cmd_str or "pocket" in cmd_str:
                                    comp_name = "Voice Studio Engine"
                                    allocated_t = 4
                                else:
                                    comp_name = "Оболочка / GUI Оркестратор"
                                    allocated_t = 1

                                breakdown.append({
                                    "name": comp_name,
                                    "pid": proc.pid,
                                    "ram_mb": p_mb,
                                    "threads": threads_cnt,
                                    "allocated_threads": allocated_t,
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

                        breakdown.sort(key=lambda x: x["ram_mb"], reverse=True)
                        mem_mb = round(total_mem_bytes / (1024.0 * 1024.0), 1)
                        cpu = round(total_cpu_val, 1)

                        status[matched]["running"] = True
                        status[matched]["pid"] = p.pid
                        status[matched]["ram_mb"] = mem_mb
                        status[matched]["cpu_pct"] = cpu
                        status[matched]["breakdown"] = breakdown
                        status["total_ram_mb"] += mem_mb
                        status["total_cpu_pct"] += cpu
                        status["running_count"] += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log.warning("Process scan error: %s", e)

        status["total_ram_mb"] = round(status["total_ram_mb"], 1)
        status["total_cpu_pct"] = round(status["total_cpu_pct"], 1)
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
    def stop_stage_1(cls) -> bool:
        """Stop Stage 1 LiveTranslate."""
        current_pid = os.getpid()
        for p in psutil.process_iter(["name"]):
            try:
                if p.pid == current_pid:
                    continue
                if "python" in (p.info.get("name") or "").lower():
                    cmdline = " ".join(p.cmdline() or []).lower()
                    if "hub.py" in cmdline:
                        continue
                    if "stage_1_audio" in cmdline or "livetranslate" in cmdline:
                        try:
                            for child in p.children(recursive=True):
                                child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return True

    @classmethod
    def stop_stage_2(cls) -> bool:
        """Stop Stage 2 OverTranslate."""
        for p in psutil.process_iter(["name"]):
            try:
                if "overtranslate" in (p.info.get("name") or "").lower():
                    p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return True

    @classmethod
    def stop_stage_3(cls) -> bool:
        """Stop Stage 3 Voice Translation Studio."""
        current_pid = os.getpid()
        for p in psutil.process_iter(["name"]):
            try:
                if p.pid == current_pid:
                    continue
                if "python" in (p.info.get("name") or "").lower():
                    cmdline = " ".join(p.cmdline() or []).lower()
                    if "hub.py" in cmdline:
                        continue
                    if "stage_3_voice" in cmdline or "studio" in cmdline:
                        try:
                            for child in p.children(recursive=True):
                                child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return True

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
                        try:
                            for child in p.children(recursive=True):
                                child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

