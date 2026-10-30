"""Main application window."""
from __future__ import annotations

import copy
import datetime as dt
import html
import logging
import os
import time

import numpy as np
from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                               QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox, QTabWidget,
                               QTextBrowser, QToolButton, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__, config
from .. import languages as L
from ..i18n import no_translate
from ..audio import devices
from ..engine import Engine
from ..providers import REGISTRY
from ..speech import NAME_STYLES
from . import theme
from ..edition import PUBLIC
from .manual_tab import ManualTabMixin
from .dashboard import DashboardMixin
from .settings_tab import SettingsTabMixin
from .overlay import SubtitleOverlay
from .text_tab import TextTabMixin
from .tour import TourMixin
from .widgets import (DataCombo, DeviceCombo, LangCombo, LevelMeter, ProviderPanel, VolumeSlider, change_signal,
                      run_async, set_widget_value, widget_value)

log = logging.getLogger("dizcord.gui")


class Bridge(QObject):
    event = Signal(object)


class QtLogHandler(logging.Handler):
    def __init__(self, bridge: Bridge):
        super().__init__(logging.INFO)
        self.bridge = bridge
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record):
        try:
            self.bridge.event.emit({"type": "log", "text": self.format(record)})
        except Exception:
            pass


def get_path(d: dict, path: str):
    for k in path.split("."):
        d = d[k]
    return d


