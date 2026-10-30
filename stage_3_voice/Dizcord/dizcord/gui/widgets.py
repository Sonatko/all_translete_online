"""Reusable widgets: level meter, language/device combos, provider settings panel."""
from __future__ import annotations

import sys
import threading

from PySide6.QtCore import QObject, QProcess, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSlider,
                               QSpinBox, QVBoxLayout, QWidget)

from .. import languages as L
from ..i18n import tr
from ..audio import devices
from ..config import app_path, portable_path
from ..providers import REGISTRY, Field, models_info
from ..providers.base import describe_downloads

DEFAULT_DEVICE = "(System default)"


class _Relay(QObject):
    done = Signal(object, object)   # result, error


class _Progress(QObject):
    progress = Signal(object, object)   # done bytes, total bytes


_pending: set = set()


def run_async(fn, on_done):
    """Run fn() in a thread, call on_done(result, error) on the GUI thread."""
    relay = _Relay()
    _pending.add(relay)  # keep alive until done

    def finish(r, e):
        _pending.discard(relay)
        on_done(r, e)
    relay.done.connect(finish)

    def work():
        try:
            res = fn()
            relay.done.emit(res, None)
        except Exception as e:  # noqa: BLE001
            relay.done.emit(None, e)
    threading.Thread(target=work, daemon=True).start()


class LevelMeter(QWidget):
    def __init__(self, colors: dict, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.db = -90.0
        self.threshold = -45.0
        self.speech = False
        self.setMinimumHeight(10)
        self.setMaximumHeight(12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_level(self, db, speech, threshold):
        self.db = 0.6 * self.db + 0.4 * db if db < self.db else db
        self.speech, self.threshold = speech, threshold
        self.update()

    def decay(self):
        self.db = max(-90.0, self.db - 3)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.colors["meter_bg"]))
        p.drawRoundedRect(r, 5, 5)
        frac = max(0.0, min(1.0, (self.db + 70) / 70))
        p.setBrush(QColor(self.colors["ok"] if self.speech else self.colors["muted"]))
        p.drawRoundedRect(r.adjusted(0, 0, -int(r.width() * (1 - frac)), 0), 5, 5)
        tx = int(r.width() * max(0.0, min(1.0, (self.threshold + 70) / 70)))
        p.setBrush(QColor(self.colors["accent"]))
        p.drawRect(tx - 1, 0, 2, r.height())


class DataCombo(QComboBox):
    """Combo whose items carry a data value; value()/setValue() use the data."""

    changed = Signal()

    def __init__(self, items=(), parent=None):
        super().__init__(parent)
        self.set_items(items)
        self.currentIndexChanged.connect(lambda _: self.changed.emit())

    def set_items(self, items):
        cur = self.value() if self.count() else None
        was_blocked = self.blockSignals(True)
        self.clear()
        for data, label in items:
            self.addItem(tr(label), data)
        if cur is not None:
            self.setValue(cur)
        self.blockSignals(was_blocked)

    def value(self):
        return self.currentData()

    def setValue(self, v):
        i = self.findData(v)
        if i >= 0:
            self.setCurrentIndex(i)


class LangCombo(DataCombo):
    def __init__(self, include_auto=False, parent=None):
        super().__init__(L.choices(include_auto), parent)
        self.setMaxVisibleItems(20)


class DeviceCombo(QComboBox):
    changed = Signal()

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumContentsLength(28)
        self.currentTextChanged.connect(lambda _: self.changed.emit())
        self.refresh()

    def refresh(self, kind: str | None = None):
        if kind:
            self.kind = kind
        cur = self.value() if self.count() else ""
        was_blocked = self.blockSignals(True)
        self.clear()
        self.addItem(tr(DEFAULT_DEVICE))
        try:
            names = devices.input_devices() if self.kind == "input" else devices.output_devices()
        except Exception:
            names = []
        self.addItems(names)
        self.setValue(cur)
        self.blockSignals(was_blocked)

    def value(self) -> str:
        t = self.currentText().strip()
        return "" if t in (DEFAULT_DEVICE, tr(DEFAULT_DEVICE)) else t

    def setValue(self, v: str):
        if not v:
            self.setCurrentIndex(0)
            return
        i = self.findText(v)
        if i < 0:
            i = next((k for k in range(self.count()) if self.itemText(k).lower().startswith(v.lower())), -1)
        if i >= 0:
            self.setCurrentIndex(i)
        else:
            self.setEditText(v)


