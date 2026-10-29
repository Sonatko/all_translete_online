"""Trilingual Localization (i18n) for Translation Ecosystem Hub.
Supports Russian, English, and Chinese.
"""
from __future__ import annotations

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        "title": "Универсальный Центр Управления Экосистемой Перевода (Hub)",
        "start_all": "🚀 ЗАПУСТИТЬ ВСЮ ЭКОСИСТЕМУ",
        "stop_all": "⏹ ОСТАНОВИТЬ ВСЁ",
        "tab_dashboard": "🚀 Пульт управления этапами",
        "tab_inventory": "🧠 Инвентарь нейросетей (100% Офлайн)",
        "tab_vault": "🛡 Патчи и Защита обновлений",
        "tab_guide": "📖 Схема и Архитектура экосистемы",
        "status_all_running": "🟢 ВСЯ ЭКОСИСТЕМА АКТИВНА (3/3 процессов) | VRAM: 0 MB",
        "status_partial": "🟡 Активно процессов: {count}/3 | VRAM: 0 MB",
        "status_stopped": "⚪ Все сервисы остановлены | ОЗУ свободно | VRAM: 0 MB",
        "stage1_title": "Этап 1: Входящий звук и субтитры (LiveTranslate)",
        "stage1_desc": "Sherpa-ONNX SenseVoice + Tencent HY-MT 1.8B. Прозрачные субтитры поверх игр и видео (RU / EN / ZH).",
        "stage1_hotkeys": "F9 (Вкл/Пауза), 2x MMB (Клик-сквозь), MMB Drag (Двигать)",
        "stage2_title": "Этап 2: Экранный OCR и текст (OverTranslate)",
        "stage2_desc": "Сверхбыстрый перевод текста с экрана рамкой, перевод буфера обмена и замена текста в чатах.",
        "stage2_hotkeys": "Ctrl+Alt+A (Рамка), Ctrl+C+C (Словарь), Ctrl+Alt+C (Замена)",
        "stage3_title": "Этап 3: Исходящий голос в CS2 / Discord (Voice Studio)",
        "stage3_desc": "Sber GigaAM v3 CTC + Opus-MT + Kyutai Pocket-TTS. Перевод речи в игре вашим клонированным голосом.",
        "stage3_hotkeys": "Shift + MMB (Рация PTT), Выход: Playback 3/4 ➔ Topping Loopback",
        "btn_start": "▶ Запустить",
        "btn_open": "Открыть окно",
        "wizard_hero_title": "⭐ Студия обучения модели под свой голос (7-Second Voice Cloning)",
        "wizard_hero_desc": "Любой человек может за 7 секунд обучить модель говорить его собственным тембром. Нажмите кнопку, прочитайте фразу в микрофон, и нейросеть сохранит ваш персональный профиль в CONFIG/.",
        "btn_wizard": "🎙 ОБУЧИТЬ ГОЛОС ПОД СЕБЯ",
        "status_running": "🟢 Работает",
        "status_stopped_pill": "⚪ Остановлен",
        "inventory_header": "Аудит локальных нейросетей на SSD-диске (100% Офлайн-готовность):",
        "btn_refresh": "🔄 Обновить статус",
        "col_stage": "Этап",
        "col_task": "Задача",
        "col_model": "Модель",
        "col_status": "Статус на диске",
        "col_size": "Размер (МБ)",
        "ready": "✔ Скачана (Готова)",
        "missing": "❌ Не найдена",
        "lang_selector": "Язык интерфейса / Language / 语言:",
        "hotkeys_label": "Горячие клавиши:",
    },
    "en": {
        "title": "Universal Real-Time Translation Ecosystem Hub & Supervisor",
        "start_all": "🚀 LAUNCH ENTIRE ECOSYSTEM",
        "stop_all": "⏹ STOP ALL SERVICES",
        "tab_dashboard": "🚀 Ecosystem Dashboard",
        "tab_inventory": "🧠 AI Models Inventory (100% Offline)",
        "tab_vault": "🛡 Patches & Upstream Vault",
        "tab_guide": "📖 Architecture & Signal Flow Guide",
        "status_all_running": "🟢 ALL ECOSYSTEM SERVICES ACTIVE (3/3) | VRAM: 0 MB",
        "status_partial": "🟡 Active services: {count}/3 | VRAM: 0 MB",
        "status_stopped": "⚪ All services stopped | RAM cleared | VRAM: 0 MB",
        "stage1_title": "Stage 1: Incoming Audio & Subtitles (LiveTranslate)",
        "stage1_desc": "Sherpa-ONNX SenseVoice + Tencent HY-MT 1.8B. Real-time overlay subtitles for games & media (RU / EN / ZH).",
        "stage1_hotkeys": "F9 (Toggle/Pause), 2x MMB (Click-through), MMB Drag (Move)",
        "stage2_title": "Stage 2: Screen OCR & Text Translation (OverTranslate)",
        "stage2_desc": "Instant screen bounding-box OCR, clipboard interception, and in-place chat text replacement.",
        "stage2_hotkeys": "Ctrl+Alt+A (Box OCR), Ctrl+C+C (QuickLookup), Ctrl+Alt+C (Replace)",
        "stage3_title": "Stage 3: Outgoing Voice in CS2 / Discord (Voice Studio)",
        "stage3_desc": "Sber GigaAM v3 CTC + Opus-MT + Kyutai Pocket-TTS. Outgoing voice translation with your cloned voice timbre.",
        "stage3_hotkeys": "Shift + MMB (PTT Wheel Click), Output: Playback 3/4 ➔ Topping Loopback",
        "btn_start": "▶ Launch",
        "btn_open": "Open Window",
        "wizard_hero_title": "⭐ 7-Second Voice Cloning Studio (Train Your AI Voice)",
        "wizard_hero_desc": "Anyone can train the model to speak in their own voice timbre in just 7 seconds. Read the prompt into your mic, and the Mimi neural codec saves your voice profile to CONFIG/.",
        "btn_wizard": "🎙 CLONE YOUR VOICE NOW",
        "status_running": "🟢 Running",
        "status_stopped_pill": "⚪ Stopped",
        "inventory_header": "Local Neural Models Audit on SSD (100% Offline Ready):",
        "btn_refresh": "🔄 Refresh Audit",
        "col_stage": "Stage",
        "col_task": "Task",
        "col_model": "Model",
        "col_status": "Disk Status",
        "col_size": "Size (MB)",
        "ready": "✔ Ready (Offline)",
        "missing": "❌ Not Found",
        "lang_selector": "Interface Language / 语言:",
        "hotkeys_label": "Hotkeys:",
    },
    "zh": {
        "title": "通用实时翻译生态控制中心 (Hub & Supervisor)",
        "start_all": "🚀 一键启动全部生态系统",
        "stop_all": "⏹ 停止全部服务",
        "tab_dashboard": "🚀 生态控制台",
        "tab_inventory": "🧠 本地AI模型清单 (100% 离线)",
        "tab_vault": "🛡 补丁与配置隔离保护",
        "tab_guide": "📖 系统架构与音频流图解",
        "status_all_running": "🟢 全部生态系统服务运行中 (3/3) | 显存占用: 0 MB",
        "status_partial": "🟡 运行中服务: {count}/3 | 显存占用: 0 MB",
        "status_stopped": "⚪ 全部服务已停止 | 内存已释放 | 显存占用: 0 MB",
        "stage1_title": "阶段一: 游戏与系统音频实时字幕 (LiveTranslate)",
        "stage1_desc": "Sherpa-ONNX SenseVoice + 腾讯混元 HY-MT 1.8B. 游戏与视频顶层透明字幕 (中文 / 俄语 / 英语).",
        "stage1_hotkeys": "F9 (全局开关), 双击滚轮 (鼠标穿透锁定), 滚轮拖拽 (移动字幕)",
        "stage2_title": "阶段二: 屏幕OCR划词翻译 (OverTranslate)",
        "stage2_desc": "框选屏幕OCR、剪贴板快速查词、聊天框原地快速翻译替换.",
        "stage2_hotkeys": "Ctrl+Alt+A (截图OCR), Ctrl+C+C (词典查词), Ctrl+Alt+C (原地替换)",
        "stage3_title": "阶段三: 游戏对局专属同声传译 (Voice Studio - CS2/Discord)",
        "stage3_desc": "Sber GigaAM v3 CTC + Opus-MT + Kyutai Pocket-TTS. 实时使用您自己的克隆声线在游戏中说英语.",
        "stage3_hotkeys": "Shift + 鼠标中键 (对讲机PTT), 输出通道: Playback 3/4 ➔ Topping Loopback",
        "btn_start": "▶ 启动",
        "btn_open": "打开窗口",
        "wizard_hero_title": "⭐ 7秒声音克隆训练工坊 (定制专属声线)",
        "wizard_hero_desc": "任何人只需朗读7秒语音，Mimi神经编解码器即可提取独特的声线特征向量，并永久保存至 CONFIG/ 目录.",
        "btn_wizard": "🎙 立即克隆我的声线",
        "status_running": "🟢 运行中",
        "status_stopped_pill": "⚪ 已停止",
        "inventory_header": "SSD 本地神经模型清单审计 (100% 离线可用):",
        "btn_refresh": "🔄 刷新状态",
        "col_stage": "阶段",
        "col_task": "任务",
        "col_model": "模型",
        "col_status": "磁盘状态",
        "col_size": "大小 (MB)",
        "ready": "✔ 已就绪 (离线)",
        "missing": "❌ 未找到",
        "lang_selector": "界面语言 / Language / Язык:",
        "hotkeys_label": "快捷键:",
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

