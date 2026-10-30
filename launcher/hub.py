"""Universal Real-Time Translation Hub & Ecosystem Orchestrator (PySide6).
Supports Trilingual UI (Russian, English, Chinese), 3-Stage Process Supervision,
Dynamic Pipeline Latency Monitoring per Stage, Modular 5-Patch Integrity Auditor,
and Embedded Stage 3 Hardware Audio Routing.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional

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
    """Calculates dynamic pipeline latency breakdown based on active model and routing choices."""

    @staticmethod
    def get_stage1_latency() -> Dict[str, Any]:
        """Inspect LiveTranslate user_settings.json for ASR and MT configuration."""
        settings_file = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate" / "user_settings.json"
        asr_name = "SenseVoice ASR"
        asr_ms = 170
        mt_name = "Hunyuan MT"
        mt_ms = 80
        is_cloud = False

        if settings_file.is_file():
            try:
                cfg = json.loads(settings_file.read_text(encoding="utf-8"))
                asr_eng = cfg.get("asr_engine", "sherpa_onnx")
                if "whisper" in asr_eng:
                    asr_name = "Whisper Local"
                    asr_ms = 900
                elif "remote" in asr_eng:
                    asr_name = "Whisper Cloud API"
                    asr_ms = 450
                    is_cloud = True

                models = cfg.get("models", [])
                active_idx = cfg.get("active_model", 0)
                if active_idx < len(models):
                    active_m = models[active_idx]
                    api_base = active_m.get("api_base", "local")
                    m_model = active_m.get("model", "")
                    if api_base == "local":
                        if "nllb" in m_model:
                            mt_name = "NLLB-200"
                            mt_ms = 280
                        else:
                            mt_name = "Hunyuan MT 1.8B"
                            mt_ms = 80
                    else:
                        mt_name = f"Облачный API ({active_m.get('name', 'Cloud')[:12]})"
                        mt_ms = 400
                        is_cloud = True
            except Exception as e:
                log.warning("Could not parse LiveTranslate settings: %s", e)

        total_ms = asr_ms + mt_ms
        return {
            "breakdown": f"{asr_name} ({asr_ms}мс) + {mt_name} ({mt_ms}мс)",
            "total_ms": total_ms,
            "is_cloud": is_cloud,
            "mode_text": I18n.t("latency_mode_cloud") if is_cloud else I18n.t("latency_mode_local"),
        }

    @staticmethod
    def get_stage2_latency() -> Dict[str, Any]:
        """Inspect OverTranslate configuration for OCR and provider choice."""
        settings_file = PROJECT_ROOT / "CONFIG" / "stage_2_screen" / "appsettings.json"
        ocr_name = "Windows OCR"
        ocr_ms = 35
        mt_name = "Локальный перевод"
        mt_ms = 50
        is_cloud = False

        if settings_file.is_file():
            try:
                cfg = json.loads(settings_file.read_text(encoding="utf-8"))
                provider = cfg.get("Provider", "Microsoft")
                if provider in ("OpenAI", "DeepL", "GoogleChrome"):
                    mt_name = f"Облачный {provider}"
                    mt_ms = 320
                    is_cloud = True
                else:
                    mt_name = "Windows Local"
                    mt_ms = 50
            except Exception as e:
                log.warning("Could not parse OverTranslate settings: %s", e)

        total_ms = ocr_ms + mt_ms
        return {
            "breakdown": f"{ocr_name} ({ocr_ms}мс) + {mt_name} ({mt_ms}мс)",
            "total_ms": total_ms,
            "is_cloud": is_cloud,
            "mode_text": I18n.t("latency_mode_cloud") if is_cloud else I18n.t("latency_mode_local"),
        }

    @staticmethod
    def get_stage3_latency(routing_mode: str = "topping") -> Dict[str, Any]:
        """Inspect Voice Studio configuration for ASR, MT, TTS, and Audio Routing."""
        asr_ms = 170  # Sber GigaAM CTC
        mt_ms = 15    # Helsinki Opus-MT
        tts_ms = 750  # Kyutai Pocket-TTS 24kHz

        if routing_mode == "topping":
            route_name = "Topping Loopback"
            route_ms = 0
            route_label = "0мс"
        else:
            route_name = "VB-Cable"
            route_ms = 15
            route_label = "15мс"

        total_ms = asr_ms + mt_ms + tts_ms + route_ms
        return {
            "breakdown": f"GigaAM ({asr_ms}мс) + Opus-MT ({mt_ms}мс) + Pocket-TTS ({tts_ms}мс) + {route_name} ({route_label})",
            "total_ms": total_ms,
            "is_cloud": False,
            "mode_text": I18n.t("latency_mode_local"),
        }


class StageCard(QFrame):
    """Visual pipeline flow, dynamic latency, and control card for a translation program."""

    def __init__(
        self,
        stage_id: str,
        title_key: str,
        flow_key: str,
        desc_key: str,
        on_start,
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
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_open = on_open
        self.open_label_key = open_label_key
        self._is_running = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
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

        # 2. Pipeline Flow Schema Banner
        self.lbl_flow = QLabel(I18n.t(self.flow_key))
        self.lbl_flow.setStyleSheet("""
            background-color: #111827;
            color: #38bdf8;
            font-size: 11px;
            font-weight: bold;
            padding: 6px 10px;
            border-radius: 5px;
            border: 1px solid #1f2937;
        """)
        layout.addWidget(self.lbl_flow)

        # 3. Plain Human Description
        self.lbl_desc = QLabel(I18n.t(self.desc_key))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #9ca3af; font-size: 11px; line-height: 1.3;")
        layout.addWidget(self.lbl_desc)

        # 4. Dynamic Pipeline Latency Monitor Bar
        self.lbl_latency = QLabel()
        self.lbl_latency.setStyleSheet("""
            background-color: #0f172a;
            color: #38bdf8;
            font-family: Consolas, monospace;
            font-size: 11px;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #1e293b;
        """)
        layout.addWidget(self.lbl_latency)

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

    def update_latency_display(self, lat_info: dict):
        prefix = I18n.t("latency_prefix")
        breakdown = lat_info.get("breakdown", "")
        total_ms = lat_info.get("total_ms", 0)
        mode_text = lat_info.get("mode_text", "")

        color = "#10b981" if total_ms < 400 else ("#facc15" if total_ms < 1100 else "#f87171")
        self.lbl_latency.setText(
            f"<b>{prefix}</b> {breakdown} ➔ <b style='color: {color};'>Итого: ~{total_ms} мс</b> "
            f"<span style='color: #64748b;'>[{mode_text}]</span>"
        )

    def retranslate(self):
        self.lbl_title.setText(f"<b>{I18n.t(self.title_key)}</b>")
        self.lbl_flow.setText(I18n.t(self.flow_key))
        self.lbl_desc.setText(I18n.t(self.desc_key))
        self.btn_start.setText(I18n.t("btn_start"))
        self.btn_stop.setText(I18n.t("btn_stop"))
        self.btn_open.setText(I18n.t(self.open_label_key))
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
        self.resize(1020, 820)
        self.setMinimumSize(940, 720)

        self._active_routing_mode = "topping"
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
        lat1 = LatencyEstimator.get_stage1_latency()
        self.card_stage1.update_latency_display(lat1)

        lat2 = LatencyEstimator.get_stage2_latency()
        self.card_stage2.update_latency_display(lat2)

        lat3 = LatencyEstimator.get_stage3_latency(self._active_routing_mode)
        self.card_stage3.update_latency_display(lat3)

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
        else:
            self.btn_hub_cable.setStyleSheet("background-color: #059669; color: #fff; font-weight: bold; border-radius: 4px; padding: 0 12px; border: 1px solid #34d399;")
            self.btn_hub_topping.setStyleSheet("background-color: #212328; color: #9ca3af; border-radius: 4px; padding: 0 12px; border: 1px solid #374151;")
            if not has_cable:
                self.btn_install_cable.show()
            else:
                self.btn_install_cable.hide()

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

        # Patch Health Quick Pill (Navigates to Tab 1)
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
        self.lbl_patch_quick.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
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
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. Module 1: LiveTranslate (Audio to Subtitles)
        self.card_stage1 = StageCard(
            "stage_1",
            "stage1_title", "stage1_flow", "stage1_desc",
            on_start=EcosystemProcessManager.start_stage_1,
            on_stop=EcosystemProcessManager.stop_stage_1,
            on_open=EcosystemProcessManager.start_stage_1,
            open_label_key="btn_open",
        )
        layout.addWidget(self.card_stage1)

        # 2. Module 2: OverTranslate (Screen OCR)
        self.card_stage2 = StageCard(
            "stage_2",
            "stage2_title", "stage2_flow", "stage2_desc",
            on_start=EcosystemProcessManager.start_stage_2,
            on_stop=EcosystemProcessManager.stop_stage_2,
            on_open=EcosystemProcessManager.start_stage_2,
            open_label_key="btn_open",
        )
        layout.addWidget(self.card_stage2)

        # 3. Module 3: Voice Studio (Outgoing Mic Speech)
        self.card_stage3 = StageCard(
            "stage_3",
            "stage3_title", "stage3_flow", "stage3_desc",
            on_start=EcosystemProcessManager.start_stage_3,
            on_stop=EcosystemProcessManager.stop_stage_3,
            on_open=EcosystemProcessManager.start_stage_3,
            open_label_key="btn_studio",
        )

        # EMBED Stage 3 Specific Controls (Audio Hardware Selector & Voice Wizard)
        self.card_stage3.stage3_container.show()
        h_stage3_hw = QHBoxLayout()
        h_stage3_hw.setSpacing(8)

        self.lbl_hw_title = QLabel(f"<b>{I18n.t('hardware_title')}</b>")
        self.lbl_hw_title.setStyleSheet("color: #e5e7eb; font-size: 11px;")
        h_stage3_hw.addWidget(self.lbl_hw_title)

        self.btn_hub_topping = QPushButton(I18n.t("hardware_topping"))
        self.btn_hub_topping.setFixedHeight(28)
        self.btn_hub_topping.clicked.connect(lambda: self._on_hub_switch_profile("topping"))
        h_stage3_hw.addWidget(self.btn_hub_topping)

        self.btn_hub_cable = QPushButton(I18n.t("hardware_cable"))
        self.btn_hub_cable.setFixedHeight(28)
        self.btn_hub_cable.clicked.connect(lambda: self._on_hub_switch_profile("cable"))
        h_stage3_hw.addWidget(self.btn_hub_cable)

        self.btn_install_cable = QPushButton(I18n.t("hardware_install_cable"))
        self.btn_install_cable.setFixedHeight(28)
        self.btn_install_cable.setStyleSheet("background-color: #0284c7; color: #fff; font-weight: bold; border-radius: 4px; padding: 0 10px; font-size: 11px;")
        self.btn_install_cable.clicked.connect(self._on_install_cable)
        self.btn_install_cable.hide()
        h_stage3_hw.addWidget(self.btn_install_cable)

        h_stage3_hw.addSpacing(10)

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
            }
            QPushButton:hover { background-color: #6366f1; }
        """)
        self.btn_launch_wizard.clicked.connect(self._on_open_voice_wizard)
        h_stage3_hw.addWidget(self.btn_launch_wizard)

        h_stage3_hw.addStretch()
        self.card_stage3.stage3_layout.addLayout(h_stage3_hw)

        layout.addWidget(self.card_stage3)

        # 4. Minimal Project Bottom Bar: Open Protected CONFIG Folder
        h_bottom = QHBoxLayout()
        h_bottom.setContentsMargins(4, 4, 4, 4)

        self.btn_open_folder = QPushButton(I18n.t("btn_open_folder"))
        self.btn_open_folder.setFixedHeight(32)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #1f2937;
                color: #94a3b8;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 14px;
                border: 1px solid #374151;
            }
            QPushButton:hover { background-color: #374151; color: #fff; }
        """)
        self.btn_open_folder.clicked.connect(self._on_open_config_folder)
        h_bottom.addWidget(self.btn_open_folder)

        h_bottom.addStretch()
        layout.addLayout(h_bottom)

        layout.addStretch()
        return w

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
        self.btn_audit_refresh.clicked.connect(self._populate_patches_view)
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

    def _populate_patches_view(self):
        audit = PatchIntegrityChecker.audit_all()
        modules = audit["modules"]

        # 1. Clear old widgets
        for layout in (self.v_m1, self.v_m2, self.v_m3, self.v_vault):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # 2. Populate Module 1
        for it in modules.get("stage_1", {}).get("items", []):
            self.v_m1.addWidget(self._render_patch_row(it))

        # 3. Populate Module 2
        for it in modules.get("stage_2", {}).get("items", []):
            self.v_m2.addWidget(self._render_patch_row(it))

        # 4. Populate Module 3
        for it in modules.get("stage_3", {}).get("items", []):
            self.v_m3.addWidget(self._render_patch_row(it))

        # 5. Populate Vault
        for it in modules.get("config", {}).get("items", []):
            self.v_vault.addWidget(self._render_patch_row(it))

        # 6. Update Summary Banner & Quick Header Pill
        if audit["all_passed"]:
            self.lbl_patches_summary.setText(f"🟢 Все 5 патчей активны (5/5) | Настройки и файлы в CONFIG/ защищены")
            self.lbl_patches_summary.setStyleSheet("background-color: #064e3b; color: #a7f3d0; padding: 10px 14px; border-radius: 6px; font-weight: bold; border: 1px solid #059669;")
            self.lbl_patch_quick.setText("🛡 5 Патчей активны (ОК)")
            self.lbl_patch_quick.setStyleSheet("background-color: #064e3b; color: #34d399; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; border-radius: 6px; padding: 0 12px; border: 1px solid #059669;")
        else:
            self.lbl_patches_summary.setText(I18n.t("patches_summary_fail"))
            self.lbl_patches_summary.setStyleSheet("background-color: #7f1d1d; color: #fecaca; padding: 10px 14px; border-radius: 6px; font-weight: bold; border: 1px solid #dc2626;")
            self.lbl_patch_quick.setText(f"🔴 Патчи: {audit['active_patches_count']}/5 (СЛЕТЕЛ)")
            self.lbl_patch_quick.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; border-radius: 6px; padding: 0 12px; border: 1px solid #dc2626;")

    def _on_restore_patches_clicked(self):
        res = PatchIntegrityChecker.restore_all_patches()
        self._populate_patches_view()
        if res["success"]:
            QMessageBox.information(
                self,
                "Успешное восстановление",
                f"Все 5 ключевых патчей и конфигурации успешно восстановлены из хранилища CONFIG/!\n\nВосстановлено файлов: {len(res['restored_files'])}.",
            )
        else:
            QMessageBox.critical(
                self,
                "Ошибка восстановления",
                f"Не удалось восстановить патчи:\n" + "\n".join(res["errors"]),
            )

    # =========================================================================
    # Tab 3: Plain-Human Architecture & Future Reference Guide
    # =========================================================================
    def _create_guide_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # Card 1: Module 1 Guide
        box_m1 = QGroupBox("1. Программа 1: Синхронные субтитры (LiveTranslate)")
        v_m1 = QVBoxLayout(box_m1)
        lbl_m1 = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b>Что делает:</b> Перехватывает любой системный звук из наушников (видео, онлайн-звонки, браузер, медиа) и выводит перевод субтитрами поверх экрана.<br><br>
<b>Как устроен поток данных:</b><br>
1. <b>Захват звука:</b> через системную петлю Windows WASAPI Loopback.<br>
2. <b>Распознавание речи:</b> локальная нейросеть <b>SenseVoice</b> расшифровывает голос всего за ~170 миллисекунд прямо на процессоре.<br>
3. <b>Перевод:</b> языковая модель <b>Tencent Hunyuan MT 1.8B</b> переводит фразу на русский язык.<br>
4. <b>Вывод:</b> прозрачные субтитры поверх всех окон.<br><br>
<b>Главные горячие клавиши:</b><br>
• <code style="color: #60a5fa; font-weight: bold;">F9</code> — Единый переключатель: мгновенно скрывает/показывает субтитры и ставит транскрипцию на паузу (чтобы не нагружать процессор в тишине).<br>
• <code style="color: #60a5fa; font-weight: bold;">2x Клик колесиком мыши (2x MMB)</code> — Режим клика сквозь окно (субтитры не мешают нажимать на кнопки под ними).<br>
• <code style="color: #60a5fa; font-weight: bold;">Зажать колесико мыши (MMB Drag)</code> — Перемещение субтитров в любую точку экрана без срыва левой кнопки.
</div>
        """)
        lbl_m1.setWordWrap(True)
        v_m1.addWidget(lbl_m1)
        layout.addWidget(box_m1)

        # Card 2: Module 2 Guide
        box_m2 = QGroupBox("2. Программа 2: Экранный переводчик по рамке (OverTranslate)")
        v_m2 = QVBoxLayout(box_m2)
        lbl_m2 = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b>Что делает:</b> Переводит невыделяемый текст на экране: из картинок, интерфейсов, документов, презентаций и окон программ.<br><br>
