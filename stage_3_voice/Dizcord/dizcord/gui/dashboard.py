"""'Dashboard' tab: everything you switch on and off in one place, with live status,
your Discord name and languages, quick tools, hotkeys and the latest translations."""
from __future__ import annotations

import html
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

from .. import languages as L
from ..i18n import source, tr
from .widgets import DataCombo, LangCombo

MAX_FEED = 40


def _muted(text: str) -> QLabel:
    lb = QLabel(text)
    lb.setWordWrap(True)
    lb.setObjectName("muted")
    return lb


class _Status(QWidget):
    """Coloured dot + one line of status text."""

    def __init__(self):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        self.dot = QLabel("●")
        self.text = QLabel("off")
        self.text.setWordWrap(True)
        h.addWidget(self.dot)
        h.addWidget(self.text, 1)

    def set(self, colors: dict, state: str, text: str):
        col = {"on": "ok", "busy": "outgoing", "error": "error"}.get(state, "muted")
        self.dot.setStyleSheet(f"color: {colors[col]}; font-size: 13pt;")
        self.text.setText(text)


class _Cards(QWidget):
    """Cards in a grid that re-flows with the window width: 3 columns, 2, or 1."""

    def __init__(self, cards: list[QWidget]):
        super().__init__()
        self.cards = cards
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.cols = 0
        self._flow(3)

    def _flow(self, cols: int):
        if cols == self.cols:
            return
        self.cols = cols
        for c in self.cards:
            self.grid.removeWidget(c)
        for i, c in enumerate(self.cards):
            self.grid.addWidget(c, i // cols, i % cols)
        for c in range(3):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)

    def resizeEvent(self, e):
        w = e.size().width()
        self._flow(3 if w >= 1150 else (2 if w >= 720 else 1))
        super().resizeEvent(e)


def _narrow(combo: QComboBox) -> QComboBox:
    """Long language names must not force the cards to be wide."""
    combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(8)
    combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return combo


