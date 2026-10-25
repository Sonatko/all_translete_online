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
- `CONFIG/` - Authoritative configuration files and custom patches (`F9` Master Toggle, `2x MMB`, `Alpha=1/255` surface).
- `stage_1_audio/` - Stage 1: Real-Time System Audio & Subtitles (NLLB-200 Server & LiveTranslate integration).
- `stage_2_screen/` - Stage 2: Screen In-Place OCR & AI Context Learning (OverTranslate integration).
- `stage_3_voice/` - Stage 3: Real-Time Voice Cloning & TTS Speech Synthesis (Piper TTS ONNX).
- `dev_notes/` - Chronological developer logs & architecture specifications.

## Quickstart (1-Click Setup)

1. **Clone the repository:**
   ```bash
   git clone https://gitee.com/Sonatko/ll_translete_online.git
   cd ll_translete_online
   ```
2. **Run Installer & Bootstrapper:**
   Double-click `SETUP_ECOSYSTEM.bat`. It will automatically:
   - Download clean upstream engines (`LiveTranslate` & `OverTranslate Portable`).
   - Apply our custom patches from `CONFIG/stage_1_audio/patches/`.
   - Download NLLB-200 1.3B INT8 translation weights via fast mirrors (`hf-mirror.com`).
   - Synchronize authoritative configuration profiles.
3. **Start the Ecosystem:**
   Double-click `START.bat`.
4. **Stop everything:**
   Double-click `STOP.bat`.

## Project Roadmap & Status

- **Stage 1: Real-Time Audio & Subtitle Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** Faster-Whisper `medium` (INT8 CUDA) + Meta NLLB-200 `1.3B` (INT8 CUDA / CPU).
  - **Pipeline:** English Speech -> English Subtitle (Line 1) + Russian / Chinese Translation (Line 2).
  - **Latency:** ~180 ms end-to-end, 100% offline without internet.
  - **Controls:** Master Hotkey (`F9`), Subtitle Lock / Click-Through (`2x MMB`), Window Drag (`MMB Drag`).

- **Stage 2: In-Place Screen OCR & Visual Translation** — **COMPLETED & OPERATIONAL**
  - **Core Engines:** OverTranslate (RapidOCR ONNX) + Optional AI linguistic breakdown.
  - **In-Place Visual Translation:** Replaces text directly on top of images and games via `Ctrl + Alt + A`.
  - **Continuous Game Monitoring:** Real-time continuous translation block via `Ctrl + Alt + S`.
  - **AI Linguistic Breakdown:** Instant dictionary and grammar learning cards via `Ctrl + C + C`.

- **Stage 3: Real-Time Voice Cloning & Speech-to-Speech (S2ST / TTS)** — **READY FOR IMPLEMENTATION**
  - **Goal:** Real-time offline speech synthesis and voice dubbing for incoming translations.
  - **Architecture:** Zero-VRAM offline TTS (Piper ONNX / CPU, < 50ms latency) in `stage_3_voice/`.
  - **Design Document:** See [`dev_notes/day_13_stage_3_voice_tts_roadmap_and_architecture.md`](file:///dev_notes/day_13_stage_3_voice_tts_roadmap_and_architecture.md).



