"""Patch, Version & Health Integrity Auditor for Translation Ecosystem.
Scans for the 4 Golden Patches in LiveTranslate, verifies local neural models,
checks executable binaries and protected CONFIG vault integrity.
Provides 1-click patch restoration if upstream updates overwrite files.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List

log = logging.getLogger("Launcher.PatchChecker")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class PatchIntegrityChecker:
    """Comprehensive ecosystem integrity monitor & self-healing patch engine."""

    # Stage 1 Target files
    LIVETRANSLATE_DIR = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate"
    SUBTITLE_WIN_PY = LIVETRANSLATE_DIR / "subtitle_window.py"
    MAIN_PY = LIVETRANSLATE_DIR / "main.py"
    SETTINGS_JSON = LIVETRANSLATE_DIR / "user_settings.json"

    # Vault files in CONFIG/
    CONFIG_DIR = PROJECT_ROOT / "CONFIG"
    VAULT_STAGE1_DIR = CONFIG_DIR / "stage_1_audio"
    VAULT_MODULES_DIR = VAULT_STAGE1_DIR / "custom_modules"
    VAULT_VOICE_FILE = CONFIG_DIR / "stage_3_voice" / "my_pocket_voice.safetensors"
    VAULT_DLL_FILE = CONFIG_DIR / "stage_2_screen" / "OverTranslate.patched.dll"

    @classmethod
    def audit_all(cls) -> Dict[str, Any]:
        """Perform full diagnostic audit across all 3 stages, patches, binaries, and vault."""
        items: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. LIVE TRANSLATE PATCHES (The 4 Golden Patches)
        # -------------------------------------------------------------
        sub_text = ""
        if cls.SUBTITLE_WIN_PY.is_file():
            try:
                sub_text = cls.SUBTITLE_WIN_PY.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                log.warning("Could not read subtitle_window.py: %s", e)

        main_text = ""
        if cls.MAIN_PY.is_file():
            try:
                main_text = cls.MAIN_PY.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                log.warning("Could not read main.py: %s", e)

        # Patch 1: F9 Master Toggle
        f9_active = ("0xF901" in main_text or "_VK_F9" in main_text) and "toggle" in main_text
        items.append({
            "stage": "Этап 1 (LiveTranslate)",
            "name": "Патч F9: Единый переключатель субтитров и транскрипции",
            "category": "Патч кода",
            "file": "stage_1_audio/LiveTranslate/main.py",
            "is_ok": f9_active,
            "status_text": "Активен (Синхронная пауза/пуск)" if f9_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Синхронно скрывает/показывает субтитры и ставит транскрипцию на паузу без задержек.",
        })

        # Patch 2: 2x MMB Click-through
        mmb_ct_active = "mouseDoubleClickEvent" in sub_text and "MiddleButton" in sub_text and "click_through" in sub_text
        items.append({
            "stage": "Этап 1 (LiveTranslate)",
            "name": "Патч 2x MMB: Клик сквозь субтитры",
            "category": "Патч кода",
            "file": "stage_1_audio/LiveTranslate/subtitle_window.py",
            "is_ok": mmb_ct_active,
            "status_text": "Активен (Двойной клик колесиком)" if mmb_ct_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Быстрое переключение прозрачности окна субтитров для кликов мыши в другие программы.",
        })

        # Patch 3: MMB Dragging
        mmb_drag_active = "MiddleButton" in sub_text and ("_drag_pos" in sub_text or "mouseMoveEvent" in sub_text)
        items.append({
            "stage": "Этап 1 (LiveTranslate)",
            "name": "Патч MMB Drag: Перетаскивание колесиком",
            "category": "Патч кода",
            "file": "stage_1_audio/LiveTranslate/subtitle_window.py",
            "is_ok": mmb_drag_active,
            "status_text": "Активен (Перемещение без срыва ЛКМ)" if mmb_drag_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Свободное перемещение окна субтитров по экрану колесиком мыши без влияния на клики левой кнопкой.",
        })

        # Patch 4: Alpha 1/255 Hit-Testing Surface
        alpha_active = ("1/255" in sub_text or "1 / 255" in sub_text or "QColor(0, 0, 0, 1)" in sub_text) and "paintEvent" in sub_text
        items.append({
            "stage": "Этап 1 (LiveTranslate)",
            "name": "Патч Alpha 1/255: Сенсорная подложка DWM",
            "category": "Патч кода",
            "file": "stage_1_audio/LiveTranslate/subtitle_window.py",
            "is_ok": alpha_active,
            "status_text": "Активен (Windows DWM hit-test)" if alpha_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Невидимая подложка, гарантирующая отклик на колесико мыши даже при 0% видимой прозрачности фона.",
        })

        # -------------------------------------------------------------
        # 2. EXECUTABLES & RUNTIME INTEGRITY
        # -------------------------------------------------------------
        # LiveTranslate Runtime
        lt_py_ok = cls.MAIN_PY.is_file() and cls.SETTINGS_JSON.is_file()
        items.append({
            "stage": "Этап 1 (LiveTranslate)",
            "name": "Движок и конфигурация LiveTranslate",
            "category": "Исполняемый файл",
            "file": "stage_1_audio/LiveTranslate/",
            "is_ok": lt_py_ok,
            "status_text": "Готов (Python + user_settings.json)" if lt_py_ok else "Ошибка конфигурации",
            "desc": "Основной модуль захвата системного аудио и вывода поверхностных субтитров.",
        })

        # OverTranslate Executable
        ot_exe = PROJECT_ROOT / "stage_2_screen" / "OverTranslate" / "current" / "OverTranslate.exe"
        if not ot_exe.is_file():
            ot_exe = PROJECT_ROOT / "stage_2_screen" / "OverTranslate" / "OverTranslate.exe"
        ot_ok = ot_exe.is_file()
        ot_size_mb = round(ot_exe.stat().st_size / (1024 * 1024), 1) if ot_ok else 0.0
        items.append({
            "stage": "Этап 2 (OverTranslate)",
            "name": "Исполняемый файл OverTranslate.exe",
            "category": "Исполняемый файл",
            "file": str(ot_exe.relative_to(PROJECT_ROOT)) if ot_ok else "OverTranslate.exe",
            "is_ok": ot_ok,
            "status_text": f"Готов ({ot_size_mb} МБ, Windows OCR)" if ot_ok else "ОТСУТСТВУЕТ",
            "desc": "Сверхбыстрый модуль оптического распознавания текста (OCR) по рамке на экране.",
        })

        # Voice Studio Engine
        studio_engine = PROJECT_ROOT / "stage_3_voice" / "studio" / "audio_engine.py"
        studio_ok = studio_engine.is_file()
        items.append({
            "stage": "Этап 3 (Voice Studio)",
            "name": "Движок синтеза и маршрутизации Voice Studio",
            "category": "Исполняемый файл",
            "file": "stage_3_voice/studio/audio_engine.py",
            "is_ok": studio_ok,
            "status_text": "Готов (VAD + Punctuation + TTS Engine)" if studio_ok else "ОТСУТСТВУЕТ",
            "desc": "Модуль перевода микрофона в реальном времени с восстановлением знаков препинания и клонированием голоса.",
        })

        # -------------------------------------------------------------
        # 3. PROTECTED CONFIG VAULT INTEGRITY
        # -------------------------------------------------------------
        vault_modules_ok = cls.VAULT_MODULES_DIR.is_dir() and len(list(cls.VAULT_MODULES_DIR.glob("*.py"))) >= 5
        items.append({
            "stage": "Хранилище CONFIG",
            "name": "Резервные копии патчей (custom_modules)",
            "category": "Защита от обновлений",
            "file": "CONFIG/stage_1_audio/custom_modules/",
            "is_ok": vault_modules_ok,
            "status_text": "Защищено (Эталонные копии сохранены)" if vault_modules_ok else "Повреждено",
            "desc": "Изолированное хранилище эталонных файлов для мгновенного восстановления при обновлении авторов.",
        })

        voice_clone_ok = cls.VAULT_VOICE_FILE.is_file()
        voice_size_mb = round(cls.VAULT_VOICE_FILE.stat().st_size / (1024 * 1024), 1) if voice_clone_ok else 0.0
        items.append({
            "stage": "Хранилище CONFIG",
            "name": "Клонированный образец голоса (my_pocket_voice)",
            "category": "Защита от обновлений",
            "file": "CONFIG/stage_3_voice/my_pocket_voice.safetensors",
            "is_ok": voice_clone_ok,
            "status_text": f"Сохранён ({voice_size_mb} МБ)" if voice_clone_ok else "Не записан (Используется стандартный)",
            "desc": "Индивидуальный акустический эмбеддинг вашего тембра, созданный за 7 секунд.",
        })

        # -------------------------------------------------------------
        # 4. OVERALL SUMMARY CALCULATION
        # -------------------------------------------------------------
        patches_ok = f9_active and mmb_ct_active and mmb_drag_active and alpha_active
        total_items = len(items)
        passed_items = sum(1 for it in items if it["is_ok"])
        all_passed = (passed_items == total_items)

        return {
            "all_passed": all_passed,
            "patches_ok": patches_ok,
            "passed_count": passed_items,
            "total_count": total_items,
            "items": items,
        }

    @classmethod
    def restore_all_patches(cls) -> Dict[str, Any]:
        """Restore all 4 golden patches and authoritative settings from CONFIG vault.
        Safe, idempotent, and fast (less than 100ms).
        """
        results = {"success": False, "restored_files": [], "errors": []}
        try:
            if not cls.VAULT_MODULES_DIR.is_dir():
                results["errors"].append(f"Vault directory not found: {cls.VAULT_MODULES_DIR}")
                return results

            cls.LIVETRANSLATE_DIR.mkdir(parents=True, exist_ok=True)

            # Copy all custom modules
            for src_file in cls.VAULT_MODULES_DIR.glob("*"):
                if src_file.suffix in (".py", ".txt"):
                    dst_file = cls.LIVETRANSLATE_DIR / src_file.name
                    shutil.copy2(src_file, dst_file)
                    results["restored_files"].append(src_file.name)

            # Copy authoritative user_settings.json if present in vault
            vault_settings = cls.VAULT_STAGE1_DIR / "user_settings.json"
            if vault_settings.is_file():
                shutil.copy2(vault_settings, cls.SETTINGS_JSON)
                results["restored_files"].append("user_settings.json")

            results["success"] = True
            log.info("Successfully restored patches: %s", results["restored_files"])
        except Exception as e:
            results["errors"].append(str(e))
            log.error("Failed to restore patches: %s", e)

        return results
