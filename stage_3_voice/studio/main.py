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

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("Studio.Main")


def main():
    parser = argparse.ArgumentParser(description="Stage 3 Voice Translation Studio")
    parser.add_argument("--no-autoload", action="store_true", help="Do not load models on startup")
    parser.add_argument("--headless", action="store_true", help="Run without GUI for automated testing")
    args = parser.parse_args()

    log.info("Starting Stage 3 Voice Translation Studio...")

    # 1. Load Settings
    cfg = load_settings()

    # 2. Initialize Model Manager
    mm = ModelManager()

    # 3. Initialize Audio Engine
    engine = AudioEngine(mm, cfg)
    engine_started = engine.start()
    if not engine_started:
        log.warning("Audio engine failed to start all streams (check device availability).")

    # 4. Initialize Hotkey Listener
    hotkeys = HotkeyListener(
        on_ptt_change=engine.set_ptt_state,
        on_master_toggle=engine.toggle_master,
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

    win = StudioWindow(engine, mm)
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
