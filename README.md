# Universal Real-Time Translation & Language Learning Hub (Windows)

A curated catalog and integration workbench for open-source, turnkey Windows applications providing real-time audio transcription, simultaneous translation, screen OCR translation, and interactive subtitle overlays.

## Core Architectural Pillars

```
+---------------------------------------------------------------------------------+
|                               WINDOWS DESKTOP PC                                |
+---------------------------------------------------------------------------------+
|  1. Audio & Speech Stream (WASAPI Loopback)                                     |
|     [Game / Discord / Video / Mic]                                             |
|              |                                                                  |
|              v                                                                  |
|     [Real-Time STT Engine] (Whisper / Faster-Whisper / Silero / VAD)            |
|              |                                                                  |
|              v                                                                  |
|     [Translation Engine] (Local MarianMT / DeepL API / LibreTranslate / LLM)    |
|              |                                                                  |
|              v                                                                  |
|     [Always-on-Top Dual Overlay] (Original Text + Translation + Word Analysis)  |
+---------------------------------------------------------------------------------+
|  2. Visual / Screen & Text Capture                                              |
|     [Screen Snipping / Active Window Capture]                                   |
|              |                                                                  |
|              v                                                                  |
|     [OCR Engine] (Tesseract / PaddleOCR / Windows Media OCR)                    |
|              |                                                                  |
|              v                                                                  |
|     [Instant Pop-up Translation & Dictionary Lookup]                            |
+---------------------------------------------------------------------------------+
```

## Directory Layout
- `AGENTS.md` - Agent instruction file and operational constraints.
- `README.md` - Technical architecture and project roadmap.
- `dev_notes/` - Daily developer journal and comparative tool analyses (in Russian).
- `configs/` - Exported presets and configuration templates for selected tools.
- `scripts/` - Easy launcher shortcuts and batch setup scripts (if needed).

## Master Turnkey Launchers (Project Root)
- `START_EN_RU.bat` (or `START_ALL.bat`) - 1-Click launcher for **English -> Russian Audio** (Whisper medium INT8 + Meta NLLB-200 1.3B on CUDA).
- `START_ZH_RU.bat` - 1-Click launcher for **Chinese -> Russian Audio** (Whisper medium INT8 Chinese ASR + Meta NLLB-200 1.3B direct ZH->RU on CUDA).
- `START_OVERTRANSLATE.bat` - 1-Click launcher for **In-Place Screen & Image Translation** (OverTranslate + OpenRouter educational breakdown).
- `STOP_ALL.bat` - 1-Click clean terminator: gracefully stops all server, transcription, and overlay processes.

## Project Roadmap & Status

- **Stage 1: Real-Time Audio & Subtitle Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** Faster-Whisper `medium` (INT8 CUDA) + Meta NLLB-200 `1.3B` (INT8 CUDA).
  - **Latency:** ~180 ms end-to-end, 100% offline without internet.
  - **Launchers:** `START_EN_RU.bat` (English -> Russian) and `START_ZH_RU.bat` (Chinese -> Russian).
  - **Controls:** Master Hotkey (`F9`), Subtitle Lock / Click-Through (`2x MMB`), Window Drag (`MMB Drag`).

- **Stage 2: In-Place Screen OCR & Visual Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** OverTranslate (RapidOCR ONNX) + Groq Cloud LPU (`openai/gpt-oss-120b`).
  - **In-Place Visual Translation:** Replaces text directly on top of images and games via `Ctrl + Alt + A`.
  - **Continuous Game Monitoring:** Real-time continuous translation block via `Ctrl + Alt + S`.
  - **AI Linguistic Breakdown:** Instant dictionary and grammar learning cards via `Ctrl + C + C`.
  - **Launcher:** `START_OVERTRANSLATE.bat`.

- **Stage 3: Spaced Repetition Memory Bridge (Anki Integration)** — **IN PROGRESS**
  - **Goal:** One-click save of vocabulary, game context, and audio to mobile Anki cards.
  - **Architecture:** Local Anki desktop (`anki-26.09.3-win-x64.msi`) + `AnkiConnect` plugin (port 8765) + cloud sync via AnkiWeb.
  - **Status:** Installer downloaded and preserved in `downloads/anki-26.09.3-win-x64.msi`. Next step: setup AnkiConnect bridge.

- **Stage 4: Real-Time Speech-to-Speech Translation & Voice Cloning (S2ST)** — **FUTURE / PLANNED**
  - **Goal:** Speak Russian into microphone -> Transmitted as fluent English speech in Discord / games with voice cloning.
  - **Architecture:** Whisper streaming ASR -> Fast NLLB MT -> F5-TTS / XTTS-v2 -> VB-Audio Virtual Cable.

## Master Turnkey Control
- `STOP_ALL.bat` - 1-Click clean terminator: gracefully stops all audio servers, LiveTranslate, and OverTranslate processes.

## Archive Directory
- `archive/` - Archived experimental and unused tools (legacy `llama.cpp` server, cloud proxy, diagnostics scripts, OBS/DWM toggles).
- `dev_notes/` - Chronological developer logs (Days 01 to 10).


