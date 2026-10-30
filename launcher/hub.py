"""Universal Real-Time Translation Hub & Ecosystem Orchestrator (PySide6).
Supports Trilingual UI (Russian, English, Chinese), 3-Stage Process Supervision,
Dynamic Pipeline Latency Monitoring with Individual Step Chips, Modular 5-Patch Integrity Auditor,
and Embedded Stage 3 Hardware Audio Routing.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from launcher.i18n import I18n
    from launcher.patch_checker import PatchIntegrityChecker
    from launcher.process_manager import EcosystemProcessManager
except ImportError:
    from i18n import I18n
    from patch_checker import PatchIntegrityChecker
    from process_manager import EcosystemProcessManager

log = logging.getLogger("Launcher.Hub")


class LatencyEstimator:
    """Dynamic, architecture-accurate latency analyzer for all 3 pipeline flows."""

    @staticmethod
    def get_stage1_latency() -> Dict[str, Any]:
        """Inspect LiveTranslate user_settings.json for VAD, ASR, and MT configuration."""
        settings_file = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "user_settings.json"
        vad_name = "Silero VAD (CPU)"
        vad_ms = 5
        asr_name = "SenseVoice INT8 (CPU)"
        asr_ms = 170
        mt_name = "Hunyuan MT 1.8B (CPU)"
        mt_ms = 80
        is_cloud = False

        if settings_file.is_file():
            try:
                cfg = json.loads(settings_file.read_text(encoding="utf-8"))
                vad_m = cfg.get("vad_mode", "silero")
                vad_name = f"{vad_m.capitalize()} VAD (CPU)"

                asr_eng = cfg.get("asr_engine", "sherpa_onnx")
                if "whisper" in asr_eng:
                    asr_name = "Whisper Local (CPU)"
                    asr_ms = 900
                elif "remote" in asr_eng:
                    asr_name = "Whisper Cloud (Облако)"
                    asr_ms = 450
                    is_cloud = True
                else:
                    asr_name = "SenseVoice INT8 (CPU)"
                    asr_ms = 170

                models = cfg.get("models", [])
                active_idx = cfg.get("active_model", 1)
                if active_idx < len(models):
                    active_m = models[active_idx]
                    api_base = active_m.get("api_base", "local")
                    m_model = active_m.get("model", "")
                    if api_base == "local":
                        if "nllb" in m_model:
                            mt_name = "NLLB-200 (CPU)"
                            mt_ms = 50
                        else:
                            mt_name = "Hunyuan MT 1.8B (CPU)"
                            mt_ms = 80
                    else:
                        clean_name = active_m.get("name", "Cloud API").split()[0]
                        mt_name = f"API {clean_name} (Облако)"
                        mt_ms = 350
                        is_cloud = True
            except Exception as e:
                log.warning("Could not parse LiveTranslate settings: %s", e)

        total_ms = vad_ms + asr_ms + mt_ms
        steps = [
            {"name": vad_name, "ms": vad_ms, "icon": "✂"},
            {"name": asr_name, "ms": asr_ms, "icon": "🎙"},
            {"name": mt_name, "ms": mt_ms, "icon": "🧠"},
        ]
        return {
            "steps": steps,
            "total_ms": total_ms,
            "is_cloud": is_cloud,
            "mode_text": I18n.t("latency_mode_cloud") if is_cloud else I18n.t("latency_mode_local"),
        }

    @staticmethod
    def get_stage2_latency() -> Dict[str, Any]:
        """Inspect OverTranslate appsettings.json for RapidOcr ONNX and translation provider."""
        settings_file = PROJECT_ROOT / "CONFIG" / "stage_2_screen" / "appsettings.json"
        ocr_name = "RapidOcr ONNX (CPU)"
        ocr_ms = 30
        mt_name = "Microsoft MT (Облако)"
        mt_ms = 150
        is_cloud = True

        if settings_file.is_file():
            try:
                cfg = json.loads(settings_file.read_text(encoding="utf-8"))
                provider = cfg.get("Provider", "Microsoft")
                if provider == "OpenAi":
                    mt_name = "Groq LPU (Облако)"
                    mt_ms = 180
                    is_cloud = True
                elif provider == "Microsoft":
                    mt_name = "Microsoft MT (Облако)"
                    mt_ms = 150
                    is_cloud = True
                elif provider == "GoogleWeb":
                    mt_name = "Google Web (Облако)"
                    mt_ms = 160
                    is_cloud = True
                else:
                    mt_name = f"API {provider} (Облако)"
                    mt_ms = 200
                    is_cloud = True
            except Exception as e:
                log.warning("Could not parse OverTranslate settings: %s", e)

        total_ms = ocr_ms + mt_ms
        steps = [
            {"name": ocr_name, "ms": ocr_ms, "icon": "🔍"},
            {"name": mt_name, "ms": mt_ms, "icon": "🌐"},
        ]
        return {
            "steps": steps,
            "total_ms": total_ms,
            "is_cloud": is_cloud,
            "mode_text": I18n.t("latency_mode_cloud") if is_cloud else I18n.t("latency_mode_local"),
        }

    @staticmethod
    def get_stage3_latency(routing_mode: str = "topping") -> Dict[str, Any]:
        """Inspect Voice Studio configuration for ASR, MT, TTS, and Audio Routing."""
        vad_ms = 10   # VAD segmentation and punctuation restoration
        asr_ms = 170  # Sber GigaAM CTC INT8
        mt_ms = 15    # Helsinki Opus-MT INT8
        tts_ms = 750  # Kyutai Pocket-TTS 24kHz

        if routing_mode == "topping":
            route_name = "Topping Loopback (Аппаратный)"
            route_ms = 0
        else:
            route_name = "VB-Cable (Драйвер)"
            route_ms = 15

        total_ms = vad_ms + asr_ms + mt_ms + tts_ms + route_ms
        steps = [
            {"name": "VAD + Пунктуация (CPU)", "ms": vad_ms, "icon": "✂"},
            {"name": "Sber GigaAM (CPU)", "ms": asr_ms, "icon": "🎙"},
            {"name": "Opus-MT (CPU)", "ms": mt_ms, "icon": "📝"},
            {"name": "Pocket-TTS клон (CPU)", "ms": tts_ms, "icon": "🗣"},
            {"name": route_name, "ms": route_ms, "icon": "🔊"},
        ]
        return {
            "steps": steps,
            "total_ms": total_ms,
            "is_cloud": False,
            "mode_text": I18n.t("latency_mode_local"),
        }


class PipelineNodeWidget(QFrame):
    """Modular sub-card representing an isolated DSP/AI pipeline stage node."""

    def __init__(self, step_idx: str, step_type: str, title: str, backend: str, parent=None):
        super().__init__(parent)
        self.step_idx = step_idx
        self.step_type = step_type
        self.title_text = title
        self.backend_text = backend

        self.setStyleSheet("""
            PipelineNodeWidget {
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
        """)
        self.setMinimumWidth(110)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # 1. Step Category / Number
        self.lbl_cat = QLabel(f"{step_idx}. {step_type}".upper())
        self.lbl_cat.setStyleSheet("color: #64748b; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_cat)

        # 2. Main Component Name
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        self.lbl_title.setWordWrap(True)
        layout.addWidget(self.lbl_title)

        # 3. Execution Target / Metric Badge
        self.lbl_backend = QLabel(backend)
        self.lbl_backend.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: Consolas, monospace;")
        self.lbl_backend.setWordWrap(True)
        layout.addWidget(self.lbl_backend)

    def update_node(self, title: str = None, backend: str = None, active: bool = False, metric: str = None):
        if title is not None:
            self.title_text = title
            self.lbl_title.setText(title)
        if backend is not None:
            self.backend_text = backend

        display_sub = self.backend_text
        if metric:
            display_sub = f"{self.backend_text} | {metric}"
        self.lbl_backend.setText(display_sub)

        if active:
            self.setStyleSheet("""
                PipelineNodeWidget {
                    background-color: #0f233a;
                    border: 1px solid #38bdf8;
                    border-radius: 6px;
                }
            """)
            self.lbl_title.setStyleSheet("color: #7dd3fc; font-size: 11px; font-weight: bold;")
            self.lbl_backend.setStyleSheet("color: #34d399; font-size: 10px; font-family: Consolas, monospace; font-weight: bold;")
        else:
            self.setStyleSheet("""
                PipelineNodeWidget {
                    background-color: #0b1120;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
            """)
            self.lbl_title.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
            self.lbl_backend.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: Consolas, monospace;")


class StageCard(QFrame):
    """Visual pipeline flow with modular node cards, hardware monitor, and process controls."""

    def __init__(
        self,
        stage_id: str,
        title_key: str,
        flow_key: str,
        desc_key: str,
        hotkeys_key: str = "",
        on_start=None,
        on_stop=None,
        on_open=None,
        open_label_key="btn_open",
        parent=None,
    ):
        super().__init__(parent)
        self.stage_id = stage_id
        self.title_key = title_key
        self.flow_key = flow_key
        self.desc_key = desc_key
        self.hotkeys_key = hotkeys_key
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_open = on_open
        self.open_label_key = open_label_key
        self._is_running = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            StageCard {
                background-color: #1a1b1e;
                border: 1px solid #2e3035;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # 1. Header Row: Title + Status Pill
        h_head = QHBoxLayout()
        self.lbl_title = QLabel(f"<b>{I18n.t(self.title_key)}</b>")
        self.lbl_title.setStyleSheet("font-size: 13px; color: #ffffff;")
        h_head.addWidget(self.lbl_title)

        h_head.addStretch()

        self.status_pill = QLabel(I18n.t("status_stopped_pill"))
        self.status_pill.setStyleSheet("""
            background-color: #212328;
            color: #9ca3af;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
            border: 1px solid #374151;
        """)
        h_head.addWidget(self.status_pill)
        layout.addLayout(h_head)

        # 2. Modular Pipeline Node Cards (Sub-cards for each DSP/AI step)
        self.nodes_frame = QFrame()
        self.nodes_frame.setStyleSheet("background: transparent; border: none;")
        self.nodes_layout = QHBoxLayout(self.nodes_frame)
        self.nodes_layout.setContentsMargins(0, 2, 0, 2)
        self.nodes_layout.setSpacing(6)
        self.nodes: List[PipelineNodeWidget] = []
        self._init_nodes()
        layout.addWidget(self.nodes_frame)

        # Compatibility flow label (hidden, kept for backwards compatibility)
        self.lbl_flow = QLabel(I18n.t(self.flow_key))
        self.lbl_flow.hide()

        # 3. Plain Human Description
        self.lbl_desc = QLabel(I18n.t(self.desc_key))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #9ca3af; font-size: 11px; line-height: 1.3;")
        layout.addWidget(self.lbl_desc)

        # 4. Authoritative Hotkeys & Control Scheme Banner
        self.lbl_hotkeys = QLabel()
        self.lbl_hotkeys.setStyleSheet("""
            QLabel {
                background-color: #0b1329;
                color: #38bdf8;
                font-size: 11px;
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #1e3a8a;
            }
        """)
        self.lbl_hotkeys.setWordWrap(True)
        if self.hotkeys_key:
            self.lbl_hotkeys.setText(f"⌨ <b>{I18n.t('hotkeys_label')}</b> {I18n.t(self.hotkeys_key)}")
        else:
            self.lbl_hotkeys.hide()
        layout.addWidget(self.lbl_hotkeys)

        # 5. Professional Hardware & Inference Telemetry Monitor (Clean, strict, real-time)
        self.monitor_frame = QFrame()
        self.monitor_frame.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border-radius: 6px;
                border: 1px solid #1e293b;
            }
        """)
        self.v_monitor = QVBoxLayout(self.monitor_frame)
        self.v_monitor.setContentsMargins(10, 8, 10, 8)
        self.v_monitor.setSpacing(4)

        # Compatibility hidden label
        self.lbl_mon_hw = QLabel()
        self.lbl_mon_hw.hide()

        self.lbl_mon_state = QLabel()
        self.lbl_mon_state.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        self.lbl_mon_state.setWordWrap(True)
        self.v_monitor.addWidget(self.lbl_mon_state)

        self.lbl_mon_alert = QLabel()
        self.lbl_mon_alert.setStyleSheet("font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        self.lbl_mon_alert.setWordWrap(True)
        self.lbl_mon_alert.hide()
        self.v_monitor.addWidget(self.lbl_mon_alert)

        layout.addWidget(self.monitor_frame)

        # 5. Embedded Stage 3 Controls Container (if stage_3)
        self.stage3_container = QWidget()
        self.stage3_layout = QVBoxLayout(self.stage3_container)
        self.stage3_layout.setContentsMargins(0, 4, 0, 4)
        self.stage3_layout.setSpacing(6)
        layout.addWidget(self.stage3_container)
        self.stage3_container.hide()

        # 6. Action Buttons and Live Telemetry
        h_btn = QHBoxLayout()
        h_btn.setSpacing(8)

        self.btn_start = QPushButton(I18n.t("btn_start"))
        self.btn_start.setFixedHeight(32)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #10b981; }
        """)
        self.btn_start.clicked.connect(self._on_start_clicked)
        h_btn.addWidget(self.btn_start)

        self.btn_stop = QPushButton(I18n.t("btn_stop"))
        self.btn_stop.setFixedHeight(32)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #b91c1c;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.hide()
        h_btn.addWidget(self.btn_stop)

        self.btn_open = QPushButton(I18n.t(self.open_label_key))
        self.btn_open.setFixedHeight(32)
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #e5e7eb;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #4b5563; }
        """)
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_open.hide()
        h_btn.addWidget(self.btn_open)

        h_btn.addStretch()

        self.lbl_telemetry = QLabel(I18n.t("res_stopped"))
        self.lbl_telemetry.setStyleSheet("""
            color: #9ca3af;
            font-family: Consolas, monospace;
            font-size: 11px;
            background-color: #1f2937;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #374151;
        """)
        h_btn.addWidget(self.lbl_telemetry)
        layout.addLayout(h_btn)

    def _get_node_configs(self) -> List[Tuple[str, str, str, str]]:
        lang = getattr(I18n, "current_lang", "ru")
        if self.stage_id == "stage_1":
            if lang == "ru":
                return [
                    ("1", "Аудиозахват", "WASAPI Loopback", "Системный звук"),
                    ("2", "Детектор речи", "Silero VAD", "In-Process CPU"),
                    ("3", "Распознавание", "SenseVoice INT8", "Sherpa-ONNX (CPU)"),
                    ("4", "Нейроперевод", "Tencent HY-MT1.5", "CPU / GGUF"),
                    ("5", "Субтитры", "Always-on-Top", "DirectX DWM"),
                ]
            elif lang == "zh":
                return [
                    ("1", "音频捕获", "WASAPI Loopback", "系统音频"),
                    ("2", "语音检测", "Silero VAD", "In-Process CPU"),
                    ("3", "语音识别", "SenseVoice INT8", "Sherpa-ONNX (CPU)"),
                    ("4", "神经翻译", "Tencent HY-MT1.5", "CPU / GGUF"),
                    ("5", "字幕输出", "Always-on-Top", "DirectX DWM"),
                ]
            else:
                return [
                    ("1", "Audio Capture", "WASAPI Loopback", "System Audio"),
                    ("2", "Voice Activity", "Silero VAD", "In-Process CPU"),
                    ("3", "Speech-to-Text", "SenseVoice INT8", "Sherpa-ONNX (CPU)"),
                    ("4", "Neural MT", "Tencent HY-MT1.5", "CPU / GGUF"),
                    ("5", "Subtitles", "Always-on-Top", "DirectX DWM"),
                ]

        elif self.stage_id == "stage_2":
            if lang == "ru":
                return [
                    ("1", "Экранный захват", "Screen Grabber", "GDI / DirectX"),
                    ("2", "Распознавание", "RapidOcrNet ONNX", "PP-OCRv6 (CPU)"),
                    ("3", "Машинный перевод", "Microsoft MT", "Облачный API"),
                    ("4", "Окно перевода", "OverTranslate UI", "WPF Desktop"),
                ]
            elif lang == "zh":
                return [
                    ("1", "屏幕截图", "Screen Grabber", "GDI / DirectX"),
                    ("2", "文字识别", "RapidOcrNet ONNX", "PP-OCRv6 (CPU)"),
                    ("3", "机器翻译", "Microsoft MT", "云端 API"),
                    ("4", "翻译窗口", "OverTranslate UI", "WPF 桌面"),
                ]
            else:
                return [
                    ("1", "Screen Capture", "Screen Grabber", "GDI / DirectX"),
                    ("2", "Optical OCR", "RapidOcrNet ONNX", "PP-OCRv6 (CPU)"),
                    ("3", "Machine Trans", "Microsoft MT", "Cloud API"),
                    ("4", "Window", "OverTranslate UI", "WPF Desktop"),
                ]

        elif self.stage_id == "stage_3":
            if lang == "ru":
                return [
                    ("1", "Вход микрофона", "WASAPI Input", "Физический микрофон"),
                    ("2", "Распознавание", "Sber GigaAM CTC", "PyTorch (CPU)"),
                    ("3", "Машинный перевод", "Helsinki Opus-MT", "In-Process (CPU)"),
                    ("4", "Нейросинтез", "Pocket-TTS 24kHz", "Клонирование тембра"),
                    ("5", "Аудиовыход", "Topping Loopback", "Аппаратный (0 мс)"),
                ]
            elif lang == "zh":
                return [
                    ("1", "麦克风输入", "WASAPI Input", "物理麦克风"),
                    ("2", "语音识别", "Sber GigaAM CTC", "PyTorch (CPU)"),
                    ("3", "机器翻译", "Helsinki Opus-MT", "In-Process (CPU)"),
                    ("4", "语音合成", "Pocket-TTS 24kHz", "声音克隆"),
                    ("5", "音频输出", "Topping Loopback", "硬件回环 (0 ms)"),
                ]
            else:
                return [
                    ("1", "Mic Input", "WASAPI Input", "Physical Mic"),
                    ("2", "Speech-to-Text", "Sber GigaAM CTC", "PyTorch (CPU)"),
                    ("3", "Machine Trans", "Helsinki Opus-MT", "In-Process (CPU)"),
                    ("4", "Voice Synth", "Pocket-TTS 24kHz", "Voice Cloning"),
                    ("5", "Audio Output", "Topping Loopback", "Hardware Loopback (0 ms)"),
                ]
        return []

    def _init_nodes(self):
        while self.nodes_layout.count():
            item = self.nodes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.nodes = []

        cfg = self._get_node_configs()
        for idx, (step_num, cat, title, backend) in enumerate(cfg):
            if idx > 0:
                arrow = QLabel("➔")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("color: #475569; font-size: 13px; font-weight: bold; padding: 0 1px;")
                self.nodes_layout.addWidget(arrow, 0)
            node = PipelineNodeWidget(step_num, cat, title, backend)
            self.nodes.append(node)
            self.nodes_layout.addWidget(node, 1)

    def _retranslate_nodes(self):
        cfg = self._get_node_configs()
        for idx, (step_num, cat, title, backend) in enumerate(cfg):
            if idx < len(self.nodes):
                self.nodes[idx].lbl_cat.setText(f"{step_num}. {cat}".upper())
                self.nodes[idx].update_node(title=title, backend=backend, active=False)

    def update_card_monitor(self, live_data: dict = None):
        """Update hardware context, signal path, and live inference metrics."""
        if self.stage_id == "stage_1":
            if self._is_running and live_data and live_data.get("has_session"):
                audio_dev = live_data.get("audio_device") or "WASAPI Loopback"
                req_dev = str(live_data.get("asr_device_requested", "cpu")).strip()
                act_dev = str(live_data.get("asr_device_actual", "cpu")).strip()
                mt_name = live_data.get("mt_model", "Hunyuan MT 1.8B").split("(")[0].strip()

                if len(self.nodes) >= 5:
                    self.nodes[0].update_node(backend=audio_dev)
                    self.nodes[2].update_node(title="SenseVoice INT8", backend=f"{act_dev.upper()} ONNX")
                    self.nodes[3].update_node(title=mt_name)

                if live_data.get("last_original") and live_data.get("last_asr_ms") is not None:
                    asr_ms = live_data.get("last_asr_ms", 0)
                    tl_ms = live_data.get("last_tl_ms", 0)
                    tot_ms = live_data.get("last_total_ms", asr_ms + tl_ms)
                    orig = live_data.get("last_original", "")
                    if len(orig) > 55:
                        orig = orig[:52] + "..."
                    trans = live_data.get("last_translation", "")
                    if len(trans) > 55:
                        trans = trans[:52] + "..."

                    if len(self.nodes) >= 5:
                        self.nodes[1].update_node(active=True, metric="Active")
                        self.nodes[2].update_node(active=True, metric=f"{asr_ms} ms")
                        self.nodes[3].update_node(active=True, metric=f"{tl_ms} ms")
                        self.nodes[4].update_node(active=True, metric="Live")

                    self.lbl_mon_state.setText(
                        f"⏱ <b>Инференс сегмента:</b> <span style='color: #38bdf8;'>ASR: {asr_ms} мс</span> ➔ "
                        f"<span style='color: #c084fc;'>MT: {tl_ms} мс</span> ➔ "
                        f"<span style='color: #34d399;'>Сквозная (E2E): {tot_ms} мс</span> | "
                        f"💬 <i>\"{orig}\"</i> ➔ <b>\"{trans}\"</b>"
                    )
                else:
                    if len(self.nodes) >= 5:
                        self.nodes[1].update_node(active=False, metric="Standby")
                        self.nodes[2].update_node(active=False, metric=None)
                        self.nodes[3].update_node(active=False, metric=None)
                        self.nodes[4].update_node(active=False, metric=None)
                    self.lbl_mon_state.setText("📡 <b>Состояние VAD:</b> Ожидание речевой активности (VAD Standby / Порог: 50%)")

                if live_data.get("error_msg"):
                    self.lbl_mon_alert.setText(f"🛑 <b>Сбой конвейера [Pipeline Failure]:</b> {live_data['error_msg']}")
                    self.lbl_mon_alert.setStyleSheet("background-color: #450a0a; color: #fca5a5; font-size: 11px; padding: 4px 8px; border-radius: 4px; border: 1px solid #dc2626;")
                    self.lbl_mon_alert.show()
                elif "cuda" in req_dev.lower() and act_dev == "cpu":
                    self.lbl_mon_alert.setText(f"ℹ️ <b>Аппаратный контекст:</b> В интерфейсе запрошен бэкенд <b>{req_dev} (RTX 5070)</b> ➔ Для SenseVoice активен <b>CPU Execution Provider</b> (рантайм sherpa-onnx скомпилирован без CUDA). Для запуска нейросетей на RTX 5070 можно подключить бэкенд Ollama / vLLM.")
                    self.lbl_mon_alert.setStyleSheet("background-color: #172554; color: #93c5fd; font-size: 11px; padding: 4px 8px; border-radius: 4px; border: 1px solid #3b82f6;")
                    self.lbl_mon_alert.show()
                else:
                    self.lbl_mon_alert.hide()
            else:
                self._retranslate_nodes()
                self.lbl_mon_state.setText("⚪ <b>Статус службы:</b> Остановлена | Тракт готов к приёму системного аудиопотока")
                self.lbl_mon_alert.hide()

        elif self.stage_id == "stage_2":
            if self._is_running:
                for n in self.nodes:
                    n.update_node(active=True)
                self.lbl_mon_state.setText("🟢 <b>Статус службы:</b> Активна в системном трее | Перевод текста с экрана и буфера готов")
            else:
                self._retranslate_nodes()
                self.lbl_mon_state.setText("⚪ <b>Статус службы:</b> Остановлена | Служба готова к запуску")
            self.lbl_mon_alert.hide()

        elif self.stage_id == "stage_3":
            if self._is_running:
                for n in self.nodes:
                    n.update_node(active=True)
                self.lbl_mon_state.setText("🟢 <b>Статус службы:</b> Активна | Перевод речи в микрофонный канал готов")
            else:
                self._retranslate_nodes()
                self.lbl_mon_state.setText("⚪ <b>Статус службы:</b> Остановлена | Акустический профиль my_pocket_voice.safetensors загружен")
            self.lbl_mon_alert.hide()

    def retranslate(self):
        self.lbl_title.setText(f"<b>{I18n.t(self.title_key)}</b>")
        self.lbl_flow.setText(I18n.t(self.flow_key))
        self.lbl_desc.setText(I18n.t(self.desc_key))
        if self.hotkeys_key:
            self.lbl_hotkeys.setText(f"⌨ <b>{I18n.t('hotkeys_label')}</b> {I18n.t(self.hotkeys_key)}")
            self.lbl_hotkeys.show()
        else:
            self.lbl_hotkeys.hide()
        self.btn_start.setText(I18n.t("btn_start"))
        self.btn_stop.setText(I18n.t("btn_stop"))
        self.btn_open.setText(I18n.t(self.open_label_key))
        self._retranslate_nodes()
        self.update_card_monitor()
        self.set_running(self._is_running, force=True)

    def update_telemetry(self, data: dict, force: bool = False):
        running = data.get("running", False)
        self.set_running(running, force=force)

        if running:
            ram = data.get("ram_mb", 0.0)
            cpu = data.get("cpu_pct", 0.0)
            self.lbl_telemetry.setText(I18n.t("res_metrics", ram=ram, cpu=cpu))
            self.lbl_telemetry.setStyleSheet("""
                color: #34d399;
                font-family: Consolas, monospace;
                font-size: 11px;
                background-color: #064e3b;
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #059669;
            """)
        else:
            self.lbl_telemetry.setText(I18n.t("res_stopped"))
            self.lbl_telemetry.setStyleSheet("""
                color: #9ca3af;
                font-family: Consolas, monospace;
                font-size: 11px;
                background-color: #1f2937;
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #374151;
            """)

    def set_running(self, running: bool, force: bool = False):
        if not force and self._is_running == running:
            return
        self._is_running = running
        if running:
            self.setStyleSheet("""
                StageCard {
                    background-color: #132338;
                    border: 1px solid #2563eb;
                    border-radius: 8px;
                }
            """)
            self.status_pill.setText(I18n.t("status_running"))
            self.status_pill.setStyleSheet("""
                background-color: #065f46;
                color: #a7f3d0;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #059669;
            """)
            self.btn_start.hide()
            self.btn_stop.show()
            if self.on_open:
                self.btn_open.show()
        else:
            self.update_card_monitor()
            self.setStyleSheet("""
                StageCard {
                    background-color: #1a1b1e;
                    border: 1px solid #2e3035;
                    border-radius: 8px;
                }
            """)
            self.status_pill.setText(I18n.t("status_stopped_pill"))
            self.status_pill.setStyleSheet("""
                background-color: #212328;
                color: #9ca3af;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #374151;
            """)
            self.btn_start.show()
            self.btn_stop.hide()
            self.btn_open.hide()

    def _on_start_clicked(self):
        if self.on_start:
            self.on_start()

    def _on_stop_clicked(self):
        if self.on_stop:
            self.on_stop()

    def _on_open_clicked(self):
        if self.on_open:
            self.on_open()


class EcosystemHub(QMainWindow):
    """Main Orchestration, Multilingual Control, and Health Hub Window."""

    def __init__(self):
        super().__init__()
        self.resize(1140, 840)
        self.setMinimumSize(960, 580)

        self._active_routing_mode = "topping"
        self._last_settings_mtimes: Dict[str, float] = {}
        self._apply_theme()
        self._init_ui()
        self._retranslate_ui(is_initial=True)

        # Decoupled Process Supervisor Poller (every 2.0 seconds)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2000)
        self.poll_timer.timeout.connect(self._poll_process_status)

        # Defer scan and process checking to after window renders
        QTimer.singleShot(40, self._initial_load)

    def _initial_load(self):
        """Runs right after GUI window appears on screen for instant startup."""
        self._poll_process_status()
        self.poll_timer.start()
        self._populate_patches_view()
        self._update_hub_profile_styles()
        self._refresh_all_latencies()

    def _refresh_all_latencies(self):
        m1 = None
        if self.card_stage1._is_running:
            try:
                from launcher.telemetry import Stage1Telemetry
                m1 = Stage1Telemetry.get_live_metrics()
            except Exception:
                pass
        self.card_stage1.update_card_monitor(m1)
        self.card_stage2.update_card_monitor()
        self.card_stage3.update_card_monitor()

        # Update translation model name from LiveTranslate config if available
        try:
            s1_file = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "user_settings.json"
            if s1_file.is_file() and hasattr(self, "card_stage1") and len(self.card_stage1.nodes) >= 5:
                cfg = json.loads(s1_file.read_text(encoding="utf-8"))
                models = cfg.get("models", [])
                active_idx = cfg.get("active_model_index", 0)
                if 0 <= active_idx < len(models):
                    m_name = models[active_idx].get("name", "Tencent HY-MT1.5")
                    clean_name = m_name.split("(")[0].strip()
                    self.card_stage1.nodes[3].update_node(title=clean_name)
        except Exception:
            pass

        # Update OCR translation provider from OverTranslate config if available
        try:
            s2_file = PROJECT_ROOT / "CONFIG" / "stage_2_screen" / "appsettings.json"
            if s2_file.is_file() and hasattr(self, "card_stage2") and len(self.card_stage2.nodes) >= 4:
                cfg = json.loads(s2_file.read_text(encoding="utf-8"))
                prov = cfg.get("Provider", "Microsoft")
                self.card_stage2.nodes[2].update_node(title=f"{prov} MT")
        except Exception:
            pass

    def _check_and_refresh_latencies_on_change(self):
        """Detect live changes in LiveTranslate or OverTranslate configs and hot-reload pipeline latency chips."""
        s1_file = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "user_settings.json"
        s2_file = PROJECT_ROOT / "CONFIG" / "stage_2_screen" / "appsettings.json"

        changed = False
        for f in (s1_file, s2_file):
            if f.is_file():
                try:
                    mtime = f.stat().st_mtime
                    if self._last_settings_mtimes.get(str(f)) != mtime:
                        self._last_settings_mtimes[str(f)] = mtime
                        changed = True
                except OSError:
                    pass

        if changed:
            self._refresh_all_latencies()

    def _update_hub_profile_styles(self):
        try:
            from stage_3_voice.studio.config import load_settings
            from stage_3_voice.studio.routing_presets import RoutingPresets
            cfg = load_settings()
            mode = cfg.get("audio", {}).get("routing_mode", "topping")
            hw = RoutingPresets.get_hardware_info()
            has_cable = hw.get("has_cable", False)
        except Exception:
            mode = "topping"
            has_cable = True

        self._active_routing_mode = mode

        if mode == "topping":
            self.btn_hub_topping.setStyleSheet("background-color: #2563eb; color: #fff; font-weight: bold; border-radius: 4px; padding: 0 12px; border: 1px solid #60a5fa;")
            self.btn_hub_cable.setStyleSheet("background-color: #212328; color: #9ca3af; border-radius: 4px; padding: 0 12px; border: 1px solid #374151;")
            self.btn_install_cable.hide()
            if hasattr(self, "card_stage3") and len(self.card_stage3.nodes) >= 5:
                self.card_stage3.nodes[4].update_node(title="Topping Loopback", backend="Аппаратный (0 мс)")
        else:
            self.btn_hub_cable.setStyleSheet("background-color: #059669; color: #fff; font-weight: bold; border-radius: 4px; padding: 0 12px; border: 1px solid #34d399;")
            self.btn_hub_topping.setStyleSheet("background-color: #212328; color: #9ca3af; border-radius: 4px; padding: 0 12px; border: 1px solid #374151;")
            if not has_cable:
                self.btn_install_cable.show()
            else:
                self.btn_install_cable.hide()
            if hasattr(self, "card_stage3") and len(self.card_stage3.nodes) >= 5:
                self.card_stage3.nodes[4].update_node(title="VB-Audio Cable", backend="Виртуальный драйвер (~15 мс)")

    def _on_hub_switch_profile(self, mode: str):
        if mode == "cable":
            try:
                from stage_3_voice.studio.routing_presets import RoutingPresets
                hw = RoutingPresets.get_hardware_info()
                if not hw.get("has_cable", False):
                    reply = QMessageBox.question(
                        self,
                        I18n.t("cable_not_found_title"),
                        I18n.t("cable_not_found_msg"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self._on_install_cable()
                    return
            except Exception as e:
                log.warning("Could not check hardware: %s", e)

        try:
            from stage_3_voice.studio.routing_presets import RoutingPresets
            from stage_3_voice.studio.config import load_settings, save_settings
            cfg = load_settings()
            success, msg = RoutingPresets.apply_preset(mode, cfg)
            if success:
                save_settings(cfg)
                self._update_hub_profile_styles()
                self._refresh_all_latencies()

                # User-friendly switch confirmation (non-blocking in tests)
                if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                    if mode == "topping":
                        QMessageBox.information(self, I18n.t("profile_topping_title"), I18n.t("profile_topping_msg"))
                    else:
                        QMessageBox.information(self, I18n.t("profile_cable_title"), I18n.t("profile_cable_msg"))
        except Exception as e:
            log.error("Failed to switch profile: %s", e)

    def _on_install_cable(self):
        import subprocess
        bat = PROJECT_ROOT / "scripts" / "install_vbcable.bat"
        if bat.is_file():
            subprocess.Popen(["cmd.exe", "/c", str(bat)])

    def _on_open_config_folder(self):
        import subprocess
        config_dir = PROJECT_ROOT / "CONFIG"
        if config_dir.is_dir():
            subprocess.Popen(["explorer.exe", str(config_dir)])

    def closeEvent(self, event):
        self.poll_timer.stop()
        super().closeEvent(event)

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # 1. Master Control Header Bar with Language Switcher and Patch Status
        root_layout.addLayout(self._create_master_header())

        # 2. Clean 3 Tabs (KISS Standard: Dashboard, Patches by Module, Architecture Guide)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_dashboard_tab(), "🎛 Пульт управления")
        self.tabs.addTab(self._create_patches_tab(), "🛡 Защита и Патчи")
        self.tabs.addTab(self._create_guide_tab(), "📖 Памятка на будущее")
        root_layout.addWidget(self.tabs, stretch=1)

    def _create_master_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(10)

        # Master Start
        self.btn_start_all = QPushButton()
        self.btn_start_all.setFixedHeight(42)
        self.btn_start_all.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #10b981; }
        """)
        self.btn_start_all.clicked.connect(EcosystemProcessManager.start_all)
        h.addWidget(self.btn_start_all)

        # Master Stop
        self.btn_stop_all = QPushButton()
        self.btn_stop_all.setFixedHeight(42)
        self.btn_stop_all.setStyleSheet("""
            QPushButton {
                background-color: #b91c1c;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.btn_stop_all.clicked.connect(EcosystemProcessManager.stop_all)
        h.addWidget(self.btn_stop_all)

        # Patch Health Quick Pill (Navigates to Tab 1 or refreshes audit)
        self.lbl_patch_quick = QPushButton("🛡 Патчи: Проверка...")
        self.lbl_patch_quick.setFixedHeight(42)
        self.lbl_patch_quick.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                font-family: Consolas, monospace;
                font-size: 11px;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 12px;
                border: 1px solid #0284c7;
            }
            QPushButton:hover { background-color: #0f172a; }
        """)
        self.lbl_patch_quick.clicked.connect(self._on_quick_patch_clicked)
        h.addWidget(self.lbl_patch_quick)

        h.addStretch()

        # Language Switcher
        h_lang = QHBoxLayout()
        self.lbl_lang = QLabel("🌐")
        self.lbl_lang.setStyleSheet("font-size: 14px;")
        h_lang.addWidget(self.lbl_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇷🇺 Русский", "ru")
        self.combo_lang.addItem("🇬🇧 English", "en")
        self.combo_lang.addItem("🇨🇳 中文", "zh")
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        h_lang.addWidget(self.combo_lang)
        h.addLayout(h_lang)

        # System Summary Badge
        self.lbl_system_summary = QLabel()
        self.lbl_system_summary.setStyleSheet("""
            color: #38bdf8;
            font-family: Consolas, monospace;
            font-weight: bold;
            font-size: 12px;
            background-color: #111827;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #1f2937;
        """)
        h.addWidget(self.lbl_system_summary)

        return h

    # =========================================================================
    # Tab 1: Ecosystem Dashboard & Pipeline Flow Map (KISS)
    # =========================================================================
    def _create_dashboard_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #16171a;
            }
            QScrollBar:vertical {
                background: #111827;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #374151;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4b5563;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        w = QWidget()
        w.setStyleSheet("background-color: #16171a;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. Module 1: LiveTranslate (Audio to Subtitles)
        self.card_stage1 = StageCard(
            "stage_1",
            "stage1_title", "stage1_flow", "stage1_desc", "stage1_hotkeys",
            on_start=EcosystemProcessManager.start_stage_1,
            on_stop=EcosystemProcessManager.stop_stage_1,
        )
        layout.addWidget(self.card_stage1)

        # 2. Module 2: OverTranslate (Screen OCR)
        self.card_stage2 = StageCard(
            "stage_2",
            "stage2_title", "stage2_flow", "stage2_desc", "stage2_hotkeys",
            on_start=EcosystemProcessManager.start_stage_2,
            on_stop=EcosystemProcessManager.stop_stage_2,
        )
        layout.addWidget(self.card_stage2)

        # 3. Module 3: Voice Studio (Outgoing Mic Speech)
        self.card_stage3 = StageCard(
            "stage_3",
            "stage3_title", "stage3_flow", "stage3_desc", "stage3_hotkeys",
            on_start=EcosystemProcessManager.start_stage_3,
            on_stop=EcosystemProcessManager.stop_stage_3,
        )

        # EMBED Stage 3 Specific Controls (Audio Hardware Selector & Voice Wizard)
        self.card_stage3.stage3_container.show()

        # Row 1: Output audio routing channel
        h_row_hw = QHBoxLayout()
        h_row_hw.setSpacing(8)

        self.lbl_hw_title = QLabel(f"<b>{I18n.t('hardware_title')}</b>")
        self.lbl_hw_title.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        h_row_hw.addWidget(self.lbl_hw_title)

        self.btn_hub_topping = QPushButton(I18n.t("hardware_topping"))
        self.btn_hub_topping.setFixedHeight(28)
        self.btn_hub_topping.clicked.connect(lambda: self._on_hub_switch_profile("topping"))
        h_row_hw.addWidget(self.btn_hub_topping)

        self.btn_hub_cable = QPushButton(I18n.t("hardware_cable"))
        self.btn_hub_cable.setFixedHeight(28)
        self.btn_hub_cable.clicked.connect(lambda: self._on_hub_switch_profile("cable"))
        h_row_hw.addWidget(self.btn_hub_cable)

        self.btn_install_cable = QPushButton(I18n.t("hardware_install_cable"))
        self.btn_install_cable.setFixedHeight(28)
        self.btn_install_cable.setStyleSheet("background-color: #0284c7; color: #fff; font-weight: bold; border-radius: 4px; padding: 0 10px; font-size: 11px;")
        self.btn_install_cable.clicked.connect(self._on_install_cable)
        self.btn_install_cable.hide()
        h_row_hw.addWidget(self.btn_install_cable)

        h_row_hw.addStretch()
        self.card_stage3.stage3_layout.addLayout(h_row_hw)

        # Row 2: Voice Cloning Profile Wizard
        h_row_wiz = QHBoxLayout()
        h_row_wiz.setSpacing(8)

        self.lbl_wiz_title = QLabel(f"<b>{I18n.t('wizard_title')}</b>")
        self.lbl_wiz_title.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        h_row_wiz.addWidget(self.lbl_wiz_title)

        self.btn_launch_wizard = QPushButton(I18n.t("btn_wizard"))
        self.btn_launch_wizard.setFixedHeight(28)
        self.btn_launch_wizard.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 12px;
                border: 1px solid #6366f1;
            }
            QPushButton:hover { background-color: #6366f1; }
        """)
        self.btn_launch_wizard.clicked.connect(self._on_open_voice_wizard)
        h_row_wiz.addWidget(self.btn_launch_wizard)

        self.lbl_wiz_desc = QLabel(I18n.t("wizard_desc"))
        self.lbl_wiz_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_row_wiz.addWidget(self.lbl_wiz_desc)

        h_row_wiz.addStretch()
        self.card_stage3.stage3_layout.addLayout(h_row_wiz)

        layout.addWidget(self.card_stage3)
        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    # =========================================================================
    # Tab 2: System Health, Patches Grouped by Module & CONFIG Vault
    # =========================================================================
    def _create_patches_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 1. Header Info Banner
        self.lbl_patches_head = QLabel()
        self.lbl_patches_head.setStyleSheet("color: #e5e7eb; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.lbl_patches_head)

        self.lbl_patches_summary = QLabel()
        self.lbl_patches_summary.setStyleSheet("""
            background-color: #111827;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid #1f2937;
        """)
        layout.addWidget(self.lbl_patches_summary)

        # 2. Action Toolbar: Restore, Re-audit, Open CONFIG
        h_ctrl = QHBoxLayout()
        h_ctrl.setSpacing(10)

        self.btn_restore_patches = QPushButton()
        self.btn_restore_patches.setFixedHeight(36)
        self.btn_restore_patches.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 0 18px;
            }
            QPushButton:hover { background-color: #3b82f6; }
        """)
        self.btn_restore_patches.clicked.connect(self._on_restore_patches_clicked)
        h_ctrl.addWidget(self.btn_restore_patches)

        self.btn_audit_refresh = QPushButton()
        self.btn_audit_refresh.setFixedHeight(36)
        self.btn_audit_refresh.setStyleSheet("background-color: #374151; color: #fff; border-radius: 4px; padding: 0 14px; font-weight: bold;")
        self.btn_audit_refresh.clicked.connect(self._on_audit_refresh_clicked)
        h_ctrl.addWidget(self.btn_audit_refresh)

        self.btn_vault_folder = QPushButton()
        self.btn_vault_folder.setFixedHeight(36)
        self.btn_vault_folder.setStyleSheet("background-color: #1f2937; color: #9ca3af; border-radius: 4px; padding: 0 14px;")
        self.btn_vault_folder.clicked.connect(self._on_open_config_folder)
        h_ctrl.addWidget(self.btn_vault_folder)

        h_ctrl.addStretch()
        layout.addLayout(h_ctrl)

        # 3. Modular Cards Container
        self.box_module1 = QGroupBox("📦 Модуль 1: Синхронные субтитры (LiveTranslate) — 4 патча")
        self.v_m1 = QVBoxLayout(self.box_module1)
        self.v_m1.setSpacing(6)
        layout.addWidget(self.box_module1)

        self.box_module2 = QGroupBox("📦 Модуль 2: Экранный переводчик (OverTranslate) — 1 патч")
        self.v_m2 = QVBoxLayout(self.box_module2)
        self.v_m2.setSpacing(6)
        layout.addWidget(self.box_module2)

        self.box_module3 = QGroupBox("📦 Модуль 3: Голосовой переводчик (Voice Studio) — 100% Автономный движок")
        self.v_m3 = QVBoxLayout(self.box_module3)
        self.v_m3.setSpacing(6)
        layout.addWidget(self.box_module3)

        self.box_vault = QGroupBox("🔒 Защищенное хранилище настроек (CONFIG/)")
        self.v_vault = QVBoxLayout(self.box_vault)
        self.v_vault.setSpacing(6)
        layout.addWidget(self.box_vault)

        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    def _render_patch_row(self, item: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #16171a;
                border: 1px solid #2e3035;
                border-radius: 6px;
            }
        """)
        h = QHBoxLayout(frame)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(10)

        # Status badge
        badge = QLabel()
        if item["is_ok"]:
            badge.setText("✔ АКТИВЕН")
            badge.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px; background-color: #064e3b; padding: 3px 8px; border-radius: 4px; border: 1px solid #059669;")
        else:
            badge.setText("❌ СЛЕТЕЛ")
            badge.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px; background-color: #7f1d1d; padding: 3px 8px; border-radius: 4px; border: 1px solid #dc2626;")
        badge.setFixedWidth(90)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(badge)

        # Name and category
        lbl_name = QLabel(f"<b>{item['name']}</b> <span style='color: #64748b;'>({item['category']})</span>")
        lbl_name.setStyleSheet("font-size: 12px; color: #ffffff;")
        h.addWidget(lbl_name)

        # Description
        lbl_desc = QLabel(item["desc"])
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        h.addWidget(lbl_desc, stretch=1)

        return frame

    def _on_quick_patch_clicked(self):
        """Top bar patch pill click: navigate to tab 1 or re-audit if already there."""
        if self.tabs.currentIndex() != 1:
            self.tabs.setCurrentIndex(1)
        else:
            self._on_audit_refresh_clicked()

    def _on_audit_refresh_clicked(self):
        """Re-audits system and provides clear, immediate visual confirmation."""
        self._populate_patches_view()
        self.btn_audit_refresh.setText(I18n.t("btn_audit_refresh_done"))
        self.btn_audit_refresh.setStyleSheet("background-color: #064e3b; color: #34d399; border-radius: 4px; padding: 0 14px; font-weight: bold; border: 1px solid #059669;")
        QTimer.singleShot(1500, self._reset_audit_refresh_button)

    def _reset_audit_refresh_button(self):
        self.btn_audit_refresh.setText(I18n.t("btn_audit_refresh"))
        self.btn_audit_refresh.setStyleSheet("background-color: #374151; color: #fff; border-radius: 4px; padding: 0 14px; font-weight: bold;")

    def _populate_patches_view(self):
        audit = PatchIntegrityChecker.audit_all()
        modules = audit["modules"]

        # 1. Update groupbox titles from i18n
        self.box_module1.setTitle(I18n.t("m1_group_title"))
        self.box_module2.setTitle(I18n.t("m2_group_title"))
        self.box_module3.setTitle(I18n.t("m3_group_title"))
        self.box_vault.setTitle(I18n.t("vault_group_title"))

        # 2. Clear old widgets
        for layout in (self.v_m1, self.v_m2, self.v_m3, self.v_vault):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # 3. Populate Module 1
        for it in modules.get("stage_1", {}).get("items", []):
            self.v_m1.addWidget(self._render_patch_row(it))

        # 4. Populate Module 2
        for it in modules.get("stage_2", {}).get("items", []):
            self.v_m2.addWidget(self._render_patch_row(it))

        # 5. Populate Module 3
        for it in modules.get("stage_3", {}).get("items", []):
            self.v_m3.addWidget(self._render_patch_row(it))

        # 6. Populate Vault
        for it in modules.get("config", {}).get("items", []):
            self.v_vault.addWidget(self._render_patch_row(it))

        # 7. Update Summary Banner & Quick Header Pill
        active_cnt = audit["active_patches_count"]
        tot_cnt = audit["total_patches_count"]
        if audit["all_passed"]:
            summary_msg = I18n.t("patches_summary_ok", active=active_cnt, total=tot_cnt)
            self.lbl_patches_summary.setText(summary_msg)
            self.lbl_patches_summary.setStyleSheet("background-color: #064e3b; color: #a7f3d0; padding: 10px 14px; border-radius: 6px; font-weight: bold; border: 1px solid #059669;")
            self.lbl_patch_quick.setText(f"🛡 {active_cnt}/{tot_cnt} Патчей активны (ОК)")
            self.lbl_patch_quick.setStyleSheet("background-color: #064e3b; color: #34d399; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; border-radius: 6px; padding: 0 12px; border: 1px solid #059669;")
        else:
            self.lbl_patches_summary.setText(I18n.t("patches_summary_fail"))
            self.lbl_patches_summary.setStyleSheet("background-color: #7f1d1d; color: #fecaca; padding: 10px 14px; border-radius: 6px; font-weight: bold; border: 1px solid #dc2626;")
            self.lbl_patch_quick.setText(f"🔴 Патчи: {active_cnt}/{tot_cnt} (СЛЕТЕЛ)")
            self.lbl_patch_quick.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; border-radius: 6px; padding: 0 12px; border: 1px solid #dc2626;")

    def _on_restore_patches_clicked(self):
        res = PatchIntegrityChecker.restore_all_patches()
        self._populate_patches_view()
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            if res["success"]:
                QMessageBox.information(
                    self,
                    "Успешное восстановление",
                    f"Все ключевые инженерные патчи и конфигурации успешно восстановлены из хранилища CONFIG/!\n\nВосстановлено файлов: {len(res['restored_files'])}.",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка восстановления",
                    f"Не удалось восстановить патчи:\n" + "\n".join(res["errors"]),
                )

    # =========================================================================
    # Tab 3: Plain-Human Architecture & Future Reference Guide (Visual Atlas)
    # =========================================================================
    def _create_guide_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f1013; }")
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 0. Master Architecture Overview Banner (Whole System at a Glance)
        box_overview = QGroupBox("🗺 Общая архитектура экосистемы (3 направления перевода)")
        box_overview.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #2e3440;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #e5e9f0;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_over = QVBoxLayout(box_overview)
        lbl_over = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<table border="0" cellpadding="10" style="width: 100%; border-collapse: separate; border-spacing: 0 8px;">
<tr style="background-color: #1e293b; border-radius: 6px;">
    <td style="width: 28%; font-weight: bold; color: #38bdf8; font-size: 12px;">
        🔊 1. Входящий звук ПК<br><span style="font-size: 10px; color: #94a3b8; font-weight: normal;">(Видео, Discord, Звонки)</span>
    </td>
    <td style="width: 44%; color: #e2e8f0; font-size: 11px;">
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">WASAPI Loopback</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">SenseVoice INT8</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">Hunyuan MT</span>
    </td>
    <td style="width: 28%; text-align: right; font-weight: bold; color: #34d399; font-size: 11px;">
        📺 Субтитры поверх экрана<br><span style="color: #64748b; font-size: 10px; font-weight: normal;">(~250 мс, 100% офлайн)</span>
    </td>
</tr>
<tr style="background-color: #1e293b; border-radius: 6px;">
    <td style="width: 28%; font-weight: bold; color: #fbbf24; font-size: 12px;">
        🖼 2. Экранный текст<br><span style="font-size: 10px; color: #94a3b8; font-weight: normal;">(Интерфейсы, Документы, Графика)</span>
    </td>
    <td style="width: 44%; color: #e2e8f0; font-size: 11px;">
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">Рамка Ctrl+Alt+A</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">RapidOcr ONNX</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">Microsoft MT</span>
    </td>
    <td style="width: 28%; text-align: right; font-weight: bold; color: #34d399; font-size: 11px;">
        📝 Замена прямо на экране<br><span style="color: #64748b; font-size: 10px; font-weight: normal;">(~180 мс, In-Place)</span>
    </td>
</tr>
<tr style="background-color: #1e293b; border-radius: 6px;">
    <td style="width: 28%; font-weight: bold; color: #a78bfa; font-size: 12px;">
        🎙 3. Исходящий голос<br><span style="font-size: 10px; color: #94a3b8; font-weight: normal;">(Вы говорите по-русски)</span>
    </td>
    <td style="width: 44%; color: #e2e8f0; font-size: 11px;">
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">GigaAM CTC</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">Opus-MT</span> ➔
        <span style="background-color: #0f172a; padding: 3px 6px; border-radius: 4px; border: 1px solid #334155;">Pocket-TTS Клон</span>
    </td>
    <td style="width: 28%; text-align: right; font-weight: bold; color: #34d399; font-size: 11px;">
        🔊 Ваш голос по-английски<br><span style="color: #64748b; font-size: 10px; font-weight: normal;">(В Discord / Topping петлю)</span>
    </td>
</tr>
</table>
</div>
        """)
        lbl_over.setWordWrap(True)
        v_over.addWidget(lbl_over)
        layout.addWidget(box_overview)

        # Card 1: Module 1 Guide
        box_m1 = QGroupBox("📦 1. Синхронные субтитры (LiveTranslate) — Аудио ➔ Субтитры")
        box_m1.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #0284c7;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #38bdf8;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_m1 = QVBoxLayout(box_m1)
        lbl_m1 = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<b>Назначение:</b> Перехват иностранной речи из аудиопотока и вывод субтитров поверх любых окон (видео, лекции, конференции, звонки).<br><br>

<b style="color: #38bdf8;">Архитектурные доработки под капотом (Почему работает быстро и без зависаний):</b>
<ul style="margin: 6px 0 10px 18px; padding: 0;">
    <li><b>Sherpa-ONNX SenseVoice INT8:</b> Заменили медленный Python Whisper на аппаратный C++ рантайм ONNX. Распознает речь за <b>~170 мс</b> прямо на 2 ядрах процессора без нагрузки на видеокарту.</li>
    <li><b>Локальная модель Tencent Hunyuan MT 1.8B:</b> Вшита напрямую в память процесса через <code>llama-cpp-python</code>. <b>Никаких внешних веб-серверов</b> (Ollama, Docker, port 8080) — чистый офлайн перевод за <b>~80 мс</b>.</li>
    <li><b>Аппаратный Silero VAD:</b> Автоматически делит речь на фразы по паузам дыхания, не обрезая окончания слов.</li>
    <li><b>Сенсорная подложка Alpha 1/255:</b> Невидимый сенсорный слой DWM позволяет мыши захватывать колесико даже при прозрачности фона 0%.</li>
</ul>

<b style="color: #facc15;">Горячие клавиши управления:</b><br>
<div style="margin-top: 6px;">
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#38bdf8;">F9</kbd> — <b>Единый рубильник:</b> мгновенно скрывает субтитры и ставит транскрипцию на паузу (нулевая нагрузка на CPU в тишине).<br>
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#38bdf8;">2x Колесико мыши</kbd> — <b>Клик сквозь окно:</b> субтитры перестают реагировать на курсор мыши и не блокируют элементы управления окон под ними.<br>
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#38bdf8;">Зажать колесико мыши</kbd> — Свободное перемещение субтитров по экрану без риска случайно кликнуть ЛКМ.
</div>
</div>
        """)
        lbl_m1.setWordWrap(True)
        v_m1.addWidget(lbl_m1)
        layout.addWidget(box_m1)

        # Card 2: Module 2 Guide
        box_m2 = QGroupBox("📦 2. Экранный переводчик (OverTranslate) — Рамка ➔ Перевод прямо на экране")
        box_m2.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #d97706;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #fbbf24;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_m2 = QVBoxLayout(box_m2)
        lbl_m2 = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<b>Назначение:</b> Мгновенный перевод невыделяемого текста с изображений, документации, диалоговых окон и интерфейсов сторонних программ с заменой текста на картинке (In-Place эффект).<br><br>

<b style="color: #fbbf24;">Архитектура и устраненный баг:</b>
<ul style="margin: 6px 0 10px 18px; padding: 0;">
    <li><b>Оптическое распознавание (RapidOcrNet ONNX):</b> Легковесная нейросеть PP-OCRv6 считывает текст с пикселей за <b>~30 мс</b>.</li>
    <li><b>Двуязычный взаимный перевод:</b> Настроен в <code>appsettings.json</code> (выделил русский — перевел на английский, выделил английский — перевел на русский).</li>
    <li><b>Фикс бага буфера обмена Windows 11:</b> В оригинале метод <code>Clipboard.SetText</code> вызывал краш Win32 API <code>0x800401D0</code> («Буфер обмена недоступен»). Мы заменили вызов на неблокирующий <code>SetDataObject(copy: false)</code> в <code>OverTranslate.dll</code> — быстрый перевод по выделению теперь работает стабильно везде.</li>
</ul>

<b style="color: #facc15;">Горячие клавиши управления:</b><br>
<div style="margin-top: 6px;">
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">Ctrl</kbd> + <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">Alt</kbd> + <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">A</kbd> — <b>Выделить рамкой:</b> обведите нужную область на экране, перевод отобразится прямо поверх слов.<br>
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">Ctrl</kbd> + <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">C</kbd> + <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#fbbf24;">C</kbd> — <b>Быстрый перевод из буфера:</b> мгновенный перевод выделенного фрагмента текста в окне.
</div>
</div>
        """)
        lbl_m2.setWordWrap(True)
        v_m2.addWidget(lbl_m2)
        layout.addWidget(box_m2)

        # Card 3: Module 3 Guide
        box_m3 = QGroupBox("📦 3. Голосовой переводчик (Voice Studio) — Микрофон (RU) ➔ Голос ИИ (EN)")
        box_m3.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #7c3aed;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #a78bfa;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_m3 = QVBoxLayout(box_m3)
        lbl_m3 = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<b>Назначение:</b> Вы говорите в микрофон по-русски — собеседники в Discord, Zoom, Telegram и веб-конференциях слышат плавную английскую речь вашим клонированным голосом.<br><br>

<b style="color: #a78bfa;">Конвейер синтеза речи (100% собственный автономный код):</b>
<ol style="margin: 6px 0 10px 18px; padding: 0;">
    <li><b>Русский слух (Sber GigaAM v3 CTC INT8):</b> Расшифровывает русскую речь за <b>~170 мс</b> без авторегрессионного ожидания.</li>
    <li><b>Умная пунктуация:</b> Алгоритм расставляет точки, вопросы и паузы в потоке слов для естественной интонации.</li>
    <li><b>Быстрый перевод (Helsinki Opus-MT INT8):</b> Переводит фразу на английский язык всего за <b>~15 мс</b>.</li>
    <li><b>Клонирование тембра (Kyutai Pocket-TTS 24kHz):</b> Синтезирует английскую речь за <b>~750 мс</b> по вашему 7-секундному образцу <code>my_pocket_voice.safetensors</code>.</li>
</ol>

<b style="color: #facc15;">Горячая клавиша:</b><br>
<div style="margin-top: 6px;">
• <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#a78bfa;">Shift</kbd> + <kbd style="background:#1e293b; border:1px solid #475569; padding:2px 7px; border-radius:4px; font-weight:bold; color:#a78bfa;">Колесико мыши</kbd> — <b>Режим рации (PTT):</b> зажмите, скажите фразу по-русски и отпустите. Перевод сразу пойдет в микрофон собеседникам.
</div>
</div>
        """)
        lbl_m3.setWordWrap(True)
        v_m3.addWidget(lbl_m3)
        layout.addWidget(box_m3)

        # Card 4: Audio Routing Guide (Topping vs Cable)
        box_audio = QGroupBox("🎛 4. Звуковая карта Topping E2x2: Шпаргалка настройки на века")
        box_audio.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #059669;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #34d399;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_audio = QVBoxLayout(box_audio)
        lbl_audio = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<b style="color: #34d399;">Правило 3 каналов (Как звук попадает собеседникам с задержкой 0 мс):</b><br><br>
