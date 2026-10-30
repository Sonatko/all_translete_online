"""Trilingual Localization (i18n) for Translation Ecosystem Hub.
Supports Russian, English, and Chinese. Clean KISS terminology without juvenile slang.
"""
from __future__ import annotations

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        "title": "Пульт Управления Программами Перевода (Hub - 100% Офлайн)",
        "start_all": "▶ Запустить все 3 программы",
        "stop_all": "⏹ Остановить всё",
        "tab_dashboard": "🎛 Пульт и Схема работы",
        "tab_inventory": "🧠 Файлы нейросетей на диске",
        "tab_patches": "🛡 Целостность и Патчи",
        "tab_guide": "ℹ Справка и Архитектура",
        "status_all_running": "🟢 Все 3 программы активны (0 MB облака)",
        "status_partial": "🟡 Работает программ: {count} из 3",
        "status_stopped": "⚪ Все программы остановлены",

        # Module 1: Audio to Subtitles (LiveTranslate)
        "stage1_title": "1. Синхронные субтитры (LiveTranslate)",
        "stage1_flow": "Схема: 🔊 Системный звук ПК  ➔  ✂ Нарезка фраз  ➔  🧠 SenseVoice + Hunyuan MT  ➔  📺 Экранные субтитры",
        "stage1_desc": "Захватывает системный звук (видео, медиа, онлайн-звонки, браузер), делит на фразы в паузах речи и выводит перевод поверхностными субтитрами поверх всех окон.",
        "stage1_hotkeys": "F9 — Вкл/Пауза и скрыть субтитры | 2x MMB — Клик сквозь окно | MMB Drag — Перемещение",

        # Module 2: Screen OCR (OverTranslate)
        "stage2_title": "2. Экранный переводчик (OverTranslate)",
        "stage2_flow": "Схема: 🖼 Рамка на экране  ➔  🔍 OCR сканер  ➔  🧠 Нейросеть перевода  ➔  📝 Окно с текстом",
        "stage2_desc": "Оптическое распознавание невыделяемого текста с экрана в заданной прямоугольной рамке (документы, графика, интерфейсы) с мгновенным переводом.",
        "stage2_hotkeys": "Ctrl + Alt + A — Выделить рамкой | Ctrl + C + C — Быстрый перевод из буфера",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Голосовой переводчик (Voice Studio)",
        "stage3_flow": "Схема: 🎙 Микрофон (RU)  ➔  ✂ Нарезка + Пунктуация  ➔  🧠 GigaAM + Pocket-TTS  ➔  🔊 Выходной микрофон (EN)",
        "stage3_desc": "Вы говорите в микрофон по-русски — программа переводит и синтезирует английскую речь вашим клонированным тембром в выходной микрофонный канал.",
        "stage3_hotkeys": "Shift + Колесико мыши — Активация рации (Push-To-Talk / PTT)",

        "btn_start": "▶ Запустить",
        "btn_stop": "⏹ Остановить",
        "btn_open": "🗔 Открыть окно",
        "btn_studio": "🗔 Студия речи",
        "btn_wizard": "🎙 Записать образец голоса (7 сек)",
        "wizard_desc": "Обучить программу говорить вашим персональным тембром голоса за 7 секунд.",

        "status_running": "● Работает",
        "status_stopped_pill": "○ Остановлена",

        # Hardware audio selector
        "hardware_title": "Выходной аудиоканал для перевода голоса:",
        "hardware_topping": "🎛 Topping E2x2 (Аппаратный Loopback)",
        "hardware_cable": "🔌 Виртуальный кабель (VB-Audio Cable)",
        "hardware_install_cable": "📥 Установить VB-Cable (1 клик)",
        "btn_open_folder": "📂 Защищенные настройки (CONFIG/)",

        # Inventory Tab
        "inventory_header": "Проверка файлов локальных нейросетей на SSD (100% готовность без интернета):",
        "btn_refresh": "🔄 Проверить файлы",
        "col_stage": "Модуль",
        "col_task": "Задача",
        "col_model": "Модель ИИ",
        "col_status": "Статус на диске",
        "col_size": "Размер (МБ)",
        "ready": "✔ Скачана (Готова к работе)",
        "missing": "❌ Отсутствует",

        # Patches & Health Tab
        "patches_header": "Аудит целостности 4 ключевых патчей, исполняемых файлов и хранилища настроек:",
        "patches_summary_ok": "🟢 Все 4 патча активны | Исполняемые файлы и нейросети проверены | CONFIG защищён",
        "patches_summary_fail": "🔴 ВНИМАНИЕ: Обнаружен сбой или слетел патч! Нажмите «Восстановить патчи из CONFIG»",
        "btn_audit_refresh": "🔄 Перепроверить целостность",
        "btn_restore_patches": "🛠 Восстановить все патчи (1 клик)",
        "col_patch_stage": "Модуль",
        "col_patch_name": "Компонент / Патч",
        "col_patch_type": "Категория",
        "col_patch_status": "Состояние",
        "col_patch_desc": "Назначение",

        "hotkeys_label": "Клавиши:",
        "res_metrics": "Память: {ram} МБ | ЦП: {cpu}%",
        "res_stopped": "Служба остановлена",
    },
    "en": {
        "title": "Translation Ecosystem Programs Control Panel (Hub - 100% Offline)",
        "start_all": "▶ Launch All 3 Programs",
        "stop_all": "⏹ Stop All Programs",
        "tab_dashboard": "🎛 Control Panel & Workflows",
        "tab_inventory": "🧠 Local AI Models on Disk",
        "tab_patches": "🛡 Integrity & Patches",
        "tab_guide": "ℹ Architecture & Reference",
        "status_all_running": "🟢 All 3 programs active (0 MB Cloud)",
        "status_partial": "🟡 Active programs: {count} of 3",
        "status_stopped": "⚪ All programs stopped",

        # Module 1: Audio to Subtitles (LiveTranslate)
        "stage1_title": "1. Synchronous Subtitles (LiveTranslate)",
        "stage1_flow": "Pipeline: 🔊 PC Audio  ➔  ✂ VAD Chunking  ➔  🧠 SenseVoice + Hunyuan MT  ➔  📺 Screen Subtitles",
        "stage1_desc": "Captures system audio (video, media streams, conference calls, browser), segments speech in natural pauses, and displays real-time subtitles overlay.",
        "stage1_hotkeys": "F9 — Run/Pause & Hide Subtitles | 2x MMB — Click-through Lock | MMB Drag — Move Window",

        # Module 2: Screen OCR (OverTranslate)
        "stage2_title": "2. Screen Text Translator (OverTranslate)",
        "stage2_flow": "Pipeline: 🖼 Screen Box  ➔  🔍 OCR Scanner  ➔  🧠 MT Neural Model  ➔  📝 Result Window",
        "stage2_desc": "Optical character recognition (OCR) of non-selectable screen text in a bounding box (documents, UI dialogues, images) with instant translation.",
        "stage2_hotkeys": "Ctrl + Alt + A — Box OCR | Ctrl + C + C — Quick Clipboard Translate",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Voice Translator (Voice Studio)",
        "stage3_flow": "Pipeline: 🎙 Mic Input (RU)  ➔  ✂ VAD + Punctuation  ➔  🧠 GigaAM + Pocket-TTS  ➔  🔊 Virtual Mic Channel (EN)",
        "stage3_desc": "Speak Russian into your mic — converts and synthesizes real-time English speech with your cloned timbre into the chosen virtual microphone output.",
        "stage3_hotkeys": "Shift + Mouse Wheel Click — Push-To-Talk Voice Translation",

        "btn_start": "▶ Launch",
        "btn_stop": "⏹ Stop",
        "btn_open": "🗔 Open Window",
        "btn_studio": "🗔 Voice Studio",
        "btn_wizard": "🎙 Record Voice Sample (7 sec)",
        "wizard_desc": "Train the neural model to speak with your unique voice timbre in 7 seconds.",

        "status_running": "● Running",
        "status_stopped_pill": "○ Stopped",

        # Hardware audio selector
        "hardware_title": "Output audio channel for voice translation:",
        "hardware_topping": "🎛 Topping E2x2 (Hardware Loopback)",
        "hardware_cable": "🔌 Virtual Cable (VB-Audio Cable)",
        "hardware_install_cable": "📥 Install VB-Cable (1 Click)",
        "btn_open_folder": "📂 Protected Settings (CONFIG/)",

        # Inventory Tab
        "inventory_header": "Local Neural Models on SSD Audit (100% Offline Ready):",
        "btn_refresh": "🔄 Refresh Audit",
        "col_stage": "Module",
        "col_task": "Task",
        "col_model": "AI Model",
        "col_status": "Disk Status",
        "col_size": "Size (MB)",
        "ready": "✔ Ready (Offline)",
        "missing": "❌ Missing",

        # Patches & Health Tab
        "patches_header": "Integrity audit of the 4 Golden Patches, binaries, and CONFIG vault:",
        "patches_summary_ok": "🟢 All 4 patches active | Executables & models verified | CONFIG protected",
        "patches_summary_fail": "🔴 WARNING: Patch corruption detected! Click 'Restore All Patches from CONFIG'",
        "btn_audit_refresh": "🔄 Re-audit Integrity",
        "btn_restore_patches": "🛠 Restore All Patches (1 Click)",
        "col_patch_stage": "Module",
        "col_patch_name": "Component / Patch",
        "col_patch_type": "Category",
        "col_patch_status": "State",
        "col_patch_desc": "Function",

        "hotkeys_label": "Hotkeys:",
        "res_metrics": "RAM: {ram} MB | CPU: {cpu}%",
        "res_stopped": "Service stopped",
    },
    "zh": {
        "title": "离线翻译程序总控制台 (Hub - 100% 本地运行)",
        "start_all": "▶ 启动全部3个程序",
        "stop_all": "⏹ 停止全部程序",
        "tab_dashboard": "🎛 控制面板与数据流",
        "tab_inventory": "🧠 本地AI模型清单",
        "tab_patches": "🛡 补丁完整性与诊断",
        "tab_guide": "ℹ 系统架构与说明",
        "status_all_running": "🟢 全部3个程序运行中 (0 云端调用)",
        "status_partial": "🟡 运行中程序: {count} / 3",
        "status_stopped": "⚪ 全部程序已停止",

        # Module 1: Audio to Subtitles (LiveTranslate)
        "stage1_title": "1. 实时音频字幕 (LiveTranslate)",
        "stage1_flow": "流程: 🔊 系统音频  ➔  ✂ 语音切分  ➔  🧠 SenseVoice + Hunyuan MT  ➔  📺 屏幕顶层字幕",
        "stage1_desc": "捕获系统声音（视频、会议、浏览器），在说话停顿处切分并在屏幕最顶层显示透明双语字幕.",
        "stage1_hotkeys": "F9 — 启停/隐藏字幕 | 双击中键 — 鼠标穿透 | 拖拽中键 — 移动字幕",

        # Module 2: Screen OCR (OverTranslate)
        "stage2_title": "2. 屏幕划词翻译 (OverTranslate)",
        "stage2_flow": "流程: 🖼 屏幕选区  ➔  🔍 OCR光学扫描  ➔  🧠 翻译模型  ➔  📝 翻译窗口",
        "stage2_desc": "框选屏幕任意不可复制文字（文档、图片、界面）并原地光学识别与翻译.",
        "stage2_hotkeys": "Ctrl + Alt + A — 框选截屏 | Ctrl + C + C — 查词",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. 语音合成翻译 (Voice Studio)",
        "stage3_flow": "流程: 🎙 麦克风输入 (RU)  ➔  ✂ 断句加标点  ➔  🧠 GigaAM + Pocket-TTS  ➔  🔊 虚拟麦克风 (EN)",
        "stage3_desc": "您说俄语，系统实时翻译为英语并通过专属克隆声线输出到虚拟麦克风通道.",
        "stage3_hotkeys": "Shift + 鼠标中键 — 对讲机通话 (PTT)",

        "btn_start": "▶ 启动",
        "btn_stop": "⏹ 停止",
        "btn_open": "🗔 打开窗口",
        "btn_studio": "🗔 声音控制台",
        "btn_wizard": "🎙 录制专属声音 (7秒)",
        "wizard_desc": "仅需7秒录音即可让AI克隆您的声线.",

        "status_running": "● 运行中",
        "status_stopped_pill": "○ 已停止",

        # Hardware audio selector
        "hardware_title": "语音输出虚拟通道路由:",
        "hardware_topping": "🎛 Topping E2x2 (硬件回路)",
        "hardware_cable": "🔌 虚拟音频线 (VB-Audio Cable)",
        "hardware_install_cable": "📥 一键安装虚拟音频线",
        "btn_open_folder": "📂 受保护配置 (CONFIG/)",

        # Inventory Tab
        "inventory_header": "本地神经模型清单 (100% 离线):",
        "btn_refresh": "🔄 刷新",
        "col_stage": "模块",
        "col_task": "任务",
        "col_model": "AI 模型",
        "col_status": "状态",
        "col_size": "大小 (MB)",
        "ready": "✔ 已就绪",
        "missing": "❌ 缺失",

        # Patches & Health Tab
        "patches_header": "四大核心补丁完整性、二进制文件与配置库审计:",
        "patches_summary_ok": "🟢 全部4个补丁正常 | 模型与程序完好 | CONFIG 受保护",
        "patches_summary_fail": "🔴 警告: 补丁丢失或异常！请点击一键从CONFIG还原",
        "btn_audit_refresh": "🔄 重新审计",
        "btn_restore_patches": "🛠 一键恢复补丁",
        "col_patch_stage": "模块",
        "col_patch_name": "组件/补丁",
        "col_patch_type": "类别",
        "col_patch_status": "状态",
        "col_patch_desc": "功能说明",

        "hotkeys_label": "快捷键:",
        "res_metrics": "内存: {ram} MB | CPU: {cpu}%",
        "res_stopped": "服务已停止",
    },
}


class I18n:
    """Static helper for application internationalization."""

    _current_lang = "ru"

    @classmethod
    def set_language(cls, lang: str):
        if lang in TRANSLATIONS:
            cls._current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        dict_lang = TRANSLATIONS.get(cls._current_lang, TRANSLATIONS["ru"])
        text = dict_lang.get(key, TRANSLATIONS["ru"].get(key, key))
        if kwargs:
            text = text.format(**kwargs)
        return text
