"""Lightweight, High-Performance Control Panel for Stage 3 Voice Translation Studio.
Features an interactive visual signal chain monitor, millisecond latency breakdown,
Topping E2x2 matrix routing, and 30 FPS decoupled VU meters for zero game lag.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer, QEvent, QRectF, QThread, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap, QLinearGradient
from PySide6.QtWidgets import (
    QDialog,
    QInputDialog,
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from .audio_engine import AudioEngine
from .config import load_settings, save_settings
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launcher.model_downloader import ModelDownloadWorker, check_spec_status, get_pipeline_specs
from .model_manager import ModelManager
from .routing_presets import RoutingPresets

log = logging.getLogger("Studio.GUI")


class VUMeter(QProgressBar):
    """Custom Peak/RMS LED Volume Unit meter (-60 dB to 0 dB)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-60, 0)
        self.setValue(-60)
        self.setTextVisible(False)
        self.setFixedHeight(14)
        self.setStyleSheet("""
            QProgressBar {
                background-color: #1a1b1e;
                border: 1px solid #2e3035;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:0.75 #eab308, stop:0.95 #ef4444);
                border-radius: 2px;
            }
        """)


class NoWheelComboBox(QComboBox):
    """QComboBox that ignores mouse wheel events to prevent accidental changes when scrolling."""

    def wheelEvent(self, event):
        event.ignore()