<table border="0" cellpadding="8" style="background-color: #111827; border-radius: 6px; width: 100%; border: 1px solid #1f2937;">
<tr style="background-color: #1e293b; color: #ffffff;">
    <th align="left" style="width: 25%;">Где настраивать</th>
    <th align="left" style="width: 30%;">Что выбрать</th>
    <th align="left" style="width: 45%;">Физический смысл</th>
</tr>
<tr>
    <td><b>1. Windows звук</b></td>
    <td><code style="color: #38bdf8; font-weight: bold;">Playback 1/2</code></td>
    <td>Ваши обычные наушники (системный звук, медиа, речь собеседников).</td>
</tr>
<tr style="background-color: #161e2e;">
    <td><b>2. Наш Лаунчер</b></td>
    <td><code style="color: #a78bfa; font-weight: bold;">Playback 3/4</code></td>
    <td>Канал синтеза: голос ИИ бесшумно направляется в звуковую карту.</td>
</tr>
<tr>
    <td><b>3. Discord / Звонки</b></td>
    <td><b style="color: #34d399;">Loopback 1/2</b></td>
    <td><b>Микрофон:</b> звуковая карта Topping аппаратно смешивает ваш перевод и отдает в сеть за 0 мс!</td>
</tr>
</table><br>
<span style="color: #94a3b8;">* Если карта Topping отключена — выберите профиль <b>«Виртуальный кабель»</b>, и звук пойдет через драйвер VB-Audio Cable.</span>
</div>
        """)
        lbl_audio.setWordWrap(True)
        v_audio.addWidget(lbl_audio)
        layout.addWidget(box_audio)

        # Card 5: Upstream Update Safety
        box_safe = QGroupBox("🔒 5. Почему обновления авторов репозиториев никогда не сломают систему")
        box_safe.setStyleSheet("""
            QGroupBox {
                background-color: #16181d;
                border: 1px solid #2e3440;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #e5e9f0;
                padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        v_safe = QVBoxLayout(box_safe)
        lbl_safe = QLabel("""
<div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
<b>1. Автономный офлайн-принцип:</b> Наша система на 100% автономна. Лаунчер никогда не делает автоматических скрытых обновлений чужого кода из интернета. То, что настроено и отлажено, продолжит стабильно работать годами.<br><br>
<b>2. Защищенное хранилище CONFIG/:</b> Все ваши файлы настроек, слепок голоса и эталонные копии всех инженерных патчей изолированы в защищенной директории <code>CONFIG/</code>.<br><br>
<b>3. Если вы сами обновите чужой репозиторий:</b> Лаунчер проверит чек-суммы и код, подсветит красный статус <code>СЛЕТЕЛ</code>. Одно нажатие на кнопку <b>«🛠 Восстановить все патчи (1 клик)»</b> моментально вернет вшитые модули ускорения и патчи на место.
</div>
        """)
        lbl_safe.setWordWrap(True)
        v_safe.addWidget(lbl_safe)
        layout.addWidget(box_safe)

        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    # =========================================================================
    # Multilingual & Polling Logic
    # =========================================================================
    def _on_language_changed(self, idx: int):
        lang = self.combo_lang.currentData()
        I18n.set_language(lang)
        self._retranslate_ui()

    def _retranslate_ui(self, is_initial: bool = False):
        self.setWindowTitle(I18n.t("title"))
        self.btn_start_all.setText(I18n.t("start_all"))
        self.btn_stop_all.setText(I18n.t("stop_all"))

        self.tabs.setTabText(0, I18n.t("tab_dashboard"))
        self.tabs.setTabText(1, I18n.t("tab_patches"))
        self.tabs.setTabText(2, I18n.t("tab_guide"))

        self.card_stage1.retranslate()
        self.card_stage2.retranslate()
        self.card_stage3.retranslate()

        self.lbl_hw_title.setText(f"<b>{I18n.t('hardware_title')}</b>")
        self.btn_hub_topping.setText(I18n.t("hardware_topping"))
        self.btn_hub_cable.setText(I18n.t("hardware_cable"))
        self.btn_install_cable.setText(I18n.t("hardware_install_cable"))
        self.lbl_wiz_title.setText(f"<b>{I18n.t('wizard_title')}</b>")
        self.btn_launch_wizard.setText(I18n.t("btn_wizard"))
        self.lbl_wiz_desc.setText(I18n.t("wizard_desc"))

        self.lbl_patches_head.setText(f"<b>{I18n.t('patches_header')}</b>")
        self.btn_audit_refresh.setText(I18n.t("btn_audit_refresh"))
        self.btn_restore_patches.setText(I18n.t("btn_restore_patches"))
        self.btn_vault_folder.setText(I18n.t("btn_open_folder"))

        if not is_initial:
            self._populate_patches_view()
            self._refresh_all_latencies()
            self._poll_process_status()

    def _poll_process_status(self):
        # 1. Hot-reload pipeline latency chips if user altered models or settings in any program
        self._check_and_refresh_latencies_on_change()

        status = EcosystemProcessManager.get_stage_status()
        self.card_stage1.update_telemetry(status["stage_1"])
        self.card_stage2.update_telemetry(status["stage_2"])
        self.card_stage3.update_telemetry(status["stage_3"])

        # 2. Update real hardware & inference telemetry monitors for all modules
        m1 = None
        if status["stage_1"]["running"]:
            try:
                from launcher.telemetry import Stage1Telemetry
                m1 = Stage1Telemetry.get_live_metrics()
            except Exception as e:
                log.debug("Telemetry error: %s", e)
        self.card_stage1.update_card_monitor(m1)
        self.card_stage2.update_card_monitor()
        self.card_stage3.update_card_monitor()

        running_count = status.get("running_count", 0)
        total_ram = status.get("total_ram_mb", 0.0)
        total_cpu = status.get("total_cpu_pct", 0.0)

        if running_count == 3:
            self.lbl_system_summary.setText(f"🟢 {I18n.t('status_all_running').split('|')[0].strip()} | ОЗУ: {total_ram} МБ | ЦП: {total_cpu}% | VRAM: 0 MB")
            self.lbl_system_summary.setStyleSheet("color: #10b981; font-weight: bold; background-color: #064e3b; padding: 8px 12px; border-radius: 6px;")
        elif running_count > 0:
            self.lbl_system_summary.setText(f"🟡 {I18n.t('status_partial', count=running_count).split('|')[0].strip()} | ОЗУ: {total_ram} МБ | ЦП: {total_cpu}% | VRAM: 0 MB")
            self.lbl_system_summary.setStyleSheet("color: #facc15; font-weight: bold; background-color: #713f12; padding: 8px 12px; border-radius: 6px;")
        else:
            self.lbl_system_summary.setText(I18n.t("status_stopped"))
            self.lbl_system_summary.setStyleSheet("color: #9ca3af; font-weight: bold; background-color: #1f2937; padding: 8px 12px; border-radius: 6px;")

    def _on_open_voice_wizard(self):
        try:
            from launcher.voice_wizard import VoiceCloningWizard
        except ImportError:
            from voice_wizard import VoiceCloningWizard
        wiz = VoiceCloningWizard(self)
        wiz.exec()
        self._populate_patches_view()
        self._refresh_all_latencies()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #111214; }
            QWidget { color: #e5e7eb; font-family: 'Segoe UI', Arial, sans-serif; }
            QTabWidget::pane {
                border: 1px solid #2e3035;
                background-color: #16171a;
                border-radius: 6px;
            }
            QScrollArea {
                border: none;
                background-color: #16171a;
            }
            QTabBar::tab {
                background-color: #1f2125;
                color: #9ca3af;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #16171a;
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
                color: #60a5fa;
                font-weight: bold;
            }
            QComboBox {
                background-color: #212328;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 4px 10px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #4b5563; }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Translation Ecosystem Hub")
    hub = EcosystemHub()
    hub.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
