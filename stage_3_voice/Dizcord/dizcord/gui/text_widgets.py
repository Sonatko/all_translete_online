"""Floating windows for text translation: popup, chat overlay, area selector, OCR result box."""
from __future__ import annotations

import html

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen, QRegion
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from ..i18n import no_translate
from .. import languages as L
from . import screens

FLOAT_FLAGS = Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool


class _Floating(QWidget):
    """Frameless, translucent, draggable, always-on-top window with a rounded background."""

    def __init__(self, colors: dict, opacity: float = 0.94):
        super().__init__(None, FLOAT_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.colors = colors
        self.opacity = opacity
        self._drag = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(self.colors["surface"])
        bg.setAlphaF(self.opacity)
        p.setPen(QPen(QColor(self.colors["border"]), 1))
        p.setBrush(bg)
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)
            self.moved_by_user = True

    def mouseReleaseEvent(self, e):
        self._drag = None


class TranslationPopup(_Floating):
    """Small bubble next to the mouse with the translation of selected/copied text."""

    def __init__(self, colors: dict):
        super().__init__(colors)
        self.setMaximumWidth(560)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)
        self.meta = QLabel()
        self.translated = no_translate(QLabel())
        self.translated.setWordWrap(True)
        self.translated.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.original = no_translate(QLabel())
        self.original.setWordWrap(True)
        self.original.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        close = QPushButton("✕")
        close.setFixedWidth(30)
        close.clicked.connect(self.hide)
        row.addWidget(self.meta, 1)
        row.addWidget(self.copy_btn)
        row.addWidget(close)
        lay.addLayout(row)
        lay.addWidget(self.translated)
        lay.addWidget(self.original)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._maybe_hide)
        self._text = ""
        self.font_pt = 11.5        # translation text size (Settings tab)

    def show_translation(self, original, translated, src, tgt, phys_x, phys_y, seconds=10, title=""):
        c = self.colors
        self._text = translated
        pt = float(self.font_pt)
        self.meta.setText(f"<span style='color:{c['muted']}; font-size:{pt * 0.74:.1f}pt'>{html.escape(title)}"
                          f"{L.name(src) if src else '?'} → {L.name(tgt)}</span>")
        self.translated.setText(f"<span style='color:{c['text']}; font-size:{pt:.1f}pt'>"
                                f"{html.escape(translated)}</span>")
        self.original.setText(f"<span style='color:{c['muted']}; font-size:{pt * 0.78:.1f}pt'>"
                              f"{html.escape(original[:600])}</span>")
        self.adjustSize()
        p = screens.to_logical(phys_x, phys_y)
        r = screens.clamp_to_screen(QRect(p.x() + 12, p.y() + 18, self.width(), self.height()))
        self.move(r.topLeft())
        self.show()
        self.raise_()
        self.timer.start(max(2, int(seconds)) * 1000)

    def _maybe_hide(self):
        if self.underMouse():
            self.timer.start(1500)
        else:
            self.hide()

    def _copy(self):
        QApplication.clipboard().setText(self._text)
        self.copy_btn.setText("Copied")
        QTimer.singleShot(1200, lambda: self.copy_btn.setText("Copy"))


