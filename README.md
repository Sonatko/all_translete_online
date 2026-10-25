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
- `START_EN_RU.bat` (or `START_ALL.bat`) - 1-Click launcher for **English -> Russian** (Whisper medium INT8 + Meta NLLB-200 1.3B on CUDA).
- `START_ZH_RU.bat` - 1-Click launcher for **Chinese -> Russian** (Whisper medium INT8 Chinese ASR + Meta NLLB-200 1.3B direct ZH->RU on CUDA).
- `STOP_ALL.bat` - 1-Click clean terminator: gracefully stops all server and transcription processes, freeing port 8080 and VRAM.

## Project Roadmap & Status

- **Stage 1: Real-Time Audio & Subtitle Translation** — **COMPLETED & QUALITY-TUNED**
  - High-quality offline pipeline on NVIDIA RTX 5070 CUDA (~100 ms ASR + ~80 ms MT).
  - Faster-Whisper `medium` INT8 + Meta NLLB-200 `1.3B` INT8 with 4-beam search.
  - Natural conversational VAD timing (`silence_duration = 0.42s`, `max_speech_duration = 7.0s`).
  - Dual 1-click launchers: `START_EN_RU.bat` (English -> Russian) and `START_ZH_RU.bat` (Chinese -> Russian).
  - Golden Control Scheme: Master Hotkey (`F9`), Subtitle Lock/Click-Through Toggle (`2x MMB`), Window Drag (`MMB Drag`), Left Click 100% untouched.
  - Headless background execution with 0 console windows and 0 polling loops.

- **Stage 2: On-Screen OCR, Image & Instant Text Translation** — **UP NEXT**
  - Screen bounding-box snipping OCR translation (for non-selectable text in games, mangas, and UI).
  - Instant hotkey translation for highlighted text & clipboard interception.
  - Battle-tested turnkey open-source tools & pre-compiled Windows binaries search and integration.

## Archive Directory
- `archive/` - Archived experimental and unused tools (legacy `llama.cpp` server, cloud proxy, diagnostics scripts, OBS/DWM toggles).

