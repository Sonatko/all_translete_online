"""'Text' tab: Discord chat translation, highlight-to-translate, write-in-their-language, screen OCR."""
from __future__ import annotations

import html
import threading
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox, QTextBrowser, QVBoxLayout, QWidget)

from .. import languages as L
from ..chat import ocr
from ..chat.service import ChatService
from .text_widgets import ChatOverlay, InlineOverlay, OcrResultBox, TranslationPopup, select_area
from ..providers import REGISTRY
from .widgets import DataCombo, LangCombo, run_async

CHAT_RESTART_KEYS = ("select_translate", "select_scope", "hotkey_selection", "hotkey_draft", "hotkey_ocr",
                     "hotkey_inline", "clipboard_watch")


DISPLAY_MODES = [("inline", "Inside Discord - on top of each message"),
                 ("window", "In a small window next to Discord"),
                 ("both", "Both")]


def _hint(text):
    lb = QLabel(text)
    lb.setWordWrap(True)
    lb.setObjectName("muted")
    return lb


class TextTabMixin:
    """Mixed into MainWindow. Needs: bind, profile, engine, colors, on_change, setStatus, _log, bridge."""

    # ------------------------------------------------------------------ setup
    def _init_text(self):
        self.chat = ChatService(self.engine, self.bridge.event.emit)
        self.popup = TranslationPopup(self.colors)
        self.ocr_box = OcrResultBox(self.colors)
        self.chat_overlay = ChatOverlay(self.colors, self.profile["chat"])
        self.inline = InlineOverlay(self.colors)
        self.chat_overlay.turned_off.connect(self._chat_overlay_off)
        self.inline.avoid = [self.chat_overlay, self.popup, self.ocr_box]   # never draw under our own windows
        self.chat_overlay.geometry_changed.connect(self.inline.update)
        if self.state.get("chat_overlay_geometry"):
            x, y, w, h = self.state["chat_overlay_geometry"]
            self.chat_overlay.setGeometry(x, y, w, h)
            self.chat_overlay.moved_by_user = bool(self.state.get("chat_overlay_moved"))
        self._ocr_area = None
        self._discord_front = True        # updated by the chat reader: Discord (or Dizcord) is the active window
        self._window_waiting = False      # small window hidden because Discord is in the background
        self._ocr_last_text = ""
        self._ocr_timer = QTimer(self)
        self._ocr_timer.timeout.connect(lambda: self._run_ocr(self._ocr_area, quiet=True))
        self._chat_keys_snapshot = None
        self.chat.start_selection()
        self._chat_keys_snapshot = {k: self.profile["chat"].get(k) for k in CHAT_RESTART_KEYS}
        if self.profile["chat"].get("auto_translate"):
            self.chat.start_reader()
            if self._show_window():
                self.chat_overlay.show()

    def _build_text_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        # ---------------------------------------------------------- Discord chat
        box = QGroupBox("Discord messages (servers, DMs, threads, forum posts)")
        bl = QVBoxLayout(box)
        row = QHBoxLayout()
        self.chat_toggle = QPushButton("▶ Start translating chat")
        self.chat_toggle.setObjectName("primary")
        self.chat_toggle.clicked.connect(self.toggle_chat)
        now = QPushButton("Translate visible messages now")
        now.clicked.connect(self._chat_translate_now)
        ov = QPushButton("Show small window")
        ov.clicked.connect(self._show_chat_overlay)
        self.chat_status = QLabel("off")
        self.chat_status.setObjectName("muted")
        row.addWidget(self.chat_toggle)
        row.addWidget(now)
        row.addWidget(ov)
        row.addWidget(self.chat_status, 1)
        bl.addLayout(row)
        bl.addWidget(_hint("Reads the messages shown in the Discord app (like a screen reader would) and translates "
                           "new ones. Nothing is sent to Discord and no account token is used."))
        f = QFormLayout()
        f.addRow("Translate to", self.bind(LangCombo(), "chat.target_lang"))
        engines = sorted(((pid, cls.label()) for pid, cls in REGISTRY["translate"].items() if pid != "none"),
                         key=lambda x: x[1])
        eng = self.bind(DataCombo([("", "Same as the Translation tab")] + engines), "chat.engine")
        eng.setToolTip("Engine for chat messages, highlighted text, OCR and 'write in their language'. "
                       "Google Translate (free) is the fastest; an AI model gives the most natural text.")
        f.addRow("Engine for text", eng)
        f.addRow(self.bind(QCheckBox("Skip messages already in that language"), "chat.skip_same_language"))
        f.addRow(self.bind(QCheckBox("Include embeds (bot cards, link previews)"), "chat.include_embeds"))
        me = self.bind(QLineEdit(), "chat.my_name")
        me.setPlaceholderText("your display name - your own messages are skipped")
        f.addRow("My Discord name", me)
        hist = QSpinBox()
        hist.setRange(0, 50)
        f.addRow("When I open a channel, translate the last", self.bind(hist, "chat.history"))
        poll = QSpinBox()
        poll.setRange(300, 10000)
        poll.setSingleStep(100)
        poll.setSuffix(" ms")
        f.addRow("Check for new messages every", self.bind(poll, "chat.poll_ms"))
        self.display_combo = self.bind(DataCombo(DISPLAY_MODES), "chat.display")
        f.addRow("Show translations", self.display_combo)
        ik = self.bind(QLineEdit(), "chat.hotkey_inline")
        ik.setPlaceholderText("e.g. ctrl+alt+i")
        f.addRow("Hotkey: show originals / translations", ik)
        f.addRow(self.bind(QCheckBox("Dock the small window to the Discord window"), "chat.overlay_attach"))
        ol = QSpinBox()
        ol.setRange(1, 20)
        f.addRow("Messages in the small window", self.bind(ol, "chat.overlay_lines"))
        f.addRow(self.bind(QCheckBox("Read translated messages out loud"), "chat.speak"))
        f.addRow("When a new message arrives while one is being read",
                 self.bind(DataCombo([("queue", "Wait - read them one after the other"),
                                      ("interrupt", "Interrupt - stop the old one and read the new one")]),
                           "chat.speak_mode"))
        bl.addLayout(f)
        self.chat_log = QTextBrowser()
        self.chat_log.setMinimumHeight(200)
        bl.addWidget(self.chat_log)
        v.addWidget(box)

        # ---------------------------------------------------------- selection
        box = QGroupBox("Highlight to translate")
        f = QFormLayout(box)
        f.addRow(self.bind(QCheckBox("Translate text when I highlight it with the mouse (drag or double-click)"),
                           "chat.select_translate"))
        f.addRow("Where", self.bind(DataCombo([("discord", "Only in Discord"),
                                               ("everywhere", "Everywhere (browsers, games, documents…)")]),
                                    "chat.select_scope"))
        ps = QSpinBox()
        ps.setRange(2, 120)
        ps.setSuffix(" s")
        f.addRow("Popup stays for", self.bind(ps, "chat.popup_seconds"))
        hk = self.bind(QLineEdit(), "chat.hotkey_selection")
        hk.setPlaceholderText("e.g. ctrl+alt+t")
        f.addRow("Hotkey: translate selection (any app)", hk)
        f.addRow(self.bind(QCheckBox("Also translate everything I copy (Ctrl+C)"), "chat.clipboard_watch"))
        f.addRow(_hint("In Discord the selected text is read directly. In other apps the app reads the selection "
                       "through Windows accessibility, or briefly copies it (your clipboard is restored)."))
        v.addWidget(box)

        # ---------------------------------------------------------- compose
        box = QGroupBox("Write in their language")
        bl = QVBoxLayout(box)
        self.compose_in = QPlainTextEdit()
        self.compose_in.setPlaceholderText("Type in your language…  (Ctrl+Enter = translate)")
        self.compose_in.setMaximumHeight(80)
        bl.addWidget(self.compose_in)
        row = QHBoxLayout()
        row.addWidget(QLabel("Translate to"))
        self.compose_lang = self.bind(DataCombo([("auto", "Auto - the language used in the chat")]
                                                + L.choices(False)), "chat.compose_lang")
        row.addWidget(self.compose_lang, 1)
        tb = QPushButton("Translate")
        tb.setObjectName("primary")
        tb.clicked.connect(self.compose_translate)
        row.addWidget(tb)
        bl.addLayout(row)
        self.compose_out = QPlainTextEdit()
        self.compose_out.setPlaceholderText("Translation (you can edit it before sending)")
        self.compose_out.setMaximumHeight(80)
        bl.addWidget(self.compose_out)
        row = QHBoxLayout()
        for text, fn in [("Copy", self._compose_copy), ("Paste into Discord", lambda: self._compose_send(False)),
                         ("Send to Discord", lambda: self._compose_send(True))]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        self.compose_note = QLabel()
        self.compose_note.setObjectName("muted")
        row.addWidget(self.compose_note, 1)
        bl.addLayout(row)
        f = QFormLayout()
        dk = self.bind(QLineEdit(), "chat.hotkey_draft")
        dk.setPlaceholderText("e.g. ctrl+alt+y")
        f.addRow("Hotkey: translate what I typed in Discord", dk)
        f.addRow(self.bind(QCheckBox("…and press Enter to send it"), "chat.draft_send"))
        bl.addLayout(f)
        bl.addWidget(_hint("Type your message in Discord's box in your language, press the hotkey, and it is replaced "
                           "by the translation (in the language people use in that chat)."))
        v.addWidget(box)
        self.compose_in.installEventFilter(self)

        # ---------------------------------------------------------- OCR
        box = QGroupBox("Text on screen (images, games, videos…) - OCR")
        f = QFormLayout(box)
        row = QHBoxLayout()
        ob = QPushButton("Select an area and translate")
        ob.clicked.connect(self.start_ocr)
        row.addWidget(ob)
        self.ocr_watch = QCheckBox("Keep translating that area every")
        self.ocr_watch.toggled.connect(self._toggle_ocr_watch)
        self.ocr_interval = QSpinBox()
        self.ocr_interval.setRange(1, 60)
        self.ocr_interval.setValue(3)
        self.ocr_interval.setSuffix(" s")
        row.addWidget(self.ocr_watch)
        row.addWidget(self.ocr_interval)
        row.addStretch(1)
        f.addRow(row)
        okk = self.bind(QLineEdit(), "chat.hotkey_ocr")
        okk.setPlaceholderText("e.g. ctrl+alt+o")
        f.addRow("Hotkey: select area", okk)
        langs = ocr.languages()
        self.ocr_lang = self.bind(DataCombo([("auto", "Auto (Windows languages)")] + [(t, t) for t in langs]),
                                  "chat.ocr_lang")
        f.addRow("Text language on screen", self.ocr_lang)
        f.addRow(_hint(f"Uses Windows' built-in OCR. Installed: {', '.join(langs) or 'none'}. To read other "
                       "alphabets (Russian, Japanese…) add that language in Windows Settings → Time & language → "
                       "Language & region (with 'Optical character recognition')."))
        v.addWidget(box)
        v.addStretch(1)
        return w

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "compose_in", None) and ev.type() == ev.Type.KeyPress:
            if ev.key() in (Qt.Key_Return, Qt.Key_Enter) and ev.modifiers() & Qt.ControlModifier:
                self.compose_translate()
                return True
        return super().eventFilter(obj, ev)

    # ------------------------------------------------------------------ chat
    def toggle_chat(self):
        on = not self.chat.reader_running or self.chat._reader_stop.is_set()
        self.profile["chat"]["auto_translate"] = on
        self.engine.profile["chat"]["auto_translate"] = on
        self.dirty = True
        self._update_title()
        if on:
            self.chat.start_reader()
            if self._show_window():
                self._show_chat_overlay()
        else:
            self.chat.stop_reader()
        self._update_chat_toggle(on)

    def _update_chat_toggle(self, on):
        self.chat_toggle.setText("■ Stop translating chat" if on else "▶ Start translating chat")
        self.chat_toggle.setObjectName("danger" if on else "primary")
        self.chat_toggle.style().unpolish(self.chat_toggle)
        self.chat_toggle.style().polish(self.chat_toggle)
        if hasattr(self, "chat_btn"):
            self.chat_btn.blockSignals(True)
            self.chat_btn.setChecked(on)
            self.chat_btn.blockSignals(False)

    def _chat_translate_now(self):
        self.chat.translate_visible_now()
        self._update_chat_toggle(True)
        self.profile["chat"]["auto_translate"] = True

    def _show_chat_overlay(self):
        self.chat_overlay.apply(self.colors, self.profile["chat"])
        self.chat_overlay.show()
        self.chat_overlay.raise_()

    def _chat_overlay_off(self):
        """Right-click → Don't show this window: same as unticking 'Show the floating chat overlay'."""
        self.display_combo.setValue("inline")   # updates the profile through the normal binding
        self.setStatus("Small window off - translations show inside Discord. Change it in the Text tab "
                       "(Show translations).")

    def _show_window(self) -> bool:
        return self.profile["chat"].get("display", "inline") in ("window", "both")

    def _show_inline(self) -> bool:
        return self.profile["chat"].get("display", "inline") in ("inline", "both")

    def _text_on_change(self):
        """Called from MainWindow.on_change."""
        self.chat_overlay.apply(self.colors, self.profile["chat"])
        if not self._show_window():
            self.chat_overlay.hide()
        elif self.chat.reader_running and not self.chat._reader_stop.is_set() and self.chat_overlay.items \
                and self._discord_front:
            self.chat_overlay.show()
        if not self._show_inline():
            self.inline.hide()
        snap = {k: self.profile["chat"].get(k) for k in CHAT_RESTART_KEYS}
        if self._chat_keys_snapshot is not None and snap != self._chat_keys_snapshot:
            self._chat_keys_snapshot = snap
            self.chat.start_selection()

    def _text_theme_changed(self):
        for wdg in (self.popup, self.ocr_box, self.chat_overlay, self.inline):
            wdg.colors = self.colors
            wdg.update()
        self.chat_overlay.apply(self.colors, self.profile["chat"])

    # ------------------------------------------------------------------ events
    def handle_text_event(self, ev: dict) -> bool:
        t = ev.get("type")
        c = self.colors
        if t == "chat_line":
            meta = f"{L.name(ev['src']) if ev.get('src') else '?'} → {L.name(ev['tgt'])}"
            if ev.get("edited"):
                meta += " · edited"
            self.chat_log.append(
                f"<div style='margin:3px 0 7px 0'><b style='color:{c['incoming']}'>{html.escape(ev['author'])}</b> "
                f"<span style='color:{c['muted']}; font-size:8.5pt'>{html.escape(ev.get('timestamp') or '')} · "
                f"{meta}</span><br><span style='font-size:11pt'>{html.escape(ev['translated'])}</span><br>"
                f"<span style='color:{c['muted']}'>{html.escape(ev['original'][:500])}</span></div>")
            self.inline.add(ev["id"], ev["translated"])
            if self._show_window():
                self.chat_overlay.add(ev)
                if not self._discord_front:
                    self._window_waiting = True      # appears when you switch back to Discord
                elif not self.chat_overlay.isVisible():
                    self.chat_overlay.show()
            if self.profile["ui"].get("autosave_transcript", True):
                self._autosave({"dir": "incoming", "time": time.strftime("%H:%M:%S"),
                                "src": ev.get("src"), "tgt": ev["tgt"], "translated": f"[chat] {ev['author']}: "
                                f"{ev['translated']}", "original": ev["original"]})
        elif t == "discord_focus":
            self._discord_front = ev["on"]
            if not ev["on"]:
                if self.chat_overlay.isVisible():
                    self.chat_overlay.hide()
                    self._window_waiting = True
            elif self._window_waiting:
                self._window_waiting = False
                if self._show_window() and self.chat.reader_running and not self.chat._reader_stop.is_set():
                    self.chat_overlay.show()
        elif t == "chat_inline":
            if ev["state"] == "show" and self._show_inline():
                self.inline.show_items(ev["window"], ev["items"])
            else:
                self.inline.hide()
        elif t == "inline_toggle":
            shown = self.inline.toggle()
            self.setStatus("Showing translations in Discord" if shown else "Showing the original messages "
                           f"({self.profile['chat'].get('hotkey_inline') or 'hotkey'} to switch back)")
        elif t == "chat_channel":
            self.inline.clear()
            self.chat_log.append(f"<div style='color:{c['accent']}; margin-top:8px'>── "
                                 f"{html.escape(ev['channel'] or '')} ──</div>")
        elif t == "chat_status":
            self.chat_status.setText(ev["text"])
            self.chat_status.setObjectName("ok" if ev.get("ok") else "muted")
            self.chat_status.style().unpolish(self.chat_status)
            self.chat_status.style().polish(self.chat_status)
        elif t == "chat_window":
            self.chat_overlay.dock_to(ev["rect"])
        elif t == "chat_error":
            self.setStatus("⚠ " + ev["text"], error=True)
            self._log(ev["text"])
        elif t == "popup":
            title = {"select": "", "hotkey": "", "clipboard": "Copied text · ", "draft": "Your draft · "}.get(
                ev.get("kind"), "")
            self.popup.show_translation(ev["original"], ev["translated"], ev.get("src"), ev["tgt"], ev["x"], ev["y"],
                                        self.profile["chat"].get("popup_seconds", 10), title)
        elif t == "ocr_request":
            self.start_ocr()
        else:
            return False
        return True

    # ------------------------------------------------------------------ compose
    def compose_translate(self):
        text = self.compose_in.toPlainText().strip()
        if not text:
            return
        target = self.chat.compose_target()
        self.compose_note.setText(f"Translating to {L.name(target)}…")
        run_async(lambda: self.chat.translate(text, target),
                  lambda r, e: self._compose_done(r, e, target))

    def _compose_done(self, res, err, target):
        if err:
            self.compose_note.setText(f"⚠ {err}")
            return
        self.compose_out.setPlainText(res[0])
        self.compose_note.setText(f"→ {L.name(target)}")

    def _compose_copy(self):
        QApplication.clipboard().setText(self.compose_out.toPlainText())
        self.compose_note.setText("Copied.")

    def _compose_send(self, enter: bool):
        text = self.compose_out.toPlainText().strip()
        if not text:
            self.compose_note.setText("Translate something first.")
            return
        self.compose_note.setText("Sending…" if enter else "Pasting…")

        def done(err, e2):
            msg = err or (f"⚠ {e2}" if e2 else ("Sent." if enter else "Pasted into Discord - press Enter there."))
            self.compose_note.setText(msg)
            if enter and not err and not e2:
                self.compose_in.clear()
                self.compose_out.clear()
        run_async(lambda: self.chat.send_to_discord(text, enter), done)

    # ------------------------------------------------------------------ OCR
    def start_ocr(self):
        if not ocr.available():
            self.setStatus("⚠ Screen OCR needs the winrt packages (run setup.bat)", error=True)
            return
        self.popup.hide()
        self.ocr_box.hide()
        QTimer.singleShot(120, lambda: select_area(self._ocr_selected))

    def _ocr_selected(self, rect):
        self._ocr_area = rect
        self._ocr_last_text = ""
        self._run_ocr(rect)

    def _toggle_ocr_watch(self, on):
        if on and self._ocr_area:
            self._ocr_timer.start(self.ocr_interval.value() * 1000)
        else:
            self._ocr_timer.stop()
            if on:
                self.setStatus("Select an area first.")
                self.ocr_watch.setChecked(False)

    def _run_ocr(self, rect, quiet=False):
        if not rect:
            return
        cfg = self.profile["chat"]
        target = cfg.get("target_lang") or self.profile["incoming"]["target_lang"]
        lang = cfg.get("ocr_lang", "auto")
        hide_box = self.ocr_box.isVisible() and quiet
        if hide_box:   # don't OCR our own translation box
            self.ocr_box.hide()

        def work():
            time.sleep(0.3)   # let the dimmed selector / our popups fade out first
            img = ocr.grab(*rect)
            text = ocr.paragraphs(ocr.recognize(img, lang))
            if quiet and text == self._ocr_last_text:
                return None
            self._ocr_last_text = text
            if not text.strip():
                return ("", "(no text found)", None)
            out, det = self.chat.translate(text, target)
            return (text, out, det)

        def done(res, err):
            if err:
                self.setStatus(f"⚠ OCR: {err}", error=True)
                if hide_box:
                    self.ocr_box.show()
                return
            if res is None:
                if hide_box:
                    self.ocr_box.show()
                return
            text, out, det = res
            self.ocr_box.show_result(rect, out, det, target)
            if text:
                self.chat_log.append(f"<div style='margin:3px 0 7px 0'><b style='color:{self.colors['outgoing']}'>"
                                     f"Screen text</b><br>{html.escape(out)}<br><span style='color:"
                                     f"{self.colors['muted']}'>{html.escape(text[:500])}</span></div>")
        run_async(work, done)

    def _text_close(self):
        self.chat.shutdown()
        g = self.chat_overlay.geometry()
        self.state["chat_overlay_geometry"] = [g.x(), g.y(), g.width(), g.height()]
        self.state["chat_overlay_moved"] = bool(self.chat_overlay.moved_by_user)
        for wdg in (self.popup, self.ocr_box, self.chat_overlay, self.inline):
            wdg.close()
