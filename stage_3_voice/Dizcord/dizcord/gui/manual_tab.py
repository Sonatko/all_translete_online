"""'Manual' tab: the user manual in the app language, chapter by chapter, read aloud by a natural voice in that
language (offline; an online voice and the Windows voices can be picked too).

Moving to another chapter - with Next / Previous or by clicking the list - cuts the voice that was reading the
old chapter, shows the new chapter and starts reading it. The narrator is silent whenever the tab is not visible."""
from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QSlider, QTextBrowser,
                               QVBoxLayout, QWidget)

from .. import config, i18n
from ..manual import chapters, speakable
from ..natural import EDGE as _NATURAL, PIPER as _PIPER, NaturalNarrator
from ..sapi import Narrator
from .widgets import DataCombo

# voice ids in the combo: "piper:<voice>" (natural, offline), "edge:<voice>" (natural, online),
# "sapi:<Windows voice>" (robotic, offline)
_WINDOWS = "sapi:"


class _Bridge(QObject):
    """Lets the voice threads report a problem to the window thread: (engine, message)."""
    failed = Signal(str, str)


class ManualTabMixin:
    """Mixed into MainWindow. Needs: tabs, state, setStatus."""

    # ------------------------------------------------------------------ build
    def _build_manual_tab(self) -> QWidget:
        saved = self.state.get("manual") or {}
        self._narrator: Narrator | None = None            # Windows voice: created the first time it is needed (loads COM)
        self._windows_items: list[tuple[str, str]] = []
        self._bridge = _Bridge()
        self._bridge.failed.connect(self._manual_natural_failed)
        self._natural = NaturalNarrator(on_error=self._bridge.failed.emit)
        self._manual_index = 0
        self._chapters = chapters(i18n.current().code)
        w = QWidget()
        root = QHBoxLayout(w)

        self.manual_list = QListWidget()
        self.manual_list.setFixedWidth(250)
        for ch in self._chapters:
            self.manual_list.addItem(i18n.tr(ch.title))
        left = QVBoxLayout()
        left.addWidget(self.manual_list, 1)
        replay = QPushButton("▶ Replay the guided tour")
        replay.setToolTip("Show the first steps again, one at a time")
        replay.clicked.connect(self._manual_replay_tour)
        left.addWidget(replay)
        root.addLayout(left)

        right = QVBoxLayout()
        self.manual_view = QTextBrowser()
        self.manual_view.setOpenExternalLinks(True)
        right.addWidget(self.manual_view, 1)

        nav = QHBoxLayout()
        self.manual_prev = QPushButton("◀ Previous")
        self.manual_prev.setToolTip("Previous chapter - the voice stops the current one and reads that one")
        self.manual_next = QPushButton("Next ▶")
        self.manual_next.setObjectName("primary")
        self.manual_next.setToolTip("Next chapter - the voice stops the current one and reads that one")
        self.manual_pos = QLabel()
        nav.addWidget(self.manual_prev)
        nav.addWidget(self.manual_next)
        nav.addWidget(self.manual_pos)
        nav.addStretch(1)
        right.addLayout(nav)

        voice = QHBoxLayout()
        self.manual_speak = QCheckBox("🔊 Read aloud")
        self.manual_speak.setChecked(bool(saved.get("speak", True)))
        again = QPushButton("🔁 Read again")
        stop = QPushButton("⏹ Stop")
        self.manual_voice = DataCombo(self._manual_items())
        self.manual_voice.setMinimumWidth(300)
        self.manual_speed = QSlider(Qt.Horizontal)
        self.manual_speed.setRange(-6, 6)
        self.manual_speed.setValue(int(saved.get("rate", 0)))
        self.manual_speed.setFixedWidth(110)
        self.manual_speed.setToolTip("Speed of the voice")
        voice.addWidget(self.manual_speak)
        voice.addWidget(again)
        voice.addWidget(stop)
        voice.addSpacing(12)
        voice.addWidget(QLabel("Voice"))
        voice.addWidget(self.manual_voice, 1)
        voice.addWidget(QLabel("Speed"))
        voice.addWidget(self.manual_speed)
        right.addLayout(voice)
        self.manual_note = QLabel("")
        self.manual_note.setWordWrap(True)
        self.manual_note.setObjectName("muted")
        right.addWidget(self.manual_note)
        root.addLayout(right, 1)

        self.manual_list.currentRowChanged.connect(lambda i: i >= 0 and self._manual_goto(i))
        self.manual_prev.clicked.connect(lambda: self._manual_goto(self._manual_index - 1))
        self.manual_next.clicked.connect(lambda: self._manual_goto(self._manual_index + 1))
        again.clicked.connect(lambda: self._manual_read())
        stop.clicked.connect(self._manual_stop)
        self.manual_speak.toggled.connect(self._manual_speak_toggled)
        self.manual_voice.changed.connect(self._manual_voice_changed)
        self.manual_speed.valueChanged.connect(self._manual_speed_changed)
        code = i18n.current().code
        pick = (saved.get("voices") or {}).get(code) or (saved.get("voice") if code == "en" else "") or ""
        if pick and not pick.startswith((_NATURAL, _WINDOWS)):      # saved by an older version: a Windows voice name
            pick = _WINDOWS + pick
        if not pick and self._natural.piper_ok:
            pick = _PIPER + self._natural.piper_voices()[0][0]          # offline natural voice: works from the first run
        elif not pick and self._natural.edge_ok:
            pick = _NATURAL + self._natural.edge_voices()[0][0]
        self._manual_saved_voice = pick
        self.manual_voice.blockSignals(True)
        self.manual_voice.setValue(pick)
        self.manual_voice.blockSignals(False)
        self._natural.warm_up(self._manual_current_voice())      # load the offline voice now, while the app starts
        self.manual_tab_widget = w
        self._manual_show(0)
        return w

    # ------------------------------------------------------------------ narrator
    def _manual_items(self) -> list[tuple[str, str]]:
        """Voices in the list: natural ones first (online), then the voices built into Windows (offline)."""
        items = []
        if self._natural.piper_ok:
            items += [(_PIPER + vid, i18n.tr("★ Natural - {0}  (offline)").format(label))
                      for vid, label in self._natural.piper_voices()]
        if self._natural.edge_ok:
            items += [(_NATURAL + vid, i18n.tr("★ Natural - {0}  (needs internet)").format(label))
                      for vid, label in self._natural.edge_voices()]
        return items + self._windows_items

    def _manual_current_voice(self) -> str:
        return self.manual_voice.value() or self._manual_saved_voice or ""

    def _manual_narrator(self) -> Narrator:
        """The Windows voice (offline). Created on first use; its voices are added to the list."""
        if self._narrator is None:
            n = Narrator()
            if n.available:
                voices = n.voices()
                self._windows_items = [(_WINDOWS + name, i18n.tr("Windows - {0}  (offline)").format(name))
                                       for _i, name, _l in voices]
                self.manual_voice.set_items(self._manual_items())
                names = [name for _i, name, _l in voices]
                wanted = self._manual_current_voice()
                pick = wanted[len(_WINDOWS):] if wanted.startswith(_WINDOWS) and wanted[len(_WINDOWS):] in names else \
                    (names[n.default_voice(i18n.current().code)] if names else "")
                if pick:
                    n.set_voice(names.index(pick))
                    if wanted.startswith(_WINDOWS) or not wanted:
                        self.manual_voice.blockSignals(True)
                        self.manual_voice.setValue(_WINDOWS + pick)
                        self.manual_voice.blockSignals(False)
                n.set_rate(self.manual_speed.value())
                if not self._natural.available and not n.has_voice(i18n.current().code):
                    self.manual_note.setText("No Windows voice for this language is installed. Add one in Windows "
                                             "Settings → Time & language → Speech.")
            elif not self._natural.available:
                self.manual_note.setText("No voice is available on this PC - the manual is shown as text only.")
                self.manual_speak.setEnabled(False)
            self._narrator = n
        return self._narrator

    def _manual_read(self):
        """Read the chapter on screen from its beginning (the previous reading is cut first)."""
        text = speakable(self._chapters[self._manual_index].body)
        voice = self._manual_current_voice()
        online = voice.startswith(_NATURAL) and self._natural.edge_ok
        offline = voice.startswith(_PIPER) and self._natural.piper_ok
        if online or offline:
            self.manual_note.setText("")
            self._manual_stop()
            self._natural.speak(text, voice, self.manual_speed.value() * 8)
        else:
            self._manual_read_windows(text)

    def _manual_read_windows(self, text: str):
        n = self._manual_narrator()
        self._manual_stop()
        n.speak(text)

    def _manual_natural_failed(self, engine: str, _msg: str):
        """A natural voice failed. The online one (no internet) falls back to the offline natural voice if it is
        installed, and any natural voice falls back to the robotic Windows voice as the last resort."""
        if not self.manual_speak.isChecked() or not self._manual_tab_visible():
            return
        text = speakable(self._chapters[self._manual_index].body)
        if engine == _NATURAL and self._natural.piper_ok:
            self.manual_note.setText("The online voice needs internet - reading with the offline natural voice instead.")
            self._natural.speak(text, _PIPER + self._natural.piper_voices()[0][0], self.manual_speed.value() * 8)
            return
        self.manual_note.setText("The natural voice is not available - reading with the Windows voice instead.")
        self._manual_read_windows(text)

    def _manual_stop(self):
        self._natural.stop()
        if self._narrator is not None:
            self._narrator.stop()

    # ------------------------------------------------------------------ navigation
    def _manual_show(self, i: int):
        self._manual_index = i
        self.manual_view.setMarkdown(self._chapters[i].body.strip())
        self.manual_view.verticalScrollBar().setValue(0)
        self.manual_pos.setText(f"   Chapter {i + 1} of {len(self._chapters)}")
        self.manual_prev.setEnabled(i > 0)
        self.manual_next.setEnabled(i < len(self._chapters) - 1)
        self.manual_list.blockSignals(True)
        self.manual_list.setCurrentRow(i)
        self.manual_list.blockSignals(False)

    def _manual_goto(self, i: int):
        i = max(0, min(len(self._chapters) - 1, i))
        changed = i != self._manual_index
        self._manual_stop()                      # the old chapter is cut at once
        self._manual_show(i)                     # the new chapter is shown...
        if changed and self.manual_speak.isChecked() and self._manual_tab_visible():
            self._manual_read()                  # ...and read

    def _manual_tab_visible(self) -> bool:
        return self.tabs.currentWidget() is getattr(self, "manual_tab_widget", None)

    # ------------------------------------------------------------------ settings, hooks
    def _manual_speak_toggled(self, on: bool):
        if on and self._manual_tab_visible():
            self._manual_read()
        elif not on:
            self._manual_stop()
        self._manual_save()

    def _manual_voice_changed(self):
        voice = self.manual_voice.value() or ""
        self._natural.warm_up(voice)
        if voice.startswith(_WINDOWS):
            n = self._manual_narrator()
            names = [v[1] for v in n.voices()]
            if voice[len(_WINDOWS):] in names:
                n.set_voice(names.index(voice[len(_WINDOWS):]))
        if voice and self.manual_speak.isChecked() and self._manual_tab_visible():
            self._manual_read()
        self._manual_save()

    def _manual_speed_changed(self, v: int):
        if self._narrator is not None:
            self._narrator.set_rate(v)
        self._manual_save()

    def _manual_save(self):
        voices = dict((self.state.get("manual") or {}).get("voices") or {})
        voices[i18n.current().code] = self.manual_voice.value() or self._manual_saved_voice   # one voice per language
        self.state["manual"] = {"speak": self.manual_speak.isChecked(), "rate": self.manual_speed.value(),
                                "voices": voices}
        try:
            config.save_app_state(self.state)
        except Exception:  # noqa: BLE001
            pass

    def _manual_tab_changed(self):
        """Called by MainWindow when the user changes tab: read when the Manual opens, be silent when it closes."""
        if getattr(self, "manual_tab_widget", None) is None:
            return
        if self._manual_tab_visible():
            self._manual_narrator()                  # makes the offline Windows voices appear in the list
            if self.manual_speak.isChecked():
                self._manual_read()
        else:
            self._manual_stop()

    def _manual_replay_tour(self):
        self._manual_stop()
        if hasattr(self, "start_tour"):
            self.start_tour()

    def _manual_close(self):
        if hasattr(self, "_natural"):            # the Manual tab is only built in the public edition
            self._manual_stop()
