"""Dark and light themes - soft, low-contrast palettes that are easy on the eyes."""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

THEMES = {
    "dark": {
        "bg": "#1d2026", "surface": "#252931", "surface2": "#2d323b", "border": "#3a404b",
        "text": "#d4d7dd", "muted": "#8f96a3", "accent": "#7aa2f7", "accent_text": "#14161a",
        "incoming": "#8bd5ca", "outgoing": "#e5c890", "error": "#ee8f8f", "ok": "#a6d189",
        "selection": "#3b4a66", "meter_bg": "#16181d",
    },
    "light": {
        "bg": "#f3f0e9", "surface": "#faf8f3", "surface2": "#ebe7de", "border": "#d6d0c4",
        "text": "#33363d", "muted": "#7a7f88", "accent": "#4a74b5", "accent_text": "#ffffff",
        "incoming": "#2a8077", "outgoing": "#9a6a12", "error": "#b84a4a", "ok": "#4f8a2f",
        "selection": "#c9d8ee", "meter_bg": "#e2ddd2",
    },
}


def colors(name: str) -> dict:
    return THEMES.get(name, THEMES["dark"])


def _arrow_icons(name: str, color: str) -> dict:
    """Write small themed arrow SVGs (Qt style sheets need files) and return their paths."""
    from ..config import DATA_DIR
    d = DATA_DIR / "ui"
    d.mkdir(parents=True, exist_ok=True)
    shapes = {"up": "M2 7 L6 3 L10 7", "down": "M2 4 L6 8 L10 4"}
    out = {}
    for k, path in shapes.items():
        f = d / f"{name}_{k}.svg"
        f.write_text(f"<svg xmlns='http://www.w3.org/2000/svg' width='12' height='11' viewBox='0 0 12 11'>"
                     f"<path d='{path}' fill='none' stroke='{color}' stroke-width='1.6' "
                     f"stroke-linecap='round' stroke-linejoin='round'/></svg>", encoding="utf-8")
        out[k] = f.as_posix()
    return out


def apply(app: QApplication, name: str, font_pt: float = 10, family: str = "") -> dict:
    """Theme + the app's text size/font (Settings tab)."""
    c = colors(name)
    font_css = f"font-size: {float(font_pt):g}pt;" + (f" font-family: '{family}';" if family else "")
    arrows = _arrow_icons(name, c["muted"])
    app.setStyle("Fusion")
    pal = QPalette()
    for role, key in [
        (QPalette.Window, "bg"), (QPalette.WindowText, "text"), (QPalette.Base, "surface"),
        (QPalette.AlternateBase, "surface2"), (QPalette.Text, "text"), (QPalette.Button, "surface2"),
        (QPalette.ButtonText, "text"), (QPalette.Highlight, "selection"), (QPalette.HighlightedText, "text"),
        (QPalette.ToolTipBase, "surface"), (QPalette.ToolTipText, "text"), (QPalette.PlaceholderText, "muted"),
        (QPalette.Link, "accent"),
    ]:
        pal.setColor(role, QColor(c[key]))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(c["muted"]))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["muted"]))
    app.setPalette(pal)
    app.setStyleSheet(f"""
        QWidget {{ {font_css} }}
        QMainWindow, QDialog {{ background: {c['bg']}; }}
        QTabWidget::pane {{ border: 1px solid {c['border']}; border-radius: 8px; top: -1px;
                            background: {c['surface']}; }}
        QTabBar::tab {{ background: transparent; color: {c['muted']}; padding: 8px 14px; margin-right: 2px;
                        border-top-left-radius: 8px; border-top-right-radius: 8px; }}
        QTabBar::tab:selected {{ background: {c['surface']}; color: {c['text']};
                                 border: 1px solid {c['border']}; border-bottom: none; }}
        QTabBar::tab:hover:!selected {{ color: {c['text']}; }}
        QGroupBox {{ border: 1px solid {c['border']}; border-radius: 8px; margin-top: 14px; padding: 10px 8px 8px 8px;
                     background: {c['surface']}; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {c['accent']};
                            font-weight: 600; }}
        QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {{
            background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['border']};
            border-radius: 6px; padding: 4px 6px; selection-background-color: {c['selection']}; }}
        QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{ subcontrol-origin: border; width: 18px;
            border-left: 1px solid {c['border']}; background: transparent; }}
        QAbstractSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 6px; }}
        QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 6px; }}
        QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{ background: {c['selection']}; }}
        QAbstractSpinBox::up-arrow {{ image: url({arrows['up']}); width: 10px; height: 9px; }}
        QAbstractSpinBox::down-arrow {{ image: url({arrows['down']}); width: 10px; height: 9px; }}
        QComboBox::drop-down {{ border: none; width: 22px; }}
        QComboBox::down-arrow {{ image: url({arrows['down']}); width: 10px; height: 9px; }}
        QComboBox QAbstractItemView {{ background: {c['surface']}; color: {c['text']};
                                       selection-background-color: {c['selection']}; border: 1px solid {c['border']}; }}
        QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {c['accent']}; }}
        QToolButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['border']};
                       border-radius: 6px; padding: 5px 10px; }}
        QToolButton:hover {{ border-color: {c['accent']}; }}
        QToolButton::menu-indicator {{ image: none; }}
        QPushButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['border']};
                       border-radius: 6px; padding: 5px 12px; }}
        QPushButton:hover {{ border-color: {c['accent']}; }}
        QPushButton:pressed, QPushButton:checked {{ background: {c['selection']}; }}
        QPushButton:disabled {{ color: {c['muted']}; }}
        QPushButton#primary {{ background: {c['accent']}; color: {c['accent_text']}; border: none;
                               font-weight: 600; padding: 7px 18px; }}
        QPushButton#primary:hover {{ background: {c['accent']}; border: 1px solid {c['text']}; }}
        QPushButton#danger {{ background: {c['error']}; color: {c['accent_text']}; border: none;
                              font-weight: 600; padding: 7px 18px; }}
        QCheckBox {{ spacing: 6px; }}
        QLabel#muted {{ color: {c['muted']}; }}
        QLabel#title {{ font-size: 12pt; font-weight: 600; }}
        QLabel#incoming {{ color: {c['incoming']}; font-weight: 600; }}
        QLabel#outgoing {{ color: {c['outgoing']}; font-weight: 600; }}
        QLabel#warn {{ color: {c['error']}; }}
        QLabel#ok {{ color: {c['ok']}; }}
        QTableWidget {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['border']};
                        border-radius: 6px; gridline-color: {c['border']};
                        selection-background-color: {c['selection']}; selection-color: {c['text']}; }}
        QHeaderView::section {{ background: {c['surface']}; color: {c['muted']}; border: none;
                                border-bottom: 1px solid {c['border']}; padding: 4px 6px; }}
        QTableCornerButton::section {{ background: {c['surface']}; border: none; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
        QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
        QSlider::handle:horizontal {{ background: {c['accent']}; width: 14px; margin: -6px 0; border-radius: 7px; }}
        QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
        QStatusBar {{ color: {c['muted']}; }}
        QToolTip {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']}; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 30px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    """)
    return c
