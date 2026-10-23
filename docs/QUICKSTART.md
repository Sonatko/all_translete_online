# Quickstart & Universal Reproduction Guide

This guide describes how to run and use the battle-tested Stage 1 real-time audio translation and subtitle setup on Windows.

---

## 1. Stage 1: Real-Time Audio Translation & Cinema Subtitles (LiveTranslate)

### Daily Usage & Controls
1. **Launch:** Run `bin\LiveTranslate\start.bat`.
2. **Master Switch (`F9` key or `Sub` button on overlay):**
   - **Press `F9`:** Shows cinema subtitles and instantly starts audio transcription (`Run`).
   - **Press `F9` again:** Hides cinema subtitles and immediately pauses transcription (`Pause`), saving GPU and LLM tokens.
3. **Repositioning Subtitles (Mouse Wheel Double-Click):**
   - **Double-click mouse wheel over subtitles:** Toggles `Click-through` OFF.
   - Hold mouse wheel and drag to desired position on screen.
   - **Double-click mouse wheel over subtitles again:** Toggles `Click-through` back ON (subtitles lock in place and clicks pass right through into games/video).

### Architecture Summary
* **Capture:** WASAPI Loopback (direct hardware stereo mix).
* **ASR:** FunASR SenseVoice Small on CUDA 12.8 (~60–90 ms latency).
* **LLM Translation:** Groq Cloud API (`openai/gpt-oss-20b`) with pedagogical CEFR A1–A2 prompt.
* **Subtitles:** Yellow 28pt bold English (primary focus), muted 20pt Russian (support), black outline, transparent background, auto-hide on pause.

---

## 2. Stage 2: Screen OCR & Selection Translation (Upcoming)

* **Tool:** [Pot-Desktop](https://github.com/pot-app/pot-desktop) (`winget install --id Pylogmon.pot`)
* **Features:**
  - `Ctrl + Shift + T`: Snip any screen region (games, images, comics) for instant OCR recognition and translation.
  - `Ctrl + Shift + Y`: Instant selection translation in any browser, document, or chat.
