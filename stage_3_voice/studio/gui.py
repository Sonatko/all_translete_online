"""Lightweight, High-Performance Control Panel for Stage 3 Voice Translation Studio.
Features an interactive visual signal chain monitor, millisecond latency breakdown,
Topping E2x2 matrix routing, and 30 FPS decoupled VU meters for zero game lag.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer, QEvent, QRectF
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap, QLinearGradient
from PySide6.QtWidgets import (
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


class StudioWindow(QMainWindow):
    """Main Control Panel Window."""

    def __init__(self, engine: AudioEngine, model_mgr: ModelManager):
        super().__init__()
        self.engine = engine
        self.mm = model_mgr
        self.cfg = engine.config

        self.setWindowTitle("Stage 3: Voice Translation Studio (S2ST) — CS2 & Discord")
        self.resize(self.cfg.get("ui", {}).get("window_width", 880),
                    self.cfg.get("ui", {}).get("window_height", 640))
        self.setMinimumSize(820, 560)

        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_hint_shown = False
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
        tabs = QTabWidget()
        tabs.addTab(self._create_routing_tab(), "🎛 Настройка звука и устройств")
        tabs.addTab(self._create_models_tab(), "🧠 Модели и Управление памятью")
        tabs.addTab(self._create_transcript_tab(), "📜 Живой журнал перевода")
        root_layout.addWidget(tabs, stretch=1)

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
        grp = QGroupBox("Интерактивная цепочка звука (Audio Signal Chain & Real-Time Monitors)")
        grp.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; }")
        layout = QHBoxLayout(grp)
        layout.setContentsMargins(8, 6, 8, 6)
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

        # Node 2: STT (GigaAM)
        self.node_stt = ChainNode("2", "STT (ASR)", "Sber GigaAM v3 CTC")
        layout.addWidget(self.node_stt, stretch=1)

        arrow2 = QLabel("➔")
        arrow2.setStyleSheet("color: #4b5563; font-size: 18px; font-weight: bold;")
        arrow2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow2)

        # Node 3: MT (Opus-MT)
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

        return grp

    # =========================================================================
    # Tab 1: Routing & Topping E2x2
    # =========================================================================
    def _create_routing_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 1-Click Hardware Profiles Selector Banner
        grp_profiles = QGroupBox("Быстрый выбор режима звука в 1 клик")
        grp_profiles.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_prof = QHBoxLayout(grp_profiles)
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

        layout.addWidget(grp_profiles)

        # Device Selection Grid (Ultra-compact)
        grp_devs = QGroupBox("Аудиоустройства")
        grp_devs.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 8px; }")
        grid = QGridLayout(grp_devs)
        grid.setContentsMargins(6, 4, 6, 6)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        inputs, outputs = AudioEngine.get_devices()

        # 1. Mic
        lbl_in = QLabel("1. Микрофон:")
        lbl_in.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(lbl_in, 0, 0)
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
        lbl_out = QLabel("2. Канал перевода:")
        lbl_out.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(lbl_out, 1, 0)
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
        lbl_side = QLabel("3. Наушники:")
        lbl_side.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 11px;")
        grid.addWidget(lbl_side, 2, 0)
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

        layout.addWidget(grp_devs)

        # Compact Controls Panel: Options & Volume in ONE horizontal row
        grp_opts = QGroupBox("Режимы микрофона и самопрослушивание")
        grp_opts.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_opts = QHBoxLayout(grp_opts)
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
        lbl_v = QLabel("Громкость:")
        lbl_v.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_opts.addWidget(lbl_v)
        self.slider_sidetone = QSlider(Qt.Orientation.Horizontal)
        self.slider_sidetone.setRange(0, 100)
        cur_vol = int(self.cfg.get("audio", {}).get("sidetone_volume", 0.70) * 100)
        self.slider_sidetone.setValue(cur_vol)
        self.lbl_sidetone_val = QLabel(f"{cur_vol}%")
        self.lbl_sidetone_val.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: Consolas, monospace;")
        self.slider_sidetone.valueChanged.connect(self._on_sidetone_slider)
        h_opts.addWidget(self.slider_sidetone)
        h_opts.addWidget(self.lbl_sidetone_val)

        layout.addWidget(grp_opts)

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
        return w

    # =========================================================================
    # Tab 2: Models & RAM Management
    # =========================================================================
    def _create_models_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Telemetry Summary Bar
        ram_grp = QGroupBox("📊 Инвентарь нейросетей и потребление памяти")
        ram_grp.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        h_ram = QHBoxLayout(ram_grp)
        h_ram.setContentsMargins(8, 6, 8, 6)

        self.lbl_ram_telemetry = QLabel("ОЗУ всех моделей: ~535 MB | Видеопамять (VRAM): 0 MB (Strict CPU) | Пул инференса: 4T (Zen 4)")
        self.lbl_ram_telemetry.setStyleSheet("font-family: Consolas, monospace; font-weight: bold; color: #38bdf8; font-size: 12px;")
        h_ram.addWidget(self.lbl_ram_telemetry)
        h_ram.addStretch()
        layout.addWidget(ram_grp)

        # 3 Clean Informational Cards (No broken load/unload buttons)
        models_grid = QGridLayout()
        models_grid.setContentsMargins(0, 0, 0, 0)
        models_grid.setSpacing(8)

        # Card 1: STT
        stt_box = QGroupBox("🎙 1. Распознавание речи (STT / ASR)")
        stt_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_stt = QVBoxLayout(stt_box)
        v_stt.setContentsMargins(8, 6, 8, 8)
        v_stt.setSpacing(3)
        v_stt.addWidget(QLabel("<b>Sber GigaAM v3 Conformer CTC</b>"))
        v_stt.addWidget(QLabel("Движок: Sherpa-ONNX INT8 | 2T (Zen 4)"))
        lbl_stt_mem = QLabel("Потребление: <b>~140 МБ ОЗУ</b> | Скорость: <b>~170 мс</b>")
        lbl_stt_mem.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_stt.addWidget(lbl_stt_mem)
        self.lbl_stt_state = QLabel("🟢 Активна в ОЗУ (Готова к инференсу)")
        self.lbl_stt_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        v_stt.addWidget(self.lbl_stt_state)
        models_grid.addWidget(stt_box, 0, 0)

        # Card 2: MT
        mt_box = QGroupBox("🌐 2. Нейроперевод (MT)")
        mt_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_mt = QVBoxLayout(mt_box)
        v_mt.setContentsMargins(8, 6, 8, 8)
        v_mt.setSpacing(3)
        v_mt.addWidget(QLabel("<b>Helsinki Opus-MT RU ➔ EN</b>"))
        v_mt.addWidget(QLabel("Движок: CTranslate2 INT8 | 2T (Zen 4)"))
        lbl_mt_mem = QLabel("Потребление: <b>~75 МБ ОЗУ</b> | Скорость: <b>~15 мс</b>")
        lbl_mt_mem.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_mt.addWidget(lbl_mt_mem)
        self.lbl_mt_state = QLabel("🟢 Активна в ОЗУ (Готова к переводу)")
        self.lbl_mt_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        v_mt.addWidget(self.lbl_mt_state)
        models_grid.addWidget(mt_box, 0, 1)

        # Card 3: TTS & Voice Selector
        tts_box = QGroupBox("🗣 3. Синтез и клонирование голоса (TTS)")
        tts_box.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; padding-top: 10px; }")
        v_tts = QVBoxLayout(tts_box)
        v_tts.setContentsMargins(8, 6, 8, 8)
        v_tts.setSpacing(4)
        
        h_tts_top = QHBoxLayout()
        h_tts_top.addWidget(QLabel("<b>Kyutai Pocket-TTS 24kHz (Mimi Codec)</b>"))
        h_tts_top.addStretch()
        self.lbl_tts_state = QLabel("🟢 Активна в ОЗУ (~320 МБ)")
        self.lbl_tts_state.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        h_tts_top.addWidget(self.lbl_tts_state)
        v_tts.addLayout(h_tts_top)

        h_voice = QHBoxLayout()
        lbl_v_sel = QLabel("Выбор тембра голоса:")
        lbl_v_sel.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        h_voice.addWidget(lbl_v_sel)
        self.combo_voices = NoWheelComboBox()
        self.combo_voices.setFixedHeight(28)
        self.combo_voices.addItem("⭐ Мой клонированный голос (my_pocket_voice)", "my_pocket_voice")
        self.combo_voices.addItem("Juergen (Мужской, уверенный)", "juergen")
        self.combo_voices.addItem("Marius (Мужской, спокойный)", "marius")
        self.combo_voices.addItem("Alba (Женский)", "alba")
        self.combo_voices.addItem("Fantine (Женский)", "fantine")
        self.combo_voices.currentIndexChanged.connect(self._on_voice_changed)
        h_voice.addWidget(self.combo_voices, stretch=1)
        v_tts.addLayout(h_voice)

        # Speed / Natural Pacing Slider (SOLA Time-Domain, zero robotic artifacts)
        h_speed = QHBoxLayout()
        lbl_speed = QLabel("Скорость речи (SOLA):")
        lbl_speed.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 11px;")
        h_speed.addWidget(lbl_speed)

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

        models_grid.addWidget(tts_box, 1, 0, 1, 2)
        layout.addLayout(models_grid)

        return w

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
        if state != self._last_rendered_state or master_enabled != self._last_rendered_master:
            self._last_rendered_state = state
            self._last_rendered_master = master_enabled

            if not master_enabled:
                self.ptt_banner.setText("⏸ СИСТЕМА НА ПАУЗЕ (Нажмите F8 для включения)")
                self.ptt_banner.setStyleSheet("background-color: #374151; color: #9ca3af; font-weight: bold; border-radius: 6px;")
            elif state == "RECORDING":
                self.ptt_banner.setText("🔴 ИДЕТ ЗАПИСЬ РЕЧИ (Shift + MMB нажат)...")
                self.ptt_banner.setStyleSheet("background-color: #991b1b; color: #ffffff; font-weight: bold; border-radius: 6px;")
            elif state == "PROCESSING":
                self.ptt_banner.setText("⚡ ПЕРЕВОД И ГЕНЕРАЦИЯ ГОЛОСА...")
                self.ptt_banner.setStyleSheet("background-color: #854d0e; color: #fef08a; font-weight: bold; border-radius: 6px;")
            elif state == "SPEAKING":
                self.ptt_banner.setText("🔊 ОЗВУЧИВАНИЕ В ИГРУ (Playback 3/4 ➔ Loopback 1+2)")
                self.ptt_banner.setStyleSheet("background-color: #065f46; color: #a7f3d0; font-weight: bold; border-radius: 6px;")
            else:
                self.ptt_banner.setText("🎙 Нажмите Shift + Колесико мыши (MMB) для записи речи")
                self.ptt_banner.setStyleSheet("background-color: #1f2937; color: #9ca3af; font-weight: bold; border: 1px solid #374151; border-radius: 6px;")

        # 3. Chain Nodes Status & Latency Badges
        stt_status = self.mm._stt_status
        mt_status = self.mm._mt_status
        tts_status = self.mm._tts_status

        self.node_stt.set_telemetry(
            "В ОЗУ" if stt_status == "ready" else stt_status.upper(),
            self.engine.last_stt_ms,
            is_active=(state == "PROCESSING")
        )
        self.node_mt.set_telemetry(
            "В ОЗУ" if mt_status == "ready" else mt_status.upper(),
            self.engine.last_mt_ms,
            is_active=(state == "PROCESSING")
        )
        self.node_tts.set_telemetry(
            "В ОЗУ" if tts_status == "ready" else tts_status.upper(),
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

    def _on_sidetone_toggle(self, checked: bool):
        self.cfg["audio"]["sidetone_enabled"] = checked
        save_settings(self.cfg)

    def _on_sidetone_slider(self, val: int):
        self.lbl_sidetone_val.setText(f"{val}%")
        self.cfg["audio"]["sidetone_volume"] = val / 100.0

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

    def _on_voice_changed(self, idx: int):
        voice_key = self.combo_voices.currentData()
        self.cfg["models"]["tts_voice"] = voice_key
        self.mm.set_voice(voice_key)
        save_settings(self.cfg)

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

