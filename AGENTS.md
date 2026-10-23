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
