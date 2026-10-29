"""Always-on-top subtitle window that floats over your game / Discord."""
from __future__ import annotations

import html

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget

from ..i18n import no_translate


class SubtitleOverlay(QWidget):
    def __init__(self, colors: dict, ui_cfg: dict):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.colors = colors
        self.cfg = dict(ui_cfg)
        self.lines: list[tuple[str, str, str]] = []   # (direction, translated, original)
        self._drag: QPoint | None = None
        self.locked = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self.label)
        self.resize(900, 140)
        self.setWindowTitle("Dizcord subtitles")
        self._render()

    def apply(self, colors: dict, ui_cfg: dict):
        self.colors, self.cfg = colors, dict(ui_cfg)
        self._render()

    def add(self, direction: str, translated: str, original: str):
        self.lines.append((direction, translated, original))
        self.lines = self.lines[-max(1, int(self.cfg.get("subtitle_lines", 3))):]
        self._render()

    def _render(self):
        size = int(self.cfg.get("subtitle_font_size", 22))
        show_orig = self.cfg.get("subtitle_show_original", True)
        parts = []
        for d, tr, orig in self.lines:
            col = self.colors["incoming"] if d == "incoming" else self.colors["outgoing"]
            who = "◀" if d == "incoming" else "▶"
            s = (f"<div style='margin:2px 0'><span style='color:{col}; font-size:{size}px; font-weight:600'>"
                 f"{who} {html.escape(tr)}</span>")
            if show_orig and orig and orig != tr:
                s += (f"<br><span style='color:#b8bcc4; font-size:{max(10, int(size * 0.6))}px'>"
                      f"{html.escape(orig)}</span>")
            parts.append(s + "</div>")
        if not parts:
            parts = [f"<span style='color:#b8bcc4; font-size:{max(12, size // 2)}px'>"
                     "Subtitles appear here · drag to move · right-click for options</span>"]
        self.label.setText("".join(parts))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(16, 18, 22)
        bg.setAlphaF(max(0.0, min(1.0, float(self.cfg.get("subtitle_opacity", 0.85)))))
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(self.rect(), 12, 12)

    # dragging / resizing with the mouse wheel
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.locked:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def wheelEvent(self, e):
        if self.locked:
            return
        dw = 40 if e.angleDelta().y() > 0 else -40
        self.resize(max(300, self.width() + dw), self.height())

    def contextMenuEvent(self, e):
        m = QMenu(self)
        a_lock = m.addAction("Unlock position" if self.locked else "Lock position")
        a_clear = m.addAction("Clear")
        a_taller = m.addAction("Taller")
        a_shorter = m.addAction("Shorter")
        a_hide = m.addAction("Hide")
        act = m.exec(e.globalPos())
        if act == a_lock:
            self.locked = not self.locked
        elif act == a_clear:
            self.lines.clear()
            self._render()
        elif act == a_taller:
            self.resize(self.width(), self.height() + 40)
        elif act == a_shorter:
            self.resize(self.width(), max(60, self.height() - 40))
        elif act == a_hide:
            self.hide()
