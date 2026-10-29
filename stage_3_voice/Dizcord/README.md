# 🎧 Dizcord Translator

**Real-time voice and chat translator for Discord** (and any voice chat). Hear everyone in your language,
speak in theirs. Runs on your own Windows PC - free engines included, no account needed.

**The app itself speaks your language:** English · Português (Brasil) · Español · Français · Deutsch · Italiano ·
Русский · Українська · Polski · Türkçe - you pick it the first time you open Dizcord.

## What it does

- **You hear them in your language.** Listens to what people say in Discord, transcribes it, translates it, shows
  subtitles and can read the translation to you. It listens to the Discord app only - never to its own voice, your
  game or your music - so it keeps listening while it talks and nothing said in the call is dropped.
- **Only the translations, or them too.** By default you hear only the translated voice; press **F9** to also hear
  the people themselves. The app voice can say who talked ("Jo: …"), never talks over itself, and speeds up a
  little when lines pile up so it stays close to live.
- **They hear you in yours.** You talk into your mic; the translation is spoken into Discord through a virtual
  audio cable. The app warns you if Discord is using your real microphone (then people would hear your own voice).
- **Text too.** Translates Discord messages inside Discord itself (servers, DMs, threads), anything you highlight
  with the mouse, and text on your screen with OCR. Write in their language with a hotkey. New messages can be read
  aloud - scrolling back through old messages never reads them out.
- **Your voice, your way.** Pick the voices for what you hear and for what they hear, with speed, pitch and volume
  for each - with any voice engine.
- **Free or premium.** Every step (speech, translation, AI, voice) has a free engine and optional cloud
  engines (OpenAI, Groq, DeepL, ElevenLabs...) or fully offline ones (Whisper, Ollama, Piper).
- **Guided first start.** The first time you open it, a short tour walks you through the set-up step by step: it
  opens the right tab, highlights what to click, ticks each step when it's done and can do some of them for you.
  It is read aloud in your language by a natural voice that runs offline on your PC.
- **Built-in manual, read aloud.** The *Manual* tab explains every part of the app, chapter by chapter, in your
  language, with the same offline voice. Next / Previous cut the old chapter and read the new one.
- **Portable.** Everything lives in the app folder. Nothing is installed in Windows.
- **Updates in one click.** *Settings → Updates → Check for updates* downloads the newest release; your settings,
  keys and models are kept.

## Quick start

1. **Download** the latest release (or *Code → Download ZIP*) and unzip it anywhere.
2. Double-click **`Dizcord.exe`**. The first time it builds its own private Python inside the folder
   (about 750 MB, a few minutes, no admin rights). If it is interrupted, just start Dizcord again - it continues.
3. Choose your language. The guided tour starts and shows you the rest:
   install the free [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) once and restart Windows, set Discord's
   input device to **CABLE Output**, pick the profile **Free - no keys needed**, choose the languages and press
   **Start** (F5).

**Requirements:** Windows 10/11 (64-bit), about 1.5 GB of free disk space, a microphone and headphones.
The speech model (Whisper small, ~460 MB) downloads the first time you use it.

## Privacy

Your API keys stay in `data\keys.json` on your PC and are never put in profiles or exports. The *Free* profile
sends text to Google Translate and Microsoft Edge voices over the internet; the *Fully offline* profile keeps
everything on your PC.

## Folder

```
Dizcord.exe / Dizcord.bat    start the app        Dizcord-debug.bat   start with a console (bug reports)
setup.bat                    (re)build the runtime  install_extras.bat  optional offline engines / GPU
main.py, dizcord\            source code          tools\selftest.py   check the whole pipeline
                                                  tools\calltest.py   a pretend call: order, echo, overlap
```