class DashboardMixin:
    """Mixed into MainWindow. Needs: bind, profile, engine, chat, colors, toggle_engine, toggle_chat, start_ocr,
    overlay, setStatus."""

    def _build_dashboard_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(10)
        cards = [self._dash_voice_card(), self._dash_chat_card()]
        cards += [self._dash_you_card(), self._dash_tools_card(), self._dash_hotkeys_card()]
        for card in cards:
            for combo in card.findChildren(QComboBox):
                _narrow(combo)
        v.addWidget(_Cards(cards))

        box = QGroupBox("Latest translations")
        bl = QVBoxLayout(box)
        self.dash_feed = QTextBrowser()
        self.dash_feed.setMinimumHeight(160)
        bl.addWidget(self.dash_feed)
        v.addWidget(box, 1)
        self._dash_items: list[dict] = []

        self._dash_timer = QTimer(self)
        self._dash_timer.timeout.connect(self._dash_refresh)
        self._dash_timer.start(500)
        return w

    # ------------------------------------------------------------------ cards
    @staticmethod
    def _card(title: str) -> tuple[QGroupBox, QVBoxLayout]:
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setSpacing(6)
        return box, lay

    def _dash_button(self, fn) -> QPushButton:
        b = QPushButton()
        b.setObjectName("primary")
        b.setMinimumHeight(34)
        b.clicked.connect(fn)
        return b

    def _dash_voice_card(self):
        box, lay = self._card("🎧  Voice translator (voice calls)")
        self.dash_voice_status = _Status()
        lay.addWidget(self.dash_voice_status)
        self.dash_voice_btn = self._dash_button(self.toggle_engine)
        lay.addWidget(self.dash_voice_btn)
        g = QGridLayout()
        g.addWidget(QLabel("They speak"), 0, 0)
        g.addWidget(self.bind(LangCombo(include_auto=True), "incoming.source_lang"), 0, 1)
        g.addWidget(QLabel("→ I hear"), 0, 2)
        g.addWidget(self.bind(LangCombo(), "incoming.target_lang"), 0, 3)
        g.addWidget(QLabel("I speak"), 1, 0)
        g.addWidget(self.bind(LangCombo(include_auto=True), "outgoing.source_lang"), 1, 1)
        g.addWidget(QLabel("→ They hear"), 1, 2)
        g.addWidget(self.bind(LangCombo(), "outgoing.target_lang"), 1, 3)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        lay.addLayout(g)
        self.dash_hear = QCheckBox("👂 Hear the people too (not only the translations)")
        self.dash_hear.setChecked(self.engine.hear_originals)
        self.dash_hear.toggled.connect(self._on_hear_toggled)
        speak = self.bind(QCheckBox("🔊 Speak the translations (off: only show the text of who is talking)"),
                          "incoming.speak")
        speak.setToolTip("Off: the translations are only shown as text (subtitles window and Live tab) and you hear "
                         "the people in the call with their own voices.")
        speak.clicked.connect(self._on_speak_clicked)
        lay.addWidget(speak)
        lay.addWidget(self.dash_hear)
        lay.addWidget(_muted("Translates what people say in a call and speaks your words in their language. "
                             "Set up the audio once in the Setup tab."))
        lay.addStretch(1)
        return box

    def _dash_chat_card(self):
        box, lay = self._card("💬  Chat translation (texts, DMs)")
        self.dash_chat_status = _Status()
        lay.addWidget(self.dash_chat_status)
        self.dash_chat_btn = self._dash_button(self.toggle_chat)
        lay.addWidget(self.dash_chat_btn)
        f = QFormLayout()
        f.addRow("Translate to", self.bind(LangCombo(), "chat.target_lang"))
        from .text_tab import DISPLAY_MODES
        f.addRow("Show translations", self.bind(DataCombo(DISPLAY_MODES), "chat.display"))
        lay.addLayout(f)
        row = QHBoxLayout()
        row.addWidget(self.bind(QCheckBox("Read out loud"), "chat.speak"))
        row.addWidget(self.bind(DataCombo([("queue", "one after the other"),
                                           ("interrupt", "new one interrupts")]), "chat.speak_mode"), 1)
        lay.addLayout(row)
        lay.addStretch(1)
        return box


    def _dash_you_card(self):
        box, lay = self._card("👤  You")
        f = QFormLayout()
        me = self.bind(QLineEdit(), "chat.my_name")
        me.setPlaceholderText("e.g. BMG - your own messages are not translated")
        f.addRow("My Discord name", me)
        f.addRow("Write to them in", self.bind(DataCombo([("auto", "Auto - the language used in the chat")]
                                                         + L.choices(False)), "chat.compose_lang"))
        lay.addLayout(f)
        lay.addWidget(_muted("'Write to them in' is used by Ctrl+Alt+Y (translate what you typed in Discord) "
                             "and the Text tab's compose box."))
        lay.addStretch(1)
        return box

    def _dash_tools_card(self):
        box, lay = self._card("🧰  Tools")
        lay.addWidget(self.bind(QCheckBox("Translate text I highlight with the mouse"), "chat.select_translate"))
        lay.addWidget(self.bind(DataCombo([("discord", "only in Discord"),
                                           ("everywhere", "everywhere (browsers, games…)")]), "chat.select_scope"))
        row = QHBoxLayout()
        ocr = QPushButton("📷 Translate text on screen")
        ocr.setToolTip("Select an area of the screen and translate the text in it (OCR)")
        ocr.clicked.connect(self.start_ocr)
        self.dash_subs_btn = QPushButton("Subtitles window")
        self.dash_subs_btn.setCheckable(True)
        self.dash_subs_btn.toggled.connect(lambda on: self.overlay.setVisible(on))
        row.addWidget(ocr)
        row.addWidget(self.dash_subs_btn)
        lay.addLayout(row)
        lay.addStretch(1)
        return box

    def _dash_hotkeys_card(self):
        box, lay = self._card("⌨  Hotkeys")
        self.dash_hotkeys = QLabel()
        self.dash_hotkeys.setTextFormat(Qt.RichText)
        self.dash_hotkeys.setWordWrap(True)
        lay.addWidget(self.dash_hotkeys)
        lay.addWidget(_muted("Change them in the Settings tab."))
        lay.addStretch(1)
        return box

    # ------------------------------------------------------------------ live state
    def _dash_set_button(self, b: QPushButton, on: bool, on_text: str, off_text: str):
        text = on_text if on else off_text
        if b.text() != tr(text):
            b.setText(text)
            b.setObjectName("danger" if on else "primary")
            b.style().unpolish(b)
            b.style().polish(b)

    def _dash_refresh(self):
        c = self.colors
        # voice
        on = self.engine.running
        stages = [s.text() for s in (self.in_stage, self.out_stage) if source(s) not in ("idle", "")]
        self.dash_voice_status.set(c, "on" if on else "off",
                                   ("Running" + (f" - {', '.join(stages)}" if stages else "")) if on else "Off")
        self._dash_set_button(self.dash_voice_btn, on, "■  Stop voice translator", "▶  Start voice translator")
        # chat
        on = self.chat.reader_running and not self.chat._reader_stop.is_set()
        txt = source(self.chat_status) if on else "Off"
        if on and txt.strip().lower() in ("", "off", "chat translation off"):
            txt = "Starting…"
        ok = on and "not found" not in txt and txt != "Starting…"
        self.dash_chat_status.set(c, "on" if ok else ("busy" if on else "off"), txt)
        self._dash_set_button(self.dash_chat_btn, on, "■  Stop chat translation", "▶  Start chat translation")
        # tools
        for b in (self.dash_subs_btn, self.overlay_btn):
            b.blockSignals(True)
            b.setChecked(self.overlay.isVisible())
            b.blockSignals(False)
        self._dash_refresh_hotkeys(c)


    def _dash_refresh_hotkeys(self, c):
        ch, inp = self.profile["chat"], self.profile["input"]
        keys = [("Translate highlighted text", ch.get("hotkey_selection")),
                ("Translate what I typed in Discord", ch.get("hotkey_draft")),
                ("Translate text on screen (OCR)", ch.get("hotkey_ocr")),
                ("Show originals / translations", ch.get("hotkey_inline")),
                ("Start / stop voice translator (in the app)", "F5"),
                ("Push-to-talk (voice, PTT mode)", inp.get("ptt_key")),
                ("Hear the people in the call on / off", inp.get("hear_key"))]
        rows = "".join(f"<tr><td style='padding-right:10px'><b>{html.escape((k or '-').upper())}</b></td>"
                       f"<td style='color:{c['muted']}'>{html.escape(tr(label))}</td></tr>" for label, k in keys)
        self.dash_hotkeys.setText(f"<table>{rows}</table>")

    def _dash_feed(self, ev: dict):
        """Called for every event: keeps the latest voice and chat translations."""
        t = ev.get("type")
        if t == "chat_line":
            item = {"kind": "💬", "who": ev.get("author") or "?", "src": ev.get("src"), "tgt": ev.get("tgt"),
                    "translated": ev.get("translated", ""), "original": ev.get("original", "")}
        elif t == "line":
            item = {"kind": "🎧", "who": tr("Them") if ev.get("dir") == "incoming" else tr("Me"), "src": ev.get("src"),
                    "tgt": ev.get("tgt"), "translated": ev.get("translated", ""), "original": ev.get("original", "")}
        else:
            return
        item["time"] = time.strftime("%H:%M")
        self._dash_items = (self._dash_items + [item])[-MAX_FEED:]
        self._dash_render_feed()

    def _dash_render_feed(self):
        c = self.colors
        parts = []
        for it in reversed(self._dash_items):
            meta = f"{it['time']} · {L.name(it['src']) if it.get('src') else '?'} → {L.name(it['tgt'])}"
            parts.append(f"<div style='margin:2px 0 8px 0'>{it['kind']} <b style='color:{c['incoming']}'>"
                         f"{html.escape(it['who'])}</b> <span style='color:{c['muted']}; font-size:8.5pt'>{meta}"
                         f"</span><br>{html.escape(it['translated'])}<br><span style='color:{c['muted']}'>"
                         f"{html.escape(it['original'][:300])}</span></div>")
        self.dash_feed.setHtml("".join(parts) or f"<span style='color:{c['muted']}'>"
                                                 f"{tr('Translations will appear here.')}</span>")