class ChatOverlay(_Floating):
    """Floating list of the latest translated chat messages (optionally docked to Discord)."""

    turned_off = Signal()      # "Don't show this window" chosen from the right-click menu
    geometry_changed = Signal()

    def __init__(self, colors: dict, cfg: dict):
        super().__init__(colors, 0.9)
        self.cfg = dict(cfg)
        self.items: list[dict] = []
        self.moved_by_user = False
        self.font_pt = 10.0        # text size (Settings tab)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        self.label = no_translate(QLabel())
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        lay.addWidget(self.label)
        self.resize(460, 320)
        self.setWindowTitle("Dizcord chat")
        self._render()

    def apply(self, colors, cfg):
        self.colors, self.cfg = colors, dict(cfg)
        self._render()
        self.update()

    def add(self, item: dict):
        self.items = [i for i in self.items if i["id"] != item["id"]] + [item]
        self.items = self.items[-max(1, int(self.cfg.get("overlay_lines", 6))):]
        self._render()

    def clear(self):
        self.items = []
        self._render()

    def _render(self):
        c = self.colors
        if not self.items:
            self.label.setText(f"<span style='color:{c['muted']}'>Translated chat messages appear here · "
                               "drag to move · right-click for options</span>")
            return
        parts = []
        pt = float(self.font_pt)
        for it in self.items:
            parts.append(
                f"<div style='margin-bottom:6px; font-size:{pt:.1f}pt'>"
                f"<b style='color:{c['incoming']}'>{html.escape(it['author'])}</b> "
                f"<span style='color:{c['muted']}; font-size:{pt * 0.8:.1f}pt'>"
                f"{L.name(it['src']) if it.get('src') else ''}"
                f"{' · edited' if it.get('edited') else ''}</span><br>"
                f"<span style='color:{c['text']}'>{html.escape(it['translated'])}</span></div>")
        self.label.setText("".join(parts))

    def moveEvent(self, e):
        super().moveEvent(e)
        self.geometry_changed.emit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.geometry_changed.emit()

    def showEvent(self, e):
        super().showEvent(e)
        self.geometry_changed.emit()

    def hideEvent(self, e):
        super().hideEvent(e)
        self.geometry_changed.emit()

    def dock_to(self, rect):
        """Dock to the bottom-right of the Discord window (rect in physical pixels)."""
        if not rect or self.moved_by_user or not self.cfg.get("overlay_attach", True):
            return
        r = screens.rect_to_logical(*rect)
        if r.width() < 400 or r.height() < 300:
            return
        x = r.right() - self.width() - int(r.width() * 0.13)
        y = r.bottom() - self.height() - 110
        self.move(screens.clamp_to_screen(QRect(x, y, self.width(), self.height())).topLeft())

    def wheelEvent(self, e):
        dh = 40 if e.angleDelta().y() > 0 else -40
        self.resize(self.width(), max(120, self.height() + dh))

    def contextMenuEvent(self, e):
        m = QMenu(self)
        a_dock = m.addAction("Dock to Discord again")
        a_wider = m.addAction("Wider")
        a_narrow = m.addAction("Narrower")
        a_clear = m.addAction("Clear")
        a_hide = m.addAction("Hide until the next message")
        a_off = m.addAction("Don't show this window (translations stay inside Discord)")
        act = m.exec(e.globalPos())
        if act == a_dock:
            self.moved_by_user = False
        elif act == a_wider:
            self.resize(self.width() + 60, self.height())
        elif act == a_narrow:
            self.resize(max(240, self.width() - 60), self.height())
        elif act == a_clear:
            self.clear()
        elif act == a_hide:
            self.hide()
        elif act == a_off:
            self.hide()
            self.turned_off.emit()


class AreaSelector(QWidget):
    """Dim the screen and let the user drag a rectangle. Emits the PHYSICAL rect (x, y, w, h)."""

    selected = Signal(tuple)
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.screen_ = screen
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.origin = None
        self.current = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        p.setPen(QColor(255, 255, 255))
        f = QFont()
        f.setPointSize(13)
        p.setFont(f)
        p.drawText(self.rect().adjusted(0, 30, 0, 0), Qt.AlignHCenter | Qt.AlignTop,
                   "Drag over the text to translate  ·  Esc to cancel")
        if self.origin and self.current:
            r = QRect(self.origin, self.current).normalized()
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(r, Qt.transparent)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor("#7aa2f7"), 2))
            p.drawRect(r)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.origin = e.position().toPoint()
            self.current = self.origin
        else:
            self._cancel()

    def mouseMoveEvent(self, e):
        if self.origin:
            self.current = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e):
        if not self.origin:
            return
        r = QRect(self.origin, e.position().toPoint()).normalized()
        self.origin = None
        if r.width() < 6 or r.height() < 6:
            self._cancel()
            return
        r.translate(self.geometry().topLeft())       # widget -> global logical
        phys = screens.rect_to_physical(r, self.screen_)
        self.close()
        self.selected.emit(phys)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._cancel()

    def _cancel(self):
        self.close()
        self.cancelled.emit()


