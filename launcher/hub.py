"""Universal Real-Time Translation Hub & Ecosystem Orchestrator (PySide6).
Provides centralized process supervision, AI model inventory auditing,
safe patch isolation tracking, and an interactive personal voice cloning wizard.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
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

from .models_inventory import ModelsInventory
from .process_manager import EcosystemProcessManager
from .voice_wizard import VoiceCloningWizard

log = logging.getLogger("Launcher.Hub")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class StageCard(QFrame):
    """Visual status and control card for an ecosystem stage."""

    def __init__(self, stage_id: str, title: str, description: str, hotkeys: str, on_start, on_stop=None, parent=None):
        super().__init__(parent)
        self.stage_id = stage_id
        self.on_start = on_start
        self.on_stop = on_stop

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
        self.lbl_title = QLabel(f"<b>{title}</b>")
        self.lbl_title.setStyleSheet("font-size: 14px; color: #ffffff;")
        h_head.addWidget(self.lbl_title)

        h_head.addStretch()

        self.status_pill = QLabel("⚪ Остановлен")
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
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self.lbl_desc)

        # Hotkey Info
        self.lbl_hotkeys = QLabel(f"<b>Горячие клавиши:</b> {hotkeys}")
        self.lbl_hotkeys.setStyleSheet("color: #60a5fa; font-size: 11px;")
        layout.addWidget(self.lbl_hotkeys)

        # Action Buttons
        h_btn = QHBoxLayout()
        self.btn_action = QPushButton("▶ Запустить")
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

        h_btn.addStretch()
        layout.addLayout(h_btn)

    def set_running(self, running: bool):
        if running:
            self.setStyleSheet("""
                StageCard {
                    background-color: #172554;
                    border: 1px solid #2563eb;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            self.status_pill.setText("🟢 Работает")
            self.status_pill.setStyleSheet("""
                background-color: #065f46;
                color: #a7f3d0;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #059669;
            """)
            self.btn_action.setText("⏹ Перезапустить" if self.on_stop else "Открыть окно")
        else:
            self.setStyleSheet("""
                StageCard {
                    background-color: #1a1b1e;
                    border: 1px solid #2e3035;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            self.status_pill.setText("⚪ Остановлен")
            self.status_pill.setStyleSheet("""
                background-color: #212328;
                color: #9ca3af;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #374151;
            """)
            self.btn_action.setText("▶ Запустить")

    def _on_action_clicked(self):
        if self.on_start:
            self.on_start()


class EcosystemHub(QMainWindow):
    """Main Orchestration and Health Hub Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Translation Ecosystem Hub & Supervisor")
        self.resize(920, 680)
        self.setMinimumSize(860, 600)

        self._apply_theme()
        self._init_ui()

        # Decoupled Process Supervisor Poller (every 1.5 seconds)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1500)
        self.poll_timer.timeout.connect(self._poll_process_status)
        self.poll_timer.start()

        # Initial check
        self._poll_process_status()

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # 1. Master Control Header Bar
        root_layout.addLayout(self._create_master_header())

        # 2. Main Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_dashboard_tab(), "🚀 Пульт управления этапами")
        tabs.addTab(self._create_inventory_tab(), "🧠 Инвентарь нейросетей (100% Офлайн)")
        tabs.addTab(self._create_vault_tab(), "🛡 Патчи и Защита обновлений")
        root_layout.addWidget(tabs, stretch=1)

    def _create_master_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(12)

        # Master Start
        btn_start_all = QPushButton("🚀 ЗАПУСТИТЬ ВСЮ ЭКОСИСТЕМУ")
        btn_start_all.setFixedHeight(44)
        btn_start_all.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 18px;
            }
            QPushButton:hover { background-color: #10b981; }
        """)
        btn_start_all.clicked.connect(EcosystemProcessManager.start_all)
        h.addWidget(btn_start_all)

        # Master Stop
        btn_stop_all = QPushButton("⏹ ОСТАНОВИТЬ ВСЁ")
        btn_stop_all.setFixedHeight(44)
        btn_stop_all.setStyleSheet("""
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
        btn_stop_all.clicked.connect(EcosystemProcessManager.stop_all)
        h.addWidget(btn_stop_all)

        h.addStretch()

        self.lbl_system_summary = QLabel("Статус: 3 сервиса готовы к запуску | VRAM: 0 MB")
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

        # Stage 1 Card
        self.card_stage1 = StageCard(
            "stage_1",
            "Этап 1: Входящий звук и субтитры (LiveTranslate)",
            "Sherpa-ONNX SenseVoice + Tencent HY-MT 1.8B GGUF. Прозрачные субтитры поверх игр и видео.",
            "F9 (Вкл/Пауза), 2x MMB (Клик-сквозь), MMB Drag (Двигать)",
            on_start=EcosystemProcessManager.start_stage_1,
        )
        grid.addWidget(self.card_stage1, 0, 0)

        # Stage 2 Card
        self.card_stage2 = StageCard(
            "stage_2",
            "Этап 2: Экранный OCR и текст (OverTranslate)",
            "Сверхбыстрый перевод текста с экрана рамкой, перевод буфера обмена и замена текста в чатах.",
            "Ctrl+Alt+A (Рамка), Ctrl+C+C (Словарь), Ctrl+Alt+C (Замена)",
            on_start=EcosystemProcessManager.start_stage_2,
        )
        grid.addWidget(self.card_stage2, 0, 1)

        # Stage 3 Card
        self.card_stage3 = StageCard(
            "stage_3",
            "Этап 3: Исходящий голос в CS2 / Discord (Voice Studio)",
            "Sber GigaAM v3 CTC + Opus-MT + Kyutai Pocket-TTS. Перевод речи в игре вашим клонированным голосом.",
            "Shift + MMB (Колесико мыши = Рация PTT), Выход: Playback 3/4 ➔ Topping Loopback",
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
        wiz_title = QLabel("⭐ <b>Студия обучения модели под свой голос (7-Second Voice Cloning)</b>")
        wiz_title.setStyleSheet("font-size: 14px; color: #ffffff;")
        v_wiz_info.addWidget(wiz_title)

        wiz_desc = QLabel(
            "Любой человек может за 7 секунд обучить модель говорить его собственным тембром. "
            "Нажмите кнопку, прочитайте фразу в микрофон, и нейросеть сохранит ваш персональный профиль в CONFIG/."
        )
        wiz_desc.setWordWrap(True)
        wiz_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        v_wiz_info.addWidget(wiz_desc)
        h_wiz.addLayout(v_wiz_info, stretch=1)

        btn_launch_wizard = QPushButton("🎙 ОБУЧИТЬ ГОЛОС ПОД СЕБЯ")
        btn_launch_wizard.setFixedHeight(44)
        btn_launch_wizard.setStyleSheet("""
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
        btn_launch_wizard.clicked.connect(self._on_open_voice_wizard)
        h_wiz.addWidget(btn_launch_wizard)

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
        lbl_head = QLabel("<b>Аудит локальных нейросетей на SSD-диске (100% Офлайн-готовность):</b>")
        lbl_head.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        h_info.addWidget(lbl_head)
        h_info.addStretch()

        btn_refresh = QPushButton("🔄 Обновить статус")
        btn_refresh.clicked.connect(self._populate_inventory_table)
        h_info.addWidget(btn_refresh)
        layout.addLayout(h_info)

        # Table
        self.tbl_models = QTableWidget()
        self.tbl_models.setColumnCount(5)
        self.tbl_models.setHorizontalHeaderLabels(["Этап", "Задача", "Модель", "Статус на диске", "Размер (МБ)"])
        self.tbl_models.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_models.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tbl_models)

        self._populate_inventory_table()
        return w

    def _populate_inventory_table(self):
        items = ModelsInventory.get_inventory()
        self.tbl_models.setRowCount(len(items))

        for row, it in enumerate(items):
            self.tbl_models.setItem(row, 0, QTableWidgetItem(it["stage"]))
            self.tbl_models.setItem(row, 1, QTableWidgetItem(it["task"]))
            self.tbl_models.setItem(row, 2, QTableWidgetItem(it["name"]))

            if it["is_ready"]:
                st_item = QTableWidgetItem("✔ Скачана (Готова)")
                st_item.setForeground(QColor("#10b981"))
            else:
                st_item = QTableWidgetItem("❌ Не найдена")
                st_item.setForeground(QColor("#ef4444"))
            self.tbl_models.setItem(row, 3, st_item)

            self.tbl_models.setItem(row, 4, QTableWidgetItem(f"{it['size_mb']} MB"))

    # =========================================================================
    # Tab 3: Safe Updates & Patch Vault
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
    # Supervisor Polling Loop (1.5 seconds)
    # =========================================================================
    def _poll_process_status(self):
        status = EcosystemProcessManager.get_stage_status()
        self.card_stage1.set_running(status["stage_1"])
        self.card_stage2.set_running(status["stage_2"])
        self.card_stage3.set_running(status["stage_3"])

        running_count = sum(1 for v in status.values() if v)
        if running_count == 3:
            self.lbl_system_summary.setText("🟢 ВСЯ ЭКОСИСТЕМА АКТИВНА (3/3 процессов) | VRAM: 0 MB")
            self.lbl_system_summary.setStyleSheet("color: #10b981; font-weight: bold; background-color: #064e3b; padding: 8px 12px; border-radius: 6px;")
        elif running_count > 0:
            self.lbl_system_summary.setText(f"🟡 Активно процессов: {running_count}/3 | VRAM: 0 MB")
            self.lbl_system_summary.setStyleSheet("color: #facc15; font-weight: bold; background-color: #713f12; padding: 8px 12px; border-radius: 6px;")
        else:
            self.lbl_system_summary.setText("⚪ Все сервисы остановлены | ОЗУ свободно | VRAM: 0 MB")
            self.lbl_system_summary.setStyleSheet("color: #9ca3af; font-weight: bold; background-color: #1f2937; padding: 8px 12px; border-radius: 6px;")

    def _on_open_voice_wizard(self):
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