<b>Как пользоваться:</b><br>
• <code style="color: #60a5fa; font-weight: bold;">Ctrl + Alt + A</code> — Обвести прямоугольную область экрана рамкой мыши. Программа прочитает текст с пикселей и покажет перевод.<br>
• <code style="color: #60a5fa; font-weight: bold;">Ctrl + C + C</code> — Быстрый перевод любого скопированного слова из буфера обмена.<br><br>
<b>Почему работает мгновенно:</b> Использует встроенный движок оптического распознавания Windows OCR с нулевой нагрузкой на видеокарту.
</div>
        """)
        lbl_m2.setWordWrap(True)
        v_m2.addWidget(lbl_m2)
        layout.addWidget(box_m2)

        # Card 3: Module 3 Guide
        box_m3 = QGroupBox("3. Программа 3: Голосовой переводчик (Voice Studio)")
        v_m3 = QVBoxLayout(box_m3)
        lbl_m3 = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b>Что делает:</b> Вы говорите в микрофон по-русски — собеседники в любой программе связи слышат беглый английский перевод вашим клонированным тембром голоса.<br><br>
<b>Как устроен поток данных:</b><br>
1. <b>Рация PTT:</b> зажали <code style="color: #60a5fa; font-weight: bold;">Shift + Колесико мыши</code> и произнесли фразу по-русски.<br>
2. <b>Русский слух:</b> нейросеть <b>Sber GigaAM v3 CTC</b> моментально расшифровывает русскую речь.<br>
3. <b>Интонации и знаки:</b> движок автоматически восстанавливает паузы, вопросы и точки.<br>
4. <b>Английский перевод:</b> модель <b>Opus-MT</b> переводит смысл за 15 миллисекунд.<br>
5. <b>Клонирование голоса:</b> нейросеть <b>Kyutai Pocket-TTS</b> синтезирует английскую речь с вашим персональным тембром.<br>
6. <b>Выход в эфир:</b> звук отправляется в аппаратный Loopback звуковой карты Topping или в виртуальный кабель.
</div>
        """)
        lbl_m3.setWordWrap(True)
        v_m3.addWidget(lbl_m3)
        layout.addWidget(box_m3)

        # Card 4: Audio Routing Guide (Topping vs Cable)
        box_audio = QGroupBox("4. Звуковая карта Topping E2x2: Шпаргалка «Куда что нажимать» (На века)")
        v_audio = QVBoxLayout(box_audio)
        lbl_audio = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b style="color: #38bdf8;">Шпаргалка из 3 пунктов для идеального звука:</b><br>
