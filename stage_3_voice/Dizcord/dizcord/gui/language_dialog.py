"""First start: the user picks the language of the app before the main window opens.

The list shows every language in its own name, with the Windows language pre-selected. After the choice the
offline natural voice of that language (~60 MB) is downloaded once, so the tour and the Manual can be read aloud
without internet. If the download fails the app still starts (the voice falls back to the online one)."""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton,
                               QVBoxLayout)

from .. import i18n, voice_download

# "Choose your language" in every language of the list - shown before any language is chosen
_TITLE = "  ·  ".join(["Choose your language", "Escolha seu idioma", "Elige tu idioma", "Choisissez votre langue",
                       "Sprache wählen", "Scegli la lingua", "Выберите язык", "Оберіть мову", "Wybierz język",
                       "Dilinizi seçin"])


class _Relay(QObject):
    progress = Signal(int, int)
    finished = Signal(str)                    # "" = ok, else the error


class LanguageDialog(QDialog):
    def __init__(self, preselect: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dizcord")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(460)
        self.code = preselect
        v = QVBoxLayout(self)
        head = i18n.no_translate(QLabel("🌐  " + _TITLE))
        head.setWordWrap(True)
        head.setObjectName("title")
        v.addWidget(head)
        self.list = QListWidget()
        for lang in i18n.LANGUAGES:
            item = QListWidgetItem(lang.name if lang.name == lang.english else f"{lang.name}   ({lang.english})")
            item.setData(Qt.UserRole, lang.code)
            self.list.addItem(item)
            if lang.code == preselect:
                self.list.setCurrentItem(item)
        self.list.setMinimumHeight(300)
        self.list.itemDoubleClicked.connect(lambda _i: self._accept())
        v.addWidget(self.list, 1)
        self.note = i18n.no_translate(QLabel(""))
        self.note.setWordWrap(True)
        self.note.setObjectName("muted")
        v.addWidget(self.note)
        self.bar = QProgressBar()
        self.bar.hide()
        v.addWidget(self.bar)
        row = QHBoxLayout()
        row.addStretch(1)
        self.ok = i18n.no_translate(QPushButton("OK  ▶"))
        self.ok.setObjectName("primary")
        self.ok.setDefault(True)
        self.ok.clicked.connect(self._accept)
        row.addWidget(self.ok)
        v.addLayout(row)
        self._relay = _Relay()
        self._relay.progress.connect(self._on_progress)
        self._relay.finished.connect(self._on_downloaded)
        self._cancel = False

    def _accept(self):
        item = self.list.currentItem()
        if item is None or not self.ok.isEnabled():
            return
        self.code = item.data(Qt.UserRole)
        lang = i18n.set_language(self.code)
        if lang.voice_installed():
            self.accept()
            return
        self.list.setEnabled(False)
        self.ok.setEnabled(False)
        self.note.setText(i18n.tr("Downloading the offline voice for the guide and the Manual (about 60 MB, only "
                                  "once)…"))
        self.bar.setRange(0, 0)
        self.bar.show()

        def work():
            try:
                voice_download.download(lang, lambda d, t: self._relay.progress.emit(d, t), lambda: self._cancel)
                self._relay.finished.emit("")
            except Exception as e:  # noqa: BLE001
                self._relay.finished.emit(str(e) or e.__class__.__name__)
        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, done: int, total: int):
        if total:
            self.bar.setRange(0, 1000)
            self.bar.setValue(int(done * 1000 / total))
            self.bar.setFormat(f"{done / 1e6:.0f} / {total / 1e6:.0f} MB")

    def _on_downloaded(self, error: str):
        if error and not self._cancel:
            self.bar.hide()
            self.note.setText(i18n.tr("The offline voice could not be downloaded ({0}). Dizcord starts anyway; the "
                                      "voice is downloaded later from Settings → Language.").format(error[:120]))
            self.ok.setText(i18n.tr("Continue  ▶"))
            self.ok.setEnabled(True)
            self.ok.clicked.disconnect()
            self.ok.clicked.connect(self.accept)
            return
        self.accept()

    def reject(self):
        """Closing the window keeps the selected language (the app needs one)."""
        if self.ok.isEnabled() and self.list.isEnabled():
            self._accept()
        else:
            self._cancel = True
            self.accept()


def choose_language(app_state: dict) -> tuple[str, bool]:
    """The app language: the saved one, or ask now (first start). Returns (code, asked_now)."""
    code = app_state.get("ui_language")
    if code in i18n.BY_CODE:
        return code, False
    dlg = LanguageDialog(i18n.detect_windows_language())
    dlg.exec()
    return dlg.code, True