class ChainNode(QFrame):
    """A visual node in the audio processing chain monitor."""

    def __init__(self, step_number: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ChainNode {
                background-color: #212328;
                border: 1px solid #32353b;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header: Step & Title
        h_layout = QHBoxLayout()
        self.step_lbl = QLabel(f"<b>{step_number}</b>")
        self.step_lbl.setStyleSheet("color: #60a5fa; font-size: 11px;")
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        h_layout.addWidget(self.step_lbl)
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()
        layout.addLayout(h_layout)

        # Subtitle / Model Info
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        self.sub_lbl.setWordWrap(True)
        layout.addWidget(self.sub_lbl)

        # Latency / Status Badge
        self.badge_lbl = QLabel("Готов (0 ms)")
        self.badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_lbl.setStyleSheet("""
            background-color: #1a1b1e;
            color: #10b981;
            font-family: Consolas, monospace;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 6px;
            border-radius: 4px;
            border: 1px solid #2e3035;
        """)
        layout.addWidget(self.badge_lbl)

    def update_info(self, title: str, subtitle: str):
        self.title_lbl.setText(title)
        self.sub_lbl.setText(subtitle)

    def set_telemetry(self, status_text: str, latency_ms: float = 0.0, is_active: bool = False):
        if is_active:
            self.setStyleSheet("""
                ChainNode {
                    background-color: #1e293b;
                    border: 1px solid #3b82f6;
                    border-radius: 6px;
                    padding: 6px;
                }
            """)
            self.badge_lbl.setStyleSheet("""
                background-color: #1e3a8a;
                color: #93c5fd;
                font-family: Consolas, monospace;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 6px;
                border-radius: 4px;
                border: 1px solid #3b82f6;
            """)
            self.badge_lbl.setText(f"● {status_text} ({latency_ms:.0f} ms)" if latency_ms > 0 else f"● {status_text}")
        else:
            self.setStyleSheet("""
                ChainNode {
                    background-color: #212328;
                    border: 1px solid #32353b;
                    border-radius: 6px;
                    padding: 6px;
                }
            """)
            self.badge_lbl.setStyleSheet("""
                background-color: #1a1b1e;
                color: #10b981;
                font-family: Consolas, monospace;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 6px;
                border-radius: 4px;
                border: 1px solid #2e3035;
            """)
            self.badge_lbl.setText(f"{status_text} ({latency_ms:.0f} ms)" if latency_ms > 0 else status_text)


class ModelLoaderWorker(QThread):
    """Background asynchronous loader for neural networks to keep GUI 100% fluid."""
    sig_status = Signal(str, str)
    sig_finished = Signal(bool)

    def __init__(self, mm, parent=None):
        super().__init__(parent)
        self.mm = mm

    def run(self):
        pipe = getattr(self.mm, "pipeline", "ru_en")
        pipe_label = "🇨🇳 Chinese" if pipe == "zh_en" else "🇷🇺 Russian"

        self.sig_status.emit(f"⏳ [1/3] Загрузка STT ({pipe_label} распознавание)...", "#38bdf8")
        ok_stt = self.mm.load_stt()

        self.sig_status.emit(f"⏳ [2/3] Загрузка MT ({pipe_label} нейроперевод)...", "#38bdf8")
        ok_mt = self.mm.load_mt()

        self.sig_status.emit("⏳ [3/3] Загрузка TTS (Pocket-TTS нейросинтез)...", "#38bdf8")
        ok_tts = self.mm.load_tts()

        self.sig_finished.emit(ok_stt and ok_mt and ok_tts)


class KeyCaptureDialog(QDialog):
    """Modal dialog to capture any keyboard key, mouse button, or combination."""

    sig_captured = Signal(str)
    sig_preview = Signal(str)

    def __init__(self, parent=None, hotkeys=None, is_zh: bool = False):
        super().__init__(parent)
        self.hotkeys = hotkeys
        self.is_zh = is_zh
        self.setWindowTitle("设置对讲按键 PTT" if is_zh else "Назначение кнопки или комбинации PTT")
        self.setFixedSize(450, 240)
        self.setModal(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 2px solid #3b82f6;
                border-radius: 8px;
            }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        title_text = "<b>请按下任意按键或组合快捷键</b>" if is_zh else "<b>Нажмите клавишу или комбинацию клавиш</b>"
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 14px;")
        v.addWidget(self.lbl_title)

        if is_zh:
            desc_text = (
                "• <b>单键:</b> V, CapsLock, Space, Mouse4, Mouse5, 滚轮中键 (MMB)...\n"
                "• <b>组合键:</b> 按住 Shift, Ctrl 或 Alt 并按下第二个按键\n"
                "  <i>(例如: Shift + 滚轮中键, Ctrl + V, Alt + Mouse4)</i>\n"
                "• <b>控制器:</b> 手柄 / VR / 踏板按键 (LB, RB, LT, RT...)\n\n"
                "(按 Esc 键取消)"
            )
        else:
            desc_text = (
                "• <b>Одиночная кнопка:</b> V, CapsLock, Space, Mouse4, Mouse5, Колесико...\n"
                "• <b>Комбинация:</b> Зажмите Shift, Ctrl или Alt и нажмите вторую кнопку\n"
                "  <i>(например: Shift + Колесико, Ctrl + V, Alt + Mouse4)</i>\n"
                "• <b>Контроллеры:</b> Кнопки геймпада / VR / педалей (LB, RB, LT, RT...)\n\n"
                "(Нажмите Esc для отмены)"
            )
        lbl_desc = QLabel(desc_text)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v.addWidget(lbl_desc)

        init_status = "等待输入按键..." if is_zh else "ОЖИДАНИЕ НАЖАТИЯ..."
        self.lbl_status = QLabel(init_status)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("""
            QLabel {
                color: #38bdf8;
                font-weight: bold;
                font-size: 15px;
                padding: 8px;
                background-color: #1e293b;
                border: 1px dashed #38bdf8;
                border-radius: 6px;
            }
        """)
        v.addWidget(self.lbl_status)

        self.captured_key: Optional[str] = None
        self.sig_captured.connect(self._finish)
        self.sig_preview.connect(self._on_preview_modifier)

        # Hook low-level global OS listener for instant detection anywhere on PC
        if self.hotkeys:
            self.hotkeys.start_capture(
                callback=lambda k: self.sig_captured.emit(k),
                preview_callback=lambda p: self.sig_preview.emit(p),
            )

    def _on_preview_modifier(self, mods: str):
        if self.captured_key is not None:
            return
        if mods:
            txt = f"已按下: {mods.upper()} + [请按第二个键]..." if getattr(self, "is_zh", False) else f"Зажато: {mods.upper()} + [нажмите кнопку]..."
            self.lbl_status.setText(txt)
            self.lbl_status.setStyleSheet("""
                QLabel {
                    color: #fbbf24;
                    font-weight: bold;
                    font-size: 15px;
                    padding: 8px;
                    background-color: #451a03;
                    border: 1px dashed #fbbf24;
                    border-radius: 6px;
                }
            """)
        else:
            txt = "等待输入按键..." if getattr(self, "is_zh", False) else "ОЖИДАНИЕ НАЖАТИЯ..."
            self.lbl_status.setText(txt)
            self.lbl_status.setStyleSheet("""
                QLabel {
                    color: #38bdf8;
                    font-weight: bold;
                    font-size: 15px;
                    padding: 8px;
                    background-color: #1e293b;
                    border: 1px dashed #38bdf8;
                    border-radius: 6px;
                }
            """)

    def reject(self):
        if self.hotkeys:
            self.hotkeys.stop_capture()
        super().reject()

    def closeEvent(self, event):
        if self.hotkeys:
            self.hotkeys.stop_capture()
        super().closeEvent(event)

    def _finish(self, key_name: str):
        if not key_name:
            self.reject()
            return
        if self.captured_key is None:
            self.captured_key = key_name
            if self.hotkeys:
                self.hotkeys.stop_capture()
            txt = f"✓ 已设定: {key_name.upper()}" if getattr(self, "is_zh", False) else f"✓ НАЗНАЧЕНО: {key_name.upper()}"
            self.lbl_status.setText(txt)
            self.lbl_status.setStyleSheet("""
                QLabel {
                    color: #10b981;
                    font-weight: bold;
                    font-size: 15px;
                    padding: 8px;
                    background-color: #064e3b;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                }
            """)
            QTimer.singleShot(350, self.accept)

    def keyPressEvent(self, event):
        k = event.key()
        from PySide6.QtCore import Qt as QTK
        if k == QTK.Key_Escape:
            self.reject()
            return
        # If hotkeys listener is inactive for any reason, fallback to Qt events
        if not self.hotkeys:
            txt = event.text()
            if txt and txt.isprintable() and len(txt) == 1:
                self._finish(txt.lower())

    def mousePressEvent(self, event):
        pass


class StudioWindow(QMainWindow):
    """Main Control Panel Window."""

    def __init__(self, engine: AudioEngine, model_mgr: ModelManager, hotkeys=None):
        super().__init__()
        self.engine = engine
        self.mm = model_mgr
        self.hotkeys = hotkeys
        self.cfg = engine.config

        self.setWindowTitle("Stage 3: Voice Translation Studio (S2ST) — CS2 & Discord")
        self.resize(self.cfg.get("ui", {}).get("window_width", 920),
                    max(self.cfg.get("ui", {}).get("window_height", 820), 800))
        self.setMinimumSize(860, 680)

        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_hint_shown = False

        # Auto-select Chinese pipeline if system locale is Chinese or Chinese models are present on disk
        configured_pipe = self.cfg.get("models", {}).get("pipeline")
        if not configured_pipe:
            import locale
            try:
                sys_loc = (locale.getdefaultlocale()[0] or "").lower()
            except Exception:
                sys_loc = ""
            sv_path = Path("stage_3_voice/models/sensevoice/model.int8.onnx")
            ga_path = Path("stage_3_voice/models/gigaam/model.int8.onnx")
            if "zh" in sys_loc or "cn" in sys_loc or (sv_path.is_file() and not ga_path.is_file()):
                self.mm.set_pipeline("zh_en", auto_reload=False)

        self._apply_dark_style()
        self._init_ui()
        self._init_system_tray()

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._cleanup_tray)

        # Cache last state to avoid redundant Qt stylesheet re-parsing at 30 FPS
        self._last_rendered_state = None
        self._last_rendered_master = None

        # Connect audio transcript callback to GUI
        self.engine.on_transcript_callback = self._on_new_transcript

        # Decoupled 30 FPS Telemetry Polling Timer (33 ms)
        # Prevents any UI stutter or Qt signal spam in high-FPS games like CS2
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)
        self.ui_timer.timeout.connect(self._update_telemetry)
        self.ui_timer.start()

    def _create_tray_icon_fallback(self) -> QIcon:
        """Render a crisp, modern vector-sharp 64x64 tray icon for Stage 3."""
        icon_path = Path("CONFIG/icons/stage3_tray_icon.png")
        if icon_path.is_file():
            return QIcon(str(icon_path))
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#7c3aed"), 4))
        painter.drawRoundedRect(QRectF(4, 4, 56, 56), 14, 14)
        painter.setPen(QColor("#c084fc"))
        font = QFont("Segoe UI Emoji", 24)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 64, 64), Qt.AlignmentFlag.AlignCenter, "🎙")
        painter.end()
        return QIcon(pix)

    def _init_system_tray(self):
        """Initialize system tray integration with instant restore and pause controls."""
        icon = self._create_tray_icon_fallback()
        self.setWindowIcon(icon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Stage 3: Voice Translation Studio (S2ST)")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #7c3aed;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 8px;
            }
        """)

        self.action_tray_restore = QAction("🎙 Развернуть Voice Studio", self)
        self.action_tray_restore.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(self.action_tray_restore)

        tray_menu.addSeparator()

        self.action_tray_toggle = QAction("⏸ Приостановить / Возобновить перевод", self)
        self.action_tray_toggle.triggered.connect(self._on_toggle_master)
        tray_menu.addAction(self.action_tray_toggle)

        tray_menu.addSeparator()

        self.action_tray_quit = QAction("❌ Закрыть Voice Studio", self)
        self.action_tray_quit.triggered.connect(self._quit_application)
        tray_menu.addAction(self.action_tray_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        try:
            self.tray_icon.show()
        except Exception:
            pass

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Single or double click toggles window visibility."""
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible() and not self.isMinimized() and self.isActiveWindow():
                self._minimize_to_tray()
            else:
                self._restore_from_tray()

    def _minimize_to_tray(self):
        """Minimize window cleanly into system tray."""
        self.hide()
        if hasattr(self, "tray_icon") and self.tray_icon and self.tray_icon.isVisible():
            if not getattr(self, "_tray_hint_shown", False):
                self._tray_hint_shown = True
                self.tray_icon.showMessage(
                    "Voice Studio свёрнута",
                    "Голосовой перевод активен в фоне. Кликните по иконке в трее, чтобы открыть.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )

    def _restore_from_tray(self):
        """Restore window from tray to foreground."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_application(self):
        """Exit the application cleanly and ensure zero ghost tray icons."""
        self._cleanup_tray()
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    def _cleanup_tray(self):
        """Guarantee tray icon unregistration from Windows Explorer."""
        if hasattr(self, "tray_icon") and self.tray_icon:
            try:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
            except Exception:
                pass
            self.tray_icon = None

    def changeEvent(self, event):
        """Intercept window minimize to send window to tray instead of taskbar clutter."""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                QTimer.singleShot(0, self._minimize_to_tray)
                return
        super().changeEvent(event)

    def closeEvent(self, event):
        """Clean shutdown when user closes window."""
        self._cleanup_tray()
        self.ui_timer.stop()
        self.engine.stop()
        save_settings(self.cfg)
        super().closeEvent(event)

    # =========================================================================
    # UI Layout Construction
    # =========================================================================
    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # 1. Master Control Header & PTT Indicator
        root_layout.addLayout(self._create_header())

        # 2. Interactive Audio Signal Chain Monitor (The core user request)
        root_layout.addWidget(self._create_signal_chain_monitor())

        # 3. Functional Tabs (Topping Routing / Models & RAM / Live Transcript)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_routing_tab(), "🎛 Настройка звука и устройств")
        self.tabs.addTab(self._create_models_tab(), "🧠 Модели и Управление памятью")
        self.tabs.addTab(self._create_transcript_tab(), "📜 Живой журнал перевода")
        root_layout.addWidget(self.tabs, stretch=1)

        # Wire China Mirror environment synchronization
        if hasattr(self, "chk_china_mirror"):
            self.chk_china_mirror.toggled.connect(self._on_china_mirror_toggled)
            if self.chk_china_mirror.isChecked():
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        # Synchronize UI with active pipeline (RU vs ZH) and audit disk models at boot
        self._update_pipeline_ui()
        self._populate_voice_combos()

    def _create_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(12)

        # Master Toggle Button
        self.btn_master = QPushButton("🟢 СИСТЕМА АКТИВНА (F8)")
        self.btn_master.setFixedHeight(34)
        self.btn_master.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """)
        self.btn_master.clicked.connect(self._on_toggle_master)
        h.addWidget(self.btn_master)

        # Glowing PTT State Banner
        self.ptt_banner = QLabel("🎙 Нажмите Shift + Колесико мыши (MMB) для записи речи")
        self.ptt_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ptt_banner.setFixedHeight(34)
        self.ptt_banner.setStyleSheet("""
            QLabel {
                background-color: #1f2937;
                color: #9ca3af;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #374151;
                border-radius: 6px;
            }
        """)
        h.addWidget(self.ptt_banner, stretch=1)

        # Total Pipeline Latency Badge
        self.total_badge = QLabel("⏱ 0 ms")
        self.total_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_badge.setFixedHeight(42)
        self.total_badge.setFixedWidth(130)
        self.total_badge.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #10b981;
                font-family: Consolas, monospace;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #1f2937;
                border-radius: 6px;
            }
        """)
        h.addWidget(self.total_badge)

        # Minimize to Tray Button
        self.btn_tray = QPushButton("📥 В трей")
        self.btn_tray.setFixedHeight(42)
        self.btn_tray.setStyleSheet("""
            QPushButton {
                background-color: #1f2937;
                color: #c084fc;
                font-family: Consolas, monospace;
                font-size: 11px;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 12px;
                border: 1px solid #7c3aed;
            }
            QPushButton:hover { background-color: #111827; }
        """)
        self.btn_tray.clicked.connect(self._minimize_to_tray)
        h.addWidget(self.btn_tray)

        return h

    def _create_signal_chain_monitor(self) -> QGroupBox:
        self.grp_chain = QGroupBox("Интерактивная цепочка звука (Audio Signal Chain & Real-Time Monitors)")
        self.grp_chain.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; }")
        main_v = QVBoxLayout(self.grp_chain)
        main_v.setContentsMargins(8, 6, 8, 6)
        main_v.setSpacing(6)

        # Pipeline selector bar
        h_pipe = QHBoxLayout()
        h_pipe.setContentsMargins(0, 0, 0, 4)
        self.lbl_pipe = QLabel("Языковой конвейер (Language Pipeline):")
        self.lbl_pipe.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
        h_pipe.addWidget(self.lbl_pipe)

        self.btn_pipe_ru = QPushButton("🇷🇺 Русский профиль (RU➔EN: GigaAM + Opus-MT)")
        self.btn_pipe_ru.setFixedHeight(26)
        self.btn_pipe_ru.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pipe_ru.clicked.connect(lambda: self._on_switch_pipeline("ru_en"))
        h_pipe.addWidget(self.btn_pipe_ru)

        self.btn_pipe_zh = QPushButton("🇨🇳 中文配置 / Китайский (ZH➔EN: SenseVoice + Opus-MT)")
        self.btn_pipe_zh.setFixedHeight(26)
        self.btn_pipe_zh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pipe_zh.clicked.connect(lambda: self._on_switch_pipeline("zh_en"))
        h_pipe.addWidget(self.btn_pipe_zh)

        h_pipe.addStretch()
        main_v.addLayout(h_pipe)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Node 1: Input Mic
        v1 = QVBoxLayout()
        self.node_mic = ChainNode("1", "ВХОД", "NVIDIA Broadcast")
        self.meter_mic = VUMeter()
        v1.addWidget(self.node_mic)
        v1.addWidget(self.meter_mic)
        layout.addLayout(v1, stretch=1)

        arrow1 = QLabel("➔")
        arrow1.setStyleSheet("color: #4b5563; font-size: 18px; font-weight: bold;")
        arrow1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow1)

        # Node 2: STT (GigaAM or SenseVoice)
        self.node_stt = ChainNode("2", "STT (ASR)", "Sber GigaAM v3 CTC")
        layout.addWidget(self.node_stt, stretch=1)

        arrow2 = QLabel("➔")
        arrow2.setStyleSheet("color: #4b5563; font-size: 18px; font-weight: bold;")
        arrow2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow2)

        # Node 3: MT (Opus-MT RU or ZH)
        self.node_mt = ChainNode("3", "MT (ПЕРЕВОД)", "Opus-MT RU➔EN")
        layout.addWidget(self.node_mt, stretch=1)

        arrow3 = QLabel("➔")
        arrow3.setStyleSheet("color: #4b5563; font-size: 18px; font-weight: bold;")
        arrow3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow3)

        # Node 4: TTS (Pocket-TTS)
        self.node_tts = ChainNode("4", "TTS (ГОЛОС)", "Pocket-TTS Клон")
        layout.addWidget(self.node_tts, stretch=1)

        arrow4 = QLabel("➔")
        arrow4.setStyleSheet("color: #4b5563; font-size: 18px; font-weight: bold;")
        arrow4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow4)

        # Node 5: Output Topping
        v5 = QVBoxLayout()
        self.node_out = ChainNode("5", "ВЫХОД", "Playback 3/4 ➔ Игра")
        self.meter_out = VUMeter()
        v5.addWidget(self.node_out)
        v5.addWidget(self.meter_out)
        layout.addLayout(v5, stretch=1)

        main_v.addLayout(layout)
        self._update_pipeline_buttons_style()
        return self.grp_chain

    # =========================================================================
    # Tab 1: Routing & Topping E2x2
    # =========================================================================
    def _create_routing_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 1-Click Hardware Profiles Selector Banner
        self.grp_profiles = QGroupBox("Быстрый выбор режима звука в 1 клик")
        self.grp_profiles.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_prof = QHBoxLayout(self.grp_profiles)
        h_prof.setContentsMargins(8, 4, 8, 6)
        h_prof.setSpacing(10)

        self.btn_prof_topping = QPushButton("🎛 Режим: Звуковая карта Topping (0 ms)")
        self.btn_prof_topping.setToolTip("Аппаратный нулевой мониторинг через карту Topping E2x2 OTG (0 ms latency)")
        self.btn_prof_topping.setFixedHeight(34)
        self.btn_prof_topping.clicked.connect(lambda: self._on_switch_profile("topping"))
        h_prof.addWidget(self.btn_prof_topping, stretch=1)

        self.btn_prof_cable = QPushButton("🔌 Режим: Виртуальный Кабель (Для ПК без Topping)")
        self.btn_prof_cable.setToolTip("Универсальная передача аудио через драйвер VB-Audio Virtual Cable для любых ПК")
        self.btn_prof_cable.setFixedHeight(34)
        self.btn_prof_cable.clicked.connect(lambda: self._on_switch_profile("cable"))
        h_prof.addWidget(self.btn_prof_cable, stretch=1)

        layout.addWidget(self.grp_profiles)

        # Device Selection Grid (Ultra-compact)
        self.grp_devs = QGroupBox("Аудиоустройства")
        self.grp_devs.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 8px; }")
        grid = QGridLayout(self.grp_devs)
        grid.setContentsMargins(6, 4, 6, 6)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        inputs, outputs = AudioEngine.get_devices()

        # 1. Mic
        self.lbl_in = QLabel("1. Микрофон:")
        self.lbl_in.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(self.lbl_in, 0, 0)
        self.combo_in = NoWheelComboBox()
        self.combo_in.setFixedHeight(26)
        for idx, name in inputs:
            label = f"[{idx}] {name}"
            if "analog 1/2" in name.lower() or "broadcast" in name.lower():
                label = f"[{idx}] ⭐ [Topping] {name}"
            self.combo_in.addItem(label, name)
        cur_in = self.cfg.get("audio", {}).get("input_device", "NVIDIA Broadcast")
        for i in range(self.combo_in.count()):
            if cur_in.lower() in self.combo_in.itemText(i).lower():
                self.combo_in.setCurrentIndex(i)
                break
        self.combo_in.currentIndexChanged.connect(self._on_device_changed)
        grid.addWidget(self.combo_in, 0, 1)

        # 2. Out
        self.lbl_out = QLabel("2. Канал перевода:")
        self.lbl_out.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(self.lbl_out, 1, 0)
        self.combo_out = NoWheelComboBox()
        self.combo_out.setFixedHeight(26)
        for idx, name in outputs:
            label = f"[{idx}] {name}"
            if "3/4" in name.lower():
                label = f"[{idx}] ⭐ [Topping: Голос ИИ] {name}"
            elif "cable" in name.lower():
                label = f"[{idx}] ⭐ [VB-Cable: Голос ИИ] {name}"
            self.combo_out.addItem(label, name)
        cur_out = self.cfg.get("audio", {}).get("output_device", "Playback 3/4")
        for i in range(self.combo_out.count()):
            if cur_out.lower() in self.combo_out.itemText(i).lower():
                self.combo_out.setCurrentIndex(i)
                break
        self.combo_out.currentIndexChanged.connect(self._on_device_changed)
        grid.addWidget(self.combo_out, 1, 1)

        # 3. Sidetone
        self.lbl_side = QLabel("3. Наушники:")
        self.lbl_side.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(self.lbl_side, 2, 0)
        self.combo_side = NoWheelComboBox()
        self.combo_side.setFixedHeight(26)
        for idx, name in outputs:
            label = f"[{idx}] {name}"
            if "1/2" in name.lower():
                label = f"[{idx}] ⭐ [Topping: Наушники] {name}"
            elif "speaker" in name.lower() or "динамик" in name.lower() or "headphone" in name.lower():
                label = f"[{idx}] ⭐ [Штатные наушники] {name}"
            self.combo_side.addItem(label, name)
        cur_side = self.cfg.get("audio", {}).get("sidetone_device", "Playback 1/2")
        for i in range(self.combo_side.count()):
            if cur_side.lower() in self.combo_side.itemText(i).lower():
                self.combo_side.setCurrentIndex(i)
                break
        self.combo_side.currentIndexChanged.connect(self._on_device_changed)
        grid.addWidget(self.combo_side, 2, 1)

        layout.addWidget(self.grp_devs)

        # Compact Controls Panel: Options & Volume in ONE horizontal row
        self.grp_opts = QGroupBox("Режимы микрофона и самопрослушивание")
        self.grp_opts.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_opts = QHBoxLayout(self.grp_opts)
        h_opts.setContentsMargins(8, 6, 8, 6)
        h_opts.setSpacing(14)

        self.chk_passthrough = QCheckBox("Пропускать голос (Passthrough)")
        self.chk_passthrough.setChecked(self.cfg.get("audio", {}).get("passthrough_enabled", True))
        self.chk_passthrough.toggled.connect(self._on_passthrough_toggle)
        h_opts.addWidget(self.chk_passthrough)

        self.chk_sidetone = QCheckBox("Слышать перевод (Sidetone)")
        self.chk_sidetone.setChecked(self.cfg.get("audio", {}).get("sidetone_enabled", True))
        self.chk_sidetone.toggled.connect(self._on_sidetone_toggle)
        h_opts.addWidget(self.chk_sidetone)

        h_opts.addSpacing(10)
        self.lbl_sidetone_title = QLabel("Громкость:")
        self.lbl_sidetone_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_opts.addWidget(self.lbl_sidetone_title)
        self.slider_sidetone = QSlider(Qt.Orientation.Horizontal)
        self.slider_sidetone.setRange(0, 100)
        cur_vol = int(self.cfg.get("audio", {}).get("sidetone_volume", 0.70) * 100)
        self.slider_sidetone.setValue(cur_vol)
        self.lbl_sidetone_val = QLabel(f"{cur_vol}%")
        self.lbl_sidetone_val.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: Consolas, monospace;")
        self.slider_sidetone.valueChanged.connect(self._on_sidetone_slider)
        h_opts.addWidget(self.slider_sidetone)
        h_opts.addWidget(self.lbl_sidetone_val)

        layout.addWidget(self.grp_opts)

        # 1. AI Voice Selection Block on Tab 1
        self.grp_voice = QGroupBox("🎙 Выбор тембра голоса ИИ")
        self.grp_voice.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_voice = QHBoxLayout(self.grp_voice)
        h_voice.setContentsMargins(8, 6, 8, 6)
        h_voice.setSpacing(10)

        self.lbl_voice_main = QLabel("Голос перевода:")
        self.lbl_voice_main.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 11px;")
        h_voice.addWidget(self.lbl_voice_main)

        self.combo_voices_main = NoWheelComboBox()
        self.combo_voices_main.setFixedHeight(28)
        self.combo_voices_main.currentIndexChanged.connect(self._on_voice_changed)
        h_voice.addWidget(self.combo_voices_main, stretch=1)

        self.btn_add_voice_main = QPushButton("🎙 Добавить свой голос (7 сек)")
        self.btn_add_voice_main.setFixedHeight(28)
        self.btn_add_voice_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_voice_main.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 14px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_add_voice_main.clicked.connect(self._on_open_voice_studio_wizard)
        h_voice.addWidget(self.btn_add_voice_main)

        layout.addWidget(self.grp_voice)

        # 2. Clean PTT Control Row
        self.grp_ptt = QGroupBox("🎮 Активация микрофона (Push-to-Talk)")
        self.grp_ptt.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_ptt = QHBoxLayout(self.grp_ptt)
        h_ptt.setContentsMargins(8, 6, 8, 6)
        h_ptt.setSpacing(10)

        self.lbl_ptt_prompt = QLabel("Кнопка PTT:")
        self.lbl_ptt_prompt.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 11px;")
        h_ptt.addWidget(self.lbl_ptt_prompt)

        self.btn_bind_ptt = QPushButton()
        self.btn_bind_ptt.setFixedHeight(28)
        self.btn_bind_ptt.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_ptt_button_text()
        self.btn_bind_ptt.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 2px 16px;
            }
            QPushButton:hover { background-color: #0f172a; }
        """)
        self.btn_bind_ptt.clicked.connect(self._on_click_bind_ptt)
        h_ptt.addWidget(self.btn_bind_ptt)

        self.btn_reset_ptt = QPushButton("↺ Shift + MMB")
        self.btn_reset_ptt.setFixedHeight(28)
        self.btn_reset_ptt.setToolTip("Сбросить кнопку на стандартную (Shift + Колесико мыши)")
        self.btn_reset_ptt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_ptt.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #94a3b8;
                font-size: 11px;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 2px 10px;
            }
            QPushButton:hover { background-color: #1e293b; color: #f1f5f9; }
        """)
        self.btn_reset_ptt.clicked.connect(self._on_reset_ptt)
        h_ptt.addWidget(self.btn_reset_ptt)

        h_ptt.addStretch()
        self.lbl_master_pause = QLabel("Мастер-пауза: <b>F8</b>")
        self.lbl_master_pause.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_ptt.addWidget(self.lbl_master_pause)

        layout.addWidget(self.grp_ptt)

        # Universal Educational Routing Banner (Compact 1-line format)
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #0f233a;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        v_info = QHBoxLayout(self.info_frame)
        v_info.setContentsMargins(4, 2, 4, 2)
        self.info_title = QLabel("💡 <b>Справка:</b> Голос ИИ идет в Playback 3/4 ➔ направлен в Loopback 1+2 (микрофон игры). Наушники: Playback 1/2 (0 ms).")
        self.info_title.setStyleSheet("color: #93c5fd; font-size: 11px;")
        v_info.addWidget(self.info_title)
        layout.addWidget(self.info_frame)

        self._update_profile_buttons_style()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        scroll.setWidget(w)
        return scroll

    # =========================================================================
    # Tab 2: Models & RAM Management
    # =========================================================================
    def _create_models_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Telemetry Summary Bar
        self.ram_grp = QGroupBox("📊 Инвентарь нейросетей и потребление памяти")
        self.ram_grp.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_ram = QHBoxLayout(self.ram_grp)
        h_ram.setContentsMargins(8, 6, 8, 6)

        self.lbl_ram_telemetry = QLabel("ОЗУ всех моделей: ~535 MB | Видеопамять (VRAM): 0 MB (Strict CPU) | Пул инференса: 4T (Zen 4)")
        self.lbl_ram_telemetry.setStyleSheet("font-family: Consolas, monospace; font-weight: bold; color: #38bdf8; font-size: 12px;")
        h_ram.addWidget(self.lbl_ram_telemetry)
        h_ram.addStretch()
        layout.addWidget(self.ram_grp)

        # Informational Dynamic Cards
        models_grid = QGridLayout()
        models_grid.setContentsMargins(0, 0, 0, 0)
        models_grid.setSpacing(8)

        # Card 1: STT
        self.stt_box = QGroupBox("🎙 1. Распознавание речи (STT / ASR)")
        self.stt_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_stt = QVBoxLayout(self.stt_box)
        v_stt.setContentsMargins(8, 6, 8, 8)
        v_stt.setSpacing(3)
        self.lbl_stt_title = QLabel("<b>Sber GigaAM v3 Conformer CTC</b>")
        v_stt.addWidget(self.lbl_stt_title)
        self.lbl_stt_engine = QLabel("Движок: Sherpa-ONNX INT8 | 2T (Zen 4)")
        v_stt.addWidget(self.lbl_stt_engine)
        self.lbl_stt_disk = QLabel("Размер на диске: 0 МБ")
        self.lbl_stt_disk.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_stt.addWidget(self.lbl_stt_disk)
        self.lbl_stt_state = QLabel("⚪ Не проверено")
        self.lbl_stt_state.setStyleSheet("font-weight: bold; font-size: 11px;")
        v_stt.addWidget(self.lbl_stt_state)
        models_grid.addWidget(self.stt_box, 0, 0)

        # Card 2: MT
        self.mt_box = QGroupBox("🌐 2. Нейроперевод (MT)")
        self.mt_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_mt = QVBoxLayout(self.mt_box)
        v_mt.setContentsMargins(8, 6, 8, 8)
        v_mt.setSpacing(3)
        self.lbl_mt_title = QLabel("<b>Helsinki Opus-MT RU ➔ EN</b>")
        v_mt.addWidget(self.lbl_mt_title)
        self.lbl_mt_engine = QLabel("Движок: CTranslate2 INT8 | 2T (Zen 4)")
        v_mt.addWidget(self.lbl_mt_engine)
        self.lbl_mt_disk = QLabel("Размер на диске: 0 МБ")
        self.lbl_mt_disk.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_mt.addWidget(self.lbl_mt_disk)
        self.lbl_mt_state = QLabel("⚪ Не проверено")
        self.lbl_mt_state.setStyleSheet("font-weight: bold; font-size: 11px;")
        v_mt.addWidget(self.lbl_mt_state)
        models_grid.addWidget(self.mt_box, 0, 1)

        # Card 3: TTS & Voice Selector
        self.tts_box = QGroupBox("🗣 3. Синтез и клонирование голоса (TTS)")
        self.tts_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_tts = QVBoxLayout(self.tts_box)
        v_tts.setContentsMargins(8, 6, 8, 8)
        v_tts.setSpacing(4)

        h_tts_top = QHBoxLayout()
        h_tts_top.addWidget(QLabel("<b>Kyutai Pocket-TTS 24kHz (Mimi Codec)</b>"))
        h_tts_top.addStretch()
        self.lbl_tts_disk = QLabel("Диск: 0 МБ")
        self.lbl_tts_disk.setStyleSheet("color: #94a3b8; font-size: 11px; margin-right: 8px;")
        h_tts_top.addWidget(self.lbl_tts_disk)
        self.lbl_tts_state = QLabel("⚪ Не проверено")
        self.lbl_tts_state.setStyleSheet("font-weight: bold; font-size: 11px;")
        h_tts_top.addWidget(self.lbl_tts_state)
        v_tts.addLayout(h_tts_top)

        h_voice = QHBoxLayout()
        self.lbl_voice_models = QLabel("Выбор тембра голоса:")
        self.lbl_voice_models.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        h_voice.addWidget(self.lbl_voice_models)
        self.combo_voices = NoWheelComboBox()
        self.combo_voices.setFixedHeight(28)
        self._populate_voice_combos()
        self.combo_voices.currentIndexChanged.connect(self._on_voice_changed)
        h_voice.addWidget(self.combo_voices, stretch=1)

        # Direct in-studio Voice Training & Cloning Studio Button
        self.btn_clone_in_studio = QPushButton("🎙 Обучить / Записать новый голос (7 сек)")
        self.btn_clone_in_studio.setFixedHeight(28)
        self.btn_clone_in_studio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clone_in_studio.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 10px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_clone_in_studio.clicked.connect(self._on_open_voice_studio_wizard)
        h_voice.addWidget(self.btn_clone_in_studio)

        v_tts.addLayout(h_voice)

        # Speed / Natural Pacing Slider
        h_speed = QHBoxLayout()
        self.lbl_speed_title = QLabel("Скорость речи (SOLA):")
        self.lbl_speed_title.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 11px;")
        h_speed.addWidget(self.lbl_speed_title)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(80, 120)
        cur_spd_pct = int(round(self.cfg.get("models", {}).get("tts_speed", 0.92) * 100))
        self.slider_speed.setValue(cur_spd_pct)
        self.lbl_speed_val = QLabel(f"{cur_spd_pct}% (Спокойная речь)")
        self.lbl_speed_val.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: Consolas, monospace; font-size: 11px;")
        self.slider_speed.valueChanged.connect(self._on_speed_slider)
        h_speed.addWidget(self.slider_speed, stretch=1)
        h_speed.addWidget(self.lbl_speed_val)
        v_tts.addLayout(h_speed)

        models_grid.addWidget(self.tts_box, 1, 0, 1, 2)
        layout.addLayout(models_grid)

        # Dedicated Honest Downloader Card (Zero Fake UI)
        self.grp_dl = QGroupBox("📥 Менеджер загрузки моделей / 模型下载器 (Zero-Fake Downloader)")
        self.grp_dl.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_dl = QVBoxLayout(self.grp_dl)
        v_dl.setContentsMargins(10, 8, 10, 10)
        v_dl.setSpacing(8)

        h_dl_ctrl = QHBoxLayout()
        self.chk_china_mirror = QCheckBox("🇨🇳 国内镜像加速 (China Mirror: hf-mirror.com)")
        self.chk_china_mirror.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.chk_china_mirror.setToolTip("Включает загрузку через китайский узел hf-mirror.com для максимальной скорости внутри КНР")
        if getattr(self.mm, "pipeline", "ru_en") == "zh_en":
            self.chk_china_mirror.setChecked(True)
        h_dl_ctrl.addWidget(self.chk_china_mirror)

        h_dl_ctrl.addStretch()

        self.btn_download_models = QPushButton("📥 一键下载所需模型 / Скачать недостающие модели")
        self.btn_download_models.setFixedHeight(32)
        self.btn_download_models.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #374151; color: #9ca3af; }
        """)
        self.btn_download_models.clicked.connect(self._on_start_download_models)
        h_dl_ctrl.addWidget(self.btn_download_models)

        self.btn_reload_models = QPushButton("⚡ Загрузить в память (Load in RAM)")
        self.btn_reload_models.setFixedHeight(32)
        self.btn_reload_models.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_reload_models.clicked.connect(self._on_reload_models)
        h_dl_ctrl.addWidget(self.btn_reload_models)

        v_dl.addLayout(h_dl_ctrl)

        # Progress bar & real telemetry
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        self.download_progress.setFixedHeight(18)
        self.download_progress.setTextVisible(True)
        self.download_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-size: 11px;
                font-family: Consolas, monospace;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        v_dl.addWidget(self.download_progress)

        self.lbl_download_status = QLabel("Статус загрузки: Все файлы проверены на диске")
        self.lbl_download_status.setStyleSheet("color: #94a3b8; font-size: 11px; font-family: Consolas, monospace;")
        v_dl.addWidget(self.lbl_download_status)

        layout.addWidget(self.grp_dl)
        self._refresh_models_tab()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        scroll.setWidget(w)
        return scroll

    # =========================================================================
    # Tab 3: Live Transcript
    # =========================================================================
    def _create_transcript_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top Bar
        h_top = QHBoxLayout()
        h_top.addWidget(QLabel("<b>История распознанных и переведенных фраз:</b>"))
        h_top.addStretch()
        btn_clear = QPushButton("🧹 Очистить журнал")
        btn_clear.clicked.connect(self._on_clear_transcript)
        h_top.addWidget(btn_clear)
        layout.addLayout(h_top)

        # Table
        self.tbl_transcript = QTableWidget()
        self.tbl_transcript.setColumnCount(4)
        self.tbl_transcript.setHorizontalHeaderLabels(["Время", "🇷🇺 Сказано (Оригинал)", "🇬🇧 Переведено в игру", "Задержка (STT+MT+TTS)"])
        self.tbl_transcript.horizontalHeader().setStretchLastSection(True)
        self.tbl_transcript.setColumnWidth(0, 75)
        self.tbl_transcript.setColumnWidth(1, 280)
        self.tbl_transcript.setColumnWidth(2, 280)
        layout.addWidget(self.tbl_transcript)

        return w

    # =========================================================================
    # Telemetry & Polling (30 FPS decoupled loop)
    # =========================================================================
    def _update_telemetry(self):
        """Called at 30 FPS. Reads atomic state from audio engine."""
        # 1. VU Meters
        self.meter_mic.setValue(int(self.engine.mic_peak_db))
        self.meter_out.setValue(int(self.engine.out_peak_db))

        # 2. PTT Banner State (Guarded to prevent Qt CSS re-parsing 30 times/sec)
        state = self.engine.engine_state
        master_enabled = self.engine._master_enabled
        is_zh = (getattr(self.mm, "pipeline", "ru_en") == "zh_en")
        if state != self._last_rendered_state or master_enabled != self._last_rendered_master:
            self._last_rendered_state = state
            self._last_rendered_master = master_enabled

            if not master_enabled:
                txt = "⏸ 系统已暂停 (按 F8 键激活)" if is_zh else "⏸ СИСТЕМА НА ПАУЗЕ (Нажмите F8 для включения)"
                self.ptt_banner.setText(txt)
                self.ptt_banner.setStyleSheet("background-color: #374151; color: #9ca3af; font-weight: bold; border-radius: 6px;")
            elif state == "RECORDING":
                txt = "🔴 正在录音对讲 (按住讲话中)..." if is_zh else "🔴 ИДЕТ ЗАПИСЬ РЕЧИ (Shift + MMB нажат)..."
                self.ptt_banner.setText(txt)
                self.ptt_banner.setStyleSheet("background-color: #991b1b; color: #ffffff; font-weight: bold; border-radius: 6px;")
            elif state == "PROCESSING":
                txt = "⚡ 正在翻译与神经合成语音..." if is_zh else "⚡ ПЕРЕВОД И ГЕНЕРАЦИЯ ГОЛОСА..."
                self.ptt_banner.setText(txt)
                self.ptt_banner.setStyleSheet("background-color: #854d0e; color: #fef08a; font-weight: bold; border-radius: 6px;")
            elif state == "SPEAKING":
                txt = "🔊 正在播放翻译语音到游戏 (Playback 3/4)..." if is_zh else "🔊 ОЗВУЧИВАНИЕ В ИГРУ (Playback 3/4 ➔ Loopback 1+2)"
                self.ptt_banner.setText(txt)
                self.ptt_banner.setStyleSheet("background-color: #065f46; color: #a7f3d0; font-weight: bold; border-radius: 6px;")
            else:
                txt = "🎙 请按住快捷键开始讲话 (Push-to-Talk)" if is_zh else "🎙 Нажмите Shift + Колесико мыши (MMB) для записи речи"
                self.ptt_banner.setText(txt)
                self.ptt_banner.setStyleSheet("background-color: #1f2937; color: #9ca3af; font-weight: bold; border: 1px solid #374151; border-radius: 6px;")

        # 3. Chain Nodes Status & Latency Badges
        stt_status = self.mm._stt_status
        mt_status = self.mm._mt_status
        tts_status = self.mm._tts_status

        badge_ready = "已加载" if is_zh else "В ОЗУ"
        self.node_stt.set_telemetry(
            badge_ready if stt_status == "ready" else stt_status.upper(),
            self.engine.last_stt_ms,
            is_active=(state == "PROCESSING")
        )
        self.node_mt.set_telemetry(
            badge_ready if mt_status == "ready" else mt_status.upper(),
            self.engine.last_mt_ms,
            is_active=(state == "PROCESSING")
        )
        self.node_tts.set_telemetry(
            badge_ready if tts_status == "ready" else tts_status.upper(),
            self.engine.last_tts_ms,
            is_active=(state == "SPEAKING")
        )

        # Total Latency Badge
        if self.engine.last_total_ms > 0:
            self.total_badge.setText(f"⏱ {self.engine.last_total_ms:.0f} ms")
        else:
            self.total_badge.setText("⏱ 0 ms")

        # 4. RAM Telemetry
        ram_mb = self.mm.get_process_ram_mb()
        self.lbl_ram_telemetry.setText(f"RAM процесса: {ram_mb:.0f} MB | VRAM: 0 MB (Strict CPU)")

    # =========================================================================
    # Callbacks & Handlers
    # =========================================================================
    def _on_toggle_master(self):
        active = self.engine.toggle_master()
        if active:
            self.btn_master.setText("🟢 СИСТЕМА АКТИВНА (F8)")
            self.btn_master.setStyleSheet("background-color: #059669; color: #fff; font-weight: bold; border-radius: 6px;")
        else:
            self.btn_master.setText("⏸ ПАУЗА (F8)")
            self.btn_master.setStyleSheet("background-color: #4b5563; color: #fff; font-weight: bold; border-radius: 6px;")

    def _on_device_changed(self):
        in_name = self.combo_in.currentData()
        out_name = self.combo_out.currentData()
        side_name = self.combo_side.currentData()

        if in_name:
            self.cfg["audio"]["input_device"] = in_name
            self.node_mic.sub_lbl.setText(in_name)
        if out_name:
            self.cfg["audio"]["output_device"] = out_name
            self.node_out.sub_lbl.setText(f"{out_name} ➔ Игра")
        if side_name:
            self.cfg["audio"]["sidetone_device"] = side_name

        save_settings(self.cfg)
        self.engine.restart_streams()

    def _on_passthrough_toggle(self, checked: bool):
        self.cfg["audio"]["passthrough_enabled"] = checked
        save_settings(self.cfg)
        if not checked:
            # Instantly drain any remaining mic chunks from output queue
            try:
                while not self.engine._out_queue.empty():
                    self.engine._out_queue.get_nowait()
            except Exception:
                pass

    def _on_sidetone_toggle(self, checked: bool):
        self.cfg["audio"]["sidetone_enabled"] = checked
        save_settings(self.cfg)

    def _on_sidetone_slider(self, val: int):
        self.lbl_sidetone_val.setText(f"{val}%")
        self.cfg["audio"]["sidetone_volume"] = val / 100.0
        save_settings(self.cfg)

    def _update_profile_buttons_style(self):
        mode = self.cfg.get("audio", {}).get("routing_mode", "topping")
        if mode == "topping":
            self.btn_prof_topping.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    font-weight: bold;
                    border: 2px solid #60a5fa;
                    border-radius: 6px;
                }
            """)
            self.btn_prof_cable.setStyleSheet("""
                QPushButton {
                    background-color: #1f2937;
                    color: #9ca3af;
                    border: 1px solid #374151;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #374151; }
            """)
        else:
            self.btn_prof_cable.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: #ffffff;
                    font-weight: bold;
                    border: 2px solid #34d399;
                    border-radius: 6px;
                }
            """)
            self.btn_prof_topping.setStyleSheet("""
                QPushButton {
                    background-color: #1f2937;
                    color: #9ca3af;
                    border: 1px solid #374151;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #374151; }
            """)

    def _on_switch_profile(self, mode: str):
        success, msg = RoutingPresets.apply_preset(mode, self.cfg)
        if success:
            save_settings(self.cfg)
            self._update_profile_buttons_style()
            self._populate_device_combos()

            hw = RoutingPresets.get_hardware_info()
            if mode == "cable" and not hw.get("has_cable", False):
                reply = QMessageBox.question(
                    self,
                    "Установка Виртуального Кабеля",
                    "На вашем ПК пока не найден виртуальный кабель (VB-Cable).\n\n"
                    "Хотите установить его автоматически в 1 клик?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    import subprocess
                    from pathlib import Path
                    bat = Path(__file__).resolve().parent.parent.parent / "scripts" / "install_vbcable.bat"
                    if bat.is_file():
                        subprocess.Popen(["cmd.exe", "/c", str(bat)])
            else:
                QMessageBox.information(self, "Профиль переключен", msg)

    def _refresh_device_combos(self):
        cur_in = self.cfg.get("audio", {}).get("input_device", "")
        cur_out = self.cfg.get("audio", {}).get("output_device", "")
        cur_side = self.cfg.get("audio", {}).get("sidetone_device", "")

        for i in range(self.combo_in.count()):
            if cur_in.lower() in self.combo_in.itemText(i).lower():
                self.combo_in.setCurrentIndex(i)
                break
        for i in range(self.combo_out.count()):
            if cur_out.lower() in self.combo_out.itemText(i).lower():
                self.combo_out.setCurrentIndex(i)
                break
        for i in range(self.combo_side.count()):
            if cur_side.lower() in self.combo_side.itemText(i).lower():
                self.combo_side.setCurrentIndex(i)
                break

        self.node_mic.sub_lbl.setText(cur_in)
        self.node_out.sub_lbl.setText(f"{cur_out} ➔ Игра")
        self.engine.restart_streams()

    def _format_key_display(self, raw_key: str) -> str:
        """Format any combination or single key into clean, human-friendly Russian label."""
        parts = [p.strip().lower() for p in raw_key.split("+") if p.strip()]
        if not parts:
            return "⌨ SHIFT + КОЛЕСИКО (MMB)"

        labels = []
        is_mouse = False
        is_gamepad = False

        for p in parts:
            if p == "shift":
                labels.append("SHIFT")
            elif p in ("ctrl", "control"):
                labels.append("CTRL")
            elif p == "alt":
                labels.append("ALT")
            elif p in ("middle", "mmb"):
                labels.append("КОЛЕСИКО (MMB)")
                is_mouse = True
            elif p in ("mouse4", "xbutton1"):
                labels.append("MOUSE 4")
                is_mouse = True
            elif p in ("mouse5", "xbutton2"):
                labels.append("MOUSE 5")
                is_mouse = True
            elif p == "left":
                labels.append("LMB")
                is_mouse = True
            elif p == "right":
                labels.append("RMB")
                is_mouse = True
            elif p.startswith("gamepad"):
                labels.append(p.replace("gamepad_", "").upper())
                is_gamepad = True
            elif p == "caps_lock":
                labels.append("CAPSLOCK")
            elif p == "space":
                labels.append("SPACE")
            else:
                labels.append(p.upper())

        combo_str = " + ".join(labels)
        icon = "🎮 " if is_gamepad else ("🖱 " if is_mouse else "⌨ ")
        return f"{icon}{combo_str}"

    def _update_ptt_button_text(self):
        """Update PTT button text with clear human-readable name."""
        cur_key = self.cfg.get("ptt", {}).get("key", "shift+middle")
        display = self._format_key_display(cur_key)
        if hasattr(self, "btn_bind_ptt"):
            self.btn_bind_ptt.setText(display)

    def _on_reset_ptt(self):
        """Reset PTT keybinding to standard Shift + MMB."""
        self.cfg.setdefault("ptt", {})["key"] = "shift+middle"
        save_settings(self.cfg)
        self._update_ptt_button_text()
        if self.hotkeys:
            self.hotkeys.set_binding("shift+middle")

    def _populate_voice_combos(self):
        """Scan all user cloned, custom, and stock voices and populate combo boxes."""
        combos = []
        if hasattr(self, "combo_voices_main"):
            combos.append(self.combo_voices_main)
        if hasattr(self, "combo_voices"):
            combos.append(self.combo_voices)

        if not combos:
            return

        available = self.mm.get_available_voices()
        cur_v = self.cfg.get("models", {}).get("tts_voice", "my_pocket_voice")
        sel_idx = 0

        for cb in combos:
            cb.blockSignals(True)
            cb.clear()
            for i, (v_id, v_label) in enumerate(available):
                cb.addItem(v_label, v_id)
                if v_id == cur_v:
                    sel_idx = i
            cb.setCurrentIndex(sel_idx)
            cb.blockSignals(False)

    def _on_voice_changed(self, idx: int):
        """Synchronize voice selection across all tabs."""
        sender = self.sender()
        if not sender:
            return
        voice_key = sender.currentData()
        if not voice_key:
            return

        self.cfg.setdefault("models", {})["tts_voice"] = voice_key
        save_settings(self.cfg)
        self.mm.set_voice(voice_key)

        # Sync other combo box
        for cb in (getattr(self, "combo_voices_main", None), getattr(self, "combo_voices", None)):
            if cb and cb is not sender:
                cb.blockSignals(True)
                for i in range(cb.count()):
                    if cb.itemData(i) == voice_key:
                        cb.setCurrentIndex(i)
                        break
                cb.blockSignals(False)

    def _on_open_voice_studio_wizard(self):
        """Launch integrated Voice Cloning Studio with custom name support."""
        name, ok = QInputDialog.getText(
            self,
            "Имя профиля голоса",
            "Введите название нового голоса (например: Мой голос 2):",
            text="Мой голос"
        )
        if not ok or not name.strip():
            return

        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name.strip().lower())
        if not safe_name:
            safe_name = "my_custom_voice"

        try:
            from launcher.voice_wizard import VoiceCloningWizard
        except ImportError:
            from voice_wizard import VoiceCloningWizard

        wiz = VoiceCloningWizard(self, target_voice_name=safe_name)
        if wiz.exec():
            # Refresh voice lists on all tabs and select newly trained voice
            custom_id = f"custom:{safe_name}.safetensors"
            self.cfg.setdefault("models", {})["tts_voice"] = custom_id
            save_settings(self.cfg)
            self.mm.set_voice(custom_id)
            self._populate_voice_combos()
            self._refresh_models_tab()

    def _on_click_bind_ptt(self):
        """Open clean key capture dialog to bind any keyboard, mouse, or gamepad button."""
        is_zh = (getattr(self.mm, "pipeline", "ru_en") == "zh_en")
        dialog = KeyCaptureDialog(self, hotkeys=self.hotkeys, is_zh=is_zh)
        if dialog.exec() and dialog.captured_key:
            new_bind = dialog.captured_key
            self.cfg.setdefault("ptt", {})["key"] = new_bind
            save_settings(self.cfg)
            self._update_ptt_button_text()
            if self.hotkeys:
                self.hotkeys.set_binding(new_bind)

    def _on_speed_slider(self, val: int):
        speed_float = val / 100.0
        self.mm.tts_speed = speed_float
        if "models" not in self.cfg:
            self.cfg["models"] = {}
        self.cfg["models"]["tts_speed"] = speed_float
        if val < 95:
            hint = "Спокойная речь"
        elif val > 105:
            hint = "Быстрая речь"
        else:
            hint = "Стандартная речь"
        self.lbl_speed_val.setText(f"{val}% ({hint})")
        save_settings(self.cfg)

    def _on_load_all_models(self):
        self.btn_load_all.setEnabled(False)
        self.btn_load_all.setText("Загрузка...")
        QTimer.singleShot(50, self._do_load_all)

    def _do_load_all(self):
        voice = self.combo_voices.currentData()
        self.mm.load_all(voice=voice)
        self.btn_load_all.setEnabled(True)
        self.btn_load_all.setText("📥 Загрузить ВСЕ модели в ОЗУ")

    def _on_unload_all_models(self):
        self.mm.unload_all()

    def _on_new_transcript(self, rec: Dict):
        # Insert row at top
        row = 0
        self.tbl_transcript.insertRow(row)
        self.tbl_transcript.setItem(row, 0, QTableWidgetItem(rec.get("time", "")))
        self.tbl_transcript.setItem(row, 1, QTableWidgetItem(rec.get("ru", "")))
        self.tbl_transcript.setItem(row, 2, QTableWidgetItem(rec.get("en", "")))
        latency_str = f"ASR: {rec.get('stt_ms')}ms | MT: {rec.get('mt_ms')}ms | TTS: {rec.get('tts_ms')}ms (Всего: {rec.get('total_ms')}ms)"
        self.tbl_transcript.setItem(row, 3, QTableWidgetItem(latency_str))

    def _on_clear_transcript(self):
        self.tbl_transcript.setRowCount(0)

    # =========================================================================
    # Styling
    # =========================================================================
    def _apply_dark_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #131416;
            }
            QWidget {
                color: #e5e7eb;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #2e3035;
                background-color: #1a1b1e;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #212328;
                color: #9ca3af;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #1a1b1e;
                color: #ffffff;
                border: 1px solid #2e3035;
                border-bottom: none;
            }
            QGroupBox {
                border: 1px solid #2e3035;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #1a1b1e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QComboBox {
                background-color: #212328;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 28px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton {
                background-color: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QTableWidget {
                background-color: #1a1b1e;
                gridline-color: #2e3035;
                border: 1px solid #2e3035;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #212328;
                color: #9ca3af;
                padding: 6px;
                border: 1px solid #2e3035;
                font-weight: bold;
            }
            QCheckBox {
                spacing: 8px;
                min-height: 24px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)



    # =========================================================================
    # Pipeline Switching & Model Downloader Handlers
    # =========================================================================
    def _update_pipeline_buttons_style(self):
        """Update active/inactive highlighting on pipeline buttons."""
        if not hasattr(self, "btn_pipe_ru") or not hasattr(self, "btn_pipe_zh"):
            return
        pipe = getattr(self.mm, "pipeline", "ru_en")
        if pipe == "zh_en":
            self.btn_pipe_zh.setStyleSheet(
                "background-color: #059669; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 2px 10px;"
            )
            self.btn_pipe_ru.setStyleSheet(
                "background-color: #1f2937; color: #9ca3af; font-weight: normal; border: 1px solid #374151; border-radius: 4px; padding: 2px 10px;"
            )
        else:
            self.btn_pipe_ru.setStyleSheet(
                "background-color: #059669; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 2px 10px;"
            )
            self.btn_pipe_zh.setStyleSheet(
                "background-color: #1f2937; color: #9ca3af; font-weight: normal; border: 1px solid #374151; border-radius: 4px; padding: 2px 10px;"
            )

    def _on_switch_pipeline(self, pipeline: str):
        """Handle user clicking language pipeline button."""
        if self.mm.pipeline == pipeline and self.mm._stt_status == "ready":
            return
        log.info("User requested pipeline switch to '%s'", pipeline)
        self.mm.set_pipeline(pipeline, auto_reload=False)
        self.cfg.setdefault("models", {})["pipeline"] = pipeline
        save_settings(self.cfg)
        self._update_pipeline_ui()

    def _on_china_mirror_toggled(self, checked: bool):
        """Ensure HF_ENDPOINT is globally updated for all python huggingface calls."""
        if checked:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            log.info("China Mirror activated: set HF_ENDPOINT='https://hf-mirror.com'")
        else:
            os.environ.pop("HF_ENDPOINT", None)
            log.info("China Mirror deactivated: restored upstream HuggingFace endpoint")

    def _update_pipeline_ui(self):
        """Update chain nodes and entire studio UI localization based on active pipeline."""
        pipe = getattr(self.mm, "pipeline", "ru_en")
        is_zh = (pipe == "zh_en")
        self._update_pipeline_buttons_style()

        if is_zh:
            self.setWindowTitle("Stage 3: 实时语音翻译控制台 (S2ST) — CS2 & Discord")
            if hasattr(self, "btn_master"):
                self.btn_master.setText("🟢 系统已激活 (F8)" if self.engine._master_enabled else "⏸ 系统已暂停 (F8)")
            if hasattr(self, "btn_tray"):
                self.btn_tray.setText("📥 最小化到托盘")
            if hasattr(self, "grp_chain"):
                self.grp_chain.setTitle("交互式音频信号链路与实时监测 (Audio Signal Chain & Real-Time Monitors)")
            if hasattr(self, "lbl_pipe"):
                self.lbl_pipe.setText("语言流水线 (Language Pipeline):")
            if hasattr(self, "node_mic"):
                self.node_mic.update_info("1 输入", self.node_mic.sub_lbl.text())
            if hasattr(self, "node_stt"):
                self.node_stt.update_info("2 STT (语音识别)", "SenseVoice Chinese (INT8)")
            if hasattr(self, "node_mt"):
                self.node_mt.update_info("3 MT (机器翻译)", "Opus-MT ZH➔EN (INT8)")
            if hasattr(self, "node_tts"):
                self.node_tts.update_info("4 TTS (语音合成)", "Pocket-TTS 声音克隆")
            if hasattr(self, "node_out"):
                self.node_out.update_info("5 输出", "Playback 3/4 ➔ 游戏麦克风")
            if hasattr(self, "tabs"):
                self.tabs.setTabText(0, "🎛 音频与设备设置")
                self.tabs.setTabText(1, "🧠 模型与内存管理")
                self.tabs.setTabText(2, "📜 实时翻译日志")
            # Routing Tab (Tab 1)
            if hasattr(self, "grp_profiles"):
                self.grp_profiles.setTitle("一键音频模式选择")
            if hasattr(self, "btn_prof_topping"):
                self.btn_prof_topping.setText("🎛 模式: Topping声卡硬件回环 (0 ms)")
                self.btn_prof_topping.setToolTip("通过 Topping E2x2 OTG 硬件监听实现零延迟回环 (0 ms latency)")
            if hasattr(self, "btn_prof_cable"):
                self.btn_prof_cable.setText("🔌 模式: VB-Cable虚拟音频线 (普通电脑)")
                self.btn_prof_cable.setToolTip("通过 VB-Audio Virtual Cable 虚拟音频线传输至各类游戏和通话软件")
            if hasattr(self, "grp_devs"):
                self.grp_devs.setTitle("音频设备选择")
            if hasattr(self, "lbl_in"):
                self.lbl_in.setText("1. 麦克风输入:")
            if hasattr(self, "lbl_out"):
                self.lbl_out.setText("2. 翻译输出通道:")
            if hasattr(self, "lbl_side"):
                self.lbl_side.setText("3. 耳机监听:")
            if hasattr(self, "grp_opts"):
                self.grp_opts.setTitle("麦克风模式与监听")
            if hasattr(self, "chk_passthrough"):
                self.chk_passthrough.setText("原声直通游戏 (Passthrough)")
            if hasattr(self, "chk_sidetone"):
                self.chk_sidetone.setText("耳机监听AI翻译 (Sidetone)")
            if hasattr(self, "lbl_sidetone_title"):
                self.lbl_sidetone_title.setText("监听音量:")
            if hasattr(self, "grp_voice"):
                self.grp_voice.setTitle("🎙 AI 声音与音色选择")
            if hasattr(self, "lbl_voice_main"):
                self.lbl_voice_main.setText("翻译音色:")
            if hasattr(self, "btn_add_voice_main"):
                self.btn_add_voice_main.setText("🎙 录制专属声音 (7秒)")
            if hasattr(self, "grp_ptt"):
                self.grp_ptt.setTitle("🎮 按键对讲设置 (Push-to-Talk: 键盘、鼠标、VR/手柄)")
            if hasattr(self, "lbl_ptt_prompt"):
                self.lbl_ptt_prompt.setText("对讲按键 (PTT):")
            if hasattr(self, "btn_reset_ptt"):
                self.btn_reset_ptt.setToolTip("重置为默认按键 (Shift + 滚轮中键)")
            if hasattr(self, "lbl_master_pause"):
                self.lbl_master_pause.setText("总开关暂停: <b>F8</b>")
            if hasattr(self, "info_title"):
                self.info_title.setText("💡 <b>说明:</b> AI翻译语音输出至 Playback 3/4 ➔ 路由到 Loopback 1+2 (游戏麦克风). 耳机监听: Playback 1/2 (0 ms).")
            # Models Tab (Tab 2)
            if hasattr(self, "ram_grp"):
                self.ram_grp.setTitle("📊 模型清单与内存占用")
            if hasattr(self, "lbl_ram_telemetry"):
                self.lbl_ram_telemetry.setText("模型内存占用: ~535 MB | 显存 (VRAM): 0 MB (严格CPU) | 推理线程池: 4T (Zen 4)")
            if hasattr(self, "stt_box"):
                self.stt_box.setTitle("🎙 1. 语音识别 (STT / ASR)")
            if hasattr(self, "mt_box"):
                self.mt_box.setTitle("🌐 2. 机器翻译 (MT)")
            if hasattr(self, "tts_box"):
                self.tts_box.setTitle("🗣 3. 语音合成与声音克隆 (TTS)")
            if hasattr(self, "lbl_voice_models"):
                self.lbl_voice_models.setText("选择发音人音色:")
            if hasattr(self, "btn_clone_in_studio"):
                self.btn_clone_in_studio.setText("🎙 训练/录制新声音 (7秒)")
            if hasattr(self, "lbl_speed_title"):
                self.lbl_speed_title.setText("语速调整 (SOLA):")
            if hasattr(self, "grp_dl"):
                self.grp_dl.setTitle("📥 模型下载与国内镜像加速 (Zero-Fake Downloader)")
            if hasattr(self, "btn_download_models"):
                self.btn_download_models.setText("📥 一键下载所需模型")
            if hasattr(self, "chk_china_mirror"):
                self.chk_china_mirror.setChecked(True)
        else:
            self.setWindowTitle("Stage 3: Voice Translation Studio (S2ST) — CS2 & Discord")
            if hasattr(self, "btn_master"):
                self.btn_master.setText("🟢 СИСТЕМА АКТИВНА (F8)" if self.engine._master_enabled else "⏸ СИСТЕМА НА ПАУЗЕ (F8)")
            if hasattr(self, "btn_tray"):
                self.btn_tray.setText("📥 В трей")
            if hasattr(self, "grp_chain"):
                self.grp_chain.setTitle("Интерактивная цепочка звука (Audio Signal Chain & Real-Time Monitors)")
            if hasattr(self, "lbl_pipe"):
                self.lbl_pipe.setText("Языковой конвейер (Language Pipeline):")
            if hasattr(self, "node_mic"):
                self.node_mic.update_info("1 ВХОД", self.node_mic.sub_lbl.text())
            if hasattr(self, "node_stt"):
                self.node_stt.update_info("STT (ASR)", "Sber GigaAM v3 CTC")
            if hasattr(self, "node_mt"):
                self.node_mt.update_info("MT (ПЕРЕВОД)", "Opus-MT RU➔EN")
            if hasattr(self, "node_tts"):
                self.node_tts.update_info("4 TTS (ГОЛОС)", "Pocket-TTS Клон")
            if hasattr(self, "node_out"):
                self.node_out.update_info("5 ВЫХОД", "Playback 3/4 ➔ Игра")
            if hasattr(self, "tabs"):
                self.tabs.setTabText(0, "🎛 Настройка звука и устройств")
                self.tabs.setTabText(1, "🧠 Модели и Управление памятью")
                self.tabs.setTabText(2, "📜 Живой журнал перевода")
            # Routing Tab (Tab 1)
            if hasattr(self, "grp_profiles"):
                self.grp_profiles.setTitle("Быстрый выбор режима звука в 1 клик")
            if hasattr(self, "btn_prof_topping"):
                self.btn_prof_topping.setText("🎛 Режим: Звуковая карта Topping (0 ms)")
                self.btn_prof_topping.setToolTip("Аппаратный нулевой мониторинг через карту Topping E2x2 OTG (0 ms latency)")
            if hasattr(self, "btn_prof_cable"):
                self.btn_prof_cable.setText("🔌 Режим: Виртуальный Кабель (Для ПК без Topping)")
                self.btn_prof_cable.setToolTip("Универсальная передача аудио через драйвер VB-Audio Virtual Cable для любых ПК")
            if hasattr(self, "grp_devs"):
                self.grp_devs.setTitle("Аудиоустройства")
            if hasattr(self, "lbl_in"):
                self.lbl_in.setText("1. Микрофон:")
            if hasattr(self, "lbl_out"):
                self.lbl_out.setText("2. Канал перевода:")
            if hasattr(self, "lbl_side"):
                self.lbl_side.setText("3. Наушники:")
            if hasattr(self, "grp_opts"):
                self.grp_opts.setTitle("Режимы микрофона и самопрослушивание")
            if hasattr(self, "chk_passthrough"):
                self.chk_passthrough.setText("Пропускать голос (Passthrough)")
            if hasattr(self, "chk_sidetone"):
                self.chk_sidetone.setText("Слышать перевод (Sidetone)")
            if hasattr(self, "lbl_sidetone_title"):
                self.lbl_sidetone_title.setText("Громкость:")
            if hasattr(self, "grp_voice"):
                self.grp_voice.setTitle("🎙 Выбор тембра голоса ИИ")
            if hasattr(self, "lbl_voice_main"):
                self.lbl_voice_main.setText("Голос перевода:")
            if hasattr(self, "btn_add_voice_main"):
                self.btn_add_voice_main.setText("🎙 Добавить свой голос (7 сек)")
            if hasattr(self, "grp_ptt"):
                self.grp_ptt.setTitle("🎮 Управление Push-to-Talk (Клавиатура, Мышь, VR / Геймпад)")
            if hasattr(self, "lbl_ptt_prompt"):
                self.lbl_ptt_prompt.setText("Кнопка активации микрофона (PTT):")
            if hasattr(self, "btn_reset_ptt"):
                self.btn_reset_ptt.setToolTip("Сбросить кнопку на стандартную (Shift + Колесико мыши)")
            if hasattr(self, "lbl_master_pause"):
                self.lbl_master_pause.setText("Мастер-пауза: <b>F8</b>")
            if hasattr(self, "info_title"):
                self.info_title.setText("💡 <b>Справка:</b> Голос ИИ идет в Playback 3/4 ➔ направлен в Loopback 1+2 (микрофон игры). Наушники: Playback 1/2 (0 ms).")
            # Models Tab (Tab 2)
            if hasattr(self, "ram_grp"):
                self.ram_grp.setTitle("📊 Инвентарь нейросетей и потребление памяти")
            if hasattr(self, "lbl_ram_telemetry"):
                self.lbl_ram_telemetry.setText("ОЗУ всех моделей: ~535 MB | Видеопамять (VRAM): 0 MB (Strict CPU) | Пул инференса: 4T (Zen 4)")
            if hasattr(self, "stt_box"):
                self.stt_box.setTitle("🎙 1. Распознавание речи (STT / ASR)")
            if hasattr(self, "mt_box"):
                self.mt_box.setTitle("🌐 2. Нейроперевод (MT)")
            if hasattr(self, "tts_box"):
                self.tts_box.setTitle("🗣 3. Синтез и клонирование голоса (TTS)")
            if hasattr(self, "lbl_voice_models"):
                self.lbl_voice_models.setText("Выбор тембра голоса:")
            if hasattr(self, "btn_clone_in_studio"):
                self.btn_clone_in_studio.setText("🎙 Обучить / Записать новый голос (7 сек)")
            if hasattr(self, "lbl_speed_title"):
                self.lbl_speed_title.setText("Скорость речи (SOLA):")
            if hasattr(self, "grp_dl"):
                self.grp_dl.setTitle("📥 Менеджер загрузки моделей / 模型下载器 (Zero-Fake Downloader)")
            if hasattr(self, "btn_download_models"):
                self.btn_download_models.setText("📥 一键下载所需模型 / Скачать недостающие модели")

        self._refresh_models_tab()

    def _refresh_models_tab(self):
        """Audit disk files and memory presence for active pipeline."""
        if not hasattr(self, "lbl_stt_title"):
            return
        pipe = getattr(self.mm, "pipeline", "ru_en")
        is_zh = (pipe == "zh_en")
        if is_zh:
            stt_key = "sensevoice_zh"
            mt_key = "opus_mt_zh_en"
            self.lbl_stt_title.setText("<b>SenseVoiceSmall Chinese ASR (INT8)</b>")
            self.lbl_stt_engine.setText("推理引擎: Sherpa-ONNX INT8 | 2T (Zen 4)")
            self.lbl_mt_title.setText("<b>Helsinki Opus-MT ZH ➔ EN (INT8)</b>")
            self.lbl_mt_engine.setText("推理引擎: CTranslate2 INT8 | 2T (Zen 4)")
        else:
            stt_key = "giga_am_ru"
            mt_key = "opus_mt_ru_en"
            self.lbl_stt_title.setText("<b>Sber GigaAM v3 Conformer CTC</b>")
            self.lbl_stt_engine.setText("Движок: Sherpa-ONNX INT8 | 2T (Zen 4)")
            self.lbl_mt_title.setText("<b>Helsinki Opus-MT RU ➔ EN</b>")
            self.lbl_mt_engine.setText("Движок: CTranslate2 INT8 | 2T (Zen 4)")

        # Audit STT
        stt_stat = check_spec_status(stt_key)
        prefix_disk = "磁盘占用" if is_zh else "Размер на диске"
        self.lbl_stt_disk.setText(f"{prefix_disk}: <b>{stt_stat['size_mb']} МБ</b>")
        if self.mm._stt_status == "ready":
            self.lbl_stt_state.setText("🟢 内存已就绪 (可直接使用)" if is_zh else "🟢 Активна в ОЗУ (Готова к работе)")
            self.lbl_stt_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        elif stt_stat["is_ready"]:
            self.lbl_stt_state.setText("💾 磁盘就绪 (未加载到内存)" if is_zh else "💾 На диске (ОК, не в ОЗУ)")
            self.lbl_stt_state.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_stt_state.setText("❌ 未下载 (缺少模型文件)" if is_zh else "❌ Не скачано (Файлы отсутствуют)")
            self.lbl_stt_state.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")

        # Audit MT
        mt_stat = check_spec_status(mt_key)
        self.lbl_mt_disk.setText(f"{prefix_disk}: <b>{mt_stat['size_mb']} МБ</b>")
        if self.mm._mt_status == "ready":
            self.lbl_mt_state.setText("🟢 内存已就绪 (可直接使用)" if is_zh else "🟢 Активна в ОЗУ (Готова к работе)")
            self.lbl_mt_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        elif getattr(self.mm, "_mt_status", "") == "error":
            err = getattr(self.mm, "_mt_error", "") or ("加载失败" if is_zh else "Ошибка загрузки")
            prefix_err = "❌ 内存错误" if is_zh else "❌ Ошибка ОЗУ"
            self.lbl_mt_state.setText(f"{prefix_err}: {err[:35]}...")
            self.lbl_mt_state.setToolTip(err)
            self.lbl_mt_state.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
        elif mt_stat["is_ready"]:
            self.lbl_mt_state.setText("💾 磁盘就绪 (未加载到内存)" if is_zh else "💾 На диске (ОК, не в ОЗУ)")
            self.lbl_mt_state.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_mt_state.setText("❌ 未下载 (缺少模型文件)" if is_zh else "❌ Не скачано (Файлы отсутствуют)")
            self.lbl_mt_state.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")

        # Audit TTS
        tts_stat = check_spec_status("pocket_tts_en")
        prefix_tts_disk = "磁盘" if is_zh else "Диск"
        self.lbl_tts_disk.setText(f"{prefix_tts_disk}: <b>{tts_stat['size_mb']} МБ</b>")
        if self.mm._tts_status == "ready":
            self.lbl_tts_state.setText("🟢 内存已就绪 (~320 МБ)" if is_zh else "🟢 Активна в ОЗУ (~320 МБ)")
            self.lbl_tts_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        elif tts_stat["is_ready"]:
            self.lbl_tts_state.setText("💾 磁盘就绪 (未加载到内存)" if is_zh else "💾 На диске (ОК, не в ОЗУ)")
            self.lbl_tts_state.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_tts_state.setText("❌ 未下载" if is_zh else "❌ Не скачано")
            self.lbl_tts_state.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")

    def _on_start_download_models(self):
        """Launch background async download worker with China mirror support."""
        if hasattr(self, "_dl_worker") and self._dl_worker and self._dl_worker.isRunning():
            return
        self.btn_download_models.setEnabled(False)
        self.btn_download_models.setText("⏳ Идет загрузка... (Downloading)")
        self.download_progress.setValue(0)
        self.lbl_download_status.setText("Подключение к серверам моделей...")
        self.lbl_download_status.setStyleSheet("color: #38bdf8; font-size: 11px; font-family: Consolas, monospace;")

        self._dl_worker = ModelDownloadWorker(
            pipeline=self.mm.pipeline,
            china_mirror=self.chk_china_mirror.isChecked(),
            parent=self,
        )
        self._dl_worker.sig_progress.connect(self._on_dl_progress)
        self._dl_worker.sig_file_completed.connect(self._on_dl_file_completed)
        self._dl_worker.sig_all_completed.connect(self._on_dl_all_completed)
        self._dl_worker.sig_error.connect(self._on_dl_error)
        self._dl_worker.start()

    def _on_dl_progress(self, filename: str, down: int, total: int, speed_mbps: float):
        pct = int((down / max(total, 1)) * 100)
        self.download_progress.setValue(pct)
        down_mb = down / (1024.0 * 1024.0)
        tot_mb = total / (1024.0 * 1024.0)
        self.lbl_download_status.setText(
            f"Загрузка: {filename} [{down_mb:.1f} MB / {tot_mb:.1f} MB] ({pct}%) | Скорость: {speed_mbps:.2f} MB/s"
        )

    def _on_dl_file_completed(self, filename: str):
        log.info("File completed: %s", filename)
        self._refresh_models_tab()

    def _on_dl_all_completed(self):
        self.download_progress.setValue(100)
        self.lbl_download_status.setText("✅ Все модели успешно скачаны и верифицированы! Загружаем в ОЗУ...")
        self.lbl_download_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")
        self.btn_download_models.setEnabled(True)
        self.btn_download_models.setText("📥 一键下载所需模型 / Скачать недостающие модели")
        self._on_reload_models()

    def _on_dl_error(self, item: str, err: str):
        self.lbl_download_status.setText(f"❌ Ошибка загрузки {item}: {err}")
        self.lbl_download_status.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")
        self.btn_download_models.setEnabled(True)
        self.btn_download_models.setText("📥 Повторить загрузку / 重试下载")

    def _on_reload_models(self):
        """Asynchronously load downloaded models into RAM without freezing the GUI."""
        if hasattr(self, "_load_worker") and self._load_worker and self._load_worker.isRunning():
            return
        if hasattr(self, "btn_reload_models"):
            self.btn_reload_models.setEnabled(False)
        self.btn_download_models.setEnabled(False)
        self.lbl_download_status.setText("⏳ Подготовка к загрузке нейросетей в память (RAM)...")
        self.lbl_download_status.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")

        self._load_worker = ModelLoaderWorker(self.mm, parent=self)
        self._load_worker.sig_status.connect(self._on_model_load_status)
        self._load_worker.sig_finished.connect(self._on_model_load_finished)
        self._load_worker.start()

    def _on_model_load_status(self, text: str, color: str):
        self.lbl_download_status.setText(text)
        self.lbl_download_status.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")

    def _on_model_load_finished(self, success: bool):
        if hasattr(self, "btn_reload_models"):
            self.btn_reload_models.setEnabled(True)
        self.btn_download_models.setEnabled(True)
        if success:
            self.lbl_download_status.setText("🟢 Все модели успешно загружены в ОЗУ и готовы к инференсу!")
            self.lbl_download_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")
        else:
            errs = []
            if getattr(self.mm, "_stt_status", "") == "error":
                errs.append(f"STT: {self.mm._stt_error}")
            if getattr(self.mm, "_mt_status", "") == "error":
                errs.append(f"MT: {self.mm._mt_error}")
            if getattr(self.mm, "_tts_status", "") == "error":
                errs.append(f"TTS: {self.mm._tts_error}")
            err_msg = " | ".join(errs) if errs else "Некоторые модели не удалось загрузить. Проверьте файлы на диске."
            self.lbl_download_status.setText(f"⚠️ {err_msg[:80]}")
            self.lbl_download_status.setToolTip(err_msg)
            self.lbl_download_status.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold; font-family: Consolas, monospace;")
        self._refresh_models_tab()
