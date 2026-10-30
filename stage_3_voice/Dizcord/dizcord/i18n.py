"""The language of the app itself (menus, buttons, messages, the tour and the Manual).

The user picks it before the main window opens the first time (gui/language_dialog.py); Settings -> Language
changes it later (after a restart). The source text is English: each other language has a dictionary
dizcord/locale/<code>.json  {"English text": "translation", ...}. Keys may contain {0}, {1}... for text built at
run time ("Chapter {0} of {1}"). Anything missing simply stays in English.

The texts are not wrapped one by one in the code: install() patches the Qt calls that put text on screen
(QLabel(...), setText, setToolTip, addTab, addRow, QMessageBox...) so every string goes through tr() on its way.
Widgets showing user content (transcripts, translation results...) are excluded with no_translate(widget).
"""
from __future__ import annotations

import atexit
import json
import os
import re
from dataclasses import dataclass

from .config import MODELS_DIR, ROOT

LOCALE_DIR = ROOT / "dizcord" / "locale"
PIPER_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


@dataclass(frozen=True)
class Language:
    code: str
    name: str            # in that language - that is how people find their own
    english: str
    piper: str           # offline natural voice (models/piper/<voice>.onnx) for the tour and the Manual
    edge: str            # online natural voice, used when the offline one is not downloaded

    @property
    def piper_urls(self) -> list[tuple[str, str]]:
        """[(url, file name)] of the two files of the offline voice."""
        loc, speaker, quality = self.piper.split("-")
        base = f"{PIPER_URL}/{loc.split('_')[0]}/{loc}/{speaker}/{quality}/{self.piper}"
        return [(f"{base}.onnx", f"{self.piper}.onnx"), (f"{base}.onnx.json", f"{self.piper}.onnx.json")]

    def voice_installed(self) -> bool:
        d = MODELS_DIR / "piper"
        return all((d / name).is_file() for _u, name in self.piper_urls)


LANGUAGES: list[Language] = [
    Language("en", "English", "English", "en_US-kristin-medium", "en-US-AriaNeural"),
    Language("pt", "Português (Brasil)", "Portuguese (Brazil)", "pt_BR-faber-medium", "pt-BR-FranciscaNeural"),
    Language("es", "Español", "Spanish", "es_ES-davefx-medium", "es-ES-ElviraNeural"),
    Language("fr", "Français", "French", "fr_FR-siwis-medium", "fr-FR-DeniseNeural"),
    Language("de", "Deutsch", "German", "de_DE-thorsten-medium", "de-DE-KatjaNeural"),
    Language("it", "Italiano", "Italian", "it_IT-paola-medium", "it-IT-ElsaNeural"),
    Language("ru", "Русский", "Russian", "ru_RU-irina-medium", "ru-RU-SvetlanaNeural"),
    Language("uk", "Українська", "Ukrainian", "uk_UA-tetiana-high", "uk-UA-PolinaNeural"),   # espeak: reads Latin names too
    Language("pl", "Polski", "Polish", "pl_PL-gosia-medium", "pl-PL-ZofiaNeural"),
    Language("tr", "Türkçe", "Turkish", "tr_TR-dfki-medium", "tr-TR-EmelNeural"),
]
BY_CODE = {lang.code: lang for lang in LANGUAGES}

_lang: Language = LANGUAGES[0]
_table: dict[str, str] = {}
_patterns: list[tuple[re.Pattern, str]] = []
_misses: dict[str, None] = {}                    # texts known not to be in the table (bounded)
_collect: dict[str, None] | None = None          # tools/i18n_collect.py: every text seen, in order
_EDGES = re.compile(r"^([^\w<&]*)(.*?)([\s.…:!?]*)$", re.S)   # emoji/space before, punctuation after the words
_LETTER = re.compile(r"[^\W\d_]")


def current() -> Language:
    return _lang


def detect_windows_language() -> str:
    """The Windows display language if the app speaks it, else English (pre-selected in the picker)."""
    try:
        import ctypes
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        import locale
        name = (locale.windows_locale.get(lcid) or "").split("_")[0]
    except Exception:  # noqa: BLE001
        name = ""
    return name if name in BY_CODE else "en"