class ModelCombo(QComboBox):
    """Editable model picker. Items show 'model-id  —  free tier · 128K ctx'; value() is just the model id."""

    SEP = "  —  "
    changed = Signal()

    def __init__(self, options=(), parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(25)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.set_models([(str(o), "") for o in options])
        self.currentTextChanged.connect(lambda _: self.changed.emit())

    def set_models(self, items):
        """items: [(model_id, suffix)] - keeps the current value."""
        cur = self.value() if self.count() or self.currentText() else ""
        was_blocked = self.blockSignals(True)
        self.clear()
        for mid, suffix in items:
            self.addItem(f"{mid}{self.SEP}{suffix}" if suffix else mid, mid)
        self.setValue(cur)
        self.blockSignals(was_blocked)

    def value(self) -> str:
        return self.currentText().split(self.SEP)[0].strip()

    def setValue(self, v):
        v = str(v or "")
        i = self.findData(v)
        if i >= 0:
            self.setCurrentIndex(i)
        else:
            self.setEditText(v)


class VolumeSlider(QWidget):
    changed = Signal()

    def __init__(self, maximum=2.0, parent=None, minimum=0.0):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(minimum * 100), int(maximum * 100))
        self.label = QLabel("100%")
        self.label.setMinimumWidth(42)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.label)
        self.slider.valueChanged.connect(self._on)

    def _on(self, v):
        self.label.setText(f"{v}%")
        self.changed.emit()

    def value(self) -> float:
        return self.slider.value() / 100.0

    def setValue(self, v: float):
        self.slider.setValue(int(round(float(v) * 100)))


# ------------------------------------------------------------------ generic value access

def widget_value(w):
    if hasattr(w, "value") and isinstance(w, (DataCombo, DeviceCombo, VolumeSlider, ModelCombo)):
        return w.value()
    if isinstance(w, QCheckBox):
        return w.isChecked()
    if isinstance(w, (QSpinBox, QDoubleSpinBox)):
        return w.value()
    if isinstance(w, QLineEdit):
        return w.text()
    if isinstance(w, QPlainTextEdit):
        return w.toPlainText()
    if isinstance(w, QComboBox):
        return w.currentText()
    raise TypeError(type(w))


def set_widget_value(w, v):
    was_blocked = w.blockSignals(True)
    try:
        if isinstance(w, (DataCombo, DeviceCombo, VolumeSlider, ModelCombo)):
            w.setValue(v)
        elif isinstance(w, QCheckBox):
            w.setChecked(bool(v))
        elif isinstance(w, QSpinBox):
            w.setValue(int(v))
        elif isinstance(w, QDoubleSpinBox):
            w.setValue(float(v))
        elif isinstance(w, QLineEdit):
            w.setText(str(v))
        elif isinstance(w, QPlainTextEdit):
            w.setPlainText(str(v))
        elif isinstance(w, QComboBox):
            i = w.findText(str(v))
            if i >= 0:
                w.setCurrentIndex(i)
            else:
                w.setEditText(str(v))
    finally:
        w.blockSignals(was_blocked)
    if isinstance(w, VolumeSlider):
        w.label.setText(f"{int(round(float(v) * 100))}%")


def change_signal(w):
    if isinstance(w, (DataCombo, DeviceCombo, VolumeSlider, ModelCombo)):
        return w.changed
    if isinstance(w, QCheckBox):
        return w.toggled
    if isinstance(w, (QSpinBox, QDoubleSpinBox)):
        return w.valueChanged
    if isinstance(w, QLineEdit):
        return w.editingFinished
    if isinstance(w, QPlainTextEdit):
        return w.textChanged
    if isinstance(w, QComboBox):
        return w.currentTextChanged
    raise TypeError(type(w))


