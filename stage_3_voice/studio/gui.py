"""Lightweight, High-Performance Control Panel for Stage 3 Voice Translation Studio.
Features an interactive visual signal chain monitor, millisecond latency breakdown,
Topping E2x2 matrix routing, and 30 FPS decoupled VU meters for zero game lag.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QLinearGradient
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
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .audio_engine import AudioEngine
from .config import load_settings, save_settings
from .model_manager import ModelManager

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
        self.resize(self.cfg.get("ui", {}).get("window_width", 840),
                    self.cfg.get("ui", {}).get("window_height", 640))
        self.setMinimumSize(780, 580)

        self._apply_dark_style()
        self._init_ui()

        # Connect audio transcript callback to GUI
        self.engine.on_transcript_callback = self._on_new_transcript

        # Decoupled 30 FPS Telemetry Polling Timer (33 ms)
        # Prevents any UI stutter or Qt signal spam in high-FPS games like CS2
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)
        self.ui_timer.timeout.connect(self._update_telemetry)
        self.ui_timer.start()

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
        tabs.addTab(self._create_routing_tab(), "🎛 Монитор и Topping E2x2")
        tabs.addTab(self._create_models_tab(), "🧠 Модели и Управление памятью")
        tabs.addTab(self._create_transcript_tab(), "📜 Живой журнал перевода")
        root_layout.addWidget(tabs, stretch=1)

    def _create_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(12)

        # Master Toggle Button
        self.btn_master = QPushButton("🟢 СИСТЕМА АКТИВНА (F9)")
        self.btn_master.setFixedHeight(42)
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
        self.ptt_banner.setFixedHeight(42)
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

        return h

    def _create_signal_chain_monitor(self) -> QGroupBox:
        grp = QGroupBox("Интерактивная цепочка звука (Audio Signal Chain & Real-Time Monitors)")
        grp.setStyleSheet("QGroupBox { font-weight: bold; color: #e5e7eb; }")
        layout = QHBoxLayout(grp)
        layout.setContentsMargins(10, 14, 10, 10)
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Device Selection Grid
        grp_devs = QGroupBox("Аудиоустройства и интеграция с Topping E2x2 OTG")
        grid = QGridLayout(grp_devs)
        grid.setSpacing(10)

        # Query devices
        inputs, outputs = AudioEngine.get_devices()

        # 1. Microphone Input
        grid.addWidget(QLabel("Входной микрофон (речь для перевода):"), 0, 0)
        self.combo_in = QComboBox()
        for idx, name in inputs:
            self.combo_in.addItem(f"[{idx}] {name}", name)
        # Select matching
        cur_in = self.cfg.get("audio", {}).get("input_device", "NVIDIA Broadcast")
        for i in range(self.combo_in.count()):
            if cur_in.lower() in self.combo_in.itemText(i).lower():
                self.combo_in.setCurrentIndex(i)
                break
        grid.addWidget(self.combo_in, 0, 1)

        # 2. Game Outgoing (Playback 3/4)
        grid.addWidget(QLabel("Вывод перевода в игру (Topping Loopback):"), 1, 0)
        self.combo_out = QComboBox()
        for idx, name in outputs:
            self.combo_out.addItem(f"[{idx}] {name}", name)
        cur_out = self.cfg.get("audio", {}).get("output_device", "Playback 3/4")
        for i in range(self.combo_out.count()):
            if cur_out.lower() in self.combo_out.itemText(i).lower():
                self.combo_out.setCurrentIndex(i)
                break
        grid.addWidget(self.combo_out, 1, 1)

        # 3. Headphones Sidetone (Playback 1/2)
        grid.addWidget(QLabel("Наушники (Самопрослушивание своего перевода):"), 2, 0)
        self.combo_side = QComboBox()
        for idx, name in outputs:
            self.combo_side.addItem(f"[{idx}] {name}", name)
        cur_side = self.cfg.get("audio", {}).get("sidetone_device", "Playback 1/2")
        for i in range(self.combo_side.count()):
            if cur_side.lower() in self.combo_side.itemText(i).lower():
                self.combo_side.setCurrentIndex(i)
                break
        grid.addWidget(self.combo_side, 2, 1)

        layout.addWidget(grp_devs)

        # Switches and Sliders
        grp_opts = QGroupBox("Режимы микрофона и громкость мониторинга")
        v_opts = QVBoxLayout(grp_opts)

        # Passthrough
        self.chk_passthrough = QCheckBox("Пропускать живой голос в игру, когда PTT не нажат (Passthrough)")
        self.chk_passthrough.setChecked(self.cfg.get("audio", {}).get("passthrough_enabled", True))
        self.chk_passthrough.toggled.connect(self._on_passthrough_toggle)
        v_opts.addWidget(self.chk_passthrough)

        # Sidetone
        self.chk_sidetone = QCheckBox("Слышать свой английский перевод в наушниках (Sidetone)")
        self.chk_sidetone.setChecked(self.cfg.get("audio", {}).get("sidetone_enabled", True))
        self.chk_sidetone.toggled.connect(self._on_sidetone_toggle)
        v_opts.addWidget(self.chk_sidetone)

        # Sidetone Volume Slider
        h_vol = QHBoxLayout()
        h_vol.addWidget(QLabel("Громкость перевода в наушниках:"))
        self.slider_sidetone = QSlider(Qt.Orientation.Horizontal)
        self.slider_sidetone.setRange(0, 100)
        cur_vol = int(self.cfg.get("audio", {}).get("sidetone_volume", 0.70) * 100)
        self.slider_sidetone.setValue(cur_vol)
        self.lbl_sidetone_val = QLabel(f"{cur_vol}%")
        self.slider_sidetone.valueChanged.connect(self._on_sidetone_slider)
        h_vol.addWidget(self.slider_sidetone)
        h_vol.addWidget(self.lbl_sidetone_val)
        v_opts.addLayout(h_vol)

        layout.addWidget(grp_opts)

        # Educational Topping Diagram Box
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #172554;
                border: 1px solid #1e40af;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        v_info = QVBoxLayout(info_frame)
        info_title = QLabel("💡 <b>Как Topping E2x2 OTG передает переведенный голос в CS2 и Discord без задержек:</b>")
        info_title.setStyleSheet("color: #bfdbfe; font-size: 12px;")
        v_info.addWidget(info_title)

        info_body = QLabel(
            "1. Студия транслирует клонированный английский голос в канал <b>Playback 3/4</b>.<br>"
            "2. В микшере Topping этот канал аппаратно направлен в <b>Loopback 1+2</b>.<br>"
            "3. В настройках звука игры (CS2 / Discord) выбран микрофон <b>«Loopback 1/2»</b>.<br>"
            "4. Вы слышите чистый звук игры и свой перевод в наушниках (<b>Playback 1/2</b>) без искажений."
        )
        info_body.setStyleSheet("color: #93c5fd; font-size: 11px;")
        v_info.addWidget(info_body)
        layout.addWidget(info_frame)

        layout.addStretch()
        return w

    # =========================================================================
    # Tab 2: Models & RAM Management
    # =========================================================================
    def _create_models_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Master RAM & Load/Unload Bar
        ram_grp = QGroupBox("Управление моделями в оперативной памяти (RAM)")
        h_ram = QHBoxLayout(ram_grp)

        self.btn_load_all = QPushButton("📥 Загрузить ВСЕ модели в ОЗУ")
        self.btn_load_all.setStyleSheet("background-color: #2563eb; color: #fff; font-weight: bold; padding: 8px 14px; border-radius: 5px;")
        self.btn_load_all.clicked.connect(self._on_load_all_models)
        h_ram.addWidget(self.btn_load_all)

        self.btn_unload_all = QPushButton("🗑 Выгрузить ВСЕ (Освободить RAM)")
        self.btn_unload_all.setStyleSheet("background-color: #b91c1c; color: #fff; font-weight: bold; padding: 8px 14px; border-radius: 5px;")
        self.btn_unload_all.clicked.connect(self._on_unload_all_models)
        h_ram.addWidget(self.btn_unload_all)

        h_ram.addStretch()

        self.lbl_ram_telemetry = QLabel("RAM процесса: 0 MB | VRAM: 0 MB (Strict CPU)")
        self.lbl_ram_telemetry.setStyleSheet("font-family: Consolas, monospace; font-weight: bold; color: #38bdf8; font-size: 13px;")
        h_ram.addWidget(self.lbl_ram_telemetry)

        layout.addWidget(ram_grp)

        # Individual Models Grid
        models_grid = QGridLayout()
        models_grid.setSpacing(10)

        # STT Card
        stt_box = QGroupBox("1. Распознавание речи (STT / ASR)")
        v_stt = QVBoxLayout(stt_box)
        v_stt.addWidget(QLabel("<b>Sber GigaAM v3 Conformer CTC</b>"))
        v_stt.addWidget(QLabel("Движок: Sherpa-ONNX INT8 | Потоков: 2 (Zen 4)"))
        self.lbl_stt_state = QLabel("Статус: Загружен (~140 MB)")
        self.lbl_stt_state.setStyleSheet("color: #10b981; font-weight: bold;")
        v_stt.addWidget(self.lbl_stt_state)
        h_stt_btn = QHBoxLayout()
        btn_stt_load = QPushButton("Загрузить")
        btn_stt_load.clicked.connect(lambda: self.mm.load_stt())
        btn_stt_unload = QPushButton("Выгрузить")
        btn_stt_unload.clicked.connect(lambda: self.mm.unload_stt())
        h_stt_btn.addWidget(btn_stt_load)
        h_stt_btn.addWidget(btn_stt_unload)
        v_stt.addLayout(h_stt_btn)
        models_grid.addWidget(stt_box, 0, 0)

        # MT Card
        mt_box = QGroupBox("2. Машинный перевод (MT)")
        v_mt = QVBoxLayout(mt_box)
        v_mt.addWidget(QLabel("<b>Helsinki Opus-MT RU ➔ EN</b>"))
        v_mt.addWidget(QLabel("Движок: CTranslate2 INT8 | Потоков: 2"))
        self.lbl_mt_state = QLabel("Статус: Загружен (~75 MB)")
        self.lbl_mt_state.setStyleSheet("color: #10b981; font-weight: bold;")
        v_mt.addWidget(self.lbl_mt_state)
        h_mt_btn = QHBoxLayout()
        btn_mt_load = QPushButton("Загрузить")
        btn_mt_load.clicked.connect(lambda: self.mm.load_mt())
        btn_mt_unload = QPushButton("Выгрузить")
        btn_mt_unload.clicked.connect(lambda: self.mm.unload_mt())
        h_mt_btn.addWidget(btn_mt_load)
        h_mt_btn.addWidget(btn_mt_unload)
        v_mt.addLayout(h_mt_btn)
        models_grid.addWidget(mt_box, 0, 1)

        # TTS Card
        tts_box = QGroupBox("3. Синтез и клонирование голоса (TTS)")
        v_tts = QVBoxLayout(tts_box)
        v_tts.addWidget(QLabel("<b>Kyutai Pocket-TTS (Mimi Codec)</b>"))
        self.combo_voices = QComboBox()
        self.combo_voices.addItem("⭐ Мой клонированный голос (my_pocket_voice)", "my_pocket_voice")
        self.combo_voices.addItem("Juergen (Мужской, уверенный)", "juergen")
        self.combo_voices.addItem("Marius (Мужской, спокойный)", "marius")
        self.combo_voices.addItem("Alba (Женский)", "alba")
        self.combo_voices.addItem("Fantine (Женский)", "fantine")
        self.combo_voices.currentIndexChanged.connect(self._on_voice_changed)
        v_tts.addWidget(self.combo_voices)

        self.lbl_tts_state = QLabel("Статус: Загружен (~320 MB)")
        self.lbl_tts_state.setStyleSheet("color: #10b981; font-weight: bold;")
        v_tts.addWidget(self.lbl_tts_state)

        h_tts_btn = QHBoxLayout()
        btn_tts_load = QPushButton("Загрузить")
        btn_tts_load.clicked.connect(lambda: self.mm.load_tts(self.combo_voices.currentData()))
        btn_tts_unload = QPushButton("Выгрузить")
        btn_tts_unload.clicked.connect(lambda: self.mm.unload_tts())
        h_tts_btn.addWidget(btn_tts_load)
        h_tts_btn.addWidget(btn_tts_unload)
        v_tts.addLayout(h_tts_btn)
        models_grid.addWidget(tts_box, 1, 0, 1, 2)

        layout.addLayout(models_grid)
        layout.addStretch()
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

        # 2. PTT Banner State
        state = self.engine.engine_state
        if not self.engine._master_enabled:
            self.ptt_banner.setText("⏸ СИСТЕМА НА ПАУЗЕ (Нажмите F9 для включения)")
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
            self.btn_master.setText("🟢 СИСТЕМА АКТИВНА (F9)")
            self.btn_master.setStyleSheet("background-color: #059669; color: #fff; font-weight: bold; border-radius: 6px;")
        else:
            self.btn_master.setText("⏸ ПАУЗА (F9)")
            self.btn_master.setStyleSheet("background-color: #4b5563; color: #fff; font-weight: bold; border-radius: 6px;")

    def _on_passthrough_toggle(self, checked: bool):
        self.cfg["audio"]["passthrough_enabled"] = checked
        save_settings(self.cfg)

    def _on_sidetone_toggle(self, checked: bool):
        self.cfg["audio"]["sidetone_enabled"] = checked
        save_settings(self.cfg)

    def _on_sidetone_slider(self, val: int):
        self.lbl_sidetone_val.setText(f"{val}%")
        self.cfg["audio"]["sidetone_volume"] = val / 100.0
        save_settings(self.cfg)

    def _on_voice_changed(self, idx: int):
        voice_key = self.combo_voices.currentData()
        self.cfg["models"]["tts_voice"] = voice_key
        self.mm.set_voice(voice_key)
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
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
