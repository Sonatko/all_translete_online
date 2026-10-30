"""Trilingual Localization (i18n) for Translation Ecosystem Hub.
Supports Russian, English, and Chinese. Clean KISS terminology.
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
        "tab_guide": "ℹ Справка и Архитектура",
        "status_all_running": "🟢 Все 3 программы активны (0 MB облака)",
        "status_partial": "🟡 Работает программ: {count} из 3",
        "status_stopped": "⚪ Все программы остановлены",

        # Module 1: Audio to Subtitles
        "stage1_title": "1. Переводчик звука ➔ Субтитры на экране (LiveTranslate)",
        "stage1_flow": "Схема: 🔊 Звук из ПК  ➔  ✂ Нарезка фраз  ➔  🧠 SenseVoice + MT  ➔  📺 Субтитры на экране",
        "stage1_desc": "Захватывает любой звук из видео, фильмов, звонков и браузера, нарезает на фразы в паузах и выводит перевод прозрачными субтитрами поверх всех окон.",
        "stage1_hotkeys": "F9 — Скрыть/Показать субтитры | 2x MMB — Клик сквозь окно",

        # Module 2: Screen OCR
        "stage2_title": "2. Экранный переводчик ➔ Текст по рамке (OverTranslate)",
        "stage2_flow": "Схема: 🖼 Рамка на экране  ➔  🔍 OCR сканер  ➔  🧠 Нейросеть перевода  ➔  📝 Окно с текстом",
        "stage2_desc": "Выделяете прямоугольную область на экране в любом месте (игры, книги, картинки, чаты) — программа распознает текст с пикселей и мгновенно переводит.",
        "stage2_hotkeys": "Ctrl + Alt + A — Выделить рамкой | Ctrl + C + C — Быстрый перевод слова",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Переводчик голоса ➔ Микрофон в Discord и игры (Voice Studio)",
        "stage3_flow": "Схема: 🎙 Ваш микрофон (RU)  ➔  ✂ Нарезка + Вдохи  ➔  🧠 GigaAM + Pocket-TTS  ➔  🎧 Выход в Discord (EN)",
        "stage3_desc": "Вы говорите в микрофон по-русски — собеседники в Discord или играх слышат английский перевод вашим собственным клонированным тембром.",
        "stage3_hotkeys": "Shift + Колесико мыши — Говорить в микрофон с переводом",

        "btn_start": "▶ Запустить",
        "btn_stop": "⏹ Остановить",
        "btn_open": "🗔 Открыть окно",
        "btn_studio": "🗔 Студия голоса",
        "btn_wizard": "🎙 Записать свой голос (7 сек)",
        "wizard_desc": "Обучить программу говорить вашим тембром голоса за 7 секунд.",

        "status_running": "● Работает",
        "status_stopped_pill": "○ Остановлена",

        "hardware_title": "Звуковое устройство для перевода голоса:",
        "hardware_topping": "🎛 Topping E2x2 (Аппаратный Loopback)",
        "hardware_cable": "🔌 Виртуальный кабель (Обычный ПК)",
        "hardware_install_cable": "📥 Установить VB-Cable (1 клик)",
        "btn_open_folder": "📂 Папка с настройками (CONFIG/)",

        "inventory_header": "Проверка файлов локальных нейросетей на SSD (100% готовность без интернета):",
        "btn_refresh": "🔄 Проверить файлы",
        "col_stage": "Модуль",
        "col_task": "Задача",
        "col_model": "Модель ИИ",
        "col_status": "Статус на диске",
        "col_size": "Размер (МБ)",
        "ready": "✔ Скачана (Готова к работе)",
        "missing": "❌ Отсутствует",
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
        "tab_guide": "ℹ Architecture & Reference",
        "status_all_running": "🟢 All 3 programs active (0 MB Cloud)",
        "status_partial": "🟡 Active programs: {count} of 3",
        "status_stopped": "⚪ All programs stopped",

        # Module 1: Audio to Subtitles
        "stage1_title": "1. Audio Translator ➔ Screen Subtitles (LiveTranslate)",
        "stage1_flow": "Pipeline: 🔊 PC Audio  ➔  ✂ VAD Chunking  ➔  🧠 SenseVoice + MT  ➔  📺 Screen Subtitles",
        "stage1_desc": "Captures any audio from videos, calls, movies and browser, splits into phrases during pauses, and displays transparent overlay subtitles.",
        "stage1_hotkeys": "F9 — Hide/Show Subtitles | 2x MMB — Click-through Lock",

        # Module 2: Screen OCR
        "stage2_title": "2. Screen Text Translator ➔ Bounding Box (OverTranslate)",
        "stage2_flow": "Pipeline: 🖼 Screen Box  ➔  🔍 OCR Reader  ➔  🧠 MT Neural Model  ➔  📝 Result Window",
        "stage2_desc": "Draw a bounding box anywhere on screen (games, documents, images) — extracts text from pixels and translates instantly.",
        "stage2_hotkeys": "Ctrl + Alt + A — Box OCR | Ctrl + C + C — Quick Word Lookup",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. Voice Translator ➔ Microphone in Discord/Games (Voice Studio)",
        "stage3_flow": "Pipeline: 🎙 Your Mic (RU)  ➔  ✂ Chunking + Punctuation  ➔  🧠 GigaAM + Pocket-TTS  ➔  🎧 Discord Output (EN)",
        "stage3_desc": "Speak Russian into your mic — teammates in Discord or games hear fluent English translated in your own cloned voice timbre.",
        "stage3_hotkeys": "Shift + Mouse Wheel Click — Push-To-Talk Voice Translation",

        "btn_start": "▶ Launch",
        "btn_stop": "⏹ Stop",
        "btn_open": "🗔 Open Window",
        "btn_studio": "🗔 Open Voice Studio",
        "btn_wizard": "🎙 Record Your Voice (7 sec)",
        "wizard_desc": "Train the model to speak with your voice timbre in 7 seconds.",

        "status_running": "● Running",
        "status_stopped_pill": "○ Stopped",

        "hardware_title": "Audio output device for voice translation:",
        "hardware_topping": "🎛 Topping E2x2 (Hardware Loopback)",
        "hardware_cable": "🔌 Virtual Cable (Standard PC)",
        "hardware_install_cable": "📥 Install VB-Cable (1 Click)",
        "btn_open_folder": "📂 Open Settings Folder (CONFIG/)",

        "inventory_header": "Local Neural Models on SSD Audit (100% Offline Ready):",
        "btn_refresh": "🔄 Refresh Audit",
        "col_stage": "Module",
        "col_task": "Task",
        "col_model": "AI Model",
        "col_status": "Disk Status",
        "col_size": "Size (MB)",
        "ready": "✔ Ready (Offline)",
        "missing": "❌ Missing",
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
        "tab_guide": "ℹ 系统架构与说明",
        "status_all_running": "🟢 全部3个程序运行中 (0 云端调用)",
        "status_partial": "🟡 运行中程序: {count} / 3",
        "status_stopped": "⚪ 全部程序已停止",

        # Module 1: Audio to Subtitles
        "stage1_title": "1. 声音翻译器 ➔ 屏幕透明字幕 (LiveTranslate)",
        "stage1_flow": "流程: 🔊 系统音频  ➔  ✂ 语音切分  ➔  🧠 SenseVoice + MT  ➔  📺 屏幕顶层字幕",
        "stage1_desc": "截取视频、影视和会议音频，在停顿处自动切分，并在屏幕顶层显示透明双语字幕.",
        "stage1_hotkeys": "F9 — 显示/隐藏字幕 | 双击滚轮 — 鼠标穿透",

        # Module 2: Screen OCR
        "stage2_title": "2. 屏幕划词翻译器 ➔ 截图框选 (OverTranslate)",
        "stage2_flow": "流程: 🖼 屏幕选区  ➔  🔍 OCR光学识别  ➔  🧠 翻译模型  ➔  📝 翻译窗口",
        "stage2_desc": "框选屏幕任意不可复制文字（游戏、文档、图片）并原地快速翻译.",
        "stage2_hotkeys": "Ctrl + Alt + A — 框选截屏 | Ctrl + C + C — 查词",

        # Module 3: Outgoing Voice Studio
        "stage3_title": "3. 语音翻译器 ➔ 麦克风输出至对局 (Voice Studio)",
        "stage3_flow": "流程: 🎙 麦克风输入  ➔  ✂ 断句加标点  ➔  🧠 GigaAM + Pocket-TTS  ➔  🎧 声卡输出 (英文)",
        "stage3_desc": "您说俄语，程序自动翻译并使用您自己的克隆声线在游戏中说英语.",
        "stage3_hotkeys": "Shift + 鼠标滚轮中键 — 对讲机说话",

        "btn_start": "▶ 启动",
        "btn_stop": "⏹ 停止",
        "btn_open": "🗔 打开窗口",
        "btn_studio": "🗔 声音控制台",
        "btn_wizard": "🎙 录制专属声音 (7秒)",
        "wizard_desc": "仅需7秒录音即可让AI克隆您的声线.",

        "status_running": "● 运行中",
        "status_stopped_pill": "○ 已停止",

        "hardware_title": "声音输出设备路由:",
        "hardware_topping": "🎛 Topping E2x2 (硬件回路)",
        "hardware_cable": "🔌 虚拟音频线 (普通电脑)",
        "hardware_install_cable": "📥 一键安装虚拟音频线",
        "btn_open_folder": "📂 打开配置目录 (CONFIG/)",

        "inventory_header": "本地神经模型清单 (100% 离线):",
        "btn_refresh": "🔄 刷新",
        "col_stage": "模块",
        "col_task": "任务",
        "col_model": "AI 模型",
        "col_status": "状态",
        "col_size": "大小 (MB)",
        "ready": "✔ 已就绪",
        "missing": "❌ 缺失",
        "hotkeys_label": "快捷键:",
        "res_metrics": "内存: {ram} MB | CPU: {cpu}%",
        "res_stopped": "已停止",
    }
}


class I18n:
    current_lang: str = "ru"

    @classmethod
    def set_language(cls, lang: str):
        if lang in TRANSLATIONS:
            cls.current_lang = lang

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        text = TRANSLATIONS.get(cls.current_lang, {}).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text