# ------------------------------------------------------------------ provider settings

def make_field_widget(f: Field, keys):
    if f.kind == "secret":
        w = QLineEdit()
        w.setEchoMode(QLineEdit.Password)
        w.setPlaceholderText("paste key here (saved locally in data/keys.json)")
        w.setText(keys.stored(f.key_ref))
        return w
    if f.kind == "bool":
        return QCheckBox()
    if f.kind == "int":
        w = QSpinBox()
        w.setRange(int(f.min), int(f.max))
        w.setSingleStep(int(f.step) or 1)
        return w
    if f.kind == "float":
        w = QDoubleSpinBox()
        w.setRange(f.min, f.max)
        w.setSingleStep(f.step if f.step != 1 else 0.1)
        w.setDecimals(2)
        return w
    if f.kind == "choice":
        return DataCombo([(o, o) for o in f.options])
    if f.kind == "model":
        return ModelCombo(f.options)
    if f.kind == "combo":
        w = QComboBox()
        w.setEditable(True)
        w.addItems([str(o) for o in f.options])
        return w
    if f.kind == "text":
        w = QPlainTextEdit()
        w.setMaximumHeight(70)
        return w
    return QLineEdit()


class ProviderPanel(QWidget):
    """Provider picker + auto-generated settings form for one provider kind."""

    changed = Signal()
    log = Signal(str)
    downloaded = Signal()           # model / voice files were downloaded

    def __init__(self, kind: str, keys, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.keys = keys
        self.settings_by_provider: dict[str, dict] = {}
        self.field_widgets: dict[str, tuple[Field, QWidget]] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        top = QFormLayout()
        items = sorted(((pid, cls.label()) for pid, cls in REGISTRY[kind].items()),
                       key=lambda x: (REGISTRY[kind][x[0]].local, x[1].lower()))
        self.combo = DataCombo(items)
        top.addRow("Engine", self.combo)
        lay.addLayout(top)
        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setObjectName("muted")
        lay.addWidget(self.desc)
        self.req_row = QWidget()
        rl = QHBoxLayout(self.req_row)
        rl.setContentsMargins(0, 0, 0, 0)
        self.req_label = QLabel()
        self.req_label.setObjectName("warn")
        self.req_label.setWordWrap(True)
        self.install_btn = QPushButton("Install now")
        self.install_btn.clicked.connect(self._install)
        rl.addWidget(self.req_label, 1)
        rl.addWidget(self.install_btn)
        lay.addWidget(self.req_row)
        self.dl_row = QWidget()             # model / voice files the engine still has to download
        dl = QHBoxLayout(self.dl_row)
        dl.setContentsMargins(0, 0, 0, 0)
        self.dl_label = QLabel()
        self.dl_label.setObjectName("warn")
        self.dl_label.setWordWrap(True)
        self.dl_btn = QPushButton("Download")
        self.dl_btn.clicked.connect(self.start_download)
        dl.addWidget(self.dl_label, 1)
        dl.addWidget(self.dl_btn)
        lay.addWidget(self.dl_row)
        self.dl_row.hide()
        self.form_host = QWidget()
        self.form = QFormLayout(self.form_host)
        self.form.setContentsMargins(0, 6, 0, 0)
        lay.addWidget(self.form_host)
        self.current = None
        self.combo.changed.connect(self._on_provider_changed)
        self._proc = None
        self.langs = lambda: []             # languages the voices speak (set by the main window)
        self._dl_busy = False
        self._dl_asked: set = set()
        self._dl_relay = _Progress()
        self._dl_relay.progress.connect(self._dl_progress)
        self._dl_timer = QTimer(self, singleShot=True, interval=700)
        self._dl_timer.timeout.connect(lambda: self.check_downloads(ask=True))

    # --- state
    def set_state(self, provider_id: str, settings_by_provider: dict):
        self.settings_by_provider = {k: dict(v) for k, v in (settings_by_provider or {}).items()}
        self.combo.blockSignals(True)
        self.combo.setValue(provider_id)
        self.combo.blockSignals(False)
        self._build(self.combo.value())

    def state(self) -> tuple[str, dict]:
        self._store_current()
        return self.combo.value(), {k: dict(v) for k, v in self.settings_by_provider.items()}

    def _store_current(self):
        if not self.current:
            return
        vals = {}
        for key, (f, w) in self.field_widgets.items():
            if f.kind == "secret":
                continue
            vals[key] = portable_path(widget_value(w)) if f.kind == "path" else widget_value(w)
        self.settings_by_provider[self.current] = vals

    def _on_provider_changed(self):
        self._store_current()
        self._build(self.combo.value(), ask=True)
        self.changed.emit()

    def _build(self, pid, ask=False):
        self._build_form(pid)
        self.check_downloads(ask)

    def _build_form(self, pid):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.field_widgets.clear()
        self.model_cls = None
        self.current = pid
        cls = REGISTRY[self.kind].get(pid)
        if cls is None:
            return
        self.desc.setText(cls.description)
        missing = cls.missing_requirements()
        self.req_row.setVisible(bool(missing))
        if missing:
            self.req_label.setText(f"Needs extra package(s): {', '.join(missing)}  ({cls.pip_hint})")
        saved = self.settings_by_provider.get(pid, {})
        for f in cls.fields:
            w = make_field_widget(f, self.keys)
            if f.kind == "path":
                set_widget_value(w, str(app_path(saved.get(f.key, f.default), f.default)))
            elif f.kind != "secret":
                set_widget_value(w, saved.get(f.key, f.default))
            if f.kind != "secret":
                change_signal(w).connect(self.changed.emit)
                if cls.has_downloads:
                    change_signal(w).connect(self._dl_timer.start)    # e.g. another Whisper model: download it?
            else:
                w.editingFinished.connect(lambda w=w, ref=f.key_ref: self._save_key(ref, w.text()))
            if f.help:
                w.setToolTip(f.help)
            row = w
            if f.kind == "model" and hasattr(cls, "list_models"):
                row = self._model_row(cls, w)
            if f.kind == "path":
                row = QWidget()
                hl = QHBoxLayout(row)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.addWidget(w, 1)
                b = QPushButton("…")
                b.setFixedWidth(30)
                b.clicked.connect(lambda _=False, w=w: self._browse(w))
                hl.addWidget(b)
            label = QLabel(f.label)
            if f.help:
                label.setToolTip(f.help)
            self.form.addRow(label, row)
            self.field_widgets[f.key] = (f, w)

    # --- model list (AI models): scan the provider's API, show free/paid, price, context and rate limits
    def _model_row(self, cls, combo: "ModelCombo") -> QWidget:
        self.model_combo, self.model_cls = combo, cls
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(combo, 1)
        self.model_refresh_btn = QPushButton("⟳")
        self.model_refresh_btn.setFixedWidth(34)
        self.model_refresh_btn.setToolTip("Refresh the model list from the provider (free/paid, prices, context)")
        self.model_refresh_btn.clicked.connect(lambda: self.refresh_models())
        self.model_limits_btn = QPushButton("Check limits")
        self.model_limits_btn.setToolTip("Send one tiny request (a few tokens) to read your rate limits for "
                                         "this model")
        self.model_limits_btn.clicked.connect(self.check_limits)
        h.addWidget(self.model_refresh_btn)
        h.addWidget(self.model_limits_btn)
        v.addLayout(h)
        self.model_info = QLabel()
        self.model_info.setObjectName("muted")
        self.model_info.setWordWrap(True)
        self.model_info.setTextFormat(Qt.RichText)
        v.addWidget(self.model_info)
        combo.changed.connect(self._update_model_info)
        self._fill_models_from_cache()
        if models_info.is_stale(cls.id) and self._can_list(cls):
            QTimer.singleShot(0, lambda: self.refresh_models(quiet=True))   # after the form is complete
        return box

    def _can_list(self, cls) -> bool:
        if cls.missing_requirements():
            return False
        if getattr(cls, "local", False) or getattr(cls, "key_optional", False) \
                or not getattr(cls, "list_needs_key", True):
            return True
        ref = next((f.key_ref for f in cls.fields if f.kind == "secret"), "")
        return bool(ref and self.keys.get(ref))

    def _fill_models_from_cache(self):
        cls = getattr(self, "model_cls", None)
        if cls is None:
            return
        items = models_info.models(cls.id)
        if items:
            ids = {m.id for m in items}
            opts = next((f.options for f in cls.fields if f.key == "model"), [])
            extra = [(o, "") for o in opts if o not in ids]
            self.model_combo.set_models(
                [(m.id, "⛔ blocked" if models_info.blocked(cls.id, m.id) else m.short()) for m in items] + extra)
        self._update_model_info()

    def _update_model_info(self, status: str = ""):
        cls = getattr(self, "model_cls", None)
        if cls is None or not hasattr(self, "model_info"):
            return
        text = models_info.describe(cls.id, self.model_combo.value(), getattr(cls, "limits_note", ""))
        n = len(models_info.models(cls.id))
        if status:
            text = status + ("<br>" + text if text else "")
        elif n:
            text += ("<br>" if text else "") + f"<i>{n} models available - ⟳ to refresh</i>"
        self.model_info.setText(text)

    def _provider_instance(self):
        self._store_current()
        cls = REGISTRY[self.kind][self.current]
        return cls(self.settings_by_provider.get(self.current, {}), self.keys)

    def refresh_models(self, quiet: bool = False):
        """Re-scan the model list of the selected provider (in the background)."""
        cls = getattr(self, "model_cls", None)
        if cls is None or self.current != cls.id:
            return
        if not self._can_list(cls):
            if not quiet:
                self._update_model_info("⚠ Add the API key first.")
            return
        pid = cls.id
        self.model_refresh_btn.setEnabled(False)
        self._update_model_info("Scanning models…")
        prov = self._provider_instance()

        def done(items, err):
            if getattr(self, "model_cls", None) is None or self.current != pid:
                return   # provider changed meanwhile (widgets rebuilt)
            self.model_refresh_btn.setEnabled(True)
            if err:
                self._update_model_info(f"⚠ {err}")
                if not quiet:
                    self.log.emit(f"Model list: {err}")
                return
            models_info.save_models(pid, items)
            self._fill_models_from_cache()
            free = sum(1 for m in items if m.free in ("free", "free tier", "local"))
            self.log.emit(f"{cls.name}: {len(items)} models ({free} free).")
        run_async(prov.list_models, done)

    def check_limits(self):
        cls = getattr(self, "model_cls", None)
        if cls is None:
            return
        pid = cls.id
        self.model_limits_btn.setEnabled(False)
        self._update_model_info("Checking limits (one tiny request)…")
        prov = self._provider_instance()

        def done(_r, err):
            if getattr(self, "model_cls", None) is None or self.current != pid:
                return
            self.model_limits_btn.setEnabled(True)
            if err:
                self._fill_models_from_cache()   # may now show the model as blocked
                self._update_model_info(f"⚠ {err}")
            elif not models_info.limits(pid, self.model_combo.value()):
                self._update_model_info("This service doesn't report its limits in its responses.")
            else:
                self._update_model_info()
        run_async(prov.check_limits, done)

    def _save_key(self, ref, value):
        if value.strip() != self.keys.stored(ref):
            self.keys.set(ref, value.strip())
            self.keys.save()
            self.log.emit(f"Saved API key '{ref}'.")
            if value.strip():
                self.refresh_models(quiet=True)

    def keys_changed(self):
        """Called after keys were saved elsewhere (API Keys tab): refresh the secret fields and the models."""
        for f, w in self.field_widgets.values():
            if f.kind == "secret":
                w.setText(self.keys.stored(f.key_ref))
        self.refresh_models(quiet=True)

    def _browse(self, w):
        path, _ = QFileDialog.getOpenFileName(self, "Choose file", w.text())
        if not path:
            path = QFileDialog.getExistingDirectory(self, "Choose folder", w.text())
        if path:
            w.setText(path)
            self.changed.emit()

    def _install(self):
        cls = REGISTRY[self.kind].get(self.current)
        if cls is None or not cls.pip_hint.startswith("pip install"):
            return
        pkgs = cls.pip_hint.split("pip install", 1)[1].split()
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Installing…")
        self.log.emit(f"Installing {' '.join(pkgs)} … (this can take a few minutes)")
        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.MergedChannels)
        self._proc.readyReadStandardOutput.connect(
            lambda: self.log.emit(bytes(self._proc.readAllStandardOutput()).decode(errors="replace").rstrip()))
        self._proc.finished.connect(self._installed)
        self._proc.start(sys.executable, ["-m", "pip", "install", "--no-warn-script-location",
                                          "--no-build-isolation", *pkgs])   # isolation can't work: tools/setup.ps1

    def _installed(self, code, _status):
        self.install_btn.setEnabled(True)
        self.install_btn.setText("Install now")
        import importlib
        importlib.invalidate_caches()
        self.log.emit("Install finished." if code == 0 else f"Install failed (exit code {code}).")
        self._store_current()
        self._build(self.current, ask=True)

    # --- model / voice files of local engines (Whisper models, Piper voices, Kokoro), downloaded into the app folder
    def check_downloads(self, ask: bool = False):
        """Show what the selected engine still has to download; ask=True (the user just chose it) also offers to
        download it now - once per engine and list of files."""
        cls = REGISTRY[self.kind].get(self.current)
        if cls is None or not cls.has_downloads or cls.missing_requirements():
            self.dl_row.hide()
            return
        if self._dl_busy:
            return
        prov, langs, pid = self._provider_instance(), list(self.langs()), self.current

        def done(need, err):
            if self.current != pid or self._dl_busy:
                return
            if err:
                self.dl_label.setText(f"⚠ Could not check the files to download: {err}")
                self.dl_btn.setText("Download")
                self.dl_btn.setEnabled(True)
                self.dl_row.show()
                return
            if not need:
                self.dl_row.hide()
                return
            what = describe_downloads(need)
            self.dl_label.setText(f"Needs to download {what} into {prov.download_dir()}")
            self.dl_btn.setText("Download")
            self.dl_btn.setEnabled(True)
            self.dl_row.show()
            key = (pid, tuple(sorted(w for w, _s in need)))
            if ask and key not in self._dl_asked and self.isVisible():
                self._dl_asked.add(key)
                if QMessageBox.question(self, "Download", f"{cls.name} needs {what}.\n\nDownload now into the app "
                                        f"folder ({prov.download_dir()})? It is downloaded once and then works "
                                        "without internet.") == QMessageBox.Yes:
                    self.start_download()
        run_async(lambda: prov.downloads_needed(langs), done)

    def start_download(self):
        cls = REGISTRY[self.kind].get(self.current)
        if cls is None or self._dl_busy:
            return
        prov, langs, pid = self._provider_instance(), list(self.langs()), self.current
        self._dl_busy = True
        self.dl_btn.setEnabled(False)
        self.dl_btn.setText("Downloading…")
        self.dl_label.setText("Downloading… (this can take a few minutes)")
        self.log.emit(f"{cls.name}: downloading into {prov.download_dir()}…")
        relay = self._dl_relay

        def done(_r, err):
            self._dl_busy = False
            if err:
                self.log.emit(f"{cls.name}: download failed: {err}")
                self.dl_label.setText(f"⚠ Download failed: {err}")
                self.dl_btn.setText("Try again")
                self.dl_btn.setEnabled(True)
                return
            self.log.emit(f"{cls.name}: download finished.")
            if self.current == pid:
                self.check_downloads()
            self.downloaded.emit()
        run_async(lambda: prov.download(langs, progress=lambda d, t: relay.progress.emit(d, t)), done)

    def _dl_progress(self, done, total):
        if self._dl_busy:
            self.dl_label.setText(f"Downloading… {done / 1e6:,.0f} of {total / 1e6:,.0f} MB" if total
                                  else f"Downloading… {done / 1e6:,.0f} MB")
