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
  - **Subtitle Lock / Click-Through Two-Way Sync**:
    - **Physical gesture**: Double-click Middle Mouse Button (2x MMB / wheel click) over the subtitle banner toggles Click-through.
    - **Panel Checkbox**: The `Click-through` checkbox on the main overlay header is bidirectionally wired to the subtitle banner: clicking it toggles subtitle click-through, and 2x MMB on the banner updates the checkbox.
    - **Safety**: Left-click is never hijacked.
  - **Subtitle Dragging (MMB Drag)**: Middle-mouse-button press and drag moves the subtitle banner across the screen; position is auto-saved to settings.
  - **Language Selection Authority**: The `Target Language` combo on the main panel is the authoritative target selector. When `target_lang == source_lang`, the subtitle banner shows pure original text with 0ms translation delay and no LLM calls.
  - **Alpha Hit-Testing Surface**: Invisible `Alpha = 1/255` background fill in `paintEvent` to ensure Windows DWM hit-testing works seamlessly across the entire banner even at 0% background opacity.

### 6. Absolute User Sovereignty Over Git (Strictly No Auto-Commit / No Auto-Push)
- **Sole Decision Maker (User Authority)**:
  - ONLY the user decides when to create a Git commit (`git commit`) and when to push (`git push`).
  - NEVER automatically stage, commit, or push code after file modifications, bugfixes, or test runs.
  - The agent works directly in the active topic branch working tree without creating Git commits.
- **No Commits Without 100% Perfection & Testing**:
  - NO commits are permitted while features are being developed, refined, or debugged.
  - A commit is executed ONLY after the code is fully implemented, passes all verification test gates (`scripts/run_all_tests.bat`), is brought to absolute perfection, and the user explicitly orders: "зафиксируй", "сохрани в коммит", or "коммить".
- **Strictly No Auto-Push**:
  - NEVER run `git push` on any branch (especially protected `main`) unless explicitly instructed by the user.
- **Configuration Safety**:
  - Keep runtime configurations synchronized with `CONFIG/` so settings are preserved on disk, but leave Git commits strictly to the user's explicit command.

### 7. Professional Git Flow, Branching Protocol & Test-Driven Verification Gate
- **Strict Branching Strategy (Anti-Merge-Hell Standard)**:
  - `main`: Protected, production-ready release branch. Never code experimental features directly on `main`.
  - `feature/<stage>-<name>`: Isolated umbrella/feature branches for discrete milestones.
  - `spike/<name>`: Short-lived exploration branches (hours to 1-2 days) for unverified open-source repos and rapid prototyping. Delete with `git branch -D` if discarded to prevent repo clutter.
  - `fix/<name>`: Discrete, atomic micro-fix branches. Never bundle bugfixes with in-progress feature development.
  - `test/<name>`: Benchmarking suites and diagnostic testbeds.
  - `refactor/<name>`: Architectural cleanups and technical debt elimination.
- **Short-Lived Topic Branches & Milestone Tags**:
  - Never maintain long-lived branches that linger for weeks and drift away from the base.
  - Tag successful verification checkpoints (`git tag ...`) for instant, risk-free rollbacks.
- **The Test-Driven Verification Gate (Evidence Before Claims)**:
  - No task or checklist item may be marked complete simply with a checkbox.
  - Completion requires tangible, reproducible instrumental output (Inference Latency in ms, RAM/VRAM in MB, Word/Character Error Rate, CPU Load %) captured via test scripts and logged in `dev_notes/`.
  - A feature branch is merged into `main` ONLY after passing the end-to-end regression check:
    1. Automated smoke gate passes all checks.
    2. Clean process lifecycle (START.bat & STOP.bat).
    3. Golden Control Scheme verification (`F9` Master Toggle, `2x MMB` Click-through, `MMB Drag`).
    4. Performance budget compliance (<200–350 ms latency, 0 MB game stutter).


