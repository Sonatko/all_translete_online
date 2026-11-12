"""Bootstrap and lifecycle coordinator for Stage 3 Voice Translation Studio.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
from pathlib import Path

# Fix Windows console encoding and unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["TQDM_DISABLE"] = "1"

# Ensure standard streams are never None under pythonw.exe
import io
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from stage_3_voice.studio.audio_engine import AudioEngine
from stage_3_voice.studio.config import load_settings, save_settings
from stage_3_voice.studio.gui import StudioWindow
from stage_3_voice.studio.hotkey_listener import HotkeyListener
from stage_3_voice.studio.model_manager import ModelManager

# Logging setup with both console and rotating file output
from logging.handlers import RotatingFileHandler

LOGS_DIR = PROJECT_ROOT / "stage_3_voice" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "studio.log"

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] (%(name)s) %(message)s", datefmt="%H:%M:%S")

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
root_logger.addHandler(ch)

# Rotating file handler (5 MB, 3 backups)
try:
    fh = RotatingFileHandler(str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)
except Exception:
    pass

log = logging.getLogger("Studio.Main")


def main():
    parser = argparse.ArgumentParser(description="Stage 3 Voice Translation Studio")
    parser.add_argument("--no-autoload", action="store_true", help="Do not load models on startup")
    parser.add_argument("--headless", action="store_true", help="Run without GUI for automated testing")
    args = parser.parse_args()

    log.info("Starting Stage 3 Voice Translation Studio...")

    # 1. Load Settings
    cfg = load_settings()

    # 2. Initialize Model Manager (Pipeline: ru_en or zh_en)
    pipeline = cfg.get("models", {}).get("pipeline", "ru_en")
    mm = ModelManager(pipeline=pipeline)

    # 3. Initialize Audio Engine
    engine = AudioEngine(mm, cfg)
    engine_started = engine.start()
    if not engine_started:
        log.warning("Audio engine failed to start all streams (check device availability).")

    # 4. Initialize Hotkey Listener
    ptt_key = cfg.get("ptt", {}).get("key", "shift+middle")
    hotkeys = HotkeyListener(
        on_ptt_change=engine.set_ptt_state,
        on_master_toggle=engine.toggle_master,
        initial_key=ptt_key,
    )
    hotkeys.start()

    # 5. Background Model Pre-loading (keeps GUI opening instantly)
    if not args.no_autoload and cfg.get("models", {}).get("auto_load_on_startup", True):
        def _bg_load():
            log.info("Pre-loading models in background thread...")
            voice = cfg.get("models", {}).get("tts_voice", "my_pocket_voice")
            mm.load_all(voice=voice)
            log.info("Background model loading complete.")

        threading.Thread(target=_bg_load, daemon=True, name="ModelLoader").start()

    if args.headless:
        log.info("Running in headless test mode for 3 seconds...")
        import time
        time.sleep(3)
        hotkeys.stop()
        engine.stop()
        log.info("Headless test passed.")
        return 0

    # 6. Run GUI Event Loop
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Translation Studio")
    app.setQuitOnLastWindowClosed(False)

    win = StudioWindow(engine, mm, hotkeys=hotkeys)
    win.show()

    # Clean shutdown hook
    def _cleanup():
        log.info("Cleaning up before exit...")
        hotkeys.stop()
        engine.stop()
        save_settings(win.cfg)
        log.info("Application cleanly exited.")

    app.aboutToQuit.connect(_cleanup)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

