"""'Settings' tab: how the app looks (theme, fonts, text sizes of the app and of the translations),
all hotkeys in one place, window options and folders. Appearance is app-wide (data/app_state.json),
hotkeys and subtitle options belong to the profile like everywhere else."""
from __future__ import annotations

import subprocess
import sys

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFontComboBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
                               QWidget)

from .. import APP_NAME, __version__, config, i18n, voice_download
from ..edition import PUBLIC, UPDATE_REPO
from .widgets import DataCombo, DeviceCombo, VolumeSlider, run_async

APPEARANCE_DEFAULTS = {
    "font_pt": 10.0,          # the app's text
    "font_family": "",        # "" = Windows default
    "inline_scale": 100,      # translations inside Discord, % of Discord's text size
    "inline_family": "",      # "" = like Discord (gg sans / Segoe UI)
    "chat_pt": 10.0,          # small chat window
    "popup_pt": 11.5,         # highlight-to-translate / OCR popup
    "always_on_top": False,   # keep the Dizcord window above other windows
}


def _muted(text):
    lb = QLabel(text)
    lb.setWordWrap(True)
    lb.setObjectName("muted")
    return lb


class _FontPicker(QWidget):
    """Font list + 'Default' button; value '' means the default font."""

    def __init__(self, value: str, on_change):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        self.combo = QFontComboBox()
        self.default = QPushButton("Default")
        self.default.setCheckable(True)
        h.addWidget(self.combo, 1)
        h.addWidget(self.default)
        self._on_change = on_change
        self.set(value)
        self.combo.currentFontChanged.connect(lambda _f: self._changed(False))
        self.default.toggled.connect(lambda on: self._changed(on))

    def set(self, value: str):
        for w in (self.combo, self.default):
            w.blockSignals(True)
        self.default.setChecked(not value)
        self.combo.setEnabled(bool(value))
        self.combo.setCurrentFont(QFont(value) if value else QApplication.font())
        for w in (self.combo, self.default):
            w.blockSignals(False)

    def value(self) -> str:
        return "" if self.default.isChecked() else self.combo.currentFont().family()

    def _changed(self, default_clicked: bool):
        if not default_clicked and self.default.isChecked() and self.sender() is self.combo:
            self.default.blockSignals(True)
            self.default.setChecked(False)
            self.default.blockSignals(False)
        self.combo.setEnabled(not self.default.isChecked())
        self._on_change()


