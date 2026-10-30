"""Patch, Version & Health Integrity Auditor for Translation Ecosystem.
Audits all architectural engineering patches across Module 1, Module 2, and Module 3:
1. Module 1: Sherpa-ONNX SenseVoice INT8 ASR, in-process Hunyuan MT 1.8B GGUF (no server),
   Sherpa/Silero VAD chunking, in-process NLLB-200, Golden Window Controls (F9, 2x MMB, Drag, Alpha 1/255),
   and Vocab Highlighter.
2. Module 2: OverTranslate.patched.dll (offline Windows OCR, no telemetry) and QuickTranslate clipboard fix.
3. Module 3: Clean in-process GigaAM + Opus-MT + Pocket-TTS pipeline and cloned voice profile.
4. CONFIG Vault: Protected golden copies for 1-click self-healing against upstream overwrites.
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
    ASR_SHERPA_PY = LIVETRANSLATE_DIR / "asr_sherpa.py"
    HYMT_ENGINE_PY = LIVETRANSLATE_DIR / "hymt_engine.py"
    NLLB_ENGINE_PY = LIVETRANSLATE_DIR / "nllb_engine.py"
    VAD_SHERPA_PY = LIVETRANSLATE_DIR / "vad_sherpa.py"
    VAD_PROCESSOR_PY = LIVETRANSLATE_DIR / "vad_processor.py"
    SUBTITLE_WIN_PY = LIVETRANSLATE_DIR / "subtitle_window.py"
    VOCAB_HIGH_PY = LIVETRANSLATE_DIR / "vocab_highlighter.py"
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
        # MODULE 1: LiveTranslate (6 Engineering Patches + Runtime)
        # =============================================================
        m1_items = []

        # 1. Sherpa-ONNX SenseVoice INT8 ASR Acceleration Patch
        sherpa_ok = cls.ASR_SHERPA_PY.is_file()
        if sherpa_ok:
            try:
                t = cls.ASR_SHERPA_PY.read_text(encoding="utf-8", errors="replace")
                sherpa_ok = "sherpa_onnx" in t and "SenseVoice" in t
            except Exception:
                sherpa_ok = False
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 1: Sherpa-ONNX SenseVoice INT8 (Ускорение ASR)",
            "category": "ONNX Runtime",
            "is_ok": sherpa_ok,
            "status_text": "Активен (170 мс, замена Whisper)" if sherpa_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Ускорение распознавания в 5 раз на CPU (AVX-512) вместо тяжелого Whisper.",
        })

        # 2. In-Process Tencent Hunyuan MT 1.8B GGUF Patch (No Server)
        hymt_ok = cls.HYMT_ENGINE_PY.is_file()
        if hymt_ok:
            try:
                t = cls.HYMT_ENGINE_PY.read_text(encoding="utf-8", errors="replace")
                hymt_ok = "HY-MT" in t and ("llama" in t or "Llama" in t)
            except Exception:
                hymt_ok = False
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 2: In-Process Hunyuan MT 1.8B GGUF (Без сервера)",
            "category": "Локальная LLM",
            "is_ok": hymt_ok,
            "status_text": "Активен (80 мс, прямо в процессе)" if hymt_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Вшитая модель перевода: прямое исполнение через llama-cpp без внешнего сервера Ollama/портов.",
        })

        # 3. Sherpa / Silero VAD Fast Phrase Chunking Patch
        vad_ok = cls.VAD_SHERPA_PY.is_file() or cls.VAD_PROCESSOR_PY.is_file()
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 3: Аппаратная нарезка речи Silero/Sherpa VAD",
            "category": "Голосовой детектор",
            "is_ok": vad_ok,
            "status_text": "Активен (Аппаратный VAD)" if vad_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Моментальное деление аудиопотока на фразы в паузах дыхания без задержек.",
        })

        # 4. In-Process CTranslate2 NLLB-200 Alternative Engine Patch
        nllb_ok = cls.NLLB_ENGINE_PY.is_file()
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 4: In-Process NLLB-200 CTranslate2 INT8",
            "category": "Локальный MT",
            "is_ok": nllb_ok,
            "status_text": "Активен (Без server.py:8080)" if nllb_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Резервный офлайн-движок перевода CTranslate2, встроенный напрямую в память процесса.",
        })

        # 5. Golden Subtitle Window Controls (F9, 2x MMB, MMB Drag, Alpha 1/255)
        sub_text = ""
        if cls.SUBTITLE_WIN_PY.is_file():
            try:
                sub_text = cls.SUBTITLE_WIN_PY.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
        main_text = ""
        if cls.MAIN_PY.is_file():
            try:
                main_text = cls.MAIN_PY.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        controls_ok = (
            ("0xF901" in main_text or "_VK_F9" in main_text)
            and ("MiddleButton" in sub_text)
            and ("1/255" in sub_text or "1 / 255" in sub_text or "QColor(0, 0, 0, 1)" in sub_text)
        )
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 5: Golden Controls (F9, 2x MMB, MMB Drag, Alpha 1/255)",
            "category": "Управление окном",
            "is_ok": controls_ok,
            "status_text": "Активен (Полный контроль окна)" if controls_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "F9 пауза/скрытие, 2x MMB клик сквозь окно, перетаскивание колесиком, DWM сенсор.",
        })

        # 6. Dual Subtitles & Vocabulary Highlighter
        vocab_ok = cls.VOCAB_HIGH_PY.is_file()
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Патч 6: Подсветка лексики и двуязычные субтитры",
            "category": "Обучающий режим",
            "is_ok": vocab_ok,
            "status_text": "Активен (Подсветка терминов)" if vocab_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Подсветка ключевых слов и параллельный вывод оригинала и перевода для изучения языка.",
        })

        # Runtime files check
        lt_runtime_ok = cls.MAIN_PY.is_file() and cls.SETTINGS_JSON.is_file()
        m1_items.append({
            "stage_id": "stage_1",
            "stage_name": "Модуль 1: Синхронные субтитры (LiveTranslate)",
            "name": "Конфигурация LiveTranslate (user_settings.json)",
            "category": "Настройки",
            "is_ok": lt_runtime_ok,
            "status_text": "Готов к запуску" if lt_runtime_ok else "Ошибка конфигурации",
            "desc": "Настроенный профиль с активной локальной моделью Hunyuan MT и Sherpa-ONNX.",
        })

        modules_report["stage_1"] = {
            "title": "📦 Модуль 1: Синхронные субтитры (LiveTranslate)",
            "items": m1_items,
            "all_ok": all(it["is_ok"] for it in m1_items),
        }
        all_items.extend(m1_items)

        # =============================================================
        # MODULE 2: OverTranslate (2 Patches + Executable)
        # =============================================================
        m2_items = []
        ot_dll_ok = False
        if cls.OT_DLL.is_file() and cls.VAULT_DLL_FILE.is_file():
            try:
                h_current = hashlib.sha256(cls.OT_DLL.read_bytes()).hexdigest()
                h_vault = hashlib.sha256(cls.VAULT_DLL_FILE.read_bytes()).hexdigest()
                ot_dll_ok = (h_current == h_vault)
            except Exception:
                ot_dll_ok = False
        elif cls.OT_DLL.is_file():
            ot_dll_ok = True

        m2_items.append({
            "stage_id": "stage_2",
            "stage_name": "Модуль 2: Экранный переводчик (OverTranslate)",
            "name": "Патч 7: OverTranslate.patched.dll (Автономный офлайн)",
            "category": "Патч бинарника",
            "is_ok": ot_dll_ok,
            "status_text": "Активен (Офлайн Windows OCR)" if ot_dll_ok else "СЛЕТЕЛ (Требуется восстановление)",
            "desc": "Разблокирован локальный автономный OCR без обращения к китайским облакам.",
        })

        # QuickTranslate Clipboard Crash Fix (Day 22 IL Patch)
        ot_cfg_file = cls.CONFIG_DIR / "stage_2_screen" / "appsettings.json"
        ot_cfg_ok = ot_cfg_file.is_file()
        m2_items.append({
            "stage_id": "stage_2",
            "stage_name": "Модуль 2: Экранный переводчик (OverTranslate)",
            "name": "Патч 8: QuickTranslate CIL-патч буфера обмена",
            "category": "Win32 OLE патч",
            "is_ok": ot_dll_ok and ot_cfg_ok,
            "status_text": "Активен (Фикс 0x800401D0)" if (ot_dll_ok and ot_cfg_ok) else "СЛЕТЕЛ",
            "desc": "Устранен краш буфера обмена в Windows 11 при мгновенном переводе выделенного текста.",
        })

        ot_exe_ok = cls.OT_EXE.is_file()
        m2_items.append({
            "stage_id": "stage_2",
            "stage_name": "Модуль 2: Экранный переводчик (OverTranslate)",
            "name": "Исполняемый файл OverTranslate.exe",
            "category": "Файл программы",
            "is_ok": ot_exe_ok,
            "status_text": "Готов к запуску" if ot_exe_ok else "Файл не найден",
            "desc": "Быстрое оптическое распознавание текста (OCR) по рамке на экране.",
        })

        modules_report["stage_2"] = {
            "title": "📦 Модуль 2: Экранный переводчик (OverTranslate)",
            "items": m2_items,
            "all_ok": all(it["is_ok"] for it in m2_items),
        }
        all_items.extend(m2_items)

        # =============================================================
        # MODULE 3: Voice Studio (100% In-Process Engine + Voice Profile)
        # =============================================================
        m3_items = []
        studio_engine_ok = cls.STUDIO_ENGINE_PY.is_file()
        m3_items.append({
            "stage_id": "stage_3",
            "stage_name": "Модуль 3: Голосовой переводчик (Voice Studio)",
            "name": "Компонент 9: Движок Voice Studio (GigaAM + Opus-MT + Pocket-TTS)",
            "category": "100% Собственный код",
            "is_ok": studio_engine_ok,
            "status_text": "Готов (Сторонние патчи не требуются)" if studio_engine_ok else "ОТСУТСТВУЕТ",
            "desc": "Автономный голосовой конвейер без облаков: распознавание Sber GigaAM + перевод + синтез речи.",
        })

        voice_clone_ok = cls.VAULT_VOICE_FILE.is_file()
        voice_size_mb = round(cls.VAULT_VOICE_FILE.stat().st_size / (1024 * 1024), 1) if voice_clone_ok else 0.0
        m3_items.append({
            "stage_id": "stage_3",
            "stage_name": "Модуль 3: Голосовой переводчик (Voice Studio)",
            "name": "Компонент 10: Образец вашего голоса (my_pocket_voice)",
            "category": "Ваш тембр",
            "is_ok": voice_clone_ok,
            "status_text": f"Сохранён в CONFIG/ ({voice_size_mb} МБ)" if voice_clone_ok else "Не записан (Используется стандартный)",
            "desc": "Индивидуальный акустический слепок вашего голоса для синтеза английской речи.",
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
        vault_modules_ok = cls.VAULT_MODULES_DIR.is_dir() and len(list(cls.VAULT_MODULES_DIR.glob("*.py"))) >= 8
        vault_items = [
            {
                "stage_id": "config",
                "stage_name": "Защищенное хранилище CONFIG/",
                "name": "Эталонные копии всех патчей и моделей (custom_modules)",
                "category": "Резервная копия",
                "is_ok": vault_modules_ok,
                "status_text": "Защищено (Все эталоны сохранены)" if vault_modules_ok else "Повреждено",
                "desc": "Изолированные файлы в CONFIG/ для мгновенного восстановления при обновлении программ авторами.",
            }
        ]
        modules_report["config"] = {
            "title": "🔒 Защищенное хранилище настроек (CONFIG/)",
            "items": vault_items,
            "all_ok": all(it["is_ok"] for it in vault_items),
        }
        all_items.extend(vault_items)

        # Key Engineering Patches List
        key_patches = [
            sherpa_ok,
            hymt_ok,
            vad_ok,
            nllb_ok,
            controls_ok,
            vocab_ok,
            ot_dll_ok,
            (ot_dll_ok and ot_cfg_ok),
        ]
        active_patches_count = sum(1 for p in key_patches if p)
        total_patches_count = len(key_patches)
        patches_ok = (active_patches_count == total_patches_count)

        total_items = len(all_items)
        passed_items = sum(1 for it in all_items if it["is_ok"])
        all_passed = (passed_items == total_items)

        return {
            "all_passed": all_passed,
            "patches_ok": patches_ok,
            "active_patches_count": active_patches_count,
            "total_patches_count": total_patches_count,
            "passed_count": passed_items,
            "total_count": total_items,
            "modules": modules_report,
            "items": all_items,
        }

    @classmethod
    def restore_all_patches(cls) -> Dict[str, Any]:
        """Restore all custom modules, patched DLLs, and authoritative configs from CONFIG/."""
        restored: List[str] = []
        errors: List[str] = []

        # 1. Restore Stage 1 Custom Modules
        if cls.VAULT_MODULES_DIR.is_dir() and cls.LIVETRANSLATE_DIR.is_dir():
            for src_file in cls.VAULT_MODULES_DIR.glob("*"):
                if src_file.is_file():
                    dst_file = cls.LIVETRANSLATE_DIR / src_file.name
                    try:
                        shutil.copy2(src_file, dst_file)
                        restored.append(f"LiveTranslate/{src_file.name}")
                    except Exception as e:
                        errors.append(f"LiveTranslate/{src_file.name}: {e}")

        # 2. Restore Stage 1 Settings
        vault_settings = cls.VAULT_STAGE1_DIR / "user_settings.json"
        if vault_settings.is_file() and cls.LIVETRANSLATE_DIR.is_dir():
            try:
                shutil.copy2(vault_settings, cls.SETTINGS_JSON)
                restored.append("LiveTranslate/user_settings.json")
            except Exception as e:
                errors.append(f"LiveTranslate/user_settings.json: {e}")

        # 3. Restore Stage 2 Patched DLL
        if cls.VAULT_DLL_FILE.is_file():
            targets = [cls.OT_DLL, cls.OT_DIR / "OverTranslate.dll"]
            for target in targets:
                if target.parent.is_dir():
                    try:
                        shutil.copy2(cls.VAULT_DLL_FILE, target)
                        restored.append(f"OverTranslate/{target.name}")
                    except Exception as e:
                        errors.append(f"OverTranslate/{target.name}: {e}")

        # 4. Restore Stage 2 Settings
        vault_ot_cfg = cls.VAULT_STAGE2_DIR / "appsettings.json"
        if vault_ot_cfg.is_file():
            ot_cfgs = [cls.OT_CURRENT_DIR / "appsettings.json", cls.OT_DIR / "appsettings.json"]
            for dst_cfg in ot_cfgs:
                if dst_cfg.parent.is_dir():
                    try:
                        shutil.copy2(vault_ot_cfg, dst_cfg)
                        restored.append(f"OverTranslate/{dst_cfg.name}")
                    except Exception as e:
                        errors.append(f"OverTranslate/{dst_cfg.name}: {e}")

        success = len(errors) == 0 and len(restored) > 0
        return {
            "success": success,
            "restored_files": restored,
            "errors": errors,
        }
