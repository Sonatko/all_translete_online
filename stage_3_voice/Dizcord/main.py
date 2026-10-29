"""Dizcord Translator - entry point.  Run:  Dizcord.bat  (or python main.py)"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Keep every download (Whisper models, HF cache...) inside the app folder -> portable.
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("ARGOS_PACKAGES_DIR", str(ROOT / "models" / "argos"))
os.environ.setdefault("XDG_DATA_HOME", str(ROOT / "models"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "models" / "cache"))


def _add_cuda_dlls():
    """Make pip-installed NVIDIA libraries (GPU extras) visible to CTranslate2 on Windows."""
    if os.name != "nt":
        return
    for sp in sys.path:
        nv = Path(sp) / "nvidia"
        if nv.is_dir():
            for bin_dir in nv.glob("*/bin"):
                try:
                    os.add_dll_directory(str(bin_dir))
                except OSError:
                    pass
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _setup_logging():
    from dizcord.config import LOGS_DIR
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = logging.handlers.RotatingFileHandler(LOGS_DIR / "dizcord.log", maxBytes=2_000_000, backupCount=3,
                                              encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(fh)
    if sys.stderr:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(sh)
    for noisy in ("httpx", "httpcore", "urllib3", "faster_whisper", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _splash(app, icon: Path):
    """A small window shown while the app loads (no text, so it needs no translation)."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import QSplashScreen
    pm = QPixmap(360, 150)
    pm.fill(QColor("#1d2026"))
    p = QPainter(pm)
    if icon.exists():
        from PySide6.QtGui import QIcon
        p.drawPixmap(24, 43, QIcon(str(icon)).pixmap(64, 64))
    p.setPen(QColor("#d4d7dd"))
    f = QFont()
    f.setPointSize(22)
    f.setBold(True)
    p.setFont(f)
    p.drawText(pm.rect().adjusted(100, 0, 0, -12), Qt.AlignVCenter, "Dizcord")
    p.setPen(QColor("#7aa2f7"))
    f.setPointSize(14)
    p.setFont(f)
    p.drawText(pm.rect().adjusted(102, 46, 0, 0), Qt.AlignVCenter, "• • •")
    p.end()
    s = QSplashScreen(pm)
    s.show()
    app.processEvents()
    return s


def main():
    sys.path.insert(0, str(ROOT))
    _add_cuda_dlls()
    _setup_logging()
    log = logging.getLogger("dizcord")

    def excepthook(et, ev, tb):
        log.error("Unhandled error", exc_info=(et, ev, tb))
    sys.excepthook = excepthook

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from dizcord import APP_NAME, __version__
    from dizcord.gui.main_window import MainWindow

    if os.name == "nt":  # own taskbar icon/group instead of python's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dizcord.Translator")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    log.info("%s %s starting (Python %s)", APP_NAME, __version__, sys.version.split()[0])

    # the language of the app: chosen before the main window opens (first start), then everything is in it
    from dizcord import config, i18n
    from dizcord.gui import theme
    from dizcord.gui.language_dialog import choose_language
    state = config.load_app_state()
    theme.apply(app, state.get("theme", "dark"))
    i18n.install()
    code, asked = choose_language(state)
    i18n.set_language(code)
    state["ui_language"] = code
    if asked and not state.get("seen_setup"):
        state["tour_pending"] = True             # a fresh install: the guided tour opens with the main window
    config.save_app_state(state)
    log.info("app language: %s", code)

    splash = _splash(app, icon)
    from dizcord.edition import PUBLIC
    if PUBLIC or state.get("tour_pending"):      # the Manual / the guide read aloud: load their voice before the
        from dizcord import natural              # window exists (loading it freezes Python for a few seconds)
        natural.preload()
    if state.get("tour_pending"):
        from dizcord.gui.tour import prepare_voice
        prepare_voice()                          # the guide's first steps are synthesised while the window is built

    win = MainWindow(app)
    win.show()
    splash.finish(win)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
