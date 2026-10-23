# Project Agent Specification: Real-Time Audio & Text Translation Workspace

## Project Overview
The goal of this project is to curate, configure, and integrate battle-tested, ready-to-use open-source tools and repositories for Windows (PC) to achieve a seamless, real-time dual-language translation ecosystem without writing application code from scratch.

## Target Functionalities

### 1. Real-Time System Audio Translation (Speech-to-Text & Subtitles)
- **Audio Capture**: Loopback capture of system audio (desktop stereo mix / WASAPI loopback) from games, Discord, browser videos, and media players, as well as direct microphone input.
- **Speech-to-Text (STT / ASR)**: Real-time transcription (Russian & English, plus multi-language auto-detection).
- **Machine Translation (MT)**: Real-time translation with low latency.
- **Overlay & Visual Feedback**: Transparent, always-on-top overlay display showing:
  - Original transcribed text
  - Target translated text
  - Educational / language-learning hints (vocabulary breakdowns, lemmas, grammar cues where supported).

### 2. Instant On-Screen & Clipboard Text Translation
- **Screen OCR Translation**: Select-and-translate via screen bounding boxes (snipping tool style) for games, images, and non-selectable text.
- **Interactive / Clipboard Translation**: Instant hotkey translation for highlighted text anywhere in Windows (using mouse selection or clipboard interception).

### 3. Non-Programmer Operational Constraint
- **No In-House Coding Required**: The user is not a software engineer. Every solution must be installable and operable via:
  - Compiled Windows binaries (standalone `.exe`, installers, GitHub Releases).
  - Package managers (`winget`, `scoop`, or simple single-command Python installers / virtual environments where an intuitive WebUI/GUI is provided).
  - Pre-configured GUI / tray-icon tools with friendly graphical configuration menus.

### 4. Project Structure & Language Standards
- **Project Configuration & Meta Files**: Written in English (`AGENTS.md`, `README.md`, config presets).
- **Developer Journal & Analysis Notes (`dev_notes/`)**: Written in clear, pedagogical Russian for the user's daily reference.
- **Agent Interaction**: Conducted in clear, patient Russian adhering to strict deep-research reality checks.

### 5. Engine Respect, User Clarification & Golden Control Scheme
- **Strict Engine Respect & Anti-Overengineering**:
  - Never alter default upstream engine mechanics or invent unrequested hotkeys/controls without explicit user approval.
  - Preserve native application conventions (e.g., LiveTranslate's middle-click dragging) rather than re-inventing standard UI patterns.
- **Mandatory User Clarification**:
  - If any user requirement, technical direction, or design choice is ambiguous, doubtful, or underspecified, **NEVER GUESS OR CODE ASSUMPTIONS**. Stop and ask the user directly for clarification.
- **Golden Subtitle & Audio Pipeline Interaction Scheme**:
  - **Master Hotkey (`F9`)**: Single master toggle that synchronously switches `Subtitles Visible + Transcription RUN` and `Subtitles Hidden + Transcription PAUSE`.
  - **Subtitle Lock / Click-Through Toggle**: Double-click Middle Mouse Button (wheel click) over the subtitle banner to toggle `Click-through` (Lock / Unlock Move Mode).
  - **Subtitle Window Dragging**: Strictly Middle Mouse Button (wheel click) drag ONLY. Left-click is never hijacked.
  - **Alpha Hit-Testing Surface**: Invisible `Alpha = 1/255` background fill in `paintEvent` to ensure Windows DWM hit-testing works seamlessly across the entire banner even at 0% background opacity.

