# Universal Real-Time Translation & Subtitle Ecosystem (Windows)

A lightweight, production-grade **Hub & Ecosystem Orchestrator** for Windows (PC) integrating battle-tested open-source engines into a unified, zero-latency bilingual/trilingual translation ecosystem for games (CS2), live streams, Discord, and desktop applications.

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
|     Microphone Audio (Behringer XM8500 -> NVIDIA Broadcast -> Equalizer APO)            |
|              │                                                                          |
|              ▼                                                                          |
|     Sber GigaAM v3 CTC (~170ms) ➔ Opus-MT INT8 (~15ms) ➔ Kyutai Pocket-TTS (~800ms)    |
|              │                                                                          |
|              ▼                                                                          |
|     Synthesized in YOUR OWN CLONED VOICE TIMBRE (Mimi 24kHz + Flow Matching)            |
|     Routing: Sent to Topping Playback 3/4 ➔ Hardware Loopback 1+2 ➔ CS2/Discord Mic     |
|     Controls: Shift + Middle Mouse Button (PTT Wheel Click with 200ms post-roll tail)   |
+-----------------------------------------------------------------------------------------+
```

---

## 🚀 Quickstart & Daily Operations

### 1. Launch the Ecosystem
### 1. Launch the Ecosystem
- 👉 **`START.bat`**: **The Single 1-Click Entry Point**. Launches the **Universal Graphical Hub (PySide6)** in under 0.25 seconds:
  - Supervised status cards with live RAM / CPU / PID metrics for Stages 1, 2, and 3.
  - **7-Second Personal Voice Cloning Studio (Wizard)** with instant headphone preview.
  - **100% Offline AI Models Storage Audit** (all models verified locally on SSD).
  - Trilingual UI language switch (**Русский / English / 中文**).
  - Interactive **Audio & Signal Flow Guide** explaining Topping Loopback.

### 2. Stop the Ecosystem
- Double-click **`STOP.bat`**: Instantly (<0.25s) terminates all ecosystem processes, audio hooks, and frees sound card streams.

---

## 🎛 Topping E2x2 OTG Hardware Routing & Loopback Guide
📖 **Full Pedagogical Russian Guide:** [HOW_TOPPING_WORKS.md](HOW_TOPPING_WORKS.md) (Шпаргалка на века)

To ensure **0 ms virtual cable delay** and 0% audio stuttering, the system utilizes the hardware DSP loopback of the **Topping E2x2 OTG** interface:

1. **Microphone Setup in Windows / Discord / CS2**:
   - Set Default Recording Device / Input to **`Loopback 1/2 (6- E2x2 OTG)`**.
2. **Normal Talking (PTT released)**:
   - Voice Studio passes your natural microphone directly through to `Playback 3/4` -> `Loopback 1/2` (teammates hear your natural voice).
3. **Translating (Hold `Shift + Middle Mouse Button`)**:
   - Natural mic is **instantly muted** for the game.
   - Sber GigaAM + Opus-MT + Pocket-TTS generate your translation in your cloned voice.
   - Audio is dispatched to `Playback 3/4` -> Topping hardware loops it into `Loopback 1/2`.
   - Your teammates hear clear, native English spoken in your personal timbre.
4. **Headphones (Your Ears)**:
   - Plugged into Topping front jack `Output 1/2` (`Playback 1/2`). You hear pure game sound plus an optional comfortable sidetone of your translation.

---

## 🎮 Golden Control Scheme & Keybindings

| Stage | Action | Hotkey / Gesture | Description |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Master Toggle** | **`F9`** | Synchronously switches subtitles Show/Hide and audio capture Run/Pause. |
| **Stage 1** | **Click-Through** | **Double Middle Click (`2x MMB`)** | Double-click mouse wheel over subtitle banner to toggle transparency click-through. |
| **Stage 1** | **Drag Subtitles** | **Middle Mouse Drag (`MMB Drag`)** | Hold mouse wheel to move the subtitle banner across monitors. |
| **Stage 2** | **Screen OCR** | **`Ctrl + Alt + A`** | Drag bounding box over screen text to translate in-place. |
| **Stage 2** | **QuickLookup** | **`Ctrl + C + C`** | Double-press Ctrl+C on highlighted text for instant lexical analysis. |
| **Stage 2** | **QuickTranslate**| **`Ctrl + Alt + C`** | In-place text replacement in input boxes. |
| **Stage 3** | **Voice PTT** | **`Shift + Middle Click`** | Hold to speak Russian into mic; releases translated English voice to CS2/Discord. |

---

## 🧠 Local AI Model Inventory (100% Offline)

| Stage | Model Name | Architecture & Engine | Local Size | VRAM Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Sherpa-ONNX SenseVoice | Multi-lingual Non-autoregressive ASR | 228.2 MB | 0 MB (CPU) |
| **Stage 1** | Tencent HY-MT 1.8B | GGUF Q4_K_M Translation LLM | 1080.6 MB | 0 MB (CPU) |
| **Stage 3** | Sber GigaAM v3 CTC | Conformer Connectionist Temporal Classification | 214.3 MB | 0 MB (CPU) |
| **Stage 3** | Helsinki Opus-MT | CTranslate2 INT8 Fast MarianMT | 145.9 MB | 0 MB (CPU) |
| **Stage 3** | Kyutai Pocket-TTS | Mimi 24kHz Neural Codec + Flow Matching | ~320 MB | 0 MB (CPU) |
| **Stage 3** | Personal Voice Clone | Safetensors Model Latent Vector | 4.2 MB | 0 MB (CPU) |

---

## 🛡 Out-of-Tree Configuration & Patch Vault (`CONFIG/`)

All critical user profiles, cloned voice weights, and hardware parameters are strictly isolated in the dedicated **`CONFIG/`** directory:
- `CONFIG/stage_1_audio/`: LiveTranslate custom UI presets and patches.
- `CONFIG/stage_2_screen/`: OverTranslate templates.
- `CONFIG/stage_3_voice/my_pocket_voice.safetensors`: Your permanent cloned voice conditioning.
- `CONFIG/stage_3_voice/studio_settings.json`: Audio matrix routing and VAD thresholds.

*Upstream updates from donor repositories can never overwrite or erase your personal configurations.*
