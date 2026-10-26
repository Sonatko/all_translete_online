# Universal Real-Time Translation & Subtitle Orchestrator (Windows)

A lightweight, production-grade **Hub & Patches Orchestrator** for Windows (PC) that integrates battle-tested open-source engines into a unified, zero-latency bilingual ecosystem for games, video streams, Discord, and desktop applications.

---

## Architecture Overview (Hub & Patches Pattern)

Rather than bundling tens of gigabytes of model weights or forking upstream codebases, this repository acts as an **authoritative orchestrator (~300 KB)**:
- **Zero Third-Party Bloat**: Upstream engines (`LiveTranslate`, `OverTranslate Portable`) are downloaded and provisioned automatically on first run via `SETUP_ECOSYSTEM.bat`.
- **Authoritative Configuration (`CONFIG/`)**: Centralized, version-controlled presets and templates that override active runtime settings.
- **Micro-Patches (`CONFIG/stage_1_audio/patches/`)**: Direct, surgical patches applied to upstream engines (e.g., Master Hotkey `F9`, Double-MMB lock, Alpha surface).
- **In-Process Local Translation Engine**: Zero-network, ultra-fast CTranslate2 engine running Meta NLLB-200 1.3B directly in memory with LRU caching and CUDA-to-CPU fallback (eliminates external server processes and network ports).

```
+-----------------------------------------------------------------------------------------+
|                                    WINDOWS DESKTOP PC                                   |
+-----------------------------------------------------------------------------------------+
|  STAGE 1: REAL-TIME SYSTEM AUDIO SUBTITLES (LiveTranslate + In-Process NLLB Engine)     |
|     System Audio / WASAPI Loopback (Games, Browser, Discord, Media Player)             |
|              |                                                                          |
|              v                                                                          |
|     Faster-Whisper `medium` (INT8 CUDA) + Silero VAD (~120ms ASR)                       |
|              |                                                                          |
|              v                                                                          |
|     Meta NLLB-200 1.3B INT8 In-Process Engine (CTranslate2 CUDA / CPU, ~45ms)           |
|              |                                                                          |
|              v                                                                          |
|     Always-on-Top Dual Subtitle Overlay:                                                |
|       Line 1: Original English Audio Transcript                                         |
|       Line 2: Instant Russian / Chinese Translation                                     |
+-----------------------------------------------------------------------------------------+
|  STAGE 2: IN-PLACE SCREEN OCR & VISUAL TRANSLATION (OverTranslate Portable)             |
|     Screen Snipping / Bounding Box Selection / Continuous Screen Zone                   |
|              |                                                                          |
|              v                                                                          |
|     RapidOCR ONNX (PaddleOCR Engine) + Local / Cloud Neural Translation                 |
|              |                                                                          |
|              v                                                                          |
|     In-Place Visual Inpainting (replaces foreign text directly over the screen/game)    |
|     + Instant Context QuickLookup (`Ctrl + C + C`)                                      |
+-----------------------------------------------------------------------------------------+
|  STAGE 3: REAL-TIME VOICE DUBBING & TTS (Piper ONNX - In Active Development)            |
|     Zero-VRAM, Ultra-low-latency (<50ms) offline Russian speech synthesis               |
+-----------------------------------------------------------------------------------------+
```

---

## Directory Layout

```
.
├── START.bat                 # Master 1-Click launcher (starts NLLB, LiveTranslate, OverTranslate)
├── STOP.bat                  # Master 1-Click terminator (gracefully kills all processes)
├── SETUP_ECOSYSTEM.bat       # 1-Click automated bootstrapper & mirror installer
├── README.md                 # English project documentation & manual
├── AGENTS.md                 # System specifications & engineering invariants
├── CONFIG/                   # Authoritative configs & micro-patches (Version Controlled)
│   ├── stage_1_audio/
│   │   ├── patches/          # Surgical patches (control_panel.py, subtitle_window.py, main.py)
│   │   └── user_settings.json# Tuned LiveTranslate audio & subtitle profile
│   └── stage_2_screen/
│       ├── appsettings.template.json       # Default global OverTranslate settings
│       └── appsettings.china.template.json # High-speed China mirror settings (SiliconFlow/Youdao)
├── stage_1_audio/
│   └── nllb_server/          # Custom Local CTranslate2 FastAPI Server (NLLB-200 1.3B INT8)
│       ├── server.py         # Dynamic translation server (CUDA with CPU int8 fallback)
│       └── run_server.bat    # Standalone server launcher
├── stage_2_screen/           # OverTranslate Portable root
├── stage_3_voice/            # Stage 3 Voice TTS workspace (Piper ONNX zero-VRAM)
└── dev_notes/                # Daily engineering logs & architecture decisions (Russian)
```

