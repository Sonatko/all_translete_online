"""Universal In-App 1-Click Update System for Translation Ecosystem.
Provides non-blocking background update checks (Git & GitHub API),
graceful process draining (stops active stages to avoid Windows Error 32 sharing violations),
atomic git pull / patch re-injection, and instant seamless app restart.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Optional, Tuple

from PySide6.QtCore import QObject, QProcess, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from launcher.i18n import I18n
from launcher.process_manager import EcosystemProcessManager

log = logging.getLogger("Launcher.Updater")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / "stage_3_voice" / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.is_file():
    PYTHON_EXE = Path(sys.executable)


def get_current_commit_info() -> Tuple[str, str]:
    """Retrieve current short commit hash and commit subject."""
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%h|%s"],
            cwd=str(PROJECT_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        ).strip()
        parts = out.split("|", 1)
        return (parts[0], parts[1] if len(parts) > 1 else "")
    except Exception:
        return ("portable", "Production Release")


class UpdateCheckerWorker(QThread):
    """Asynchronous background worker checking for remote updates without GUI latency."""

    update_available = Signal(int, list)  # count, list of commit subjects
    up_to_date = Signal(str)             # current hash
    check_failed = Signal(str)           # error description

    def run(self):
        try:
            # 1. Check if git repo exists
            git_dir = PROJECT_ROOT / ".git"
            if not git_dir.is_dir():
                self.up_to_date.emit("standalone")
                return

            # 2. Fetch origin main with a short timeout to prevent hang behind strict firewalls
            curr_hash, _ = get_current_commit_info()
            fetch_res = subprocess.run(
                ["git", "fetch", "--quiet", "origin", "main"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=12,
            )

            # 3. Check commit difference
            count_res = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=4,
            )
            count_str = count_res.stdout.strip()
            count = int(count_str) if count_str.isdigit() else 0

            if count > 0:
                log_res = subprocess.run(
                    ["git", "log", "HEAD..origin/main", "--oneline", "-n", "10"],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=4,
                )
                commits = [line.strip() for line in log_res.stdout.splitlines() if line.strip()]
                self.update_available.emit(count, commits)
            else:
                self.up_to_date.emit(curr_hash)
        except Exception as e:
            log.warning("Update check notice: %s", e)
            self.check_failed.emit(str(e))


class UpdateExecutionWorker(QThread):
    """Executes the complete safe update pipeline with live step reporting."""

    progress = Signal(int, str)      # percent (0-100), status label
    log_line = Signal(str)          # console line
    finished = Signal(bool, str)     # success, message

    def run(self):
        try:
            # Step 1: Drain and terminate all running stages to prevent file lock
            self.progress.emit(10, I18n.t("update_progress_stopping") or "Stopping active services...")
            self.log_line.emit("[1/4] Stopping active stages to release Windows file handles...")
            EcosystemProcessManager.stop_all()
            self.msleep(300)

            # Step 2: Fetch and pull newest code cleanly
            self.progress.emit(35, I18n.t("update_progress_pulling") or "Pulling updates from repository...")
            self.log_line.emit("[2/4] Pulling latest commits from origin/main...")
            pull = subprocess.run(
                ["git", "pull", "--ff-only", "origin", "main"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,
            )
            self.log_line.emit(pull.stdout.strip() if pull.stdout else "Git pull executed.")
            if pull.returncode != 0:
                # If local changes blocked ff-only, attempt safe merge
                merge = subprocess.run(
                    ["git", "pull", "--no-edit", "origin", "main"],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30,
                )
                self.log_line.emit(merge.stdout.strip())
                if merge.returncode != 0:
                    self.finished.emit(False, f"Git pull failed (code {merge.returncode})")
                    return

            # Step 3: Run ecosystem bootstrapper to re-inject custom modules and patches
            self.progress.emit(70, I18n.t("update_progress_syncing") or "Syncing modules and patches...")
            self.log_line.emit("[3/4] Running bootstrapper and patch integrity synchronization...")
            bootstrap_script = PROJECT_ROOT / "scripts" / "bootstrap_ecosystem.py"
            py = str(PYTHON_EXE) if PYTHON_EXE.is_file() else sys.executable
            boot = subprocess.run(
                [py, str(bootstrap_script)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=45,
            )
            for line in (boot.stdout or "").splitlines():
                if any(k in line for k in ("Injected:", "Synchronized", "Audit:", "SUCCESS")):
                    self.log_line.emit(f"  {line.strip()}")

            if boot.returncode != 0:
                self.finished.emit(False, "Bootstrap patch injection returned warnings or errors.")
                return

            # Step 4: Verification and ready for restart
            self.progress.emit(100, I18n.t("update_progress_done") or "Update complete! Ready to restart.")
            self.log_line.emit("[4/4] Ecosystem updated and verified successfully!")
            self.finished.emit(True, "Success")
        except Exception as e:
            log.error("Update execution error: %s", e)
            self.log_line.emit(f"[ERROR] {e}")
            self.finished.emit(False, str(e))


class UpdateDialog(QDialog):
    """Modern modal dialog showing changelog, update progress, and 1-click execution."""

    def __init__(self, parent: Optional[QWidget] = None, commits: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle(I18n.t("update_dialog_title") or "Обновление экосистемы")
        self.resize(600, 440)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
            }
            QLabel {
                color: #f8fafc;
            }
            QTextEdit {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 5px;
                text-align: center;
                background-color: #1e293b;
                color: #ffffff;
                font-weight: bold;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)

        self.commits = commits or []
        self._worker: Optional[UpdateExecutionWorker] = None
        self._is_success = False

        self._init_ui()

    def _init_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        # Header Title & Icon
        h_head = QHBoxLayout()
        lbl_icon = QLabel("🚀")
        lbl_icon.setStyleSheet("font-size: 26px;")
        h_head.addWidget(lbl_icon)

        v_head = QVBoxLayout()
        lbl_title = QLabel(I18n.t("update_dialog_title") or "Обновление экосистемы")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        v_head.addWidget(lbl_title)

        curr_hash, curr_subj = get_current_commit_info()
        lbl_sub = QLabel(f"Текущая версия: {curr_hash} | {curr_subj}")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        v_head.addWidget(lbl_sub)
        h_head.addLayout(v_head)
        h_head.addStretch()
        v.addLayout(h_head)

        # Changelog / Commit List Box
        lbl_changelog = QLabel(f"Доступные изменения ({len(self.commits)} новых коммитов):")
        lbl_changelog.setStyleSheet("font-weight: bold; font-size: 12px; color: #e2e8f0;")
        v.addWidget(lbl_changelog)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        if self.commits:
            self.txt_log.append("Новые улучшения в репозитории:")
            for c in self.commits:
                self.txt_log.append(f"  • {c}")
        else:
            self.txt_log.append("Проверка репозитория готова. Нажмите «Обновить», чтобы синхронизировать проект.")
        v.addWidget(self.txt_log, stretch=1)

        # Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        v.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #38bdf8;")
        self.lbl_status.hide()
        v.addWidget(self.lbl_status)

        # Action Buttons
        self.h_btn = QHBoxLayout()
        self.h_btn.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155; color: #f8fafc; border-radius: 5px;
                padding: 7px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        self.h_btn.addWidget(self.btn_cancel)

        self.btn_action = QPushButton(I18n.t("update_btn_start") or "🚀 Обновить в 1 клик")
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: #ffffff; border-radius: 5px;
                padding: 7px 20px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #3b82f6; }
        """)
        self.btn_action.clicked.connect(self._start_update)
        self.h_btn.addWidget(self.btn_action)
        v.addLayout(self.h_btn)

    def _start_update(self):
        self.btn_action.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.show()
        self.lbl_status.show()
        self.txt_log.clear()
        self.txt_log.append("=== ЗАПУСК АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ ===")

        self._worker = UpdateExecutionWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.log_line.connect(self.txt_log.append)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, percent: int, text: str):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(text)

    def _on_finished(self, success: bool, message: str):
        self._is_success = success
        if success:
            self.lbl_status.setText("✓ Обновление успешно! Перезапустите приложение.")
            self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #4ade80;")
            self.btn_action.setText("🔄 Перезапустить сейчас")
            self.btn_action.setEnabled(True)
            self.btn_action.setStyleSheet("""
                QPushButton {
                    background-color: #059669; color: #ffffff; border-radius: 5px;
                    padding: 7px 20px; font-weight: bold; font-size: 12px;
                }
                QPushButton:hover { background-color: #10b981; }
            """)
            self.btn_action.clicked.disconnect()
            self.btn_action.clicked.connect(self._restart_application)
            self.btn_cancel.setText("Закрыть")
            self.btn_cancel.setEnabled(True)
        else:
            self.lbl_status.setText(f"❌ Ошибка обновления: {message}")
            self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #f87171;")
            self.btn_cancel.setEnabled(True)

    def _restart_application(self):
        """Cleanly restart the Hub application using QProcess."""
        hub_script = PROJECT_ROOT / "launcher" / "hub.py"
        py = str(PYTHON_EXE) if PYTHON_EXE.is_file() else sys.executable
        QProcess.startDetached(py, [str(hub_script)], str(PROJECT_ROOT))
        QApplication.instance().quit()

