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
        "tab_dashboard": "🎛 Пульт управления",
        "tab_patches": "🛡 Защита и Патчи",
        "tab_guide": "📖 Памятка на будущее",
        "status_all_running": "🟢 Все 3 программы активны (0 MB облака)",
        "status_partial": "🟡 Работает программ: {count} из 3",
        "status_stopped": "⚪ Все программы остановлены",

        # Module 1: Audio to Subtitles (LiveTranslate)
        "stage1_title": "1. Потоковое распознавание и перевод аудио (LiveTranslate)",
        "stage1_flow": "Конвейер: 🔊 WASAPI Loopback ➔ ✂ Silero VAD ➔ 🎙 SenseVoice INT8 ➔ 🧠 Tencent HY-MT1.5 ➔ 📺 Overlay",
        "stage1_desc": "Низколатентный захват системного аудиопотока через WASAPI Loopback, сегментация речи через нейросетевой VAD, акустическое распознавание ASR и синхронный машинный перевод в оверлей субтитров.",
        "stage1_hotkeys": "F9 — Master Toggle (Вкл/Пауза) | 2x MMB — Click-Through (Сквозной клик) | MMB Drag — Перемещение окна",

        # Module 2: Screen OCR (OverTranslate)
        "stage2_title": "2. Оптическое распознавание и перевод с экрана (OverTranslate)",
        "stage2_flow": "Конвейер: 🖼 Экранный захват ➔ 🔍 RapidOcrNet ONNX ➔ 🌐 Microsoft MT ➔ 📝 Оверлей перевода",
        "stage2_desc": "Оптический захват невыделяемых экранных областей (OCR PP-OCRv6 ONNX) и перехват буфера обмена Windows с автоматической заменой текста на перевод.",
        "stage2_hotkeys": "Ctrl + Alt + A — Выделение прямоугольной области | Ctrl + C + C — Перевод выделенного текста из буфера",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Синхронный перевод речи и нейросинтез тембра (Voice Studio)",
        "stage3_flow": "Конвейер: 🎙 Входной микрофон (RU) ➔ ✂ VAD ➔ 🧠 GigaAM CTC ➔ 📝 Opus-MT ➔ 🗣 Pocket-TTS ➔ 🔊 Выходной аудиоканал",
        "stage3_desc": "Потоковый конвейер Speech-to-Speech: акустическое распознавание русской речи (GigaAM), машинный перевод (Opus-MT) и синтез английской речи клонированным голосом (Pocket-TTS) в виртуальный микрофонный канал.",
        "stage3_hotkeys": "Shift + Колесико мыши — Активация рации (Push-To-Talk / PTT)",

        "btn_start": "▶ Запустить",
        "btn_stop": "⏹ Остановить",
        "btn_open": "🗔 Открыть окно",
        "btn_studio": "🗔 Студия речи",
        "btn_wizard": "🎙 Записать образец голоса (7 сек)",
        "wizard_desc": "Обучить программу говорить вашим персональным тембром голоса за 7 секунд.",

        "status_running": "● Работает",
        "status_stopped_pill": "○ Остановлена",

        # Dynamic Latency Monitor
        "latency_prefix": "⏱ Задержка пайплайна:",
        "latency_mode_local": "100% Локально (CPU)",
        "latency_mode_cloud": "Облачный API",

        # Hardware audio selector
        "hardware_title": "Канал вывода переведенного голоса:",
        "hardware_topping": "🎛 Topping E2x2 (Аппаратный Loopback)",
        "hardware_cable": "🔌 Виртуальный кабель (VB-Audio Cable)",
        "hardware_install_cable": "📥 Установить VB-Cable (1 клик)",
        "btn_open_folder": "📂 Защищенные настройки (CONFIG/)",

        # Audio profile switch feedback
        "profile_topping_title": "Профиль Topping E2x2 активен",
        "profile_topping_msg": "Аудиоканал переключен на Topping E2x2!\n\n• Аппаратная петля Topping Loopback: задержка ~0 мс.\n• В Discord, Zoom и звонках выберите микрофон: 'Loopback 1/2'.",
        "profile_cable_title": "Профиль Виртуального кабеля активен",
        "profile_cable_msg": "Аудиоканал переключен на Виртуальный Кабель!\n\n• Программа отправляет голос ИИ в: 'CABLE Input'.\n• В Discord, Zoom и звонках выберите микрофон: 'CABLE Output'.",

        # Virtual cable prompt dialog
        "cable_not_found_title": "Виртуальный аудиокабель не обнаружен",
        "cable_not_found_msg": "Виртуальный аудиокабель (VB-Audio Cable) не установлен в вашей системе Windows.\n\nОн необходим для передачи переведенного голоса в программы связи на компьютерах без звуковой карты Topping.\n\nХотите скачать и установить его прямо сейчас в 1 клик?",

        # Patches & Health Tab (Modular Structure)
        "patches_header": "Состояние инженерных патчей экосистемы (разбивка по 3 модулям):",
        "patches_summary_ok": "🟢 Все ключевые патчи активны ({active}/{total}) | Настройки и файлы в CONFIG/ защищены",
        "patches_summary_fail": "🔴 ВНИМАНИЕ: Слетел патч или повреждён файл! Нажмите «Восстановить все патчи»",
        "btn_audit_refresh": "🔄 Перепроверить целостность",
        "btn_audit_refresh_done": "✓ Проверено: Все патчи на месте!",
        "btn_restore_patches": "🛠 Восстановить все патчи (1 клик)",
        "m1_group_title": "📦 Модуль 1: Синхронные субтитры (LiveTranslate) — 6 инженерных патчей ядра",
        "m2_group_title": "📦 Модуль 2: Экранный переводчик (OverTranslate) — Готовая программа + фикс буфера Windows 11",
        "m3_group_title": "📦 Модуль 3: Голосовой переводчик (Voice Studio) — 100% Собственный движок",
        "vault_group_title": "🔒 Хранилище эталонов (CONFIG/) — Защита от обновлений авторов",

        "hotkeys_label": "Клавиши:",
        "res_metrics": "Память: {ram} МБ | ЦП: {cpu}%",
        "res_stopped": "Служба остановлена",
    },
    "en": {
        "title": "Translation Ecosystem Programs Control Panel (Hub - 100% Offline)",
        "start_all": "▶ Launch All 3 Programs",
        "stop_all": "⏹ Stop All Programs",
        "tab_dashboard": "🎛 Control Panel",
        "tab_patches": "🛡 Integrity & Patches",
        "tab_guide": "📖 Future Reference Guide",
        "status_all_running": "🟢 All 3 programs active (0 MB Cloud)",
        "status_partial": "🟡 Active programs: {count} of 3",
        "status_stopped": "⚪ All programs stopped",

        # Module 1: Audio to Subtitles (LiveTranslate)
        "stage1_title": "1. Streaming Audio Transcription & Translation (LiveTranslate)",
        "stage1_flow": "Pipeline: 🔊 WASAPI Loopback ➔ ✂ Silero VAD ➔ 🎙 SenseVoice INT8 ➔ 🧠 Tencent HY-MT1.5 ➔ 📺 Overlay",
        "stage1_desc": "Low-latency system audio ingestion via WASAPI Loopback, speech segmentation via neural VAD, ASR acoustic decoding, and synchronous MT overlay.",
        "stage1_hotkeys": "F9 — Master Toggle (Run/Pause) | 2x MMB — Click-Through Lock | MMB Drag — Move Window",

        # Module 2: Screen OCR (OverTranslate)
        "stage2_title": "2. Optical Character Recognition & Screen Translation (OverTranslate)",
        "stage2_flow": "Pipeline: 🖼 Screen Capture ➔ 🔍 RapidOcrNet ONNX ➔ 🌐 Microsoft MT ➔ 📝 Translation Overlay",
        "stage2_desc": "Bounding-box screen OCR (PP-OCRv6 ONNX) and clipboard interceptor with in-place translation replacement.",
        "stage2_hotkeys": "Ctrl + Alt + A — Bounding Box OCR | Ctrl + C + C — Clipboard Text Translation",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Synchronous Speech Translation & Timbre Cloning (Voice Studio)",
        "stage3_flow": "Pipeline: 🎙 Mic Input (RU) ➔ ✂ VAD ➔ 🧠 GigaAM CTC ➔ 📝 Opus-MT ➔ 🗣 Pocket-TTS ➔ 🔊 Output Channel",
        "stage3_desc": "Real-time Speech-to-Speech pipeline: Russian ASR (GigaAM), neural translation (Opus-MT), and voice cloning synthesis (Pocket-TTS) into virtual mic.",
        "stage3_hotkeys": "Shift + Mouse Wheel — Push-To-Talk (PTT)",

        "btn_start": "▶ Launch",
        "btn_stop": "⏹ Stop",
        "btn_open": "🗔 Open Window",
        "btn_studio": "🗔 Voice Studio",
        "btn_wizard": "🎙 Record Voice Sample (7 sec)",
        "wizard_desc": "Train the neural model to speak with your unique voice timbre in 7 seconds.",

        "status_running": "● Running",
        "status_stopped_pill": "○ Stopped",

        # Dynamic Latency Monitor
        "latency_prefix": "⏱ Pipeline Latency:",
        "latency_mode_local": "100% Offline (CPU)",
        "latency_mode_cloud": "Cloud API",

        # Hardware audio selector
        "hardware_title": "Translated voice output audio channel:",
        "hardware_topping": "🎛 Topping E2x2 (Hardware Loopback)",
        "hardware_cable": "🔌 Virtual Cable (VB-Audio Cable)",
        "hardware_install_cable": "📥 Install VB-Cable (1 Click)",
        "btn_open_folder": "📂 Protected Settings (CONFIG/)",

        # Audio profile switch feedback
        "profile_topping_title": "Topping E2x2 Profile Active",
        "profile_topping_msg": "Audio channel switched to Topping E2x2!\n\n• Hardware Loopback latency: ~0 ms.\n• In Discord, Zoom and calls select microphone: 'Loopback 1/2'.",
        "profile_cable_title": "Virtual Cable Profile Active",
        "profile_cable_msg": "Audio channel switched to Virtual Cable!\n\n• Voice synth outputs to: 'CABLE Input'.\n• In Discord, Zoom and calls select microphone: 'CABLE Output'.",

        # Virtual cable prompt dialog
        "cable_not_found_title": "Virtual Audio Cable Not Found",
        "cable_not_found_msg": "VB-Audio Virtual Cable was not detected in your Windows system.\n\nIt is required to route voice translations into voice software on PCs without a Topping sound card.\n\nWould you like to download and install it now in 1 click?",

        # Patches & Health Tab (Modular Structure)
        "patches_header": "Engineering Patches and Modules Integrity Audit (Grouped by Module):",
        "patches_summary_ok": "🟢 All key patches active ({active}/{total}) | Settings and files in CONFIG/ protected",
        "patches_summary_fail": "🔴 WARNING: Patch corrupted or missing! Click 'Restore All Patches'",
        "btn_audit_refresh": "🔄 Re-audit Integrity",
        "btn_audit_refresh_done": "✓ Verified: All patches intact!",
        "btn_restore_patches": "🛠 Restore All Patches (1 Click)",
        "m1_group_title": "📦 Module 1: Synchronous Subtitles (LiveTranslate) — 6 Engineering Patches",
        "m2_group_title": "📦 Module 2: Screen Translator (OverTranslate) — Portable App + Win11 Clipboard Bugfix",
        "m3_group_title": "📦 Module 3: Voice Translator (Voice Studio) — 100% In-Process Engine",
        "vault_group_title": "🔒 Vault Storage (CONFIG/) — Protection against upstream updates",

        "hotkeys_label": "Hotkeys:",
        "res_metrics": "RAM: {ram} MB | CPU: {cpu}%",
        "res_stopped": "Service stopped",
    },
    "zh": {
        "title": "离线翻译程序总控制台 (Hub - 100% 本地运行)",
        "start_all": "▶ 启动全部3个程序",
        "stop_all": "⏹ 停止全部程序",
        "tab_dashboard": "🎛 控制面板",
        "tab_patches": "🛡 补丁完整性",
        "tab_guide": "📖 长期架构指南",
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

        # Dynamic Latency Monitor
        "latency_prefix": "⏱ 流程延迟:",
        "latency_mode_local": "100% 本地运行 (CPU)",
        "latency_mode_cloud": "云端 API",

        # Hardware audio selector
        "hardware_title": "语音输出虚拟通道路由:",
        "hardware_topping": "🎛 Topping E2x2 (硬件回路)",
        "hardware_cable": "🔌 虚拟音频线 (VB-Audio Cable)",
        "hardware_install_cable": "📥 一键安装虚拟音频线",
        "btn_open_folder": "📂 受保护配置 (CONFIG/)",

        # Audio profile switch feedback
        "profile_topping_title": "已激活 Topping E2x2 配置文件",
        "profile_topping_msg": "音频已切换至 Topping E2x2!\n\n• 硬件回路延迟: ~0 毫秒.\n• 在语音软件中选择麦克风: 'Loopback 1/2'.",
        "profile_cable_title": "已激活虚拟音频线配置文件",
        "profile_cable_msg": "音频已切换至虚拟音频线!\n\n• 声音输出至: 'CABLE Input'.\n• 在语音软件中选择麦克风: 'CABLE Output'.",

        # Virtual cable prompt dialog
        "cable_not_found_title": "未检测到虚拟音频线",
        "cable_not_found_msg": "系统中未检测到 VB-Audio Virtual Cable.\n\n普通电脑需要此驱动将声音路由至语音软件.\n\n是否立即一键下载并安装？",

        # Patches & Health Tab (Modular Structure)
        "patches_header": "核心工程补丁与模块完整性（按模块分组）：",
        "patches_summary_ok": "🟢 全部核心补丁正常运行 ({active}/{total}) | CONFIG/ 配置受保护",
        "patches_summary_fail": "🔴 警告: 补丁异常！请点击一键恢复补丁",
        "btn_audit_refresh": "🔄 重新审计完整性",
        "btn_audit_refresh_done": "✓ 已验证: 全部补丁就绪！",
        "btn_restore_patches": "🛠 一键恢复全部补丁",
        "m1_group_title": "📦 模块 1: 同步字幕 (LiveTranslate) — 6 个核心补丁",
        "m2_group_title": "📦 模块 2: 屏幕翻译 (OverTranslate) — 便携独立程序 + Win11 剪贴板修复",
        "m3_group_title": "📦 模块 3: 语音翻译 (Voice Studio) — 100% 自研本地引擎",
        "vault_group_title": "🔒 备份金库 (CONFIG/) — 防止作者更新覆盖",

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
