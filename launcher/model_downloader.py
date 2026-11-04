"""High-Performance, China-Resilient Model Downloader for Translation Ecosystem.
Supports streaming chunked downloads with real MB/s progress, atomic writes (.tmp),
and automatic fallback to Chinese mirrors (hf-mirror.com / ghproxy.net).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import time
from typing import Callable, Dict, List, Optional
import urllib.request

try:
    from PySide6.QtCore import QThread, Signal
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False
    # Stub for CLI mode
    class QThread:
        pass
    def Signal(*args):
        return None

log = logging.getLogger("ModelDownloader")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "stage_3_voice" / "models"


MODEL_SPECS: Dict[str, Dict] = {
    # 🇷🇺 Russian Pipeline Models
    "giga_am_ru": {
        "name": "Sber GigaAM v3 CTC (Sherpa-ONNX INT8)",
        "pipeline": "ru_en",
        "task": "STT (ASR)",
        "repo": "csukuangfj/sherpa-onnx-nemo-ctc-giga-am-russian-2024-10-24",
        "dest_dir": MODELS_DIR / "giga-am-v3",
        "files": [
            ("model.int8.onnx", 224_721_476),
            ("tokens.txt", 196),
        ],
    },
    "opus_mt_ru_en": {
        "name": "Helsinki Opus-MT RU➔EN (CTranslate2 INT8)",
        "pipeline": "ru_en",
        "task": "MT (Перевод)",
        "repo": "gaudi/opus-mt-ru-en-ctranslate2",
        "dest_dir": MODELS_DIR / "opus-mt-ru-en-ct2",
        "files": [
            ("model.bin", 152_000_000),
            ("source.spm", 1_500_000),
            ("target.spm", 1_500_000),
        ],
    },

    # 🇨🇳 Chinese Pipeline Models
    "sensevoice_zh": {
        "name": "SenseVoiceSmall Chinese ASR (Sherpa-ONNX INT8)",
        "pipeline": "zh_en",
        "task": "STT (ASR)",
        "repo": "csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17",
        "dest_dir": MODELS_DIR / "sensevoice",
        "files": [
            ("model.int8.onnx", 232_000_000),
            ("tokens.txt", 1_500_000),
        ],
    },
    "opus_mt_zh_en": {
        "name": "Helsinki Opus-MT ZH➔EN (CTranslate2 INT8)",
        "pipeline": "zh_en",
        "task": "MT (Перевод)",
        "repo": "gaudi/opus-mt-zh-en-ctranslate2",
        "dest_dir": MODELS_DIR / "opus-mt-zh-en-ct2",
        "files": [
            ("model.bin", 152_000_000),
            ("source.spm", 1_500_000),
            ("target.spm", 1_500_000),
        ],
    },

    # 🗣 Common TTS Model (English speech output for both pipelines)
    "pocket_tts_en": {
        "name": "Kyutai Pocket-TTS 24kHz Backbone (Mimi Codec)",
        "pipeline": "common",
        "task": "TTS (Голос)",
        "repo": "latent-variable/pocket-tts-cloning-en",
        "dest_dir": MODELS_DIR / "pocket_tts",
        "files": [
            ("languages/english/model.safetensors", 295_000_000, "model.safetensors"),
        ],
    },
}


def build_download_urls(repo_id: str, remote_filename: str, china_mirror: bool = False) -> List[str]:
    """Build list of primary and fallback mirror URLs."""
    urls = []
    if china_mirror:
        # Prioritize Chinese mirror
        urls.append(f"https://hf-mirror.com/{repo_id}/resolve/main/{remote_filename}")
        urls.append(f"https://huggingface.co/{repo_id}/resolve/main/{remote_filename}")
    else:
        urls.append(f"https://huggingface.co/{repo_id}/resolve/main/{remote_filename}")
        urls.append(f"https://hf-mirror.com/{repo_id}/resolve/main/{remote_filename}")
    return urls


def download_single_file(
    urls: List[str],
    dest_path: Path,
    expected_size: int = 0,
    progress_cb: Optional[Callable[[int, int, float], None]] = None,
    stop_check: Optional[Callable[[], bool]] = None,
    max_retries_per_url: int = 3,
) -> bool:
    """Download single file with chunked streaming, HTTP Range (206 Partial Content) resume,
    speed telemetry, automatic retry on network drops, and atomic destination swap.
    Retains partial .part downloads so subsequent retries resume rather than restart.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")

    chunk_size = 64 * 1024  # 64 KB chunks
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for url in urls:
        if stop_check and stop_check():
            return False

        for attempt in range(1, max_retries_per_url + 1):
            if stop_check and stop_check():
                return False

            existing_bytes = part_path.stat().st_size if part_path.is_file() else 0
            headers = dict(base_headers)

            if existing_bytes > 0:
                headers["Range"] = f"bytes={existing_bytes}-"
                log.info("Resuming %s from byte %d (attempt %d/%d) via %s", dest_path.name, existing_bytes, attempt, max_retries_per_url, url)
            else:
                log.info("Downloading %s from byte 0 (attempt %d/%d) via %s", dest_path.name, attempt, max_retries_per_url, url)

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    status = getattr(resp, "status", 200)

                    if status == 206:
                        # Server honored Range request (Partial Content)
                        mode = "ab"
                        downloaded_bytes = existing_bytes
                        cr = resp.headers.get("Content-Range", "")
                        if "/" in cr:
                            try:
                                total_bytes = int(cr.split("/")[-1])
                            except ValueError:
                                total_bytes = existing_bytes + int(resp.headers.get("Content-Length", 0))
                        else:
                            total_bytes = existing_bytes + int(resp.headers.get("Content-Length", 0))
                    else:
                        # Full response (status 200) - starting from 0 or server ignored Range
                        mode = "wb"
                        downloaded_bytes = 0
                        total_bytes = int(resp.headers.get("Content-Length", 0)) or expected_size

                    # Immediate UI update showing resume starting point
                    if progress_cb:
                        progress_cb(downloaded_bytes, total_bytes, 0.0)

                    t_start = time.perf_counter()
                    last_update = t_start
                    session_bytes_start = downloaded_bytes

                    with open(part_path, mode) as f_out:
                        while True:
                            if stop_check and stop_check():
                                return False

                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            downloaded_bytes += len(chunk)

                            now = time.perf_counter()
                            if now - last_update >= 0.15:
                                duration = now - t_start
                                session_bytes = downloaded_bytes - session_bytes_start
                                speed_mbps = (session_bytes / (1024.0 * 1024.0)) / max(duration, 0.001)
                                if progress_cb:
                                    progress_cb(downloaded_bytes, total_bytes, speed_mbps)
                                last_update = now

                # Verify downloaded file
                actual_size = part_path.stat().st_size if part_path.is_file() else 0
                if (expected_size == 0 and actual_size > 1024) or (expected_size > 0 and actual_size >= min(expected_size * 0.8, 1024)):
                    if dest_path.exists():
                        dest_path.unlink()
                    shutil.move(part_path, dest_path)
                    log.info("Successfully completed download of %s (%d bytes)", dest_path.name, dest_path.stat().st_size)
                    if progress_cb:
                        progress_cb(dest_path.stat().st_size, dest_path.stat().st_size, 0.0)
                    return True

            except urllib.error.HTTPError as e:
                if e.code == 416:
                    # HTTP 416 Range Not Satisfiable: file might already be complete
                    actual_size = part_path.stat().st_size if part_path.is_file() else 0
                    if expected_size > 0 and actual_size >= min(expected_size * 0.8, 1024):
                        if dest_path.exists():
                            dest_path.unlink()
                        shutil.move(part_path, dest_path)
                        log.info("File %s is already complete (%d bytes), finalized", dest_path.name, actual_size)
                        if progress_cb:
                            progress_cb(dest_path.stat().st_size, dest_path.stat().st_size, 0.0)
                        return True
                    else:
                        log.warning("HTTP 416 on %s (size %d): resetting .part file", url, actual_size)
                        part_path.unlink(missing_ok=True)
                else:
                    log.warning("HTTP %d error from %s (attempt %d/%d): %s", e.code, url, attempt, max_retries_per_url, e.reason)
            except Exception as e:
                log.warning("Download error from %s (attempt %d/%d): %s", url, attempt, max_retries_per_url, e)

            # Wait before in-mirror retry (2 seconds)
            if attempt < max_retries_per_url:
                for _ in range(20):
                    if stop_check and stop_check():
                        return False
                    time.sleep(0.1)

    return False