<table border="0" cellpadding="8" style="background-color: #16171a; border-radius: 6px; width: 100%; border: 1px solid #2e3035;">
<tr style="background-color: #212328; color: #ffffff;">
    <th align="left">Где настраивать</th>
    <th align="left">Что выбрать</th>
    <th align="left">Простым языком: зачем это нужно</th>
</tr>
<tr>
    <td><b>1. Windows (Вывод звука)</b></td>
    <td><code style="color: #60a5fa; font-weight: bold;">Playback 1/2</code></td>
    <td>Ваши наушники: слышно музыку, видео, собеседников и тихий самоконтроль перевода.</td>
</tr>
<tr>
    <td><b>2. Наш Лаунчер (Этап 3)</b></td>
    <td><code style="color: #60a5fa; font-weight: bold;">Playback 3/4</code></td>
    <td>Канал озвучки: ИИ бесшумно шепчет английскую речь в карту Topping.</td>
</tr>
<tr>
    <td><b>3. Программа связи (Discord, Zoom, звонки)</b></td>
    <td><b style="color: #34d399;">Loopback 1/2 (Topping OTG)</b></td>
    <td><b>Микрофон:</b> карта Topping аппаратно смешивает ваш перевод и отправляет собеседникам с нулевой задержкой!</td>