def set_language(code: str) -> Language:
    global _lang
    _lang = BY_CODE.get(code, LANGUAGES[0])
    _table.clear()
    _patterns.clear()
    _misses.clear()
    if _lang.code != "en":
        try:
            data = json.loads((LOCALE_DIR / f"{_lang.code}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for src, dst in data.items():
            if not isinstance(dst, str) or not dst or src.startswith("_"):
                continue
            if "{0}" in src:
                rx = re.escape(src)
                for i in range(10):
                    rx = rx.replace(re.escape(f"{{{i}}}"), f"(?P<g{i}>.+?)")
                _patterns.append((re.compile(rx, re.S), dst))
            else:
                _table[src] = dst
    return _lang


def tr(text):
    """`text` in the app language (unchanged when there is no translation)."""
    if not isinstance(text, str) or not text or not _LETTER.search(text):
        return text
    if _collect is not None:
        _collect.setdefault(text, None)
    if not _table and not _patterns:
        return text
    hit = _table.get(text)
    if hit is not None:
        return hit
    if text in _misses:
        return text
    pre, core, post = _EDGES.match(text).groups()
    if core and core != text:
        hit = _table.get(core)
        if hit is not None:
            return pre + hit + post
    for rx, out in _patterns:
        m = rx.fullmatch(text)
        edges = ("", "")
        if not m and pre:                            # "⚠ " + a message with {0} parts
            m, edges = rx.fullmatch(text[len(pre):]), (pre, "")
        if m:
            groups = m.groupdict()
            return edges[0] + re.sub(r"\{(\d)\}", lambda g: groups.get(f"g{g.group(1)}") or "", out) + edges[1]
    if len(_misses) > 20000:
        _misses.clear()
    _misses[text] = None
    return text


def no_translate(widget):
    """Never translate what this widget shows (user content: transcripts, results, names...)."""
    widget._i18n_off = True
    return widget


def source(widget) -> str:
    """The English text last given to a label/button (its text() is translated)."""
    return getattr(widget, "_i18n_src", None) or widget.text()


# ---------------------------------------------------------------------------------------------- Qt hooks
def _wrap_init(cls, positions=(0,)):
    orig = cls.__init__

    def __init__(self, *a, **k):
        a = list(a)
        for i in positions:
            if i < len(a) and isinstance(a[i], str):
                self._i18n_src = a[i]
                a[i] = tr(a[i])
        if isinstance(k.get("text"), str):
            k["text"] = tr(k["text"])
        orig(self, *a, **k)
    cls.__init__ = __init__


def _wrap_method(cls, name, positions=(0,), remember=False):
    orig = getattr(cls, name)

    def method(self, *a, **k):
        if not getattr(self, "_i18n_off", False):
            a = list(a)
            for i in positions:
                if i < len(a) and isinstance(a[i], str):
                    if remember:
                        self._i18n_src = a[i]
                    a[i] = tr(a[i])
        return orig(self, *a, **k)
    setattr(cls, name, method)


def _wrap_static(cls, name, positions):
    orig = getattr(cls, name)

    def method(*a, **k):
        a = list(a)
        for i in positions:
            if i < len(a) and isinstance(a[i], str):
                a[i] = tr(a[i])
        return orig(*a, **k)
    setattr(cls, name, staticmethod(method))


_installed = False


def install() -> None:
    """Route the text of every Qt widget through tr(). Call once, after set_language, before building windows."""
    global _installed
    if _installed:
        return
    _installed = True
    from PySide6.QtWidgets import (QAbstractButton, QCheckBox, QFileDialog, QFormLayout, QGroupBox, QInputDialog,
                                   QLabel, QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QRadioButton,
                                   QStatusBar, QTabWidget, QTextBrowser, QTextEdit, QToolButton, QWidget)
    for cls in (QLabel, QPushButton, QCheckBox, QRadioButton, QGroupBox):
        _wrap_init(cls)
    _wrap_method(QLabel, "setText", remember=True)
    _wrap_method(QAbstractButton, "setText", remember=True)
    _wrap_method(QToolButton, "setText", remember=True)
    _wrap_method(QGroupBox, "setTitle")
    _wrap_method(QWidget, "setToolTip")
    _wrap_method(QWidget, "setWindowTitle")
    for cls in (QLineEdit, QPlainTextEdit, QTextEdit):
        _wrap_method(cls, "setPlaceholderText")
    _wrap_method(QTextBrowser, "setHtml")
    _wrap_method(QTabWidget, "addTab", positions=(1, 2))
    _wrap_method(QTabWidget, "insertTab", positions=(2, 3))
    _wrap_method(QTabWidget, "setTabText", positions=(1,))
    _wrap_method(QTabWidget, "setTabToolTip", positions=(1,))
    _wrap_method(QMenu, "addAction", positions=(0, 1))
    _wrap_method(QMenu, "addMenu", positions=(0, 1))
    _wrap_method(QMenu, "setTitle")
    _wrap_method(QFormLayout, "addRow", positions=(0,))
    _wrap_method(QStatusBar, "showMessage")
    for name in ("information", "warning", "critical", "question"):
        _wrap_static(QMessageBox, name, positions=(1, 2))
    _wrap_static(QInputDialog, "getText", positions=(1, 2))
    _wrap_static(QInputDialog, "getItem", positions=(1, 2))
    for name in ("getOpenFileName", "getSaveFileName", "getExistingDirectory"):
        _wrap_static(QFileDialog, name, positions=(1,))


def start_collecting(path: str) -> None:
    """tools/i18n_collect.py: remember every text that reaches the screen and write the list to `path` at exit."""
    global _collect
    _collect = {}

    def dump():
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(_collect), f, ensure_ascii=False, indent=0)
    atexit.register(dump)
