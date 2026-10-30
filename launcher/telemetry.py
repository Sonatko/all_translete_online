"""Live Telemetry Reader for Translation Ecosystem (Stage 1 LiveTranslate).
Reads real execution metrics directly from the active LiveTranslate session log:
- Actual ASR inference latency (ms)
- Actual Machine Translation latency (ms)
- Last transcribed text & translated output
- Execution device verification (CPU fallback notice when CUDA is selected)
- Audio capture device & stream health
- Stage error extraction for human-readable diagnostic messages
"""
from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional

log = logging.getLogger("Launcher.Telemetry")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGE1_LOGS_DIR = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "logs"
STAGE1_SETTINGS = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "user_settings.json"


class Stage1Telemetry:
    """Extracts live telemetry and diagnostics from active LiveTranslate logs."""

    @staticmethod
    def get_live_metrics() -> Dict[str, Any]:
        """Poll the newest log file from LiveTranslate and return tangible runtime metrics."""
        result = {
            "has_session": False,
            "audio_device": None,
            "asr_engine": "Sherpa-ONNX SenseVoice",
            "asr_device_requested": "cpu",
            "asr_device_actual": "cpu",
            "cuda_fallback_notice": False,
            "mt_model": "Hunyuan MT 1.8B",
            "last_asr_ms": None,
            "last_tl_ms": None,
            "last_total_ms": None,
            "last_original": None,
            "last_translation": None,
            "last_lang": None,
            "is_speaking": False,
            "error_msg": None,
        }

        # 1. Read requested settings from user_settings.json
        if STAGE1_SETTINGS.is_file():
            try:
                import json
                cfg = json.loads(STAGE1_SETTINGS.read_text(encoding="utf-8"))
                result["asr_device_requested"] = cfg.get("asr_device", "cpu")
                models = cfg.get("models", [])
                act_idx = cfg.get("active_model", 1)
                if act_idx < len(models):
                    result["mt_model"] = models[act_idx].get("name", "Hunyuan MT 1.8B")
            except Exception as e:
                log.debug("Settings parse error: %s", e)

        # 2. Find newest log file
        if not STAGE1_LOGS_DIR.is_dir():
            return result

        log_files = sorted(STAGE1_LOGS_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not log_files:
            return result

        latest_log = log_files[0]
        # Only inspect if the file was touched recently (within last 10 minutes)
        import time
        file_age_s = time.time() - latest_log.stat().st_mtime
        if file_age_s > 600:
            return result

        result["has_session"] = True

        try:
            # Read tail of log file (~64 KB is plenty for recent 200 lines)
            with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2)
                size = f.tell()
                read_size = min(size, 65536)
                f.seek(size - read_size)
                lines = f.readlines()

            for line in lines:
                # Device fallback detection
                if "Fallback to cpu!" in line or "Please compile with -DSHERPA_ONNX_ENABLE_GPU" in line:
                    result["cuda_fallback_notice"] = True
                    result["asr_device_actual"] = "cpu"
                elif "Audio capture started" in line:
                    pass
                elif "Loopback device:" in line:
                    m_dev = re.search(r"Loopback device:\s*(.+)", line)
                    if m_dev:
                        result["audio_device"] = m_dev.group(1).strip()

                # Errors
                if "[ERROR]" in line and "LiveTranslate" in line:
                    # Filter benign or spam errors
                    if "Interim ASR error" in line or "Failed to load ASR" in line or "Audio capture error" in line:
                        err = line.split("[ERROR]")[-1].strip()
                        result["error_msg"] = err

                # ASR metric
                m_asr = re.search(r"ASR \[([a-z]+)\] \((\d+)ms\):\s*(.+)", line)
                if m_asr:
                    result["last_lang"] = m_asr.group(1)
                    result["last_asr_ms"] = int(m_asr.group(2))
                    result["last_original"] = m_asr.group(3).strip()

                # Translation metric
                m_tl = re.search(r"Translate \((\d+)ms\):\s*(.+)", line)
                if m_tl:
                    result["last_tl_ms"] = int(m_tl.group(1))
                    result["last_translation"] = m_tl.group(2).strip()

            if result["last_asr_ms"] is not None and result["last_tl_ms"] is not None:
                result["last_total_ms"] = result["last_asr_ms"] + result["last_tl_ms"]

        except Exception as e:
            log.warning("Telemetry log scan failed: %s", e)

        return result
