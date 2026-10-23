# Quickstart & Universal Reproduction Guide

This guide ensures that on any Windows PC today, next month, or years from now, you can restore your real-time translation and language-learning workstation within minutes without coding knowledge.

---

## 1. Ergonomic Keymap for Compact Keyboards (60% / 65% / TKL)

No physical `F1–F12` row is needed. All shortcuts are bound to standard, left-hand-friendly modifier combinations:

| Action | Universal Hotkey | Behavior |
|---|---|---|
| **Live Audio Subtitles** | `Win` + `Ctrl` + `L` | Toggles native Windows on-device speech recognition. Set source to **English (US)**. |
| **Screen OCR Translation** | `Alt` + `Q` | Snip any screen region (games, images, comics) for instant OCR recognition and translation. |
| **Selection Translation** | `Alt` + `W` | Highlights text in any browser, document, or chat and translates immediately. |
| **Dictionary & Vocabulary** | `Alt` + `S` | Opens dictionary lookup card with phonetic transcription and Cambridge definitions. |

---

## 2. Fast 1-Click Installation (Any Machine)

Open PowerShell and run the setup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

### What this script does automatically:
1. Installs **Pot-Desktop** using Microsoft's official Windows Package Manager (`winget install --id Pylogmon.pot`).
2. Downloads the standalone **LiveCaptions-Translator** (bundled with `.NET` runtime) into the local `bin/` directory.
3. Automatically deploys the **Educational Preset** (`configs/livecaptions-translator/setting.template.json`) which enables the dual-line subtitle format:
   - Line 1: Natural Russian translation.
   - Line 2: `💡` Educational breakdown of idioms, phrasal verbs, and B2–C2 vocabulary.

---

## 3. Daily Workflow (Playing Games & Learning English)

1. **Before launching your game or video:**
   - Press `Win` + `Ctrl` + `L` once to activate Windows Live Captions.
   - Run `bin/LiveCaptionsTranslator.exe` (or let it launch with Windows).
2. **In games:**
   - Set the game's display mode to **Borderless Windowed** (so overlays render seamlessly).
   - Position the subtitle overlay where you want (it is click-through, so you can shoot and click right through it).
3. **When reading text or menus:**
   - Press `Alt` + `Q` and draw a box around any dialogue box or text.
   - Press `Esc` to dismiss the translation popup and continue playing.