class OcrResultBox(_Floating):
    """Shows the translation on top of the area that was read (like a lens). Click ✕ or Esc to close."""

    def __init__(self, colors: dict):
        super().__init__(colors, 0.96)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 8)
        row = QHBoxLayout()
        self.meta = QLabel()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(lambda: (QApplication.clipboard().setText(self._text),
                                               self.copy_btn.setText("Copied")))
        close = QPushButton("✕")
        close.setFixedWidth(30)
        close.clicked.connect(self.hide)
        row.addWidget(self.meta, 1)
        row.addWidget(self.copy_btn)
        row.addWidget(close)
        lay.addLayout(row)
        self.body = no_translate(QLabel())
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay.addWidget(self.body, 1)
        self._text = ""

    def show_result(self, phys_rect, translated, src, tgt, note=""):
        c = self.colors
        self._text = translated
        self.copy_btn.setText("Copy")
        self.meta.setText(f"<span style='color:{c['muted']}; font-size:8.5pt'>"
                          f"{L.name(src) if src else '?'} → {L.name(tgt)} {html.escape(note)}</span>")
        x, y, w, h = phys_rect
        r = screens.rect_to_logical(x, y, x + w, y + h)
        width = max(260, r.width())
        self.body.setText(f"<span style='color:{c['text']}; font-size:11pt'>"
                          f"{html.escape(translated).replace(chr(10), '<br>')}</span>")
        self.body.setFixedWidth(width - 20)
        self.adjustSize()
        height = max(self.sizeHint().height(), min(r.height(), 600))
        self.resize(width, height)
        self.move(screens.clamp_to_screen(QRect(r.x(), r.y(), width, height)).topLeft())
        self.show()
        self.raise_()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()


def select_area(callback, cancelled=None):
    """Open a selector on every screen; callback(phys_rect) when the user is done."""
    sels = []

    def done(rect):
        for s in sels:
            if s.isVisible():
                s.close()
        callback(rect)

    def cancel():
        for s in sels:
            if s.isVisible():
                s.close()
        if cancelled:
            cancelled()
    for scr in QGuiApplication.screens():
        s = AreaSelector(scr)
        s.selected.connect(done)
        s.cancelled.connect(cancel)
        s.show()
        s.activateWindow()
        sels.append(s)
    select_area._alive = sels   # keep references
    return sels


