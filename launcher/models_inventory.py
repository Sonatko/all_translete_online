"""Model Inventory and Storage Auditor for Translation Ecosystem.
Scans disk paths across all 3 stages, verifies model files, and calculates sizes.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

log = logging.getLogger("Launcher.ModelsInventory")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


_SIZE_CACHE: Dict[str, Tuple[float, float]] = {}


def get_dir_size_mb(path: Path) -> float:
    """Calculate total folder size in Megabytes with mtime caching."""
    try:
        if not path.exists():
            return 0.0
        mtime = path.stat().st_mtime
        p_str = str(path)
        if p_str in _SIZE_CACHE and _SIZE_CACHE[p_str][0] == mtime:
            return _SIZE_CACHE[p_str][1]

        if path.is_file():
            size = path.stat().st_size / (1024.0 * 1024.0)
        else:
            total = sum(p.stat().st_size for p in path.glob("**/*.*") if p.is_file())
            size = total / (1024.0 * 1024.0)

        _SIZE_CACHE[p_str] = (mtime, size)
        return size
    except Exception:
        return 0.0


class ModelsInventory:
    """Audits local neural models across Stage 1, Stage 2, and Stage 3."""

    @classmethod
    def get_inventory(cls) -> List[Dict]:
        """Return list of models with their existence, size, and paths."""
        models = [
            # Stage 1
            {
                "stage": "Этап 1 (Звук)",
                "task": "Входящий ASR",
                "name": "Sherpa-ONNX SenseVoice INT8",
                "path": PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "models" / "sherpa-onnx" / "sensevoice" / "model.int8.onnx",
                "is_file": True,
                "expected_mb": 200.0,
            },
            {
                "stage": "Этап 1 (Звук)",
                "task": "Входящий MT",
                "name": "Tencent HY-MT 1.8B GGUF",
                "path": PROJECT_ROOT / "stage_1_audio" / "nllb_server" / "models" / "hy-mt1.5-1.8b-gguf" / "HY-MT1.5-1.8B-Q4_K_M.gguf",
                "is_file": True,
                "expected_mb": 1100.0,
            },
            # Stage 3
            {
                "stage": "Этап 3 (Голос)",
                "task": "Исходящий STT",
                "name": "Sber GigaAM v3 CTC INT8",
                "path": PROJECT_ROOT / "stage_3_voice" / "models" / "giga-am-v3" / "model.int8.onnx",
                "is_file": True,
                "expected_mb": 210.0,
            },
            {
                "stage": "Этап 3 (Голос)",
                "task": "Исходящий MT",
                "name": "Helsinki Opus-MT RU->EN INT8",
                "path": PROJECT_ROOT / "stage_3_voice" / "models" / "opus-mt-ru-en-ct2" / "model.bin",
                "is_file": True,
                "expected_mb": 150.0,
            },
            {
                "stage": "Этап 3 (Голос)",
                "task": "Голосовой бэкбон",
                "name": "Kyutai Pocket-TTS (Mimi)",
                "path": PROJECT_ROOT / "stage_3_voice" / "models" / "pocket_tts",
                "is_file": False,
                "expected_mb": 300.0,
            },
            {
                "stage": "Этап 3 (Голос)",
                "task": "Ваш личный клон",
                "name": "my_pocket_voice.safetensors",
                "path": PROJECT_ROOT / "CONFIG" / "stage_3_voice" / "my_pocket_voice.safetensors",
                "is_file": True,
                "expected_mb": 4.4,
            },
        ]

        result = []
        for m in models:
            path: Path = m["path"]
            exists = path.is_file() if m["is_file"] else path.exists()

            size_mb = get_dir_size_mb(path) if exists else 0.0

            result.append({
                "stage": m["stage"],
                "task": m["task"],
                "name": m["name"],
                "path": str(path),
                "exists": exists,
                "size_mb": round(size_mb, 1),
                "is_ready": exists and (size_mb > 0.5 or m["expected_mb"] < 1.0),
            })
        return result
