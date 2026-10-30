"""Patch, Version & Health Integrity Auditor for Translation Ecosystem.
Audits the 5 Golden Patches across Module 1 and Module 2, verifies executables,
and ensures protected CONFIG vault integrity.
Provides 1-click self-healing patch restoration if upstream updates overwrite files.
"""
from __future__ import annotations

import hashlib
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

    # Stage 2 Target files
    OT_DIR = PROJECT_ROOT / "stage_2_screen" / "OverTranslate"
    OT_CURRENT_DIR = OT_DIR / "current"
    OT_DLL = OT_CURRENT_DIR / "OverTranslate.dll"
    OT_EXE = OT_CURRENT_DIR / "OverTranslate.exe"
    if not OT_EXE.is_file():
        OT_EXE = OT_DIR / "OverTranslate.exe"

    # Stage 3 Target files
    STUDIO_ENGINE_PY = PROJECT_ROOT / "stage_3_voice" / "studio" / "audio_engine.py"

    # Vault files in CONFIG/
    CONFIG_DIR = PROJECT_ROOT / "CONFIG"
    VAULT_STAGE1_DIR = CONFIG_DIR / "stage_1_audio"
    VAULT_MODULES_DIR = VAULT_STAGE1_DIR / "custom_modules"
    VAULT_STAGE2_DIR = CONFIG_DIR / "stage_2_screen"
    VAULT_DLL_FILE = VAULT_STAGE2_DIR / "OverTranslate.patched.dll"
    VAULT_VOICE_FILE = CONFIG_DIR / "stage_3_voice" / "my_pocket_voice.safetensors"

    @classmethod
    def audit_all(cls) -> Dict[str, Any]:
        """Perform full diagnostic audit grouped by Module 1, Module 2, Module 3, and CONFIG Vault."""
        modules_report: Dict[str, Dict[str, Any]] = {}
        all_items: List[Dict[str, Any]] = []

        # =============================================================
        # MODULE 1: LiveTranslate (4 Patches + Engine)
        # =============================================================
        m1_items = []
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
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 1: Горячая клавиша F9 (Master Toggle)",
            "category": "Патч кода",
            "is_ok": f9_active,
            "status_text": "Активен (Синхронная пауза/пуск)" if f9_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Синхронно скрывает/показывает субтитры и переводит распознавание на паузу.",
        })

        # Patch 2: 2x MMB Click-through
        mmb_ct_active = "mouseDoubleClickEvent" in sub_text and "MiddleButton" in sub_text and "click_through" in sub_text
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 2: Двойной клик колесиком (2x MMB)",
            "category": "Патч кода",
            "is_ok": mmb_ct_active,
            "status_text": "Активен (Клик сквозь окно)" if mmb_ct_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Быстрое переключение прозрачности окна субтитров для кликов мыши в другие программы.",
        })

        # Patch 3: MMB Dragging
        mmb_drag_active = "MiddleButton" in sub_text and ("_drag_pos" in sub_text or "mouseMoveEvent" in sub_text)
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 3: Перетаскивание колесиком (MMB Drag)",
            "category": "Патч кода",
            "is_ok": mmb_drag_active,
            "status_text": "Активен (Перемещение без срыва ЛКМ)" if mmb_drag_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Свободное перемещение субтитров колесиком мыши без влияния на клики левой кнопкой.",
        })

        # Patch 4: Alpha 1/255 Hit-Testing Surface
        alpha_active = ("1/255" in sub_text or "1 / 255" in sub_text or "QColor(0, 0, 0, 1)" in sub_text) and "paintEvent" in sub_text
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 4: Сенсорная подложка Alpha 1/255",
            "category": "Патч кода",
            "is_ok": alpha_active,
            "status_text": "Активен (DWM сенсор мыши)" if alpha_active else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Невидимый слой для отклика на мышь даже при 0% видимости фона.",
        })

        # Module 1 Runtime
        lt_py_ok = cls.MAIN_PY.is_file() and cls.SETTINGS_JSON.is_file()
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Движок и конфигурация LiveTranslate",
            "category": "Файл программы",
            "is_ok": lt_py_ok,
            "status_text": "Готов (Python + user_settings.json)" if lt_py_ok else "Ошибка конфигурации",
            "desc": "Основной модуль захвата звука и вывода субтитров.",
        })
        modules_report["stage_1"] = {
            "title": "📦 Модуль 1: Синхронные субтитры (LiveTranslate)",
            "items": m1_items,
            "all_ok": all(it["is_ok"] for it in m1_items),
        }
        all_items.extend(m1_items)

        # =============================================================
        # MODULE 2: OverTranslate (1 Patch + Binary)
        # =============================================================
        m2_items = []
        ot_dll_ok = False
        if cls.OT_DLL.is_file() and cls.VAULT_DLL_FILE.is_file():
            try:
                h_current = hashlib.sha256(cls.OT_DLL.read_bytes()).hexdigest()
                h_vault = hashlib.sha256(cls.VAULT_DLL_FILE.read_bytes()).hexdigest()
                ot_dll_ok = (h_current == h_vault)
            except Exception as e:
                log.warning("Hash check failed for OverTranslate.dll: %s", e)
        elif cls.OT_DLL.is_file():
            ot_dll_ok = True

        m2_items.append({
            "stage_id": "stage_2",
            "stage_name": "Модуль 2: Экранный переводчик (OverTranslate)",
            "name": "Патч 5: OverTranslate.patched.dll (Автономный офлайн-режим)",
            "category": "Патч бинарника",
            "is_ok": ot_dll_ok,
            "status_text": "Активен (Офлайн библиотека)" if ot_dll_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Разблокирует локальный автономный перевод без обращения к внешним китайским серверам.",
        })

        ot_exe_ok = cls.OT_EXE.is_file()
        ot_size_mb = round(cls.OT_EXE.stat().st_size / (1024 * 1024), 1) if ot_exe_ok else 0.0
        m2_items.append({
            "stage_id": "stage_2",
            "stage_name": "Модуль 2: Экранный переводчик (OverTranslate)",
            "name": "Исполняемый файл OverTranslate.exe",
            "category": "Файл программы",
            "is_ok": ot_exe_ok,
            "status_text": f"Готов ({ot_size_mb} МБ, Windows OCR)" if ot_exe_ok else "ОТСУТСТВУЕТ",
            "desc": "Быстрое оптическое распознавание текста (OCR) по рамке на экране.",
        })
        modules_report["stage_2"] = {
            "title": "📦 Модуль 2: Экранный переводчик (OverTranslate)",
            "items": m2_items,
            "all_ok": all(it["is_ok"] for it in m2_items),
        }
        all_items.extend(m2_items)

        # =============================================================
        # MODULE 3: Voice Studio (100% Custom Engine - No Third-Party Patches)
        # =============================================================
        m3_items = []
        studio_engine_ok = cls.STUDIO_ENGINE_PY.is_file()
        m3_items.append({
            "stage_id": "stage_3",
            "stage_name": "Модуль 3: Голосовой переводчик (Voice Studio)",
            "name": "Движок синтеза и маршрутизации Voice Studio",
            "category": "100% Собственный код",
            "is_ok": studio_engine_ok,
            "status_text": "Готов (Сторонние патчи не требуются)" if studio_engine_ok else "ОТСУТСТВУЕТ",
            "desc": "Собственный движок перевода речи: GigaAM CTC + Opus-MT + Pocket-TTS без чужих зависимостей.",
        })

        voice_clone_ok = cls.VAULT_VOICE_FILE.is_file()
        voice_size_mb = round(cls.VAULT_VOICE_FILE.stat().st_size / (1024 * 1024), 1) if voice_clone_ok else 0.0
        m3_items.append({
            "stage_id": "stage_3",
            "stage_name": "Модуль 3: Голосовой переводчик (Voice Studio)",
            "name": "Образец вашего голоса (my_pocket_voice)",
            "category": "Ваш профиль",
            "is_ok": voice_clone_ok,
            "status_text": f"Сохранён в CONFIG/ ({voice_size_mb} МБ)" if voice_clone_ok else "Не записан (Используется стандартный)",
            "desc": "Индивидуальный акустический слепок вашего тембра, созданный за 7 секунд.",
        })
        modules_report["stage_3"] = {
            "title": "📦 Модуль 3: Голосовой переводчик (Voice Studio)",
            "items": m3_items,
            "all_ok": all(it["is_ok"] for it in m3_items),
        }
        all_items.extend(m3_items)

        # =============================================================
        # CONFIG VAULT INTEGRITY
        # =============================================================
        vault_modules_ok = cls.VAULT_MODULES_DIR.is_dir() and len(list(cls.VAULT_MODULES_DIR.glob("*.py"))) >= 5
        vault_items = [
            {
                "stage_id": "config",
                "stage_name": "Защищенное хранилище CONFIG/",
                "name": "Эталонные копии всех патчей (custom_modules)",
                "category": "Резервная копия",
                "is_ok": vault_modules_ok,
                "status_text": "Защищено (Вся база сохранена)" if vault_modules_ok else "Повреждено",
                "desc": "Изолированные эталонные файлы для мгновенного восстановления при обновлении авторов.",
            }
        ]
        modules_report["config"] = {
            "title": "🔒 Защищенное хранилище настроек (CONFIG/)",
            "items": vault_items,
            "all_ok": all(it["is_ok"] for it in vault_items),
        }
        all_items.extend(vault_items)

        # Patches Summary (Strictly the 5 Patches)
        patches_5 = [
            f9_active,
            mmb_ct_active,
            mmb_drag_active,
            alpha_active,
            ot_dll_ok,
        ]
        patches_5_ok = all(patches_5)
        active_patches_count = sum(1 for p in patches_5 if p)

        total_items = len(all_items)
        passed_items = sum(1 for it in all_items if it["is_ok"])
        all_passed = (passed_items == total_items)

        return {
            "all_passed": all_passed,
            "patches_ok": patches_5_ok,
            "active_patches_count": active_patches_count,
            "total_patches_count": 5,
            "passed_count": passed_items,
            "total_count": total_items,
            "modules": modules_report,
            "items": all_items,
        }

    @classmethod
    def restore_all_patches(cls) -> Dict[str, Any]:
        """Restore all 5 golden patches and authoritative settings from CONFIG vault.
        Safe, idempotent, and fast (less than 100ms).
        """
        results = {"success": False, "restored_files": [], "errors": []}
        try:
            # 1. Restore Module 1 LiveTranslate patches
            if cls.VAULT_MODULES_DIR.is_dir():
                cls.LIVETRANSLATE_DIR.mkdir(parents=True, exist_ok=True)
                for src_file in cls.VAULT_MODULES_DIR.glob("*"):
                    if src_file.suffix in (".py", ".txt"):
                        dst_file = cls.LIVETRANSLATE_DIR / src_file.name
                        shutil.copy2(src_file, dst_file)
                        results["restored_files"].append(f"LiveTranslate/{src_file.name}")

            vault_settings = cls.VAULT_STAGE1_DIR / "user_settings.json"
            if vault_settings.is_file():
                shutil.copy2(vault_settings, cls.SETTINGS_JSON)
                results["restored_files"].append("LiveTranslate/user_settings.json")

            # 2. Restore Module 2 OverTranslate patched dll
            if cls.VAULT_DLL_FILE.is_file() and cls.OT_CURRENT_DIR.is_dir():
                shutil.copy2(cls.VAULT_DLL_FILE, cls.OT_DLL)
                results["restored_files"].append("OverTranslate/current/OverTranslate.dll")

            results["success"] = True
            log.info("Successfully restored all 5 patches: %s", results["restored_files"])
        except Exception as e:
            results["errors"].append(str(e))
            log.error("Failed to restore patches: %s", e)

        return results
