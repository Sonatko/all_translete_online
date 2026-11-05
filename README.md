# Universal Real-Time Translation & Subtitle Ecosystem (Windows)

**[English / Русский (README.md)](README.md)** | **[简体中文操作指南 (README_ZH.md)](README_ZH.md)**

A lightweight, production-grade **Hub & Ecosystem Orchestrator** for Windows (PC) integrating battle-tested open-source engines into a unified, low-latency bilingual/trilingual translation ecosystem for games (CS2, Battlefield), live streams, Discord, and desktop applications.

---

## 🌟 Ecosystem Architecture

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
|       Line 2: Instant Translation (Russian / English)                                   |
|     Controls: F9 Master Toggle | Double-MMB Click-Through | MMB Drag                     |
+-----------------------------------------------------------------------------------------+
|  STAGE 2: IN-PLACE SCREEN OCR & VISUAL TRANSLATION (OverTranslate Portable)             |
|     Screen Snipping / Bounding Box Selection / Clipboard Interception                   |
|              │                                                                          |
|              ▼                                                                          |
|     RapidOCR ONNX (PaddleOCR Engine) + Neural In-Place Inpainting Text Replacement      |
|     Controls: Ctrl + Alt + A (Box OCR) | Ctrl + C + C (Instant Context Lookup)          |
+-----------------------------------------------------------------------------------------+
|  STAGE 3: REAL-TIME OUTGOING S2ST VOICE TRANSLATOR (Voice Studio - CS2 & Discord)       |
|     Microphone Audio (Behringer / USB Mic / NVIDIA Broadcast / Equalizer APO)           |
|              │                                                                          |
|              ▼                                                                          |
|     ASR: Sber GigaAM v3 CTC (RU) / SenseVoice-Small INT8 (ZH) (~170ms)                  |
|     MT:  Helsinki Opus-MT INT8 (RU->EN / ZH->EN) (~15ms)                                |
|     TTS: Kyutai Pocket-TTS 24kHz (~800ms) with Cloned Personal Voice Timbre             |
|              │                                                                          |
|              ▼                                                                          |
|     Routing: Sent to Topping Playback 3/4 (Loopback 1/2) or VB-Audio Virtual Cable      |
|     Controls: Shift + Middle Mouse Button (PTT Wheel Click with 200ms post-roll tail)   |
+-----------------------------------------------------------------------------------------+
```

---

## 📦 Deployment Options

### Option A: 1-Click Portable Standalone Release (Zero-Dependency)
*Recommended for clean PCs, gamers, and secondary laptops without developer tools.*

1. Go to the GitHub repository **Releases** page and download:
   👉 **`TranslationEcosystem-v0.3.1-Windows-x64.zip`**
2. Extract the archive into any folder on your SSD (e.g. `D:\TranslationEcosystem`).
3. Double-click **`START.bat`**.
   - Ships with an embedded `tools/uv.exe` runtime manager.
   - Automatically bootstraps managed Python 3.12 without requiring system Python, Git, or administrative rights.
   - Launches the Universal Graphical Hub in under 0.25 seconds.

### Option B: Clone from Git (Developers)
```bash
# 1. Clone repository
git clone https://github.com/SONATO-DESIGN/all_translete_online.git
cd all_translete_online

# 2. Run automated setup wizard (auto-configures Tsinghua / PyPI mirrors)
scripts\setup.bat

# 3. Launch Universal Hub
START.bat
```

---

## 🚀 Quickstart & Daily Operations

### 1. Launch the Ecosystem
- 👉 **`START.bat`**: **The Single 1-Click Entry Point**. Launches the **Universal Graphical Hub (PySide6)**:
  - Supervised status cards with live RAM / CPU / PID metrics for Stages 1, 2, and 3.
  - **7-Second Personal Voice Cloning Studio (Wizard)** with instant headphone preview.
  - **100% Offline AI Models Storage Audit** (all models verified locally on SSD).
  - Trilingual UI language switch (**Русский / English / 简体中文**).
  - Interactive **Audio & Signal Flow Guide** explaining Topping DSP Loopback & VB-Cable routing.

### 2. Stop the Ecosystem
- Double-click **`STOP.bat`**: Instantly (<0.25s) terminates all ecosystem processes, audio hooks, and frees sound card streams.

---

## 📥 Model Weights Download (High-Speed China & Global Mirrors)

To maintain a lightweight Git repository, large neural network weights are downloaded on demand:

- **For Mainland China (国内直连加速):**
  - Run **`scripts\download_models_china.bat`**, or:
  - In Stage 3 Studio (Tab 2), check `🇨🇳 国内镜像加速 (China Mirror: hf-mirror.com)` and click `一键下载所需模型`.
  - All downloads utilize resilient chunked streaming, HTTP 206 Range resume, and automated exponential backoff.
- **For Russia / Global:**
  - Run **`scripts\download_models_russia.bat`**, or click download directly in Stage 3 Studio.

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

## 🛡 Out-of-Tree Configuration & Patch Vault (`CONFIG/`)

All critical user profiles, cloned voice weights, and hardware parameters are isolated in **`CONFIG/`**:
- `CONFIG/stage_1_audio/`: LiveTranslate custom UI presets and patches.
- `CONFIG/stage_2_screen/`: OverTranslate templates.
- `CONFIG/stage_3_voice/my_pocket_voice.safetensors`: Your permanent cloned voice conditioning.
- `CONFIG/stage_3_voice/studio_settings.json`: Audio matrix routing and VAD thresholds.

*Upstream updates from donor repositories can never overwrite or erase your personal configurations.*