def check_spec_status(spec_key: str) -> Dict:
    """Audit actual disk existence and size for a model spec."""
    spec = MODEL_SPECS.get(spec_key)
    if not spec:
        return {"exists": False, "size_mb": 0.0, "is_ready": False, "missing_files": []}

    dest_dir: Path = spec["dest_dir"]
    missing = []
    total_size = 0

    for file_info in spec["files"]:
        if len(file_info) == 3:
            local_name = file_info[2]
            exp_size = file_info[1]
        else:
            local_name = file_info[0]
            exp_size = file_info[1]

        target_file = dest_dir / local_name
        if target_file.is_file() and target_file.stat().st_size >= min(exp_size * 0.8, 1024):
            total_size += target_file.stat().st_size
        else:
            missing.append(local_name)

    size_mb = round(total_size / (1024.0 * 1024.0), 1)
    is_ready = (len(missing) == 0)

    return {
        "exists": is_ready,
        "size_mb": size_mb,
        "is_ready": is_ready,
        "missing_files": missing,
        "name": spec["name"],
        "task": spec["task"],
    }


def get_pipeline_specs(pipeline: str) -> List[str]:
    """Return keys of specs required for the given pipeline ('ru_en' or 'zh_en')."""
    if pipeline == "zh_en":
        return ["sensevoice_zh", "opus_mt_zh_en", "pocket_tts_en"]
    return ["giga_am_ru", "opus_mt_ru_en", "pocket_tts_en"]


