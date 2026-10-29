"""Universal Real-Time Translation Hub & Ecosystem Orchestrator (PySide6).
Supports Trilingual UI (Russian, English, Chinese), AI Models Storage Audit,
Process Lifecycle Supervision, and Architecture / Signal Flow Guide.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import sys
from typing import Dict, List

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
    from launcher.models_inventory import ModelsInventory
    from launcher.process_manager import EcosystemProcessManager
except ImportError:
    from i18n import I18n
    from models_inventory import ModelsInventory
    from process_manager import EcosystemProcessManager

log = logging.getLogger("Launcher.Hub")


class StageCard(QFrame):
    """Visual status and control card for an ecosystem stage."""

    def __init__(self, stage_id: str, title_key: str, desc_key: str, hotkeys_key: str, on_start, on_stop=None, parent=None):
        super().__init__(parent)
        self.stage_id = stage_id
        self.title_key = title_key
        self.desc_key = desc_key
        self.hotkeys_key = hotkeys_key
        self.on_start = on_start
        self.on_stop = on_stop
        self._is_running = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            StageCard {
                background-color: #1a1b1e;
                border: 1px solid #2e3035;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Header Row: Title + Status Pill
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

        # Description
        self.lbl_desc = QLabel(I18n.t(self.desc_key))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self.lbl_desc)

        # Hotkey Info
        self.lbl_hotkeys = QLabel(f"<b>Горячие клавиши:</b> {I18n.t(self.hotkeys_key)}")
        self.lbl_hotkeys.setStyleSheet("color: #60a5fa; font-size: 11px;")
        layout.addWidget(self.lbl_hotkeys)

        # Action Buttons and Live Telemetry
        h_btn = QHBoxLayout()
        self.btn_action = QPushButton(I18n.t("btn_start"))
        self.btn_action.setFixedHeight(30)
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #3b82f6; }
        """)
        self.btn_action.clicked.connect(self._on_action_clicked)
        h_btn.addWidget(self.btn_action)

        # Resource Telemetry Badge
        self.lbl_telemetry = QLabel(I18n.t("res_stopped"))
        self.lbl_telemetry.setStyleSheet("""
            color: #9ca3af;
            font-family: Consolas, monospace;
            font-size: 11px;
            background-color: #1f2937;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #374151;
        """)
        h_btn.addWidget(self.lbl_telemetry)

        h_btn.addStretch()
        layout.addLayout(h_btn)

        self._last_metrics = {"running": False, "ram_mb": 0.0, "cpu_pct": 0.0, "pid": None}

    def retranslate(self):
        self.lbl_title.setText(f"<b>{I18n.t(self.title_key)}</b>")
        self.lbl_desc.setText(I18n.t(self.desc_key))
        self.lbl_hotkeys.setText(f"<b>{I18n.t('hotkeys_label')}</b> {I18n.t(self.hotkeys_key)}")
        self.update_telemetry(self._last_metrics, force=True)

    def update_telemetry(self, data: Dict[str, Any], force: bool = False):
        self._last_metrics = data
        running = data.get("running", False)
        self.set_running(running, force=force)

        if running:
            ram = data.get("ram_mb", 0.0)
            cpu = data.get("cpu_pct", 0.0)
            pid = data.get("pid", "-")
            self.lbl_telemetry.setText(I18n.t("res_metrics", ram=ram, cpu=cpu, pid=pid))
            self.lbl_telemetry.setStyleSheet("""
                color: #34d399;
                font-family: Consolas, monospace;
                font-size: 11px;
                background-color: #064e3b;
                padding: 4px 8px;
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
                padding: 4px 8px;
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
                    background-color: #172554;
                    border: 1px solid #2563eb;
                    border-radius: 8px;
                    padding: 10px;
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
            self.btn_action.setText(I18n.t("btn_open") if "3" in self.stage_id else I18n.t("btn_start"))
        else:
            self.setStyleSheet("""
                StageCard {
                    background-color: #1a1b1e;
                    border: 1px solid #2e3035;
                    border-radius: 8px;
                    padding: 10px;
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
            self.btn_action.setText(I18n.t("btn_start"))

    def _on_action_clicked(self):
        if self.on_start:
            self.on_start()


class EcosystemHub(QMainWindow):
    """Main Orchestration, Multilingual Control, and Health Hub Window."""

    def __init__(self):
        super().__init__()
        self.resize(940, 720)
        self.setMinimumSize(880, 640)

        self._apply_theme()
        self._init_ui()
        self._retranslate_ui(is_initial=True)

        # Decoupled Process Supervisor Poller (every 2.0 seconds)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2000)
        self.poll_timer.timeout.connect(self._poll_process_status)

        # Defer disk inventory scan and process checking to after window renders
        QTimer.singleShot(40, self._initial_load)

    def _initial_load(self):
        """Runs right after GUI window appears on screen for instant startup."""
        self._poll_process_status()
        self.poll_timer.start()
        self._populate_inventory_table()

    def closeEvent(self, event):
        self.poll_timer.stop()
        super().closeEvent(event)

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # 1. Master Control Header Bar with Language Switcher
        root_layout.addLayout(self._create_master_header())

        # 2. Main Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_dashboard_tab(), "🚀 Dashboard")
        self.tabs.addTab(self._create_inventory_tab(), "🧠 Models Inventory")
        self.tabs.addTab(self._create_guide_tab(), "📖 Architecture & Models Guide")
        self.tabs.addTab(self._create_vault_tab(), "🛡 Vault & Patches")
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
    # Tab 1: Ecosystem Dashboard & Voice Wizard
    # =========================================================================
    def _create_dashboard_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Stage Cards Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_stage1 = StageCard(
            "stage_1",
            "stage1_title", "stage1_desc", "stage1_hotkeys",
            on_start=EcosystemProcessManager.start_stage_1,
        )
        grid.addWidget(self.card_stage1, 0, 0)

        self.card_stage2 = StageCard(
            "stage_2",
            "stage2_title", "stage2_desc", "stage2_hotkeys",
            on_start=EcosystemProcessManager.start_stage_2,
        )
        grid.addWidget(self.card_stage2, 0, 1)

        self.card_stage3 = StageCard(
            "stage_3",
            "stage3_title", "stage3_desc", "stage3_hotkeys",
            on_start=EcosystemProcessManager.start_stage_3,
        )
        grid.addWidget(self.card_stage3, 1, 0, 1, 2)

        layout.addLayout(grid)

        # Voice Wizard Hero Card
        wiz_frame = QFrame()
        wiz_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e1b4b, stop:1 #1e293b);
                border: 1px solid #6366f1;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        h_wiz = QHBoxLayout(wiz_frame)
        h_wiz.setSpacing(16)

        v_wiz_info = QVBoxLayout()
        self.lbl_wiz_title = QLabel()
        self.lbl_wiz_title.setStyleSheet("font-size: 14px; color: #ffffff;")
        v_wiz_info.addWidget(self.lbl_wiz_title)

        self.lbl_wiz_desc = QLabel()
        self.lbl_wiz_desc.setWordWrap(True)
        self.lbl_wiz_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        v_wiz_info.addWidget(self.lbl_wiz_desc)
        h_wiz.addLayout(v_wiz_info, stretch=1)

        self.btn_launch_wizard = QPushButton()
        self.btn_launch_wizard.setFixedHeight(44)
        self.btn_launch_wizard.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #6366f1; }
        """)
        self.btn_launch_wizard.clicked.connect(self._on_open_voice_wizard)
        h_wiz.addWidget(self.btn_launch_wizard)

        layout.addWidget(wiz_frame)
        layout.addStretch()
        return w

    # =========================================================================
    # Tab 2: AI Models Inventory (100% Offline)
    # =========================================================================
    def _create_inventory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header Info
        h_info = QHBoxLayout()
        self.lbl_inv_head = QLabel()
        self.lbl_inv_head.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        h_info.addWidget(self.lbl_inv_head)
        h_info.addStretch()

        self.btn_refresh = QPushButton()
        self.btn_refresh.clicked.connect(self._populate_inventory_table)
        h_info.addWidget(self.btn_refresh)
        layout.addLayout(h_info)

        # Table
        self.tbl_models = QTableWidget()
        self.tbl_models.setColumnCount(5)
        self.tbl_models.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_models.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tbl_models)
        return w

    def _populate_inventory_table(self):
        self.tbl_models.setHorizontalHeaderLabels([
            I18n.t("col_stage"), I18n.t("col_task"), I18n.t("col_model"),
            I18n.t("col_status"), I18n.t("col_size")
        ])
        items = ModelsInventory.get_inventory()
        self.tbl_models.setRowCount(len(items))

        for row, it in enumerate(items):
            self.tbl_models.setItem(row, 0, QTableWidgetItem(it["stage"]))
            self.tbl_models.setItem(row, 1, QTableWidgetItem(it["task"]))
            self.tbl_models.setItem(row, 2, QTableWidgetItem(it["name"]))

            if it["is_ready"]:
                st_item = QTableWidgetItem(I18n.t("ready"))
                st_item.setForeground(QColor("#10b981"))
            else:
                st_item = QTableWidgetItem(I18n.t("missing"))
                st_item.setForeground(QColor("#ef4444"))
            self.tbl_models.setItem(row, 3, st_item)

            self.tbl_models.setItem(row, 4, QTableWidgetItem(f"{it['size_mb']} MB"))

    # =========================================================================
    # Tab 3: Architecture & Models Guide (Pedagogical Overview)
    # =========================================================================
    def _create_guide_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # Signal Flow Diagram Box
        flow_box = QGroupBox("1. Схема движения звуковых потоков и OCR (Signal Flow Diagram)")
        v_flow = QVBoxLayout(flow_box)
        diag = QLabel("""
<pre style="font-family: Consolas, monospace; color: #a7f3d0; font-size: 11px;">
[ВХОДЯЩИЙ ЗВУК ИГР / СТРИМОВ (RU, EN, ZH)]
    │
    ▼ (WASAPI Loopback)
[Этап 1: LiveTranslate] ──► [SenseVoice ASR (170ms)] ──► [HY-MT 1.8B GGUF (80ms)] ──► [ПРОЗРАЧНЫЕ СУБТИТРЫ]

[ЭКРАННЫЙ ТЕКСТ / ИГРЫ (RU, EN, ZH)]
    │
    ▼ (Ctrl + Alt + A)
[Этап 2: OverTranslate] ──► [Windows OCR / Paddle] ──► [Переводчик] ──► [Окно перевода / Замена в чате]

[ИСХОДЯЩИЙ ГОЛОС В CS2 / DISCORD]
    │
    ▼ (Микрофон NVIDIA Broadcast)
[Этап 3: Voice Studio] ──► [GigaAM v3 CTC (170ms)] ──► [Opus-MT (15ms)] ──► [Pocket-TTS Клон (800ms)]
                                                                               │
                                                                               ▼
                                                                     [Topping Playback 3/4]
                                                                               │
                                                                      (Аппаратный Loopback)
                                                                               │
                                                                               ▼
                                                                     [Микрофон CS2 и Discord]
                                                                     Тиммейты слышат ваш английский!
</pre>
        """)
        v_flow.addWidget(diag)
        layout.addWidget(flow_box)

        # Detailed Models Explanations Box
        models_box = QGroupBox("2. Как работают наши нейросети под капотом (Model Technology Breakdown)")
        v_models = QVBoxLayout(models_box)

        models_info = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b>1. Sber GigaAM v3 CTC (Sherpa-ONNX INT8, ~214 MB):</b><br>
Конформерная архитектура (Conformer = CNN + Self-Attention) для моментального распознавания русской речи. 
Благодаря CTC-декодированию (Connectionist Temporal Classification) не тратит время на авторегрессионный цикл и работает за <b>~170 мс на 2 ядрах CPU</b>.<br><br>

<b>2. Tencent Hunyuan MT 1.8B (GGUF INT4, ~1080 MB):</b><br>
Современная языковая модель перевода от Tencent, квантованная до 4 бит. Специально оптимизирована для живых диалогов, игрового сленга и триады языков: <b>Русский ⇄ Английский ⇄ Китайский</b>.<br><br>

<b>3. Helsinki Opus-MT (CTranslate2 INT8, ~146 MB):</b><br>
Ультра-легковесный трансформер MarianMT, оптимизированный в движке CTranslate2. Переводит тактические команды CS2 с русского на английский всего за <b>14–18 миллисекунд</b> с нулевой нагрузкой на GPU.<br><br>

<b>4. Kyutai Pocket-TTS & Mimi Codec (Mimi + Flow Matching, ~320 MB):</b><br>
Нейросеть последнего поколения (Kyutai 2025–2026). Использует 24 кГц нейронный аудиокодек <b>Mimi</b> и диффузионный поток <b>Flow Matching</b>. В отличие от старых XTTS-v2, она не роботит, не заикается и клонирует тембр всего по 7-секундному образцу голоса прямо на обычном процессоре за ~800 мс!
</div>
        """)
        models_info.setWordWrap(True)
        v_models.addWidget(models_info)
        layout.addWidget(models_box)

        # Section 3: Topping E2x2 Loopback Guide (Forget-Proof Standard)
        loopback_box = QGroupBox("3. Звуковая карта Topping E2x2: Как устроен Loopback и что выбрать в Discord (Шпаргалка на века)")
        v_loopback = QVBoxLayout(loopback_box)
        loopback_info = QLabel("""
<div style="font-size: 12px; line-height: 1.5; color: #cbd5e1;">
<b style="color: #38bdf8; font-size: 13px;">Что такое Loopback простыми словами?</b><br>
<b>Loopback (аппаратная петля)</b> — это встроенный в звуковую карту Topping «провод-невидимка». Он аппаратно перенаправляет любой звук, отправленный в канал <b>Playback 3/4</b>, прямо во вход виртуального микрофона <b>Loopback 1/2</b> со скоростью света (0 мс задержки) и с 0% нагрузки на процессор.<br><br>

<b style="color: #a7f3d0; font-size: 13px;">Шпаргалка: Куда что нажимать в Windows и Discord (За 30 секунд):</b><br>
<table border="0" cellpadding="8" style="background-color: #16171a; border-radius: 6px; width: 100%; border: 1px solid #2e3035;">
<tr style="background-color: #212328; color: #ffffff;">
    <th align="left">Программа / Место</th>
    <th align="left">Что выбрать в настройках звука</th>
    <th align="left">Зачем это нужно</th>
</tr>
<tr>
    <td><b>1. Windows (Вывод звука)</b></td>
    <td><code style="color: #60a5fa; font-weight: bold;">Playback 1/2</code></td>
    <td>Обычный звук: вы слышите игру, музыку, тиммейтов и свой перевод в наушниках.</td>
</tr>
<tr>
    <td><b>2. Наш Лаунчер (Этап 3)</b></td>
    <td><code style="color: #60a5fa; font-weight: bold;">Вывод ➔ Playback 3/4</code></td>
    <td>Канал озвучки: ИИ бесшумно отправляет сгенерированный английский голос в карту Topping.</td>
</tr>
<tr>
    <td><b>3. Discord / CS2 / Telegram</b></td>
    <td><b style="color: #34d399; font-size: 13px;">Loopback 1/2 (Topping E2x2 OTG)</b></td>
    <td><b>Самое главное!</b> Микрофон в игре, через который тиммейты слышат ваш чистый перевод!</td>
</tr>
</table><br>

<b style="color: #facc15; font-size: 12px;">Почему эта схема вечная и не ломается:</b><br>
Вам не нужны виртуальные кабели (типа VB-Audio Cable), которые постоянно слетают при обновлениях Windows и дают задержку 100+ мс. 
Всё смешивание делает сам чип Topping на уровне железа. Даже если через год вы переустановите систему, достаточно просто запустить START.bat и выбрать эти 3 пункта!
</div>
        """)
        loopback_info.setWordWrap(True)
        v_loopback.addWidget(loopback_info)
        layout.addWidget(loopback_box)

        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    # =========================================================================
    # Tab 4: Safe Updates & Patch Vault
    # =========================================================================
    def _create_vault_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        box_vault = QGroupBox("Защита настроек и патчей от обновлений авторов (CONFIG Vault)")
        v_vault = QVBoxLayout(box_vault)

        v_vault.addWidget(QLabel("<b>Почему наши доработки никогда не потеряются при выходе обновлений:</b>"))
        desc = QLabel(
            "1. <b>Изолированное хранилище `CONFIG/`</b>: Все ваши индивидуальные профили (клонированный голос, "
            "настройки карты Topping, задержки VAD) хранятся в защищенной директории, отделенной от чужих репозиториев.<br>"
            "2. <b>Независимая Студия</b>: Наша Студия (`stage_3_voice/studio/`) использует чистые API нейросетей, "
            "поэтому любые внешние изменения чужих интерфейсов не ломают наш голосовой перевод.<br>"
            "3. <b>Git Invariant</b>: Все доработки зафиксированы в изолированной ветке <code>feature/stage3-audio-routing</code>."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        v_vault.addWidget(desc)
        layout.addWidget(box_vault)

        # Topping Checklist Box
        box_topping = QGroupBox("Памятка по настройке звука в Windows и играх (Topping E2x2)")
        v_top = QVBoxLayout(box_topping)
        top_txt = QLabel(
            "• <b>Микрофон в Windows / Discord / CS2</b>: установите <code>Loopback 1/2 (6- E2x2 OTG)</code>.<br>"
            "• <b>Вывод перевода</b>: Студия отправляет английский голос в <code>Playback 3/4</code> (Topping аппаратно перенаправляет в Loopback 1/2).<br>"
            "• <b>Наушники</b>: слушайте игру в <code>Playback 1/2</code> (слышен чистый звук игры + тихий самоконтроль своего английского голоса)."
        )
        top_txt.setWordWrap(True)
        top_txt.setStyleSheet("color: #93c5fd; font-size: 12px;")
        v_top.addWidget(top_txt)
        layout.addWidget(box_topping)

        layout.addStretch()
        return w

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
        self.tabs.setTabText(1, I18n.t("tab_inventory"))
        self.tabs.setTabText(2, I18n.t("tab_guide"))
        self.tabs.setTabText(3, I18n.t("tab_vault"))

        self.card_stage1.retranslate()
        self.card_stage2.retranslate()
        self.card_stage3.retranslate()

        self.lbl_wiz_title.setText(f"<b>{I18n.t('wizard_hero_title')}</b>")
        self.lbl_wiz_desc.setText(I18n.t("wizard_hero_desc"))
        self.btn_launch_wizard.setText(I18n.t("btn_wizard"))

        self.lbl_inv_head.setText(f"<b>{I18n.t('inventory_header')}</b>")
        self.btn_refresh.setText(I18n.t("btn_refresh"))

        if not is_initial:
            self._populate_inventory_table()
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
        self._populate_inventory_table()

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
                padding: 8px 16px;
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
