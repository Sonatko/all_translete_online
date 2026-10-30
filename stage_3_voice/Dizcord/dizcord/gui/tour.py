"""The guided tour: shown once, the first time the app opens after a fresh install (Manual tab → replay it).

A small panel walks through the first set-up step by step. Each step opens the right tab, highlights the control
it talks about, shows a ✔ when that step is done and can do it for you. Nothing is forced: Next skips a step that
is not done, Back returns to the previous one, and the step list jumps to any step. It is read aloud in the app language by
the offline natural voice; Next / Back cut the old step's voice at once, and the next and previous steps are
prepared in advance, so the voice starts right away.

The panel lives inside the main window and can't be dragged: for every step it is placed in the first corner of
the window that does not cover the highlighted control, so it never hides what it explains and never jumps back
somewhere the user did not expect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QEvent, QObject, QRect, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import config, i18n
from ..audio import devices
from ..i18n import tr
from ..manual import speakable
from ..natural import EDGE, PIPER, NaturalNarrator

MARGIN = 16
WIDTH = 420


@dataclass
class Step:
    title: str
    text: str
    target: Callable[[], object] | None = None           # widget, or list of widgets (highlighted together)
    check: Callable[[], bool] | None = None              # True = this step is done
    action: tuple[str, Callable[[], None]] | None = None  # (button text, what it does)


def steps(w) -> list[Step]:
    """The tour of the main window `w`."""
    free = config.TEMPLATES[0][0]

    def cable():
        return devices.find_virtual_cable()

    def use_cable():
        c = cable()
        if c:
            w.out_dev.setValue(c)
            w.on_change()

    return [
        Step("Welcome to Dizcord!",
             "This short guide shows you how to get started, one step at a time. Each step points at the part of "
             "the app it explains. Use Next and Back to move, and the speaker button to turn the voice on or off. "
             "You can skip the guide at any time: the Manual tab explains every part of the app."),
        Step("Choose a profile",
             "A profile keeps all your settings: engines, languages and devices. Start with 'Free - no keys "
             "needed'. It works without any account or payment. You can switch to paid engines later.",
             lambda: w.profile_combo,
             lambda: w.profile["name"] == free,
             ("Choose it for me", lambda: w.profile_combo.setValue(free))),
        Step("Install the virtual cable",
             "To speak into Discord, the app needs a free virtual audio cable: VB-Audio Virtual Cable. Install it "
             "once and restart your PC. When it is installed, you see a green check mark here.",
             lambda: w.setup_cable_label,
             lambda: bool(cable()),
             ("Download VB-Cable", lambda: QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/")))),
        Step("Send your voice to the cable",
             "Here you choose where your translated voice goes. Pick CABLE Input: Discord will hear it as a "
             "microphone.",
             lambda: w.out_dev,
             lambda: "cable input" in w.out_dev.value().lower(),
             ("Do it for me", use_cable)),
        Step("Set up Discord",
             "Now open Discord, User Settings, Voice and Video. Set the Input Device to CABLE Output and keep your "
             "headphones as the Output Device. Turn off Noise Suppression, Echo Cancellation and Automatic Gain "
             "Control: they can cut the translated voice."),
        Step("What the app listens to",
             "The app hears only the Discord app, so it never hears its own voice, your game or your music, and it "
             "keeps listening while it talks. Keep 'Only the Discord app'. You hear only the translations: press F9 "
             "to also hear the people.",
             lambda: w.listen_mode),
        Step("Your microphone",
             "Choose the microphone you really speak into. The app translates what you say and speaks it into "
             "Discord for you.",
             lambda: w.mic_device),
        Step("Choose the languages",
             "On the left: the language they speak, or Auto-detect, and the language you want to hear. On the "
             "right: the language you speak and the language they will hear.",
             lambda: [w.in_src.parentWidget(), w.out_src.parentWidget()]),
        Step("Start translating",
             "Press Start, or the F5 key. The first time, the speech model is downloaded, about 460 megabytes, so "
             "the first start takes a little longer. Press the button again to stop.",
             lambda: w.start_btn,
             lambda: w.engine.running),
        Step("Translate Discord messages",
             "Press Chat to translate text messages too. The translations appear right inside Discord, on top of "
             "each message, in servers, direct messages and threads.",
             lambda: w.chat_btn),
        Step("More tools",
             "Highlight any text with the mouse to translate it. Ctrl+Alt+O translates text on your screen, for "
             "example in a game or an image. The subtitles window shows the translations on top of your game.",
             lambda: w.dash_subs_btn.parentWidget()),
        Step("Voices and sound",
             "On the Voice tab you choose the voices and their speed, pitch and volume. The Settings tab has all "
             "sound devices in one place, and the language of the app.",
             lambda: w.voice_in.parentWidget()),
        Step("You are ready!",
             "That's it! The Manual tab explains every part of the app, read aloud in your language. Have fun!"),
    ]


def speech(step: Step) -> str:
    """What the voice says for a step, in the app language."""
    return speakable(f"{tr(step.title)}\n\n{tr(step.text)}")


def prepare_voice() -> None:
    """Called by main.py on a fresh install as soon as the language is chosen: loads the offline voice (a few
    seconds) and synthesises the first steps while the main window is being built, so the guide speaks at once."""
    n = NaturalNarrator()
    if n.piper_ok:
        voice = PIPER + n.piper_voices()[0][0]
        n.prefetch([speech(s) for s in steps(None)[:2]], voice)


class _Spotlight(QWidget):
    """A glowing frame drawn around the highlighted control. Clicks go through it."""

    def __init__(self, parent, color: str):
        super().__init__(parent)
        self.color = QColor(color)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._phase = 0
        self._pulse = QTimer(self)
        self._pulse.timeout.connect(self._tick)
        self._pulse.start(90)

    def _tick(self):
        self._phase = (self._phase + 1) % 20
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(self.color)
        c.setAlpha(140 + int(115 * abs(10 - self._phase) / 10))
        p.setPen(QPen(c, 3))
        p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)


class _Bridge(QObject):
    failed = Signal(str, str)


class TourPanel(QFrame):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setObjectName("tour")
        self.steps = steps(win)
        self.i = 0
        c = win.colors
        self.setStyleSheet(f"QFrame#tour {{ background: {c['surface']}; border: 2px solid {c['accent']}; "
                           f"border-radius: 12px; }}")
        self.setFixedWidth(WIDTH)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        top = QHBoxLayout()
        self.step_list = QComboBox()                    # jump to any step
        for k, s in enumerate(self.steps):
            self.step_list.addItem(f"{k + 1}/{len(self.steps)}  {tr(s.title)}")
        self.step_list.setToolTip(tr("Go to any step"))
        self.step_list.currentIndexChanged.connect(lambda k: self.go(k))
        top.addWidget(self.step_list, 1)
        self.voice_btn = QPushButton()
        self.voice_btn.setCheckable(True)
        self.voice_btn.setFixedWidth(44)
        self.voice_btn.setChecked(bool(win.state.get("tour_voice", True)))
        self.voice_btn.toggled.connect(self._voice_toggled)
        top.addWidget(self.voice_btn)
        v.addLayout(top)
        self.title = QLabel()
        self.title.setObjectName("title")
        self.title.setWordWrap(True)
        v.addWidget(self.title)
        self.body = QLabel()
        self.body.setWordWrap(True)
        v.addWidget(self.body)
        row = QHBoxLayout()
        self.state_label = QLabel()
        row.addWidget(self.state_label, 1)
        self.action_btn = QPushButton()
        self.action_btn.clicked.connect(self._do_action)
        row.addWidget(self.action_btn)
        v.addLayout(row)
        nav = QHBoxLayout()
        skip = QPushButton("Skip the guide")
        skip.clicked.connect(self.finish)
        nav.addWidget(skip)
        nav.addStretch(1)
        self.back_btn = QPushButton("◀ Back")
        self.back_btn.clicked.connect(lambda: self.go(self.i - 1))
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setObjectName("primary")
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.next_btn)
        v.addLayout(nav)

        self.spot = _Spotlight(win, c["accent"])
        self.spot.hide()
        self._bridge = _Bridge()
        self._bridge.failed.connect(self._voice_failed)
        self.narrator = NaturalNarrator(on_error=self._bridge.failed.emit)
        self.voice = self._pick_voice()
        self._prepared = False
        self._follow = QTimer(self)                     # keeps the highlight on its control and the ✔ up to date
        self._follow.timeout.connect(self._refresh)
        win.installEventFilter(self)
        self._update_voice_btn()
        self.hide()

    # ------------------------------------------------------------------ voice
    def prepare(self):
        """Load the offline voice and synthesise the first steps in the background, so the guide speaks at once."""
        if not self._prepared:
            self._prepared = True
            self.narrator.warm_up(self.voice)
            self.narrator.prefetch([self._speech(0), self._speech(1)], self.voice)

    def _pick_voice(self) -> str:
        if self.narrator.piper_ok:
            return PIPER + self.narrator.piper_voices()[0][0]
        if self.narrator.edge_ok:
            return EDGE + self.narrator.edge_voices()[0][0]
        return ""

    def _speech(self, i: int) -> str:
        return speech(self.steps[i]) if 0 <= i < len(self.steps) else ""

    def _read(self):
        self.narrator.stop()                            # the old step is cut at once
        if self.voice_btn.isChecked() and self.voice:
            self.narrator.speak(self._speech(self.i), self.voice)
            self.narrator.prefetch([self._speech(self.i + 1), self._speech(self.i - 1)], self.voice)

    def _voice_failed(self, kind: str, _msg: str):
        """The online voice failed (no internet): use the offline one if there is one, else stay silent."""
        if kind == EDGE and self.narrator.piper_ok:
            self.voice = PIPER + self.narrator.piper_voices()[0][0]
            self._read()

    def _voice_toggled(self, on: bool):
        self.win.state["tour_voice"] = on
        self._update_voice_btn()
        self._read() if on else self.narrator.stop()

    def _update_voice_btn(self):
        self.voice_btn.setText("🔊" if self.voice_btn.isChecked() else "🔇")
        self.voice_btn.setToolTip("Read the guide aloud")

    # ------------------------------------------------------------------ steps
    def start(self, i: int = 0):
        self.prepare()
        self.show()
        self.raise_()
        self._follow.start(400)
        self.go(i, force=True)

    def go(self, i: int, force: bool = False):
        i = max(0, min(len(self.steps) - 1, i))
        if i == self.i and not force:
            return
        self.i = i
        s = self.steps[i]
        self.step_list.blockSignals(True)
        self.step_list.setCurrentIndex(i)
        self.step_list.blockSignals(False)
        self.title.setText(s.title)
        self.body.setText(s.text)
        self.action_btn.setVisible(bool(s.action))
        if s.action:
            self.action_btn.setText(s.action[0])
        self.back_btn.setEnabled(i > 0)
        self.next_btn.setText("Finish ✔" if i == len(self.steps) - 1 else "Next ▶")
        self._show_target()
        self._refresh()
        self.adjustSize()
        self._place()
        self._read()

    def _next(self):
        if self.i >= len(self.steps) - 1:
            self.finish()
        else:
            self.go(self.i + 1)

    def _do_action(self):
        s = self.steps[self.i]
        if s.action:
            s.action[1]()
            self._refresh()

    def finish(self):
        self.narrator.stop()
        self._follow.stop()
        self.spot.hide()
        self.hide()
        self.win.state["tour_pending"] = False
        self.win.state["tour_done"] = True
        try:
            config.save_app_state(self.win.state)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ highlight + placement
    def _targets(self) -> list:
        s = self.steps[self.i]
        if not s.target:
            return []
        try:
            t = s.target()
        except Exception:  # noqa: BLE001
            return []
        return [x for x in (t if isinstance(t, (list, tuple)) else [t]) if isinstance(x, QWidget)]

    def _show_target(self):
        targets = self._targets()
        if not targets:
            return
        tabs = self.win.tabs
        for k in range(tabs.count()):                    # open the tab the control is on
            page = tabs.widget(k)
            if page is targets[0] or page.isAncestorOf(targets[0]):
                if tabs.currentIndex() != k:
                    tabs.setCurrentIndex(k)
                break
        p = targets[0].parentWidget()
        while p is not None:                             # scroll it into view
            if isinstance(p, QScrollArea):
                p.ensureWidgetVisible(targets[0], 40, 40)
                break
            p = p.parentWidget()

    def _target_rect(self) -> QRect | None:
        rect = None
        for t in self._targets():
            if not t.isVisible():
                continue
            r = QRect(t.mapTo(self.win, t.rect().topLeft()), t.size())
            rect = r if rect is None else rect.united(r)
        return rect

    def _place(self):
        """First window corner (bottom right, bottom left, top right, top left) that doesn't cover the target."""
        area = self.win.rect()
        sb = self.win.statusBar()
        bottom = area.bottom() - (sb.height() if sb and sb.isVisible() else 0) - MARGIN
        w, h = self.width(), self.sizeHint().height()
        self.resize(w, h)
        spots = [(area.right() - MARGIN - w, bottom - h), (area.left() + MARGIN, bottom - h),
                 (area.right() - MARGIN - w, area.top() + 70), (area.left() + MARGIN, area.top() + 70)]
        target = self._target_rect()
        best, best_overlap = spots[0], None
        for x, y in spots:
            r = QRect(x, y, w, h).adjusted(-12, -12, 12, 12)
            overlap = 0 if target is None else (r.intersected(target).width() * r.intersected(target).height()
                                                if r.intersects(target) else 0)
            if best_overlap is None or overlap < best_overlap:
                best, best_overlap = (x, y), overlap
            if overlap == 0:
                break
        self.move(*best)
        self.raise_()

    def _refresh(self):
        if not self.isVisible():
            return
        r = self._target_rect()
        if r is None:
            self.spot.hide()
        else:
            self.spot.setGeometry(r.adjusted(-6, -6, 6, 6))
            self.spot.show()
            self.spot.raise_()
            self.raise_()
        s = self.steps[self.i]
        if s.check:
            try:
                done = bool(s.check())
            except Exception:  # noqa: BLE001
                done = False
            c = self.win.colors
            self.state_label.setText("✔ Done" if done else "○ Not done yet")
            self.state_label.setStyleSheet(f"color: {c['ok'] if done else c['muted']};")
            self.state_label.show()
        else:
            self.state_label.hide()

    def eventFilter(self, obj, ev):
        if obj is self.win and ev.type() == QEvent.Resize and self.isVisible():
            QTimer.singleShot(0, self._place)
        return False


class TourMixin:
    """Mixed into MainWindow. Needs: state, colors, tabs and the controls the steps point at."""

    def _init_tour(self):
        self.tour = TourPanel(self)
        if self.state.get("tour_pending"):
            self.tour.prepare()                         # the voice loads while the window appears
            QTimer.singleShot(300, self.start_tour)

    def start_tour(self):
        self.tour.start(0)

    def _tour_close(self):
        if getattr(self, "tour", None) is not None:
            self.tour.narrator.stop()