if HAS_PYSIDE:
    class ModelDownloadWorker(QThread):
        """Asynchronous download worker for PySide6 GUI with real-time speed & progress."""

        sig_progress = Signal(str, int, int, float)  # file_name, bytes_down, total_bytes, speed_mbps
        sig_file_completed = Signal(str)             # file_name
        sig_spec_completed = Signal(str)             # spec_key
        sig_all_completed = Signal()
        sig_error = Signal(str, str)                 # item_name, error_msg

        def __init__(self, pipeline: str = "ru_en", china_mirror: bool = False, parent=None):
            super().__init__(parent)
            self.pipeline = pipeline
            self.china_mirror = china_mirror
            self._is_stopped = False

        def stop(self):
            self._is_stopped = True

        def run(self):
            spec_keys = get_pipeline_specs(self.pipeline)
            for key in spec_keys:
                if self._is_stopped:
                    break
                spec = MODEL_SPECS[key]
                dest_dir: Path = spec["dest_dir"]
                dest_dir.mkdir(parents=True, exist_ok=True)

                for file_info in spec["files"]:
                    if self._is_stopped:
                        break

                    if len(file_info) == 3:
                        remote_name = file_info[0]
                        exp_size = file_info[1]
                        local_name = file_info[2]
                    else:
                        remote_name = file_info[0]
                        exp_size = file_info[1]
                        local_name = file_info[0]

                    target_file = dest_dir / local_name
                    if target_file.is_file() and target_file.stat().st_size >= min(exp_size * 0.8, 1024):
                        # File already downloaded
                        self.sig_file_completed.emit(local_name)
                        continue

                    urls = build_download_urls(spec["repo"], remote_name, china_mirror=self.china_mirror)

                    def on_progress(down: int, total: int, spd: float):
                        self.sig_progress.emit(local_name, down, total, spd)

                    ok = download_single_file(
                        urls=urls,
                        dest_path=target_file,
                        expected_size=exp_size,
                        progress_cb=on_progress,
                        stop_check=lambda: self._is_stopped,
                    )

                    if ok:
                        self.sig_file_completed.emit(local_name)
                    else:
                        if not self._is_stopped:
                            self.sig_error.emit(local_name, f"Failed to download from mirrors: {urls}")
                            return

                self.sig_spec_completed.emit(key)

            if not self._is_stopped:
                self.sig_all_completed.emit()

