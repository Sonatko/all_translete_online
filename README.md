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

## Directory Layout (Root)
- `stage_1_audio/` - Stage 1: Real-Time System Audio & Subtitles (LiveTranslate + NLLB-200 Server).
- `stage_2_screen/` - Stage 2: Screen In-Place OCR & AI Context Learning (OverTranslate).
- `stage_4_voice/` - Stage 3: Real-Time Voice Cloning & Speech-to-Speech Translation (Planned).
- `archive/` - Archived logs, developer journals (`dev_notes/`), legacy tools, and setup scripts.

## Master Turnkey Launchers (Project Root)
- `START.bat` - 1-Click launcher for the entire ecosystem (Audio Subtitles + Screen OCR & QuickLookup).
- `STOP.bat` - 1-Click clean terminator: gracefully stops all servers, LiveTranslate, and OverTranslate.
- `SETUP_ECOSYSTEM.bat` - 1-Click universal environment validator.

## Project Roadmap & Status

- **Stage 1: Real-Time Audio & Subtitle Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** Faster-Whisper `medium` (INT8 CUDA) + Meta NLLB-200 `1.3B` (INT8 CUDA).
  - **Pipeline:** English Speech -> English Subtitle (Line 1) + Russian Translation (Line 2).
  - **Latency:** ~180 ms end-to-end, 100% offline without internet.
  - **Controls:** Master Hotkey (`F9`), Subtitle Lock / Click-Through (`2x MMB`), Window Drag (`MMB Drag`).

- **Stage 2: In-Place Screen OCR & Visual Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** OverTranslate (RapidOCR ONNX) + Optional AI linguistic breakdown.
  - **In-Place Visual Translation:** Replaces text directly on top of images and games via `Ctrl + Alt + A`.
  - **Continuous Game Monitoring:** Real-time continuous translation block via `Ctrl + Alt + S`.
  - **AI Linguistic Breakdown:** Instant dictionary and grammar learning cards via `Ctrl + C + C`.

- **Stage 3: Real-Time Voice Cloning & Speech-to-Speech (S2ST / TTS)** — **FUTURE / PLANNED**
  - **Goal:** Real-time offline speech synthesis and voice cloning for incoming translations.
  - **Architecture:** Zero-VRAM offline TTS (Piper ONNX / FastSpeech) in `stage_4_voice/`.

## Master Turnkey Control
- `START.bat` - Launches all active services.
- `STOP.bat` - Gracefully stops all active services.

## Archive Directory
- `archive/` - Archived experimental and unused tools (legacy `llama.cpp` server, cloud proxy, diagnostics scripts, OBS/DWM toggles).
- `dev_notes/` - Chronological developer logs (Days 01 to 10).


