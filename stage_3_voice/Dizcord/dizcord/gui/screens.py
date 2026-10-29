"""Physical (Windows / UI Automation / screenshots) <-> logical (Qt) coordinates.

Windows APIs, UI Automation and mss work in physical pixels; Qt works in
device-independent pixels. With display scaling (125 %, 150 %, ...) they differ.
Qt 6 keeps each screen's origin in native pixels and scales inside the screen.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QGuiApplication


def _native_rect(screen) -> tuple[int, int, int, int, float]:
    g = screen.geometry()
    dpr = screen.devicePixelRatio()
    return g.x(), g.y(), int(round(g.width() * dpr)), int(round(g.height() * dpr)), dpr


def _screen_for_physical(x: int, y: int):
    for s in QGuiApplication.screens():
        sx, sy, sw, sh, dpr = _native_rect(s)
        if sx <= x < sx + sw and sy <= y < sy + sh:
            return s
    return QGuiApplication.primaryScreen()


def to_logical(x: int, y: int) -> QPoint:
    s = _screen_for_physical(x, y)
    sx, sy, _sw, _sh, dpr = _native_rect(s)
    return QPoint(int(round(sx + (x - sx) / dpr)), int(round(sy + (y - sy) / dpr)))


def rect_to_logical(x1: int, y1: int, x2: int, y2: int) -> QRect:
    s = _screen_for_physical((x1 + x2) // 2, (y1 + y2) // 2)
    sx, sy, _sw, _sh, dpr = _native_rect(s)
    return QRect(int(round(sx + (x1 - sx) / dpr)), int(round(sy + (y1 - sy) / dpr)),
                 int(round((x2 - x1) / dpr)), int(round((y2 - y1) / dpr)))


def to_physical(p: QPoint, screen=None) -> tuple[int, int]:
    s = screen or QGuiApplication.screenAt(p) or QGuiApplication.primaryScreen()
    g = s.geometry()
    dpr = s.devicePixelRatio()
    return int(round(g.x() + (p.x() - g.x()) * dpr)), int(round(g.y() + (p.y() - g.y()) * dpr))


def rect_to_physical(r: QRect, screen=None) -> tuple[int, int, int, int]:
    """QRect (logical) -> (x, y, w, h) physical."""
    s = screen or QGuiApplication.screenAt(r.center()) or QGuiApplication.primaryScreen()
    x, y = to_physical(r.topLeft(), s)
    dpr = s.devicePixelRatio()
    return x, y, int(round(r.width() * dpr)), int(round(r.height() * dpr))


def clamp_to_screen(r: QRect) -> QRect:
    s = QGuiApplication.screenAt(r.center()) or QGuiApplication.primaryScreen()
    a = s.availableGeometry()
    x = min(max(r.x(), a.left()), a.right() - r.width())
    y = min(max(r.y(), a.top()), a.bottom() - r.height())
    return QRect(x, y, r.width(), r.height())
