# Universal Real-Time Translation & Subtitle Ecosystem (Windows)

[![Release](https://img.shields.io/github/v/release/Sonatko/all_translete_online?color=blue&label=Latest%20Release)](https://github.com/Sonatko/all_translete_online/releases)
[![License](https://img.shields.io/badge/License-MIT%20%2F%20Apache-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20x64-blue.svg)](https://microsoft.com)

**[English & Русский (README.md)](README.md)** | **[简体中文操作指南 (README_ZH.md)](README_ZH.md)**

A production-grade **Hub & Ecosystem Orchestrator** for Windows (PC) integrating battle-tested open-source engines into a unified, low-latency translation and speech ecosystem for games (CS2, Battlefield), live streams, Discord, and desktop applications.

---

## 🌟 Ecosystem Architecture / Архитектура Экосистемы

```
+-----------------------------------------------------------------------------------------+
|                                    WINDOWS DESKTOP PC                                   |
+-----------------------------------------------------------------------------------------+
|  STAGE 1: REAL-TIME INCOMING AUDIO SUBTITLES (LiveTranslate + Tencent HY-MT 1.8B)       |
|     System Audio Loopback (WASAPI) from Games, Discord, YouTube, Media Players          |
|              │                                                                          |
|              ▼                                                                          |
|     Sherpa-ONNX SenseVoice INT8 (~160ms ASR) + Tencent HY-MT 1.8B GGUF (~80ms MT)       |
|              │                                                                          |
|              ▼                                                                          |
|     Always-on-Top Dual Subtitle Overlay:                                                |
|       Line 1: Original Spoken Audio (English / Chinese / Japanese)                      |
|       Line 2: Instant Translation (Russian / Chinese / English - Auto OS Locale)        |
|     Controls: F9 Master Toggle | Double-MMB Click-Through | MMB Drag                     |
+-----------------------------------------------------------------------------------------+
|  STAGE 2: IN-PLACE SCREEN OCR & VISUAL TRANSLATION (OverTranslate Portable)             |
|     Screen Snipping / Bounding Box Selection / Clipboard Interception                   |
|              │                                                                          |
|              ▼                                                                          |
|     RapidOCR ONNX (PaddleOCR Engine) + Neural In-Place Inpainting Text Replacement      |
|     Universal Locale: Auto-switches Target to RU, ZH-CN, or EN based on Windows locale   |
|     Controls: Ctrl + Alt + A (Box OCR) | Ctrl + C + C (Instant Context Lookup)          |
+-----------------------------------------------------------------------------------------+
|  STAGE 3: REAL-TIME OUTGOING S2ST VOICE TRANSLATOR (Voice Studio - CS2 & Discord)       |
|     Microphone Audio (Behringer / USB Mic / NVIDIA Broadcast / Equalizer APO)           |
|              │                                                                          |
|              ▼                                                                          |
|     ASR: Sber GigaAM v3 CTC (RU) / SenseVoice-Small INT8 (ZH) (~170ms)                  |
|     MT:  Helsinki Opus-MT INT8 (RU->EN / ZH->EN) (~15ms)                                |
|     TTS: Kyutai Pocket-TTS 24kHz (~600ms) with Cloned Personal Voice Timbre             |
|              │                                                                          |
|              ▼                                                                          |
|     Routing: Sent to Topping Playback 3/4 (Loopback 1/2) or VB-Audio Virtual Cable      |
|     Controls: Shift + Middle Mouse Button (PTT Wheel Click with 200ms post-roll tail)   |
+-----------------------------------------------------------------------------------------+
```

---

## 🇷🇺 Русская Инструкция / Russian Guide

### Быстрый старт (1 клик)
1. Скачайте последний архив из **Releases**:  
   👉 **`TranslationEcosystem-v0.3.5-Windows-x64.zip`**
2. Распакуйте в любую папку на быстрый SSD (например, `D:\TranslationEcosystem`).
3. Запустите **`START.bat`**:
   - Автоматически проверяет и поднимает изолированное окружение.
   - За 0.2 секунды открывает единую панель управления (**Universal Hub**).
   - Все 3 этапа готовы к работе «из коробки» без ручных настроек.

### Развёртывание из Git (для разработчиков)
```bash
# Клонирование репозитория
git clone https://github.com/Sonatko/all_translete_online.git
cd all_translete_online

# Для пользователей в Китае (зеркало):
# git clone https://ghproxy.net/https://github.com/Sonatko/all_translete_online.git

# Запуск единого скрипта (автоматически настроит зависимости и патчи)
START.bat
```

### Обновление проекта (1 клик)
- Чтобы обновить репозиторий, доустановить новые библиотеки и актуализировать патчи, просто запустите **`UPDATE.bat`**.
- Либо сделайте `git pull` и запустите **`START.bat`** — система за 0.3 секунды автоматически проверит целостность и накатит свежие патчи.

### Основные возможности
1. **Этап 1: Субтитры системного звука (LiveTranslate)**
   - Перехватывает речь из Discord, игр и браузера в реальном времени.
   - Показывает прозрачный баннер поверх всех окон (игры не сворачиваются).
   - `F9`: вкл/выкл субтитры и прослушивание.
   - `Двойной клик колесиком мыши (2x MMB)`: включить/выключить кликабельность (Click-Through) сквозь субтитры.
   - `Зажать колесико мыши (MMB Drag)`: перетащить субтитры в любое место экрана.
2. **Этап 2: Экранный переводчик игр и картинок (OverTranslate)**
   - `Ctrl + Alt + A`: выделить прямоугольную область на экране для моментального перевода текста на месте.
   - `Ctrl + C + C`: двойное нажатие Ctrl+C на любом слове для грамматического разбора и подсказок.
   - **Универсальность:** автоматически понимает язык системы (переводит на русский в РФ, на китайский в КНР).
3. **Этап 3: Голосовой переводчик в игру и Discord (Voice Studio)**
   - Зажмите `Shift + Колесико мыши` и говорите в микрофон на русском или китайском.
   - При отпускании система клонированным вашим голосом озвучит фразу на английском языке прямо в голосовой чат CS2 / Discord.
   - Студия клонирования голоса за 7 секунд встроена прямо в интерфейс!

---

## 🇬🇧 English Guide

### 1-Click Quickstart
1. Download the latest release from the **Releases** tab:  
   👉 **`TranslationEcosystem-v0.3.5-Windows-x64.zip`**
2. Extract the archive into any folder on an SSD (e.g., `D:\TranslationEcosystem`).
3. Double-click **`START.bat`**.
   - Auto-verifies the runtime environment and dependencies.
   - Launches the **Universal Hub GUI** in ~0.25s.
   - All three stages are fully wired and operational out of the box.

### Clone from Git
```bash
git clone https://github.com/Sonatko/all_translete_online.git
cd all_translete_online

# Launch
START.bat
```

---

## 🎮 Golden Control Scheme & Keybindings

| Stage | Action | Hotkey / Gesture | Description |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Master Toggle** | **`F9`** | Synchronously switches subtitles Show/Hide and audio capture Run/Pause. |
| **Stage 1** | **Click-Through** | **Double Middle Click (`2x MMB`)** | Double-click mouse wheel over subtitle banner to toggle transparency click-through. |
| **Stage 1** | **Drag Subtitles** | **Middle Mouse Drag (`MMB Drag`)** | Hold mouse wheel to move the subtitle banner across monitors. Auto-saved to config. |
| **Stage 2** | **Screen OCR** | **`Ctrl + Alt + A`** | Drag bounding box over screen text to translate in-place. |
| **Stage 2** | **QuickLookup** | **`Ctrl + C + C`** | Double-press Ctrl+C on highlighted text for instant lexical analysis. |
| **Stage 2** | **QuickTranslate**| **`Ctrl + Alt + C`** | In-place text replacement in input boxes. |
| **Stage 3** | **Voice PTT** | **`Shift + Middle Click`** | Hold to speak into mic (RU or ZH); releases translated English voice to CS2/Discord. |

---

## 🎛 Audio Routing Guide (Topping DSP Loopback & VB-Cable)
📖 **Full Pedagogical Guide (Russian):** [HOW_TOPPING_WORKS.md](HOW_TOPPING_WORKS.md)

1. **With Hardware Audio Interface (Topping E2x2 OTG):**
   - Windows & Discord Recording Device: **`Loopback 1/2 (Topping E2x2 OTG)`**.
   - Stage 3 Output Device: **`Playback 3/4`**.
   - Natural mic is hardware-routed to teammates when PTT is released; during `Shift + MMB`, the translated voice is dispatched to `Playback 3/4` -> `Loopback 1/2` with 0ms latency.
2. **Without Hardware Interface (Laptops / Standard Audio):**
   - Install virtual sound card via `scripts\install_vbcable.bat`.
   - In Discord / Game: set input device to **`CABLE Output (VB-Audio Virtual Cable)`**.
   - In Stage 3 Studio: set output device to **`CABLE Input (VB-Audio Virtual Cable)`**.

---

## 🧠 Local AI Model Inventory (100% Offline)

| Stage | Model Name | Architecture & Engine | Precision | Local Size | Compute |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Sherpa-ONNX SenseVoice | Non-autoregressive ASR | INT8 ONNX | 228.2 MB | CPU (AVX2/Zen4) |
| **Stage 1** | Tencent HY-MT 1.8B | GGUF Translation LLM | Q4_K_M | 1080.6 MB | CPU Dispatch |
| **Stage 3** | Sber GigaAM v3 CTC | Russian Conformer ASR | INT8 ONNX | 262.1 MB | CPU (Sherpa) |
| **Stage 3** | SenseVoice-Small | Chinese Multi-lingual ASR | INT8 ONNX | 228.1 MB | CPU (Sherpa) |
| **Stage 3** | Helsinki Opus-MT | MarianMT (RU->EN / ZH->EN) | INT8 CT2 | ~148 MB | CPU (CTranslate2) |
| **Stage 3** | Kyutai Pocket-TTS | Mimi 24kHz + Flow Matching | FP32 | 208.9 MB | CPU (PyTorch) |
| **Stage 3** | Cloned Voice Timbre | Voice conditioning latent | Safetensors | 4.2 MB | 0 MB (In-Memory) |

---

## 📥 Model Weights Download (High-Speed China & Global Mirrors)

- **For Mainland China (国内直连高速镜像):**
  - Run `scripts\download_models_china.bat`, or:
  - In Stage 3 Studio (Tab 2), check `🇨🇳 国内镜像加速 (China Mirror: hf-mirror.com)` and click `一键下载所需模型`.
- **For Russia & Global:**
  - Run `scripts\download_models_russia.bat`, or click download directly in Stage 3 Studio.

---

## 🛑 Stopping the Ecosystem

Double-click **`STOP.bat`**:  
Instantly terminates all background workers, unhooks audio devices, and frees memory.