class InlineOverlay(QWidget):
    """Click-through layer over the Discord window that draws each translation on top of its message text,
    in Discord's own background colour - it looks like part of Discord without touching Discord."""

    LINE_RATIO = 1.375        # Discord: 16 px text on 22 px lines

    def __init__(self, colors: dict):
        super().__init__(None, FLOAT_FLAGS | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.colors = colors
        self.texts: dict[str, str] = {}
        self.items: list[tuple[str, QRect, QRect]] = []    # (message id, text rect, visible list rect) - logical
        self.user_hidden = False
        self._last = None          # last (window, items) payload, to show again after Ctrl+Alt+I
        self._bg = QColor("#313338")
        self._line_h = None        # height of one Discord text line (logical px), measured on screen
        self.scale = 1.0           # text size relative to Discord's (Settings tab)
        self.family = ""           # font ("" = Discord's look: gg sans / Segoe UI)
        self.avoid: list[QWidget] = []   # our own windows that sit over Discord (never draw under them)

    # ------------------------------------------------------------------ data
    def add(self, mid: str, text: str):
        self.texts[mid] = text
        if any(m == mid for m, _r, _c in self.items):
            self.update()
        elif self._last and any(it["id"] == mid for it in self._last[1]) and not self.user_hidden:
            self.show_items(*self._last)

    def clear(self):
        self.texts.clear()
        self.items = []
        self._last = None
        self._line_h = None
        self.hide()

    def toggle(self) -> bool:
        """Ctrl+Alt+I: originals <-> translations. Returns True when translations are shown."""
        self.user_hidden = not self.user_hidden
        if self.user_hidden:
            self.hide()
        elif self._last:
            self.show_items(*self._last)
        return not self.user_hidden

    def show_items(self, window, items):
        self._last = (window, items)
        if self.user_hidden or not window:
            return
        shown = [it for it in items if self.texts.get(it["id"])]
        if not shown:
            self.hide()
            return
        self.setGeometry(screens.rect_to_logical(*window))
        self.items = [(it["id"], screens.rect_to_logical(*it["rect"]), screens.rect_to_logical(*it["clip"]))
                      for it in shown]
        singles = [r.height() for _m, r, _c in self.items if r.height() > 8]
        if singles:
            h = min(singles)
            if self._line_h is None or h < self._line_h * 1.5:   # one-line messages give the line height
                self._line_h = h if self._line_h is None else min(self._line_h, h)
        self._sample_background(shown[0]["rect"])
        self.show()
        self.raise_()
        for w in self.avoid:          # keep e.g. the small chat window above this layer
            if w.isVisible():
                w.raise_()
        self.update()

    def _sample_background(self, rect):
        """Discord's background colour next to the text (works with any Discord theme)."""
        try:
            import mss
            x = max(rect[0], rect[2] - 3)
            with mss.mss() as s:
                shot = s.grab({"left": x, "top": rect[1], "width": 1, "height": max(1, rect[3] - rect[1])})
            counts: dict = {}
            for y in range(shot.height):
                px = shot.pixel(0, y)
                counts[px] = counts.get(px, 0) + 1
            r, g, b = max(counts, key=counts.get)[:3]
            if not self.isVisible() or (r, g, b) != (self._bg.red(), self._bg.green(), self._bg.blue()):
                self._bg = QColor(r, g, b)
        except Exception:
            pass

    # ------------------------------------------------------------------ drawing
    def _font(self, px: int) -> QFont:
        f = QFont()
        f.setFamilies(([self.family] if self.family else []) + ["gg sans", "Segoe UI", "Arial"])
        f.setPixelSize(max(9, px))
        return f

    def paintEvent(self, _):
        if not self.items:
            return
        from PySide6.QtGui import QFontMetrics
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        origin = self.geometry().topLeft()
        light = self._bg.lightnessF() > 0.5
        fg = QColor("#2e3338" if light else "#dbdee1")
        accent = QColor(self.colors.get("accent", "#7aa2f7"))
        base_px = round((self._line_h or 22) / self.LINE_RATIO * float(self.scale))
        flags = int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop)
        holes = QRegion()
        for w in self.avoid:
            if w.isVisible():
                holes = holes.united(QRegion(w.frameGeometry().translated(-origin)))
        for mid, r, clip in self.items:
            text = self.texts.get(mid)
            if not text:
                continue
            r = r.translated(-origin)
            clip = clip.translated(-origin)
            area = r.adjusted(6, 0, 0, 0)
            font = self._font(base_px)
            for scale in (1.0, 0.92, 0.84, 0.76, 0.68):   # shrink long translations to fit the original's space
                font = self._font(int(base_px * scale))
                need = QFontMetrics(font).boundingRect(area, flags, text).height()
                if need <= r.height() + 2:
                    break
            p.save()
            p.setClipRegion(QRegion(clip).subtracted(holes))
            p.setPen(Qt.NoPen)
            p.setBrush(self._bg)
            p.drawRect(r.adjusted(-2, -1, 2, 1))
            p.setBrush(accent)
            p.drawRoundedRect(QRect(r.left(), r.top() + 2, 3, max(4, r.height() - 4)), 1.5, 1.5)
            p.setClipRegion(QRegion(clip.intersected(r.adjusted(0, -1, 2, 1))).subtracted(holes))
            p.setPen(fg)
            p.setFont(font)
            p.drawText(area, flags, text)
            p.restore()