def set_path(d: dict, path: str, value):
    keys = path.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def scroll(widget: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(widget)
    return sa


def hint(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setWordWrap(True)
    lb.setObjectName("muted")
    lb.setOpenExternalLinks(True)
    return lb


STAGES = {None: "idle", "stt": "recognizing…", "translate": "translating…", "tts": "speaking…"}


class MainWindow(DashboardMixin, SettingsTabMixin, ManualTabMixin, TextTabMixin, TourMixin, QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.state = config.load_app_state()
        config.ensure_starter_profiles()
        self.keys = config.KeyStore()
        self.theme_name = self.state.get("theme", "dark")
        self.colors = self._apply_theme()

        self.bridge = Bridge()
        self.bridge.event.connect(self.on_event)
        logging.getLogger().addHandler(QtLogHandler(self.bridge))

        names = config.list_profiles()
        name = self.state.get("last_profile")
        if name not in names:
            free = config.TEMPLATES[0][0]
            name = free if free in names else (names[0] if names else "Default")
        self.profile = config.load_profile(name)
        self.engine = Engine(copy.deepcopy(self.profile), self.keys, self.bridge.event.emit)

        self.bindings: list[tuple[QWidget, str]] = []
        self._loading = False
        self.dirty = False
        self.lines: list[dict] = []
        self.transcript_file = None
        self.overlay = SubtitleOverlay(self.colors, self.profile["ui"])
        if self.state.get("overlay_geometry"):
            x, y, w, h = self.state["overlay_geometry"]
            self.overlay.setGeometry(x, y, w, h)
        else:
            scr = app.primaryScreen().availableGeometry()
            self.overlay.move(scr.center().x() - 450, scr.bottom() - 220)

        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.setMinimumSize(860, 560)
        avail = app.primaryScreen().availableGeometry()
        self.resize(min(1360, avail.width() - 40), min(900, avail.height() - 40))
        self._init_text()
        self._build_ui()
        self.apply_appearance(on_top_changed=bool(self.appearance["always_on_top"]))
        self.load_profile_into_ui()
        self._refresh_profile_combo()
        self._update_chat_toggle(bool(self.profile["chat"].get("auto_translate")))
        if self.state.get("geometry"):
            self.setGeometry(*self.state["geometry"])

        self._autosave_timer = QTimer(self)      # saves the profile shortly after the last change
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(1000)
        self._autosave_timer.timeout.connect(self._autosave_profile)
        self._meter_timer = QTimer(self)
        self._meter_timer.timeout.connect(self._decay_meters)
        self._meter_timer.start(80)
        self._last_level = {"incoming": 0.0, "outgoing": 0.0}
        self.setStatus("Ready. Pick a profile and press Start.")
        if self.state.get("overlay_visible"):
            self.overlay.show()
        if not self.state.get("seen_setup"):
            if not self.state.get("tour_pending"):         # a fresh install gets the guided tour instead
                self.tabs.setCurrentWidget(self.setup_tab)
            self.state["seen_setup"] = True
        self._init_tour()

    # ======================================================================= UI
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 6)
        root.addLayout(self._build_topbar())
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.addTab(scroll(self._build_dashboard_tab()), "Dashboard")
        self.tabs.addTab(self._build_live_tab(), "Live")
        self.tabs.addTab(scroll(self._build_text_tab()), "Text")
        self.tabs.addTab(scroll(self._build_input_tab()), "Input")
        self.tabs.addTab(scroll(self._build_output_tab()), "Output")
        self.tabs.addTab(scroll(self._build_stt_tab()), "Speech")
        self.tabs.addTab(scroll(self._build_translation_tab()), "Translation")
        self.tabs.addTab(scroll(self._build_ai_tab()), "AI Model")
        self.tabs.addTab(scroll(self._build_voice_tab()), "Voice")
        self.tabs.addTab(scroll(self._build_keys_tab()), "API Keys")
        self.setup_tab = scroll(self._build_setup_tab())
        self.tabs.addTab(self.setup_tab, "Setup")
        self.tabs.addTab(scroll(self._build_settings_tab()), "Settings")
        if PUBLIC:                           # the user manual, read aloud by the Windows voice
            self.tabs.addTab(self._build_manual_tab(), "Manual")
        self.tabs.addTab(self._build_log_tab(), "Log")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        sb = self.statusBar()
        self.status_label = QLabel()
        self.their_label = QLabel()
        self.latency_label = QLabel()
        sb.addWidget(self.status_label, 1)
        sb.addPermanentWidget(self.their_label)
        sb.addPermanentWidget(self.latency_label)

        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_profile)
        QShortcut(QKeySequence("F5"), self, activated=self.toggle_engine)

    def _build_topbar(self):
        bar = QHBoxLayout()
        title = QLabel("🎧 Dizcord")
        title.setObjectName("title")
        bar.addWidget(title)
        bar.addSpacing(12)
        bar.addWidget(QLabel("Profile"))
        self.profile_combo = DataCombo()
        self.profile_combo.setMinimumWidth(240)
        self.profile_combo.changed.connect(self._on_profile_selected)
        bar.addWidget(self.profile_combo)
        save = QPushButton("Save")
        save.setToolTip("Save profile (Ctrl+S)")
        save.clicked.connect(self.save_profile)
        bar.addWidget(save)
        more = QToolButton()
        more.setText("Profile ▾")
        more.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(more)
        for text, fn in [("Save as…", self.save_profile_as), ("Delete", self.delete_profile),
                         ("Import…", self.import_profile), ("Export… (API keys are never included)",
                                                            self.export_profile)]:
            menu.addAction(text, fn)
        more.setMenu(menu)
        bar.addWidget(more)
        bar.addStretch(1)
        self.overlay_btn = QPushButton("Subtitles")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.setToolTip("Show the floating subtitle window")
        self.overlay_btn.toggled.connect(lambda on: self.overlay.setVisible(on))
        bar.addWidget(self.overlay_btn)
        self.chat_btn = QPushButton("💬 Chat")
        self.chat_btn.setCheckable(True)
        self.chat_btn.setToolTip("Translate Discord text messages (see the Text tab)")
        self.chat_btn.toggled.connect(lambda _on: self.toggle_chat())
        bar.addWidget(self.chat_btn)
        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.setToolTip("Start / stop the voice translator for voice calls (F5)")
        self.start_btn.clicked.connect(self.toggle_engine)
        bar.addWidget(self.start_btn)
        return bar

    def bind(self, w: QWidget, path: str) -> QWidget:
        self.bindings.append((w, path))
        sig = change_signal(w)
        sig.connect(lambda *_a, w=w: setattr(self, "_changed_widget", w))
        sig.connect(self.on_change)
        return w

    # ------------------------------------------------------------------ Live
    def _direction_card(self, direction: str) -> QGroupBox:
        inc = direction == "incoming"
        box = QGroupBox("They speak  →  I hear" if inc else "I speak  →  They hear")
        g = QGridLayout(box)
        src = self.bind(LangCombo(include_auto=True), f"{direction}.source_lang")
        tgt = self.bind(LangCombo(include_auto=False), f"{direction}.target_lang")
        swap = QPushButton("⇄")
        swap.setFixedWidth(36)
        swap.setToolTip("Swap languages")
        swap.clicked.connect(lambda: self._swap_langs(src, tgt))
        g.addWidget(QLabel("Listen for" if inc else "I speak"), 0, 0)
        g.addWidget(src, 0, 1)
        g.addWidget(swap, 0, 2)
        g.addWidget(QLabel("Translate to" if inc else "They hear"), 1, 0)
        g.addWidget(tgt, 1, 1, 1, 2)
        meter = LevelMeter(self.colors)
        g.addWidget(meter, 2, 0, 1, 3)
        en = self.bind(QCheckBox("Enabled"), f"{direction}.enabled")
        sp = self.bind(QCheckBox("Speak translation" if inc else "Speak into Discord"), f"{direction}.speak")
        if inc:
            sp.setToolTip("Off: only show the text of who is talking (subtitles) - you hear their own voices")
            sp.clicked.connect(self._on_speak_clicked)
        row = QHBoxLayout()
        row.addWidget(en)
        row.addWidget(sp)
        stage = QLabel("idle")
        stage.setObjectName("muted")
        row.addStretch(1)
        row.addWidget(stage)
        g.addLayout(row, 3, 0, 1, 3)
        if inc:
            self.in_src, self.in_tgt, self.in_meter, self.in_stage = src, tgt, meter, stage
            pause = QPushButton("Pause listening")
            pause.setCheckable(True)
            pause.toggled.connect(lambda on: setattr(self.engine, "paused_incoming", on))
            stop = QPushButton("Stop speaking")
            stop.setToolTip("Cut the translation that is playing now")
            stop.clicked.connect(self.engine.stop_speaking)
            self.hear_btn = QPushButton("👂 Hear people")
            self.hear_btn.setCheckable(True)
            self.hear_btn.setChecked(self.engine.hear_originals)
            self.hear_btn.setToolTip("Also hear the people in the call (their own voices), not only the "
                                     "translations. Global hotkey: Input tab (default F9).")
            self.hear_btn.toggled.connect(self._on_hear_toggled)
            r2 = QHBoxLayout()
            r2.addWidget(pause)
            r2.addWidget(stop)
            r2.addWidget(self.hear_btn)
            r2.addStretch(1)
            g.addLayout(r2, 4, 0, 1, 3)
        else:
            self.out_src, self.out_tgt, self.out_meter, self.out_stage = src, tgt, meter, stage
            follow = self.bind(QCheckBox("Reply in the language they speak"), "outgoing.follow_their_language")
            follow.setToolTip("Automatically switch 'They hear' to the last language detected from them")
            g.addWidget(follow, 4, 0, 1, 3)
            r2 = QHBoxLayout()
            self.ptt_btn = QPushButton("🎤 Hold to talk")
            self.ptt_btn.setToolTip("Push-to-talk (only in PTT/toggle mode). Global hotkey set in the Input tab.")
            self.ptt_btn.pressed.connect(lambda: self.engine.set_ptt(True))
            self.ptt_btn.released.connect(lambda: self.engine.set_ptt(False))
            mute = QPushButton("Mute mic")
            mute.setCheckable(True)
            mute.toggled.connect(lambda on: setattr(self.engine, "muted_outgoing", on))
            r2.addWidget(self.ptt_btn)
            r2.addWidget(mute)
            r2.addStretch(1)
            g.addLayout(r2, 5, 0, 1, 3)
        return box

    def _build_live_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        cards = QHBoxLayout()
        cards.addWidget(self._direction_card("incoming"))
        cards.addWidget(self._direction_card("outgoing"))
        v.addLayout(cards)
        self.restart_hint = QLabel("Audio device/mode changes apply after Stop → Start.")
        self.restart_hint.setObjectName("warn")
        self.restart_hint.hide()
        v.addWidget(self.restart_hint)
        self.transcript = QTextBrowser()
        self.transcript.setOpenExternalLinks(True)
        v.addWidget(self.transcript, 1)
        row = QHBoxLayout()
        self.say_edit = QLineEdit()
        self.say_edit.setPlaceholderText("Type a message to say it (translated) in Discord, then press Enter…")
        self.say_edit.returnPressed.connect(self.say_typed)
        say = QPushButton("Say it")
        say.setObjectName("primary")
        say.clicked.connect(self.say_typed)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_transcript)
        export = QPushButton("Export…")
        export.clicked.connect(self.export_transcript)
        row.addWidget(self.say_edit, 1)
        row.addWidget(say)
        row.addWidget(clear)
        row.addWidget(export)
        v.addLayout(row)
        return w

    # ------------------------------------------------------------------ Input
    def _vad_group(self, title, prefix):
        box = QGroupBox(title)
        f = QFormLayout(box)
        f.addRow("Automatic sensitivity", self.bind(QCheckBox("adapt to background noise"), f"{prefix}.auto"))
        th = QDoubleSpinBox()
        th.setRange(-80, -5)
        th.setSuffix(" dB")
        f.addRow("Threshold (manual)", self.bind(th, f"{prefix}.threshold_db"))
        for key, label, lo, hi, suf in [("silence_ms", "End of sentence after silence", 150, 3000, " ms"),
                                        ("min_speech_ms", "Ignore sounds shorter than", 50, 3000, " ms"),
                                        ("pre_roll_ms", "Keep audio before speech", 0, 1500, " ms")]:
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setSingleStep(50)
            sp.setSuffix(suf)
            f.addRow(label, self.bind(sp, f"{prefix}.{key}"))
        mx = QDoubleSpinBox()
        mx.setRange(2, 60)
        mx.setSuffix(" s")
        f.addRow("Split long speech every", self.bind(mx, f"{prefix}.max_utterance_s"))
        return box

    def _build_input_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("What the app listens to (other people in Discord)")
        f = QFormLayout(box)
        self.listen_mode = self.bind(DataCombo([
            ("app", "Only the Discord app (recommended) - never hears the app's own voice, games or music"),
            ("loopback", "Capture what plays on an output device (loopback)"),
            ("device", "Capture an input/recording device (CABLE-B Output, Voicemeeter Out…)"),
        ]), "input.listen_mode")
        self.listen_mode.changed.connect(self._sync_listen_kind)
        f.addRow("Method", self.listen_mode)
        self.listen_device = DeviceCombo("output")
        self.listen_device.changed.connect(self.on_change)
        f.addRow("Device", self.listen_device)
        f.addRow(hint("<b>Only the Discord app</b> needs Windows 10 (2004) or 11: the app keeps listening while it "
                      "talks, and you can turn the original voices off (Hear people). Loopback: choose the "
                      "headphones/speakers Discord plays to."))
        lg = QDoubleSpinBox()
        lg.setRange(-20, 30)
        lg.setSuffix(" dB")
        f.addRow("Input boost", self.bind(lg, "input.listen_gain_db"))
        f.addRow(self.bind(QCheckBox("Loopback: pause listening while a translation plays on that device "
                                     "(prevents echo loops)"), "input.pause_listen_while_speaking"))
        hk = self.bind(QLineEdit(), "input.hear_key")
        hk.setPlaceholderText("e.g. f9, ctrl+alt+h - empty = off")
        f.addRow("Hotkey: hear the people on / off", hk)
        f.addRow(self.bind(QCheckBox("Hear the people in the call when Dizcord starts (not only the translations)"),
                           "incoming.hear_originals"))
        v.addWidget(box)

        box = QGroupBox("Your microphone")
        f = QFormLayout(box)
        self.mic_device = self.bind(DeviceCombo("input"), "input.mic_device")
        f.addRow("Microphone", self.mic_device)
        self.mic_mode = self.bind(DataCombo([("vad", "Voice activity (automatic)"),
                                             ("ptt", "Push-to-talk (hold key)"),
                                             ("toggle", "Toggle (press to start, press to send)")]),
                                  "input.mic_mode")
        f.addRow("Mode", self.mic_mode)
        self.ptt_key = self.bind(QLineEdit(), "input.ptt_key")
        self.ptt_key.setPlaceholderText("e.g. f8, caps lock, ctrl, x")
        f.addRow("Push-to-talk hotkey (global)", self.ptt_key)
        mg = QDoubleSpinBox()
        mg.setRange(-20, 30)
        mg.setSuffix(" dB")
        f.addRow("Mic boost", self.bind(mg, "input.mic_gain_db"))
        f.addRow(self.bind(QCheckBox("Ignore my mic while translations play (only without headphones - it cuts "
                                     "you off while the app talks)"), "input.ignore_mic_while_playing"))
        v.addWidget(box)

        row = QHBoxLayout()
        row.addWidget(self._vad_group("Voice detection - other people", "input.listen_vad"))
        row.addWidget(self._vad_group("Voice detection - my mic", "input.mic_vad"))
        v.addLayout(row)
        b = QPushButton("Refresh device lists")
        b.clicked.connect(self.refresh_devices)
        v.addWidget(b, 0, Qt.AlignLeft)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ Output
    def _build_output_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Translations of other people  →  you")
        f = QFormLayout(box)
        self.in_out_dev = self.bind(DeviceCombo("output"), "incoming.output_device")
        f.addRow("Play on", self.in_out_dev)
        f.addRow("Volume", self.bind(VolumeSlider(), "incoming.volume"))
        f.addRow(self.bind(QCheckBox("Don't speak lines that are already in my language"),
                           "incoming.skip_same_language"))
        f.addRow(self.bind(QCheckBox("Pass-through: also play the captured Discord audio on this device"),
                           "incoming.passthrough"))
        f.addRow("Pass-through volume", self.bind(VolumeSlider(), "incoming.passthrough_volume"))
        f.addRow("Original voices while translating", self.bind(VolumeSlider(1.0), "incoming.duck_passthrough"))
        v.addWidget(box)

        box = QGroupBox("The app voice")
        f = QFormLayout(box)
        f.addRow("Say who is talking", self.bind(DataCombo(NAME_STYLES), "speech.names"))
        f.addRow(self.bind(QCheckBox("Say the name again when the same person goes on talking"),
                           "speech.repeat_names"))
        f.addRow(self.bind(QCheckBox("Speak a little faster when translations pile up (stays close to live)"),
                           "speech.catchup"))
        f.addRow(hint("Call translations and chat messages read aloud share one voice: never two at the same "
                      "time, in the order they were said. Chat messages use the author's name; in calls the name "
                      "comes from <i>Who is talking</i> below."))
        v.addWidget(box)
        v.addWidget(self._build_speakers_box())

        box = QGroupBox("Your translated voice  →  Discord")
        f = QFormLayout(box)
        self.out_dev = self.bind(DeviceCombo("output"), "outgoing.output_device")
        f.addRow("Send to (virtual cable)", self.out_dev)
        f.addRow(hint("In Discord → Settings → Voice & Video, set <b>Input Device</b> to <b>CABLE Output</b>. "
                      "See the Setup tab."))
        f.addRow("Volume", self.bind(VolumeSlider(), "outgoing.volume"))
        f.addRow(self.bind(QCheckBox("Let me hear my translated voice"), "outgoing.monitor"))
        f.addRow("Monitor on", self.bind(DeviceCombo("output"), "outgoing.monitor_device"))
        f.addRow("Monitor volume", self.bind(VolumeSlider(), "outgoing.monitor_volume"))
        v.addWidget(box)

        box = QGroupBox("Subtitles && transcript")
        f = QFormLayout(box)
        f.addRow(self.bind(QCheckBox("Show subtitles for other people"), "incoming.show_subtitles"))
        f.addRow(self.bind(QCheckBox("Show subtitles for what I say"), "ui.subtitle_show_mine"))
        f.addRow(self.bind(QCheckBox("Show original text under the translation"), "ui.subtitle_show_original"))
        fs = QSpinBox()
        fs.setRange(10, 72)
        f.addRow("Font size", self.bind(fs, "ui.subtitle_font_size"))
        nl = QSpinBox()
        nl.setRange(1, 10)
        f.addRow("Lines shown", self.bind(nl, "ui.subtitle_lines"))
        f.addRow("Background opacity", self.bind(VolumeSlider(1.0), "ui.subtitle_opacity"))
        f.addRow(self.bind(QCheckBox("Auto-save transcripts to data/transcripts"), "ui.autosave_transcript"))
        v.addWidget(box)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ STT
    def _build_stt_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Speech recognition (speech → text)")
        bl = QVBoxLayout(box)
        self.stt_panel = ProviderPanel("stt", self.keys)
        self.stt_panel.changed.connect(self.on_change)
        self.stt_panel.log.connect(self._log)
        bl.addWidget(self.stt_panel)
        v.addWidget(box)
        box = QGroupBox("Test")
        h = QHBoxLayout(box)
        b = QPushButton("🎤 Record 4 s from my mic and transcribe")
        b.clicked.connect(self.test_stt)
        self.stt_result = no_translate(QLabel())
        self.stt_result.setWordWrap(True)
        h.addWidget(b)
        h.addWidget(self.stt_result, 1)
        v.addWidget(box)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ Translation
    def _build_translation_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Translation engine")
        bl = QVBoxLayout(box)
        self.tr_panel = ProviderPanel("translate", self.keys)
        self.tr_panel.changed.connect(self.on_change)
        self.tr_panel.log.connect(self._log)
        bl.addWidget(self.tr_panel)
        v.addWidget(box)
        box = QGroupBox("Style")
        f = QFormLayout(box)
        f.addRow("Tone", self.bind(DataCombo([("natural", "Natural"), ("casual", "Casual / gamer"),
                                              ("formal", "Formal"), ("literal", "Literal")]), "translation.style"))
        cl = QSpinBox()
        cl.setRange(0, 20)
        f.addRow("Context lines (AI only)", self.bind(cl, "translation.context_lines"))
        f.addRow(self.bind(QCheckBox("Keep swearing / don't censor (AI only)"), "translation.keep_profanity"))
        gl = QPlainTextEdit()
        gl.setPlaceholderText("One per line:\nGG = GG\nheadshot\nMarcão = Big Marc")
        gl.setMaximumHeight(110)
        f.addRow("Glossary", self.bind(gl, "translation.glossary"))
        v.addWidget(box)
        box = QGroupBox("Test")
        g = QGridLayout(box)
        self.tr_test_in = QLineEdit("Hey, are you guys ready? Let's push mid together!")
        self.tr_test_lang = LangCombo()
        self.tr_test_lang.setValue(self.profile["incoming"]["target_lang"])
        b = QPushButton("Translate")
        b.clicked.connect(self.test_translation)
        self.tr_test_out = no_translate(QLabel())
        self.tr_test_out.setWordWrap(True)
        self.tr_test_out.setTextInteractionFlags(Qt.TextSelectableByMouse)
        g.addWidget(self.tr_test_in, 0, 0)
        g.addWidget(self.tr_test_lang, 0, 1)
        g.addWidget(b, 0, 2)
        g.addWidget(self.tr_test_out, 1, 0, 1, 3)
        v.addWidget(box)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ AI model
    def _build_ai_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(hint("The AI model is used when the translation engine is <b>AI model (LLM)</b>. "
                         "Cloud: OpenAI, Claude, Gemini, Groq, OpenRouter, Mistral, DeepSeek, xAI, Together, "
                         "Fireworks, Cerebras… Local: Ollama, LM Studio, or any OpenAI-compatible server."))
        box = QGroupBox("AI model")
        bl = QVBoxLayout(box)
        self.ai_panel = ProviderPanel("llm", self.keys)
        self.ai_panel.changed.connect(self.on_change)
        self.ai_panel.log.connect(self._log)
        bl.addWidget(self.ai_panel)
        v.addWidget(box)
        box = QGroupBox("Extra instructions (optional)")
        bl = QVBoxLayout(box)
        cp = QPlainTextEdit()
        cp.setPlaceholderText("e.g. We are playing Valorant. Translate callouts using the English names. "
                              "Our friend 'Zé' is called Joe.")
        cp.setMaximumHeight(100)
        bl.addWidget(self.bind(cp, "ai.custom_prompt"))
        v.addWidget(box)
        row = QHBoxLayout()
        b = QPushButton("Test AI model")
        b.clicked.connect(self.test_ai)
        self.ai_result = no_translate(QLabel())
        self.ai_result.setWordWrap(True)
        row.addWidget(b)
        row.addWidget(self.ai_result, 1)
        v.addLayout(row)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------------ Voice
    def _build_voice_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Voice engine (text → speech)")
        bl = QVBoxLayout(box)
        self.tts_panel = ProviderPanel("tts", self.keys)
        self.tts_panel.changed.connect(self.on_change)
        self.tts_panel.changed.connect(self._on_tts_provider_maybe_changed)
        self.tts_panel.log.connect(self._log)
        self.tts_panel.langs = lambda: [self.profile[d]["target_lang"] for d in ("incoming", "outgoing")]
        self.tts_panel.downloaded.connect(self._voices_downloaded)
        bl.addWidget(self.tts_panel)
        v.addWidget(box)
        box = QGroupBox("Voices")
        g = QGridLayout(box)
        self.voice_in = DataCombo()
        self.voice_out = DataCombo()
        for cb in (self.voice_in, self.voice_out):
            cb.setEditable(True)
            cb.setInsertPolicy(DataCombo.NoInsert)
            cb.setMinimumWidth(260)
            cb.currentTextChanged.connect(self._on_voice_changed)
        for col, head in enumerate(("", "Voice", "Speed", "Pitch", "Volume", "")):
            if head:
                lb = QLabel(head)
                lb.setObjectName("muted")
                g.addWidget(lb, 0, col)
        for row, (d, label, cb) in enumerate((("incoming", "Translations I hear", self.voice_in),
                                              ("outgoing", "My voice in Discord", self.voice_out)), 1):
            g.addWidget(QLabel(label), row, 0)
            g.addWidget(cb, row, 1)
            speed = self.bind(VolumeSlider(2.0, minimum=0.5), f"{d}.voice_speed")
            speed.setToolTip("Speed of this voice (100% = normal). Works with every voice engine.")
            g.addWidget(speed, row, 2)
            pitch = QDoubleSpinBox()
            pitch.setRange(-12, 12)
            pitch.setSingleStep(1)
            pitch.setDecimals(0)
            pitch.setToolTip("Pitch in semitones: lower (-) or higher (+). 0 = the voice as it is.")
            g.addWidget(self.bind(pitch, f"{d}.voice_pitch"), row, 3)
            vol = self.bind(VolumeSlider(), f"{d}.volume")
            vol.setToolTip("Volume of this voice (the same setting as in the Output tab)")
            g.addWidget(vol, row, 4)
            test = QPushButton("▶ Test")
            test.setToolTip("Say the test sentence with this voice, on your headphones")
            test.clicked.connect(lambda _=False, d=d: self.test_voice(d))
            g.addWidget(test, row, 5)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 2)
        g.setColumnStretch(4, 2)
        row = QHBoxLayout()
        row.addWidget(QLabel("Auto voice gender"))
        self.gender = self.bind(DataCombo([("female", "Female"), ("male", "Male")]), "tts.gender")
        row.addWidget(self.gender)
        lb = QPushButton("⟳ Reload voice list")
        lb.clicked.connect(self.load_voices)
        row.addWidget(lb)
        row.addStretch(1)
        g.addLayout(row, 3, 0, 1, 6)
        g.addWidget(hint("'auto' picks a natural voice that matches the language automatically. The list shows "
                         "the voices of the languages you translate to."), 4, 0, 1, 6)
        v.addWidget(box)
        box = QGroupBox("Test")
        g = QGridLayout(box)
        self.tts_test_text = QLineEdit("Hi! This is how I will sound in Discord.")
        g.addWidget(self.tts_test_text, 0, 0, 1, 3)
        self.tts_result = QLabel()
        self.tts_result.setObjectName("muted")
        g.addWidget(self.tts_result, 1, 0, 1, 3)
        v.addWidget(box)
        self._voice_list_key = None
        v.addStretch(1)
        self._voices_provider = None
        return w

    # ------------------------------------------------------------------ Keys
    def _build_keys_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(hint("Keys are stored only on this PC in <code>data/keys.json</code> and are never put in "
                         "profiles, so exported profiles are safe to share. Environment variables work too."))
        box = QGroupBox("API keys")
        g = QGridLayout(box)
        self.key_edits: dict[str, QLineEdit] = {}
        known = config.KNOWN_KEYS
        for i, (kid, (label, env)) in enumerate(known.items()):
            e = QLineEdit()
            e.setEchoMode(QLineEdit.Password)
            e.setPlaceholderText(f"or set {env}")
            show = QCheckBox("show")
            show.toggled.connect(lambda on, e=e: e.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
            g.addWidget(QLabel(label), i, 0)
            g.addWidget(e, i, 1)
            g.addWidget(show, i, 2)
            self.key_edits[kid] = e
        v.addWidget(box)
        b = QPushButton("Save keys")
        b.setObjectName("primary")
        b.clicked.connect(self.save_keys)
        v.addWidget(b, 0, Qt.AlignLeft)
        v.addStretch(1)
        self._load_keys_tab()
        return w

    def _load_keys_tab(self):
        for kid, e in self.key_edits.items():
            e.setText(self.keys.stored(kid))

    def save_keys(self):
        for kid, e in self.key_edits.items():
            self.keys.set(kid, e.text())
        self.keys.save()
        if hasattr(self, "rpc_secret"):
            self.rpc_secret.setText(self.keys.stored("discord_rpc_secret"))
        self.ai_panel.keys_changed()
        self._log("API keys saved.")
        self.setStatus("API keys saved.")

    # ------------------------------------------------------------------ Setup
    def _build_setup_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        cable = devices.find_virtual_cable()
        box = QGroupBox("Status")
        f = QFormLayout(box)
        if cable:
            lb = QLabel(f"✔ Virtual cable found: {cable}")
            lb.setObjectName("ok")
        else:
            lb = QLabel("✖ No virtual audio cable found - install VB-Audio Virtual Cable (free) and restart.")
            lb.setObjectName("warn")
        self.setup_cable_label = lb
        f.addRow("Virtual cable", lb)
        row = QHBoxLayout()
        b = QPushButton("Use it for my translated voice")
        b.setEnabled(bool(cable))
        b.clicked.connect(lambda: (self.out_dev.setValue(cable), self.on_change(), self.setStatus(f"Sending to {cable}")))
        dl = QPushButton("Download VB-Cable")
        dl.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/")))
        row.addWidget(b)
        row.addWidget(dl)
        row.addStretch(1)
        f.addRow(row)
        v.addWidget(box)
        guide = self.setup_guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setHtml(SETUP_GUIDE)
        guide.setMinimumHeight(520)
        v.addWidget(guide, 1)
        return w

    def _build_log_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        v.addWidget(self.log_view, 1)
        row = QHBoxLayout()
        for text, path in [("Open logs folder", config.LOGS_DIR), ("Open transcripts folder", config.TRANSCRIPTS_DIR),
                           ("Open app folder", config.ROOT)]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))))
            row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        return w

    # ======================================================================= profile <-> UI
    def load_profile_into_ui(self):
        self._loading = True
        try:
            p = self.profile
            for w, path in self.bindings:
                try:
                    set_widget_value(w, get_path(p, path))
                except KeyError:
                    pass
            self._sync_listen_kind()
            set_widget_value(self.listen_device, p["input"]["listen_device"])
            self._sync_settings_listen()
            self.stt_panel.set_state(p["stt"]["provider"], p["stt"]["settings"])
            self.tr_panel.set_state(p["translation"]["provider"], p["translation"]["settings"])
            self.ai_panel.set_state(p["ai"]["provider"], p["ai"]["settings"])
            self.tts_panel.set_state(p["tts"]["provider"], p["tts"]["settings"])
            self._load_voice_combos()
            self.overlay.apply(self.colors, p["ui"])
        finally:
            self._loading = False
        self._sync_text_only()
        self.dirty = False
        self._update_title()

    def collect(self):
        p = self.profile
        changed = getattr(self, "_changed_widget", None)
        changed_path = next((path for w, path in self.bindings if w is changed), None)
        for w, path in self.bindings:
            if path == changed_path and w is not changed:
                continue          # a twin of the widget the user just changed: it is updated below
            set_path(p, path, widget_value(w))
        if changed_path:
            value = get_path(p, changed_path)
            for w, path in self.bindings:
                if path == changed_path and w is not changed:
                    set_widget_value(w, value)
        self._changed_widget = None
        p["input"]["listen_device"] = self.listen_device.value()
        p["stt"]["provider"], p["stt"]["settings"] = self.stt_panel.state()
        p["translation"]["provider"], p["translation"]["settings"] = self.tr_panel.state()
        p["ai"]["provider"], p["ai"]["settings"] = self.ai_panel.state()
        p["tts"]["provider"], p["tts"]["settings"] = self.tts_panel.state()
        return p

    def on_change(self, *_):
        if self._loading:
            return
        before = copy.deepcopy(self.engine.profile)
        self.collect()
        self.dirty = True
        self._update_title()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        self.overlay.apply(self.colors, self.profile["ui"])
        self._text_on_change()
        self._sync_text_only()
        if any(before[d]["target_lang"] != self.profile[d]["target_lang"] for d in ("incoming", "outgoing")):
            self.tts_panel.check_downloads()       # a voice for the new language?
        if self.profile["ui"].get("autosave_settings", True):
            self._autosave_timer.start()         # restarts while you keep changing things
        if self.engine.running:
            restart_keys = [("input", k) for k in ("listen_mode", "listen_device", "mic_device", "mic_mode",
                                                   "ptt_key", "hear_key", "listen_app")]
            restart_keys += [("incoming", "enabled"), ("outgoing", "enabled"), ("incoming", "passthrough")]
            if any(before[a].get(b) != self.profile[a].get(b) for a, b in restart_keys):
                self.restart_hint.show()

    def _update_title(self):
        star = " *" if self.dirty else ""
        self.setWindowTitle(f"{APP_NAME} {__version__} — {self.profile['name']}{star}")

    def _sync_listen_kind(self):
        mode = self.listen_mode.value()
        kind = "input" if mode == "device" else "output"
        if self.listen_device.kind != kind:
            cur = self.listen_device.value()
            self.listen_device.refresh(kind)
            self.listen_device.setValue(cur if not self._loading else "")
        self.listen_device.setEnabled(mode != "app")          # Discord only: whatever device Discord plays on
        self._sync_settings_listen()

    def refresh_devices(self):
        for w in self.findChildren(DeviceCombo):
            w.refresh()
        self.setStatus("Device lists refreshed.")

    # ======================================================================= profiles
    def _refresh_profile_combo(self):
        names = config.list_profiles()
        if self.profile["name"] not in names:
            names.append(self.profile["name"])
        self.profile_combo.blockSignals(True)
        self.profile_combo.set_items([(n, n) for n in names])
        self.profile_combo.setValue(self.profile["name"])
        self.profile_combo.blockSignals(False)

    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        r = QMessageBox.question(self, "Unsaved changes",
                                 f"Save changes to profile '{self.profile['name']}'?",
                                 QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if r == QMessageBox.Cancel:
            return False
        if r == QMessageBox.Save:
            self.save_profile()
        return True

    def _on_profile_selected(self):
        name = self.profile_combo.value()
        if not name or name == self.profile["name"]:
            return
        if not self._confirm_discard():
            self._refresh_profile_combo()
            return
        self.switch_profile(config.load_profile(name))

    def switch_profile(self, prof: dict):
        was_running = self.engine.running
        if was_running:
            self.engine.stop()
        self.profile = prof
        self.engine.apply_profile(copy.deepcopy(prof))
        self.load_profile_into_ui()
        self._refresh_profile_combo()
        self.state["last_profile"] = prof["name"]
        chat_on = bool(prof["chat"].get("auto_translate"))
        if chat_on != (self.chat.reader_running and not self.chat._reader_stop.is_set()):
            self.chat.start_reader() if chat_on else self.chat.stop_reader()
        self._update_chat_toggle(chat_on)
        self.chat.start_selection()
        self.setStatus(f"Loaded profile '{prof['name']}'." + (" Press Start to resume." if was_running else ""))

    def save_profile(self, quiet: bool = False):
        self.collect()
        config.save_profile(self.profile)
        self.dirty = False
        self._update_title()
        self._refresh_profile_combo()
        self.state["last_profile"] = self.profile["name"]
        if not quiet:
            self.setStatus(f"Profile '{self.profile['name']}' saved.")

    def _autosave_profile(self):
        if not self.dirty or self._loading or not self.profile["ui"].get("autosave_settings", True):
            return
        try:
            self.save_profile(quiet=True)
        except Exception as e:  # noqa: BLE001 - never crash the UI because the disk said no
            log.warning("autosave failed: %s", e)
            self.setStatus(f"⚠ Could not save automatically: {e}", error=True)

    def save_profile_as(self):
        name, ok = QInputDialog.getText(self, "Save profile as", "Profile name:", text=self.profile["name"] + " copy")
        if ok and name.strip():
            self.collect()
            self.profile = copy.deepcopy(self.profile)
            self.profile["name"] = name.strip()
            self.save_profile()

    def delete_profile(self):
        name = self.profile["name"]
        if QMessageBox.question(self, "Delete profile", f"Delete profile '{name}'?") != QMessageBox.Yes:
            return
        config.delete_profile(name)
        names = config.list_profiles()
        self.dirty = False
        self.switch_profile(config.load_profile(names[0]) if names else config.load_profile("Default"))

    def import_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import profile", str(config.ROOT), "Profile (*.json)")
        if not path:
            return
        try:
            prof = config.import_profile(path)
        except Exception as e:
            QMessageBox.warning(self, "Import failed", str(e))
            return
        if not self._confirm_discard():
            return
        config.save_profile(prof)
        self.switch_profile(prof)

    def export_profile(self):
        self.collect()
        path, _ = QFileDialog.getSaveFileName(self, "Export profile",
                                              str(config.ROOT / f"{self.profile['name']}.json"), "Profile (*.json)")
        if path:
            config.export_profile(self.profile, path)
            self.setStatus(f"Exported to {path}")

    # ======================================================================= engine
    def toggle_engine(self):
        if self.engine.running:
            self.engine.stop()
        else:
            self.collect()
            self.restart_hint.hide()
            self.engine.apply_profile(copy.deepcopy(self.profile))
            self.engine.start()

    def on_event(self, ev: dict):
        self._dash_feed(ev)
        if self.handle_text_event(ev):
            return
        t = ev.get("type")
        if t == "level":
            meter = self.in_meter if ev["dir"] == "incoming" else self.out_meter
            meter.set_level(ev["db"], ev["speech"], ev["threshold"])
            self._last_level[ev["dir"]] = time.monotonic()
        elif t == "line":
            self.add_line(ev)
        elif t == "spoken":
            tm = ev.get("timings", {})
            parts = [f"{k.upper()} {v:.1f}s" for k, v in tm.items()]
            self.latency_label.setText(f"Last: {ev['latency']:.1f}s  ({' · '.join(parts)})")
        elif t == "busy":
            lbl = self.in_stage if ev["dir"] == "incoming" else self.out_stage
            lbl.setText(STAGES.get(ev["stage"], ev["stage"]) if self.engine.running or ev["stage"] else "idle")
        elif t == "status":
            self.setStatus(ev["text"])
        elif t == "error":
            self.setStatus("⚠ " + ev["text"], error=True)
            self._add_notice(ev["text"])
        elif t == "state":
            running = ev["running"]
            self.start_btn.setText("■  Stop" if running else "▶  Start")
            self.start_btn.setObjectName("danger" if running else "primary")
            self.start_btn.style().unpolish(self.start_btn)
            self.start_btn.style().polish(self.start_btn)
            if not running:
                self.in_stage.setText("idle")
                self.out_stage.setText("idle")
                self.restart_hint.hide()
        elif t == "their_lang":
            self.their_label.setText(f"They speak: {L.name(ev['lang'])}")
        elif t == "hear":
            self._show_hear(ev["on"])
        elif t == "rpc_status":
            self.rpc_status.setText(("✔ " if ev.get("ok") else "⚠ ") + ev["text"])
            self.rpc_status.setObjectName("ok" if ev.get("ok") else "warn")
            self.rpc_status.style().unpolish(self.rpc_status)
            self.rpc_status.style().polish(self.rpc_status)
        elif t == "ptt":
            self.ptt_btn.setText("🔴 Recording…" if ev["down"] else "🎤 Hold to talk")
        elif t == "log":
            self.log_view.appendPlainText(ev["text"])

    def _decay_meters(self):
        now = time.monotonic()
        for d, m in (("incoming", self.in_meter), ("outgoing", self.out_meter)):
            if now - self._last_level[d] > 0.2:
                m.decay()

    # ======================================================================= transcript
    def _line_html(self, ln: dict) -> str:
        c = self.colors
        inc = ln["dir"] == "incoming"
        col = c["incoming"] if inc else c["outgoing"]
        who = html.escape(ln["who"]) if inc and ln.get("who") else (
            "Them" if inc else ("Me (typed)" if ln.get("typed") else "Me"))
        src = L.name(ln["src"]) if ln.get("src") else "?"
        meta = f"{ln['time']} · {src} → {L.name(ln['tgt'])}"
        if ln.get("skipped"):
            meta += " · same language"
        body = f"<span style='font-size:11.5pt'>{html.escape(ln['translated'])}</span>"
        orig = ""
        if ln["original"] != ln["translated"]:
            orig = f"<br><span style='color:{c['muted']}'>{html.escape(ln['original'])}</span>"
        return (f"<div style='margin:4px 0 8px 0'><b style='color:{col}'>{who}</b> "
                f"<span style='color:{c['muted']}; font-size:8.5pt'>{meta}</span><br>{body}{orig}</div>")

    def add_line(self, ev: dict):
        ln = dict(ev, time=dt.datetime.now().strftime("%H:%M:%S"))
        self.lines.append(ln)
        self.transcript.append(self._line_html(ln))
        self.transcript.verticalScrollBar().setValue(self.transcript.verticalScrollBar().maximum())
        ui = self.profile["ui"]
        if (ev["dir"] == "incoming" and self.profile["incoming"].get("show_subtitles", True)) or \
                (ev["dir"] == "outgoing" and ui.get("subtitle_show_mine", True)):
            name = f"{ev['who']}: " if ev.get("who") else ""
            self.overlay.add(ev["dir"], name + ev["translated"], ev["original"])
        if ui.get("autosave_transcript", True):
            self._autosave(ln)

    def _add_notice(self, text):
        self.transcript.append(f"<div style='color:{self.colors['error']}; font-size:9pt'>⚠ {html.escape(text)}</div>")

    def _rerender_transcript(self):
        self.transcript.clear()
        for ln in self.lines:
            self.transcript.append(self._line_html(ln))

    def _autosave(self, ln):
        try:
            if self.transcript_file is None:
                stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.transcript_file = config.TRANSCRIPTS_DIR / f"session_{stamp}.txt"
            who = (ln.get("who") or "THEM") if ln["dir"] == "incoming" else "ME"
            with open(self.transcript_file, "a", encoding="utf-8") as fh:
                fh.write(f"[{ln['time']}] {who} ({ln.get('src') or '?'}→{ln['tgt']}): {ln['translated']}\n")
                if ln["original"] != ln["translated"]:
                    fh.write(f"           original: {ln['original']}\n")
        except Exception as e:
            log.warning("transcript autosave failed: %s", e)

    def clear_transcript(self):
        self.lines.clear()
        self.transcript.clear()

    def export_transcript(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export transcript",
                                              str(config.TRANSCRIPTS_DIR / "transcript.txt"), "Text (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            for ln in self.lines:
                who = (ln.get("who") or "THEM") if ln["dir"] == "incoming" else "ME"
                fh.write(f"[{ln['time']}] {who}: {ln['translated']}\n")
                if ln["original"] != ln["translated"]:
                    fh.write(f"    ({ln['original']})\n")
        self.setStatus(f"Transcript saved to {path}")

    def say_typed(self):
        text = self.say_edit.text().strip()
        if not text:
            return
        self.say_edit.clear()
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        self.engine.say(text)

    # ======================================================================= hear people / who is talking
    def _on_hear_toggled(self, on: bool):
        if on != self.engine.hear_originals:
            self.engine.set_hear(on)

    def _on_speak_clicked(self, on: bool):
        """'Speak translation' off = text only: show the subtitles window (with the subtitles of the others)."""
        if on:
            return
        for w, path in self.bindings:
            if path == "incoming.show_subtitles" and not w.isChecked():
                w.setChecked(True)
        if not self.overlay.isVisible():
            self.overlay.show()
            for b in (getattr(self, "overlay_btn", None), getattr(self, "dash_subs_btn", None)):
                if b is not None:
                    b.blockSignals(True)
                    b.setChecked(True)
                    b.blockSignals(False)
        self.setStatus("Text only: the translations are shown in the subtitles window and you hear the people "
                       "in the call with their own voices. Names: Output tab → Who is talking.")

    def _sync_text_only(self):
        """Text only (translations not spoken): the people are always heard, so 'Hear people' has nothing to do."""
        text_only = not self.profile["incoming"].get("speak", True)
        for w in (getattr(self, "hear_btn", None), getattr(self, "dash_hear", None)):
            if w is not None:
                w.setEnabled(not text_only)

    def _show_hear(self, on: bool):
        for w in (getattr(self, "hear_btn", None), getattr(self, "dash_hear", None)):
            if w is not None and w.isChecked() != on:
                w.blockSignals(True)
                w.setChecked(on)
                w.blockSignals(False)

    def _build_speakers_box(self):
        box = QGroupBox("Who is talking (names in voice calls)")
        f = QFormLayout(box)
        f.addRow(self.bind(QCheckBox("Get the names of the people talking from the Discord app"),
                           "speakers.enabled"))
        cid = self.bind(QLineEdit(), "speakers.client_id")
        cid.setPlaceholderText("Application ID - a number like 1234567890123456789")
        f.addRow("Discord Application ID", cid)
        self.rpc_secret = QLineEdit()
        self.rpc_secret.setEchoMode(QLineEdit.Password)
        self.rpc_secret.setPlaceholderText("Client Secret (OAuth2 page) - kept only on this PC")
        self.rpc_secret.setText(self.keys.stored("discord_rpc_secret"))
        self.rpc_secret.editingFinished.connect(self._save_rpc_secret)
        f.addRow("Client Secret", self.rpc_secret)
        f.addRow(hint("Once: open <a href='https://discord.com/developers/applications'>Discord Developer "
                      "Portal</a> → New Application → copy the Application ID; OAuth2 → Reset Secret → copy the "
                      "Client Secret, and add the redirect <code>http://localhost</code>. Then tick the box above "
                      "and click <b>Authorize</b> in the window Discord shows. Nothing else is shared."))
        self.rpc_status = QLabel("Off")
        self.rpc_status.setWordWrap(True)
        self.rpc_status.setObjectName("muted")
        f.addRow("Status", self.rpc_status)
        return box

    def _save_rpc_secret(self):
        self.keys.set("discord_rpc_secret", self.rpc_secret.text())
        self.keys.save()
        if "discord_rpc_secret" in getattr(self, "key_edits", {}):
            self.key_edits["discord_rpc_secret"].setText(self.rpc_secret.text())

    # ======================================================================= tests
    def test_stt(self):
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        self.stt_result.setText("Recording 4 seconds… speak now!")
        mic = self.profile["input"]["mic_device"]
        lang = self.profile["outgoing"]["source_lang"]

        def work():
            from ..audio.capture import InputDeviceSource
            from ..audio.utils import resample
            chunks = []
            src = InputDeviceSource(mic, chunks.append)
            src.start()
            time.sleep(4)
            src.stop()
            if not chunks:
                raise RuntimeError("No audio captured from the microphone.")
            audio = resample(np.concatenate(chunks), src.samplerate, 16000)
            t = time.monotonic()
            text, det = self.engine.provider("stt").transcribe(audio, None if lang == L.AUTO else lang)
            return text, det, time.monotonic() - t

        def done(res, err):
            if err:
                self.stt_result.setText(f"⚠ {err}")
            else:
                text, det, secs = res
                self.stt_result.setText(f"“{text or '(nothing heard)'}”  — {L.name(det) if det else '?'}, {secs:.1f}s")
        self.stt_result.setText("Recording 4 seconds… speak now!")
        run_async(work, done)

    def test_translation(self):
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        text, target = self.tr_test_in.text(), self.tr_test_lang.value()
        self.tr_test_out.setText("Translating…")

        def work():
            t = time.monotonic()
            out, det = self.engine.provider("translate").translate(text, None, target,
                                                                  self.engine.translate_context("incoming"))
            return out, det, time.monotonic() - t
        run_async(work, lambda r, e: self.tr_test_out.setText(
            f"⚠ {e}" if e else f"{r[0]}    ({L.name(r[1]) if r[1] else '?'} → {L.name(target)}, {r[2]:.1f}s)"))

    def test_ai(self):
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        self.ai_result.setText("Asking the model…")

        def work():
            t = time.monotonic()
            out = self.engine.provider("llm").chat("You are a helpful assistant. Answer in one short sentence.",
                                                   [{"role": "user", "content": "Say hello and name yourself."}],
                                                   max_tokens=100)
            return out, time.monotonic() - t
        run_async(work, lambda r, e: self.ai_result.setText(f"⚠ {e}" if e else f"✔ {r[0]}  ({r[1]:.1f}s)"))

    def test_voice(self, direction):
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        text = self.tts_test_text.text().strip() or "Hello!"
        lang = self.profile[direction]["target_lang"]
        dev = self.profile["incoming"]["output_device"]
        self.tts_result.setText("Generating…")

        def work():
            from ..audio.player import OutputDevice
            src_text = text
            if L.base(lang) != "en":
                try:
                    src_text, _ = self.engine.provider("translate").translate(
                        text, "en", lang, self.engine.translate_context(direction))
                except Exception:
                    pass
            t = time.monotonic()
            audio, sr = self.engine.synthesize(src_text, lang, direction)
            secs = time.monotonic() - t
            out = OutputDevice(dev)
            out.open()
            try:
                out.play(audio, sr, float(self.profile[direction].get("volume", 1.0))).done.wait(len(audio) / sr + 3)
            finally:
                out.close()
            return secs
        run_async(work, lambda r, e: self.tts_result.setText(f"⚠ {e}" if e else f"✔ generated in {r:.1f}s"))

    # ======================================================================= voices
    def _current_voices(self) -> dict:
        pid = self.tts_panel.combo.value()
        return self.profile["tts"].setdefault("voices", {}).setdefault(pid, {"incoming": "auto", "outgoing": "auto"})

    def _load_voice_combos(self, items=None):
        vs = self._current_voices()
        self._voices_provider = self.tts_panel.combo.value()
        for cb, d in ((self.voice_in, "incoming"), (self.voice_out, "outgoing")):
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("auto", "auto")
            for vid, label in (items or []):
                cb.addItem(label, vid)
            cur = vs.get(d, "auto") or "auto"
            i = cb.findData(cur)
            if i < 0:
                cb.addItem(cur, cur)
                i = cb.count() - 1
            cb.setCurrentIndex(i)
            cb.blockSignals(False)

    def _on_tts_provider_maybe_changed(self):
        if self.tts_panel.combo.value() != self._voices_provider:
            self._load_voice_combos()
            self._auto_load_voices()

    def _voices_downloaded(self):
        self._voice_list_key = None
        self._auto_load_voices()

    def _on_voice_changed(self, *_):
        if self._loading:
            return
        vs = self._current_voices()
        for cb, d in ((self.voice_in, "incoming"), (self.voice_out, "outgoing")):
            data = cb.currentData()
            text = cb.currentText().strip()
            vs[d] = data if data is not None and cb.itemText(cb.currentIndex()) == text else (text or "auto")
        self.on_change()

    def _auto_load_voices(self):
        """The voice list fills itself when the Voice tab opens (again after the engine or a language changed)."""
        if not self.tabs.currentWidget() or not self.tabs.currentWidget().isAncestorOf(self.voice_in):
            return
        key = (self.tts_panel.combo.value(), self.profile["incoming"]["target_lang"],
               self.profile["outgoing"]["target_lang"])
        if key != self._voice_list_key:
            self._voice_list_key = key
            self.load_voices()

    def load_voices(self):
        self.collect()
        self.engine.apply_profile(copy.deepcopy(self.profile))
        langs = {self.profile["incoming"]["target_lang"], self.profile["outgoing"]["target_lang"]}
        self.tts_result.setText("Loading voices…")

        def work():
            prov = self.engine.provider("tts")
            out, seen = [], set()
            for lang in langs:
                for vid, label in prov.list_voices(lang):
                    if vid not in seen:
                        seen.add(vid)
                        out.append((vid, label))
            return out

        def done(res, err):
            if err:
                self.tts_result.setText(f"⚠ {err}")
                return
            self._loading = True
            self._load_voice_combos(res)
            self._loading = False
            self.tts_result.setText(f"{len(res)} voices loaded.")
        run_async(work, done)

    # ======================================================================= misc
    def _swap_langs(self, src: LangCombo, tgt: LangCombo):
        s, t = src.value(), tgt.value()
        if s == L.AUTO:
            return
        src.setValue(t)
        tgt.setValue(s)

    def _apply_theme(self) -> dict:
        a = self.appearance
        return theme.apply(self.app, self.theme_name, a["font_pt"], a["font_family"])

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.colors = self._apply_theme()
        for m in (self.in_meter, self.out_meter):
            m.colors = self.colors
            m.update()
        self.overlay.apply(self.colors, self.profile["ui"])
        self._update_theme_btn()
        self._rerender_transcript()
        self._text_theme_changed()
        self.state["theme"] = self.theme_name

    def _update_theme_btn(self):
        if hasattr(self, "set_theme"):
            self.set_theme.blockSignals(True)
            self.set_theme.setValue(self.theme_name)
            self.set_theme.blockSignals(False)
        if hasattr(self, "dash_feed"):
            self._dash_render_feed()

    def _on_tab_changed(self, _):
        self._manual_tab_changed()
        self._auto_load_voices()
        self._load_keys_tab()
        self.overlay_btn.blockSignals(True)
        self.overlay_btn.setChecked(self.overlay.isVisible())
        self.overlay_btn.blockSignals(False)

    def setStatus(self, text, error=False):
        self.status_label.setText(text)
        self.status_label.setObjectName("warn" if error else "")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _log(self, text):
        log.info(text)

    def closeEvent(self, e):
        if not self._confirm_discard():
            e.ignore()
            return
        self.engine.shutdown()
        self._text_close()
        self._manual_close()
        self._tour_close()
        g = self.geometry()
        og = self.overlay.geometry()
        self.state.update({"geometry": [g.x(), g.y(), g.width(), g.height()],
                           "overlay_geometry": [og.x(), og.y(), og.width(), og.height()],
                           "overlay_visible": self.overlay.isVisible(),
                           "last_profile": self.profile["name"], "theme": self.theme_name})
        config.save_app_state(self.state)
        self.overlay.close()
        e.accept()


SETUP_GUIDE = """
<h2>How it works</h2>
<p><b>Hearing others:</b> the app records only what the Discord app plays, recognises the speech, translates it and
shows subtitles / reads it to you in a natural voice. By default you hear only the translations; press <b>F9</b>
(Hear people) to also hear their own voices.<br>
<b>Speaking:</b> the app listens to your microphone, translates what you say and speaks it with a natural voice into
a <i>virtual audio cable</i>. Discord uses that cable as its microphone, so your friends hear the translated voice.</p>

<h2>1. Install a virtual audio cable (once)</h2>
<p>Install <a href="https://vb-audio.com/Cable/">VB-Audio Virtual Cable</a> (free), then reboot. It adds
<b>CABLE Input</b> (a speaker) and <b>CABLE Output</b> (a microphone).</p>

<h2>2. Discord settings</h2>
<ul>
<li>Settings → Voice &amp; Video → <b>Input Device: CABLE Output (VB-Audio Virtual Cable)</b></li>
<li>Output Device: your headphones (as usual).</li>
<li>Input Mode: <b>Voice Activity</b>, and turn <b>off</b> "Automatically determine input sensitivity" - set the
slider low (around -60 dB).</li>
<li>Turn <b>off</b> Noise Suppression (Krisp), Echo Cancellation and Automatic Gain Control - they can cut the
synthetic voice.</li>
</ul>

<h2>3. App settings</h2>
<ul>
<li><b>Output tab →</b> "Send to (virtual cable)": <b>CABLE Input</b>. "Play on": your headphones.</li>
<li><b>Input tab →</b> Method: <i>Only the Discord app</i>. Microphone: your real mic.</li>
<li><b>Live tab →</b> choose languages (or Auto-detect) and press <b>Start</b>.</li>
</ul>

<h2>Older Windows (before Windows 10 2004): isolate Discord's audio</h2>
<p>Loopback hears <i>everything</i> on that device (game, music…). To translate only Discord: install a second cable
(VB-Cable A+B) or use Voicemeeter, set Discord's <b>Output Device</b> to that cable, choose it as the Input-tab device
(Method: <i>input device</i> → "CABLE-A Output", or loopback of "CABLE-A Input"), and enable
<b>Pass-through</b> in the Output tab so you still hear your friends on your headphones (their voices get quieter
automatically while a translation is spoken).</p>

<h2>Free vs paid engines</h2>
<p>The <b>"Free - no keys needed"</b> profile uses Whisper on your PC + free Google Translate + free Microsoft Edge
neural voices. For the best quality and speed use an AI model (OpenAI, Claude, Gemini, Groq…) for translation and
ElevenLabs / OpenAI voices. Put keys in the <b>API Keys</b> tab.</p>

<h2>Tips</h2>
<ul>
<li>Wear headphones - otherwise your mic hears the translations. The app recognises its own voice and ignores
it; without headphones you can also tick "Ignore my mic while translations play" (Input tab).</li>
<li>The app warns you when Discord uses your real microphone - then people would hear your own voice instead of
only the translation.</li>
<li>Latency is usually 1-3 s per sentence. Faster: Groq/OpenAI speech recognition, a small/fast AI model,
Edge or ElevenLabs Flash voices, and a shorter "End of sentence after silence" (Input tab).</li>
<li>Use push-to-talk if you talk a lot in your own language and only want some sentences translated.</li>
<li>"Reply in the language they speak" auto-switches your output language to whatever they last spoke.</li>
</ul>
"""