class SettingsTabMixin:
    """Mixed into MainWindow. Needs: bind, state, app, theme_name, toggle_theme, popup, chat_overlay, inline,
    overlay, setStatus."""

    @property
    def appearance(self) -> dict:
        a = dict(APPEARANCE_DEFAULTS)
        a.update(self.state.get("appearance") or {})
        return a

    def _build_settings_tab(self):
        a = self.appearance
        w = QWidget()
        v = QVBoxLayout(w)

        # ---------------------------------------------------------- app look
        box = QGroupBox("App")
        f = QFormLayout(box)
        self.set_language = DataCombo([(lang.code, lang.name) for lang in i18n.LANGUAGES])
        self.set_language.setValue(i18n.current().code)
        self.set_language.changed.connect(self._language_changed)
        f.addRow("Language", self.set_language)
        self.set_theme = DataCombo([("dark", "Dark"), ("light", "Light")])
        self.set_theme.setValue(self.theme_name)
        self.set_theme.changed.connect(lambda: self.set_theme.value() != self.theme_name and self.toggle_theme())
        f.addRow("Theme", self.set_theme)
        self.set_font = _FontPicker(a["font_family"], self._appearance_changed)
        f.addRow("Font", self.set_font)
        self.set_font_pt = QDoubleSpinBox()
        self.set_font_pt.setRange(8, 16)
        self.set_font_pt.setSingleStep(0.5)
        self.set_font_pt.setSuffix(" pt")
        self.set_font_pt.setValue(a["font_pt"])
        self.set_font_pt.valueChanged.connect(self._appearance_changed)
        f.addRow("Text size", self.set_font_pt)
        self.set_on_top = QCheckBox("Keep the Dizcord window above other windows")
        self.set_on_top.setChecked(bool(a["always_on_top"]))
        self.set_on_top.toggled.connect(self._appearance_changed)
        f.addRow(self.set_on_top)
        f.addRow(self.bind(QCheckBox("Save changes automatically (the profile is saved ~1 s after every change)"),
                           "ui.autosave_settings"))
        v.addWidget(box)

        v.addWidget(self._build_devices_box())

        # ---------------------------------------------------------- translations look
        box = QGroupBox("Translations")
        f = QFormLayout(box)
        self.set_inline_scale = QSpinBox()
        self.set_inline_scale.setRange(60, 180)
        self.set_inline_scale.setSingleStep(5)
        self.set_inline_scale.setSuffix(" % of Discord's text")
        self.set_inline_scale.setValue(int(a["inline_scale"]))
        self.set_inline_scale.valueChanged.connect(self._appearance_changed)
        f.addRow("Inside Discord - size", self.set_inline_scale)
        self.set_inline_font = _FontPicker(a["inline_family"], self._appearance_changed)
        self.set_inline_font.default.setText("Like Discord")
        f.addRow("Inside Discord - font", self.set_inline_font)
        self.set_chat_pt = QDoubleSpinBox()
        self.set_chat_pt.setRange(7, 24)
        self.set_chat_pt.setSingleStep(0.5)
        self.set_chat_pt.setSuffix(" pt")
        self.set_chat_pt.setValue(a["chat_pt"])
        self.set_chat_pt.valueChanged.connect(self._appearance_changed)
        f.addRow("Small chat window - size", self.set_chat_pt)
        self.set_popup_pt = QDoubleSpinBox()
        self.set_popup_pt.setRange(8, 28)
        self.set_popup_pt.setSingleStep(0.5)
        self.set_popup_pt.setSuffix(" pt")
        self.set_popup_pt.setValue(a["popup_pt"])
        self.set_popup_pt.valueChanged.connect(self._appearance_changed)
        f.addRow("Highlight / OCR popup - size", self.set_popup_pt)
        fs = QSpinBox()
        fs.setRange(10, 72)
        fs.setSuffix(" px")
        f.addRow("Voice subtitles - size", self.bind(fs, "ui.subtitle_font_size"))
        f.addRow("Voice subtitles - background", self.bind(VolumeSlider(1.0), "ui.subtitle_opacity"))
        f.addRow(self.bind(QCheckBox("Show the original text under voice subtitles"), "ui.subtitle_show_original"))
        v.addWidget(box)

        # ---------------------------------------------------------- hotkeys
        box = QGroupBox("Hotkeys (work everywhere)")
        f = QFormLayout(box)
        for label, path, eg in [("Translate highlighted text", "chat.hotkey_selection", "ctrl+alt+t"),
                                ("Translate what I typed in Discord", "chat.hotkey_draft", "ctrl+alt+y"),
                                ("Translate text on screen (OCR)", "chat.hotkey_ocr", "ctrl+alt+o"),
                                ("Show originals / translations in Discord", "chat.hotkey_inline", "ctrl+alt+i"),
                                ("Push-to-talk (voice translator)", "input.ptt_key", "f8"),
                                ("Hear the people in the call on / off", "input.hear_key", "f9")]:
            e = self.bind(QLineEdit(), path)
            e.setPlaceholderText(f"e.g. {eg} - empty = off")
            f.addRow(label, e)
        f.addRow(_muted("Write keys like ctrl+alt+t, f8, caps lock. Hotkeys don't work while a game running as "
                        "administrator is in front, unless Dizcord is also run as administrator."))
        v.addWidget(box)

        if PUBLIC:
            v.addWidget(self._build_updates_box())

        # ---------------------------------------------------------- windows & folders
        box = QGroupBox("Windows && folders")
        bl = QVBoxLayout(box)
        row = QHBoxLayout()
        reset = QPushButton("Reset window positions")
        reset.setToolTip("Put the subtitles and the small chat window back in their default places")
        reset.clicked.connect(self._reset_windows)
        row.addWidget(reset)
        for text, path in [("Open app folder", config.ROOT), ("Open data folder", config.DATA_DIR),
                           ("Open logs", config.LOGS_DIR)]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))))
            row.addWidget(b)
        row.addStretch(1)
        bl.addLayout(row)
        bl.addWidget(_muted(f"{APP_NAME} {__version__} - settings in this box and the look of the app are saved "
                            "for the whole app; everything else belongs to the current profile."))
        v.addWidget(box)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ sound devices (same settings as Input/Output)
    def _build_devices_box(self):
        box = QGroupBox("Sound devices")
        f = QFormLayout(box)
        self.set_listen_dev = DeviceCombo(self.listen_device.kind)
        self.set_listen_dev.setToolTip("Loopback: the headphones/speakers Discord plays to (Input tab → Method)")
        self.set_listen_dev.changed.connect(self._settings_listen_changed)
        f.addRow("Hear other people from", self.set_listen_dev)
        self.listen_device.changed.connect(self._sync_settings_listen)
        f.addRow("My microphone", self.bind(DeviceCombo("input"), "input.mic_device"))
        f.addRow("Play translations on", self.bind(DeviceCombo("output"), "incoming.output_device"))
        f.addRow("Send my translated voice to (virtual cable)",
                 self.bind(DeviceCombo("output"), "outgoing.output_device"))
        row = QHBoxLayout()
        b = QPushButton("Refresh device lists")
        b.clicked.connect(self.refresh_devices)
        row.addWidget(b)
        row.addStretch(1)
        f.addRow(row)
        f.addRow(_muted("The same settings as in the Input and Output tabs. Device changes apply after Stop → Start."))
        return box

    def _settings_listen_changed(self):
        if self._loading:
            return
        self.listen_device.blockSignals(True)
        self.listen_device.setValue(self.set_listen_dev.value())
        self.listen_device.blockSignals(False)
        self.on_change()

    def _sync_settings_listen(self, *_):
        """Keep the Settings copy of 'what the app listens to' equal to the Input tab."""
        if not hasattr(self, "set_listen_dev"):
            return
        self.set_listen_dev.blockSignals(True)
        if self.set_listen_dev.kind != self.listen_device.kind:
            self.set_listen_dev.refresh(self.listen_device.kind)
        self.set_listen_dev.setValue(self.listen_device.value())
        self.set_listen_dev.setEnabled(self.listen_device.isEnabled())
        self.set_listen_dev.blockSignals(False)

    # ------------------------------------------------------------------ language of the app
    def _language_changed(self):
        lang = i18n.BY_CODE.get(self.set_language.value())
        if not lang or lang.code == self.state.get("ui_language"):
            return
        self.state["ui_language"] = lang.code
        try:
            config.save_app_state(self.state)
        except Exception:  # noqa: BLE001
            pass

        def ask_restart(_r=None, err=None):
            if err:
                self.setStatus(f"⚠ Could not download the offline voice: {err}", error=True)
            if QMessageBox.question(self, lang.name, "The new language is used after a restart. Restart Dizcord "
                                    "now?") == QMessageBox.Yes:
                self._restart_app()
        if lang.voice_installed():
            ask_restart()
        else:
            self.setStatus(f"Downloading the offline voice for {lang.name} (about 60 MB)…")
            run_async(lambda: voice_download.download(lang), ask_restart)

    # ------------------------------------------------------------------ updates (public edition)
    def _build_updates_box(self):
        box = QGroupBox("Updates")
        bl = QVBoxLayout(box)
        row = QHBoxLayout()
        self.upd_check_btn = QPushButton("⟳ Check for updates")
        self.upd_check_btn.setEnabled(bool(UPDATE_REPO))
        self.upd_check_btn.clicked.connect(lambda: self._upd_check(quiet=False))
        self.upd_apply_btn = QPushButton("⬇ Update now")
        self.upd_apply_btn.setObjectName("primary")
        self.upd_apply_btn.setVisible(False)
        self.upd_apply_btn.clicked.connect(self._upd_apply)
        row.addWidget(self.upd_check_btn)
        row.addWidget(self.upd_apply_btn)
        self.upd_label = QLabel(f"You have version {__version__}." if UPDATE_REPO else
                                f"You have version {__version__}. No update source is set in this copy.")
        self.upd_label.setWordWrap(True)
        row.addWidget(self.upd_label, 1)
        bl.addLayout(row)
        bl.addWidget(_muted("Downloads the newest release from GitHub and replaces the program files. Your "
                            "settings, profiles, API keys and downloaded models are never touched."))
        self._upd_release = None
        if UPDATE_REPO:
            QTimer.singleShot(5000, lambda: self._upd_check(quiet=True))     # silent look at start-up
        return box

    def _upd_check(self, quiet: bool):
        from .. import updater
        self.upd_check_btn.setEnabled(False)
        if not quiet:
            self.upd_label.setText("Checking…")

        def done(rel, err):
            self.upd_check_btn.setEnabled(bool(UPDATE_REPO))
            if err:
                if not quiet:
                    self.upd_label.setText(f"⚠ Could not check: {err}")
                return
            self._upd_release = rel
            if rel.newer:
                self.upd_label.setText(f"⬆ New version {rel.tag} is available (you have {__version__})."
                                       + (f"\n{rel.notes.strip()[:300]}" if rel.notes.strip() else ""))
                self.upd_apply_btn.setText(f"⬇ Update to {rel.tag}")
                self.upd_apply_btn.setVisible(True)
                self.setStatus(f"New version {rel.tag} available - Settings → Updates.")
            else:
                self.upd_apply_btn.setVisible(False)
                if not quiet:
                    self.upd_label.setText(f"✔ You have the latest version ({__version__}).")
        run_async(updater.check, done)

    def _upd_apply(self):
        from .. import updater
        rel = self._upd_release
        if not rel or not rel.newer:
            return
        if QMessageBox.question(self, "Update", f"Download and install {rel.tag}?\nYour settings, keys and models "
                                "are kept. Dizcord will need a restart.") != QMessageBox.Yes:
            return
        self.upd_apply_btn.setEnabled(False)
        self.upd_check_btn.setEnabled(False)
        self.upd_label.setText(f"Downloading {rel.tag}…")

        def done(res, err):
            self.upd_apply_btn.setEnabled(True)
            self.upd_check_btn.setEnabled(True)
            if err:
                self.upd_label.setText(f"⚠ Update failed (nothing was changed or only partly): {err}")
                return
            self.upd_apply_btn.setVisible(False)
            extra = ""
            if res.skipped:
                extra += (f"\n{len(res.skipped)} file(s) were in use and will update on the next start: "
                          + ", ".join(res.skipped[:4]))
            if res.pip_error:
                extra += f"\n⚠ Packages could not be updated automatically - run setup.bat. ({res.pip_error[:120]})"
            self.upd_label.setText(f"✔ Updated to {rel.tag} ({res.files} files). Restart Dizcord to use it." + extra)
            if QMessageBox.question(self, "Updated", f"Updated to {rel.tag}. Restart Dizcord now?") == QMessageBox.Yes:
                self._restart_app()
        run_async(lambda: updater.apply(rel), done)

    def _restart_app(self):
        try:
            self.save_profile(quiet=True)
        except Exception:  # noqa: BLE001
            pass
        subprocess.Popen([sys.executable, str(config.ROOT / "main.py")], cwd=str(config.ROOT))
        QApplication.quit()

    # ------------------------------------------------------------------ apply
    def _appearance_changed(self, *_):
        a = {"font_pt": self.set_font_pt.value(), "font_family": self.set_font.value(),
             "inline_scale": self.set_inline_scale.value(), "inline_family": self.set_inline_font.value(),
             "chat_pt": self.set_chat_pt.value(), "popup_pt": self.set_popup_pt.value(),
             "always_on_top": self.set_on_top.isChecked()}
        on_top_changed = bool(a["always_on_top"]) != bool(self.appearance["always_on_top"])
        self.state["appearance"] = a
        self.apply_appearance(on_top_changed)
        try:
            config.save_app_state(self.state)
        except Exception:
            pass

    def apply_appearance(self, on_top_changed: bool = False):
        """Push the app-wide look to the theme and every translation window."""
        a = self.appearance
        self.colors = self._apply_theme()
        self.popup.font_pt = float(a["popup_pt"])
        self.ocr_box.font_pt = float(a["popup_pt"])
        self.chat_overlay.font_pt = float(a["chat_pt"])
        self.chat_overlay._render()
        self.inline.scale = int(a["inline_scale"]) / 100
        self.inline.family = a["inline_family"]
        self.inline.update()
        if on_top_changed:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(a["always_on_top"]))
            self.show()

    def _reset_windows(self):
        self.chat_overlay.moved_by_user = False
        scr = self.app.primaryScreen().availableGeometry()
        self.overlay.move(scr.center().x() - self.overlay.width() // 2, scr.bottom() - 220)
        self.chat_overlay.move(scr.right() - self.chat_overlay.width() - 40, scr.bottom() - self.chat_overlay.height()
                               - 60)
        for k in ("overlay_geometry", "chat_overlay_geometry", "chat_overlay_moved"):
            self.state.pop(k, None)
        self.setStatus("Window positions reset.")