---

## Quickstart (1-Click Bootstrap)

### 1. Prerequisites
- **OS**: Windows 10 / 11 (64-bit).
- **GPU**: NVIDIA GPU with CUDA support recommended (minimum 4 GB VRAM). Automatic CPU fallback supported.
- **Git**: Installed and available in PATH.

### 2. Clone the Repository
- **Mainland China (High Speed)**:
  ```bash
  git clone https://gitee.com/Sonatko/ll_translete_online.git
  cd ll_translete_online
  ```
- **Global / GitHub**:
  ```bash
  git clone https://github.com/Sonatko/all_translete_online.git
  cd all_translete_online
  ```

### 3. Run Automated Bootstrapper
Double-click `SETUP_ECOSYSTEM.bat` (or run from terminal):
```cmd
SETUP_ECOSYSTEM.bat
```
This automated script will:
1. Download clean upstream `LiveTranslate` and install its Python virtual environment.
2. Apply custom patches from `CONFIG/stage_1_audio/patches/` (Master `F9`, Double-MMB lock, Alpha surface).
3. Download clean `OverTranslate Portable` via `ghproxy.net` / GitHub releases.
4. Download Meta `nllb-200-1.3B-ctranslate2-int8` model weights (~1.34 GB) via high-speed `hf-mirror.com`.
5. Deploy authoritative configurations from `CONFIG/` to active applications.

---

## Daily Operational Controls

### Launch Ecosystem
Double-click `START.bat`. It automatically:
- Starts `LiveTranslate` dual-subtitle overlay with built-in in-process NLLB-200 translation and audio capture.
- Starts `OverTranslate` screen translator and docks it in the system tray.

### Stop Ecosystem
Double-click `STOP.bat`. It cleanly terminates all child processes and releases resources safely.

---

## Hotkeys & Golden Control Scheme

### Stage 1: Audio Subtitles (LiveTranslate)
| Action | Control | Description |
| :--- | :--- | :--- |
| **Master Toggle** | **`F9`** | Synchronously toggles **Subtitles Visible + Audio RUN** and **Subtitles Hidden + Audio PAUSE**. |
| **Lock / Click-Through** | **Double Middle Click (`2x MMB`)** | Double-click mouse wheel anywhere over the subtitle banner to toggle transparency click-through. Left-click is never intercepted. |
| **Drag / Move Banner** | **Middle Mouse Drag (`MMB Drag`)** | Press and hold mouse wheel to drag the subtitle banner to any monitor position. |

### Stage 2: In-Place Screen Translation (OverTranslate)
| Action | Hotkey | Description |
| :--- | :--- | :--- |
| **Screen Bounding Box OCR** | **`Ctrl + Alt + A`** | Drag a bounding box over any game UI or comic to replace foreign text with Russian in-place. |
| **Continuous Screen Zone** | **`Ctrl + Alt + S`** | Select a static screen zone for automatic continuous real-time translation updates. |
| **Instant QuickLookup** | **`Ctrl + C + C`** | Press `Ctrl + C` twice on any highlighted text to open the instant context translation card. |
| **Main Settings Window** | **`Ctrl + Alt + W`** | Toggle OverTranslate configuration window. |

---

## Regional Resilience (China & Global)

For users in mainland China where foreign endpoints are throttled:
- **Git Repository**: Available on [Gitee](https://gitee.com/Sonatko/ll_translete_online).
- **HuggingFace Mirror**: Automatically configured to `https://hf-mirror.com`.
- **GitHub Release Proxy**: Automatically accelerated via `https://ghproxy.net`.
- **Screen OCR Providers**: `CONFIG/stage_2_screen/appsettings.china.template.json` comes pre-configured with SiliconFlow (Qwen MT) and Youdao OCR.

---

## Current Status & Next Steps

- [x] **Stage 1 (System Audio & Subtitles)**: Faster-Whisper `medium` + NLLB-200 `1.3B` INT8 (<180 ms latency, 100% offline).
- [x] **Stage 2 (In-Place Screen OCR)**: OverTranslate RapidOCR ONNX integration with inpainting and quick lookup.
- [ ] **Stage 3 (Real-Time Voice Dubbing)**: Piper TTS (ONNX / CPU, <50ms latency, zero-VRAM). Architecture blueprint in [`dev_notes/day_13_stage_3_voice_tts_roadmap_and_architecture.md`](dev_notes/day_13_stage_3_voice_tts_roadmap_and_architecture.md).
