"""Studio configuration management.
Handles persistent settings saved in CONFIG/stage_3_voice/studio_settings.json.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger("Studio.Config")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "CONFIG" / "stage_3_voice"
CONFIG_FILE = CONFIG_DIR / "studio_settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "audio": {
        "input_device": "NVIDIA Broadcast",
        "output_device": "Playback 3/4",
        "sidetone_device": "Playback 1/2",
        "sidetone_enabled": True,
        "sidetone_volume": 0.70,
        "passthrough_enabled": True,
        "passthrough_volume": 1.0,
        "sample_rate": 48000,
    },
    "ptt": {
        "key": "shift+middle",
        "tail_ms": 200,
        "master_key": "f9",
    },
    "models": {
        "stt_provider": "gigaam",
        "stt_threads": 2,
        "mt_provider": "opus_mt",
        "mt_threads": 2,
        "tts_provider": "pocket_tts",
        "tts_voice": "my_pocket_voice",
        "tts_temperature": 0.3,
        "auto_load_on_startup": True,
    },
    "ui": {
        "dark_theme": True,
        "always_on_top": False,
        "show_vu_meters": True,
        "window_width": 780,
        "window_height": 620,
    }
}


def load_settings() -> Dict[str, Any]:
    """Load settings from JSON, merging with defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = _merge_dicts(DEFAULT_SETTINGS, data)
            log.info("Settings loaded from %s", CONFIG_FILE)
            return merged
        except Exception as e:
            log.warning("Failed to parse %s: %s. Using defaults.", CONFIG_FILE, e)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings atomically to JSON file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = CONFIG_FILE.with_suffix(".tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        tmp_file.replace(CONFIG_FILE)
        log.info("Settings successfully saved to %s", CONFIG_FILE)
    except Exception as e:
        log.error("Failed to save settings: %s", e)


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    res = dict(base)
    for k, v in override.items():
        if k in res and isinstance(res[k], dict) and isinstance(v, dict):
            res[k] = _merge_dicts(res[k], v)
        else:
            res[k] = v
    return res