</tr>
</table><br>
<b style="color: #facc15;">Если у вас обычный ПК без звуковой карты Topping:</b><br>
Нажмите кнопку <b>«Виртуальный кабель (VB-Audio Cable)»</b> на карточке Этапа 3. Лаунчер сам предложит установить драйвер виртуального кабеля в 1 клик.
</div>
        """)
        lbl_audio.setWordWrap(True)
        v_audio.addWidget(lbl_audio)
        layout.addWidget(box_audio)

        # Card 5: Upstream Update Safety
        box_safe = QGroupBox("5. Почему обновления авторов репозиториев никогда не сломают систему")
        v_safe = QVBoxLayout(box_safe)
        lbl_safe = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b>1. Автономный офлайн-принцип:</b> Наша система на 100% автономна. Лаунчер никогда не делает автоматических обновлений чужого кода из интернета. То, что работает сегодня, будет работать и через 5 лет.<br><br>
<b>2. Защищенное хранилище CONFIG/:</b> Все ваши настройки, образец голоса и эталонные копии 5 патчей изолированы в защищенной директории <code>CONFIG/</code>.<br><br>
<b>3. Если вы сами обновите чужой репозиторий:</b> Лаунчер сразу покажет красный статус <code>СЛЕТЕЛ</code>. Одно нажатие на кнопку <b>«🛠 Восстановить все 5 патчей»</b> вернет все файлы на место за 0.1 секунды.
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
        self.btn_launch_wizard.setText(I18n.t("btn_wizard"))
        self.btn_open_folder.setText(I18n.t("btn_open_folder"))

        self.lbl_patches_head.setText(f"<b>{I18n.t('patches_header')}</b>")
        self.btn_audit_refresh.setText(I18n.t("btn_audit_refresh"))
        self.btn_restore_patches.setText(I18n.t("btn_restore_patches"))
        self.btn_vault_folder.setText(I18n.t("btn_open_folder"))

        if not is_initial:
            self._populate_patches_view()
            self._refresh_all_latencies()
            self._poll_process_status()

    def _poll_process_status(self):
        status = EcosystemProcessManager.get_stage_status()
        self.card_stage1.update_telemetry(status["stage_1"])
        self.card_stage2.update_telemetry(status["stage_2"])
        self.card_stage3.update_telemetry(status["stage_3"])

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
