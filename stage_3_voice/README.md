# Stage 3: Real-Time Russian-to-English Outgoing Voice Translator

## Overview
Stage 3 is a dedicated, real-time outgoing speech-to-speech translation subsystem for Windows.
It captures the user's spoken Russian voice from their hardware microphone, translates it into clean, idiomatic English with sub-second latency, and speaks it out via high-fidelity neural TTS directly into the audio interface's hardware Loopback channel for Discord, multiplayer gaming, or streaming without third-party virtual audio cables.

---

## 1. Hardware Environment & Routing
* **Microphone:** Behringer XM8500 (dynamic cardioid vocal microphone, XLR connection).
* **Audio Interface:** Topping Professional E2x2 OTG (USB audio interface with dedicated hardware DSP Loopback, ASIO and WASAPI Exclusive support).
  - Physical Input: `Topping E2x2 OTG: Analog 1/2 (IN 1)`
  - Loopback Target: `Topping E2x2 OTG: Loopback Out`
  - In-Game / Discord Input: `Topping E2x2 OTG: Loopback In` (selected as standard microphone in Discord/Teams/Games).
* **GPU Accelerator:** NVIDIA GeForce RTX 5070 (12 GB VRAM, Tensor Cores).
* **CPU Host:** AMD Ryzen Zen 4 (high multi-thread IPC).

---

## 2. Technical Findings: OpenAI Whisper Translation Mechanics
* **Why Whisper translates only to English:**
  - OpenAI trained Whisper on 680,000 hours of web audio.
  - 117,000 hours consisted of non-English audio paired strictly with English transcripts (e.g. YouTube videos with English subtitles).
  - In Whisper's decoder architecture, the `<|translate|>` token forces the model to generate **only English tokens**.
  - Whisper **cannot** translate `English -> Russian` or `Japanese -> Russian` (which is why Stage 1 strictly required a dedicated translation model like Tencent HY-MT 1.8B).
  - Whisper **can natively** translate `Russian -> English` in a single pass (`task="translate"`).
* **Model Checkpoints for Russian -> English (`task="translate"`):**
  - `tiny` (~75 MB, ~39M params): ~15–20 ms on RTX 5070. Prone to grammar and declension errors on conversational Russian.
  - `base` (~140 MB, ~74M params): ~25–30 ms on RTX 5070. Usable for short words, but struggles with background noise.
  - `small` (~460 MB, ~244M params): ~40–55 ms on RTX 5070. The "sweet spot" for conversational Russian; low Word Error Rate (WER).
  - `medium` (~1.5 GB, ~769M params): ~100–120 ms on RTX 5070. High accuracy, but higher latency.
  - `large-v3-turbo` (~1.6 GB, ~809M params): ~80–95 ms on RTX 5070. Modern pruned architecture with excellent English idioms.

---

## 3. Candidate Architectural Pathways

### Pathway A: Direct Monolithic Translation (Whisper `task="translate"` + Kokoro-82M TTS)
* **Pipeline:** Mic IN -> VAD (250 ms pause) -> Faster-Whisper `task="translate"` (50 ms) -> Kokoro-82M (45 ms) -> Topping Loopback OUT.
* **Latency:** ~350–400 ms total.
* **Pros:** Only two neural networks in pipeline; zero extra LLM overhead.
* **Cons:** Whisper literal translations might lack colloquial slang nuances compared to dedicated LLMs.

### Pathway B: Cascaded Hybrid Pipeline (ASR + HY-MT 1.8B + Kokoro-82M TTS)
* **Pipeline:** Mic IN -> VAD (250 ms) -> Faster-Whisper / GigaAM ASR (35 ms) -> Tencent HY-MT 1.8B (50 ms) -> Kokoro-82M (45 ms) -> Topping Loopback OUT.
* **Latency:** ~400–450 ms total.
* **Pros:** State-of-the-art slang and gaming idiom translation; full control over translation prompts.
* **Cons:** Requires running HY-MT simultaneously with ASR and TTS.

---

## 4. TTS (Text-to-Speech) Candidates Comparison

| Engine | Size / VRAM | Latency / RTF | Voice Quality (UTMOS) | Offline Status | Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kokoro-82M ONNX** | ~150 MB / 0.3 GB | ~40–50 ms (RTF 0.08) | **4.45 / 5.0 (Studio)** | 100% Offline (Apache 2.0) | **Primary Contender** |
| **Piper TTS (VITS)** | ~60 MB / 0 GB (CPU) | ~15–25 ms (RTF 0.03) | 3.50 / 5.0 (Robotic) | 100% Offline (MIT) | Fast but robotic |
| **XTTS v2 (Coqui)** | ~2.5 GB VRAM | ~800–1200 ms (RTF 0.6) | 4.20 / 5.0 (Natural) | 100% Offline | Abandoned, high latency |
| **ChatTTS / CosyVoice** | ~4–6 GB VRAM | ~700–1500 ms | 4.40 / 5.0 (Natural) | 100% Offline | Heavy diffusion, game stutter |
| **Edge-TTS (MS Cloud)**| 0 MB | ~400–800 ms (Net ping) | 4.30 / 5.0 (Natural) | Cloud only | Requires Internet, ping jitter |

---

## 5. Selected Open-Source Base: `Dizcord`
* **Upstream:** [Lagalizer/Dizcord](https://github.com/Lagalizer/Dizcord) (GPL-3.0, Oct 2026, Windows).
* **Architecture:** Decoupled multi-threaded PySide6 pipeline (`capture` -> `VAD` -> `transcribe` -> `translate` -> `synthesize` -> `playback`).
* **Key Native Advantages:**
  1. Built-in native support for **Kokoro-82M ONNX** (`KokoroTTS`) and **Faster-Whisper** (`FasterWhisperSTT`).
  2. Native loopback capture and playback via `PyAudioWPatch` and `sounddevice` with DirectSound/WASAPI.
  3. Push-to-Talk, voice activity detection (VAD), live audio meters, and full Russian GUI localization out-of-the-box.
  4. Fully offline operation without any paid cloud APIs.
