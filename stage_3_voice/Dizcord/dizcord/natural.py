"""Natural voices for the guided tour and the Manual tab, in the language of the app.

Two engines, same interface (speak / stop):
  - "piper:<voice>"  Piper neural voices that run on this PC - fully offline, no AI service, no internet. The voice
                     files are downloaded once by setup into models/piper.
  - "edge:<voice>"   Microsoft Edge neural voices - very natural, free, no key, but they need internet.

The text is turned into speech sentence by sentence in a background thread, so the first words start quickly and a
new call cuts the previous reading at once. If an engine fails, `on_error(kind, message)` is called from the worker
thread and nothing is played (the caller picks another voice).

prefetch() synthesises the beginning of a text in advance (the next / previous step of the tour), so pressing Next
starts the voice at once.
"""
from __future__ import annotations

import asyncio
import logging
import queue
import re
import threading

import numpy as np

from . import i18n
from . import languages as L
from .audio.utils import decode_audio
from .config import MODELS_DIR

log = logging.getLogger("dizcord.natural")

EDGE = "edge:"
PIPER = "piper:"
PIPER_DIR = MODELS_DIR / "piper"

# (voice id, label) - a short, curated list of English neural voices of the online engine
EDGE_VOICES_EN = [
    ("en-US-AriaNeural", "Aria - US, female"),
    ("en-US-JennyNeural", "Jenny - US, female"),
    ("en-US-AvaNeural", "Ava - US, female"),
    ("en-US-GuyNeural", "Guy - US, male"),
    ("en-US-AndrewNeural", "Andrew - US, male"),
    ("en-GB-SoniaNeural", "Sonia - UK, female"),
    ("en-GB-RyanNeural", "Ryan - UK, male"),
    ("en-AU-NatashaNeural", "Natasha - Australia, female"),
]
_CHUNK = 280                       # characters per request: long enough to sound natural
_SECOND = 140                      # the second is medium, so synthesis always stays ahead of playback
_FIRST = 60                    # the first piece is short, so the voice starts speaking sooner


def _chunks(text: str) -> list[str]:
    """Sentences grouped into pieces; the first piece is kept short so the first words come out fast."""
    sentences = re.split(r"(?<=[.!?:])\s+", text.strip())
    out, cur = [], ""
    for s in sentences:
        limit = (_FIRST, _SECOND)[len(out)] if len(out) < 2 else _CHUNK         # pieces grow: 60, 140, then 280
        if cur and len(cur) + len(s) + 1 > limit:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def preload() -> None:
    """Load the offline voice of the app language now, in this thread. ONNX Runtime holds Python's lock for the
    few seconds it takes to load a voice, which would freeze the window - so main.py does it at start-up, before the
    window exists. Afterwards the guide and the Manual start speaking at once (synthesis does not hold the lock)."""
    n = NaturalNarrator()
    if n.piper_ok:
        try:
            n._piper_synth(n.piper_voices()[0][0], 0)
        except Exception as e:  # noqa: BLE001
            log.info("could not preload the offline voice: %s", e)


def _can_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:  # noqa: BLE001
        return False


class NaturalNarrator:
    _piper_loaded: dict = {}
    _load_lock = threading.Lock()
    _cache: dict = {}                                # (voice, rate, piece) -> (audio, sample rate), see prefetch()

    def __init__(self, on_error=None):
        self.on_error = on_error
        self._gen = 0
        self._lock = threading.Lock()
        sound = _can_import("sounddevice")
        self.edge_ok = sound and _can_import("edge_tts")
        self.piper_ok = sound and _can_import("piper") and bool(self.piper_voices())
        self.available = self.edge_ok or self.piper_ok

    # ------------------------------------------------------------------ voices
    def edge_voices(self) -> list[tuple[str, str]]:
        """Online voices of the app language."""
        lang = i18n.current()
        if lang.code == "en":
            return list(EDGE_VOICES_EN)
        info = L.LANGUAGES.get(lang.code)
        voices = [lang.edge] + [v for v in (info[2:4] if info else ()) if v != lang.edge]
        return [(v, v.split("-")[-1].replace("Neural", "") + f" - {lang.name}") for v in voices]

    def piper_voices(self) -> list[tuple[str, str]]:
        """[(file name without .onnx, label)] of the offline voices of the app language found in models/piper
        (the one the app downloads first)."""
        lang = i18n.current()
        prefix = lang.piper.split("-")[0]
        try:
            files = sorted((f for f in PIPER_DIR.glob(f"{prefix}-*.onnx") if f.with_name(f.name + ".json").exists()),
                           key=lambda f: (f.stem != lang.piper, f.stem))
        except OSError:
            return []
        out = []
        for f in files:
            lang, name, quality = (f.stem.split("-") + ["", ""])[:3]
            out.append((f.stem, f"{name.replace('_', ' ').title()} - {lang.replace('_', ' ')}, {quality}"))
        return out

    def warm_up(self, voice: str) -> None:
        """Load the offline voice in the background (and run it once) so the first reading starts at once."""
        if not voice.startswith(PIPER) or not self.piper_ok:
            return

        def work():
            try:
                self._piper_synth(voice[len(PIPER):], 0)("Ready.")
            except Exception as e:  # noqa: BLE001
                log.info("could not warm up the offline voice: %s", e)
        threading.Thread(target=work, daemon=True).start()

    def refresh(self) -> None:
        """Look for voices again (after the voice of the app language was downloaded)."""
        self.piper_ok = _can_import("sounddevice") and _can_import("piper") and bool(self.piper_voices())
        self.available = self.edge_ok or self.piper_ok

    def prefetch(self, texts: list[str], voice: str, rate: int = 0) -> None:
        """Synthesise the first piece of each text in the background, so speak() can start it at once."""
        if not voice.startswith(PIPER) or not self.piper_ok:
            return                                     # the online voice is fast enough and needs no cache

        def work():
            try:
                synth = self._piper_synth(voice[len(PIPER):], rate)
                for text in texts:
                    pieces = _chunks(text)
                    key = (voice, rate, pieces[0]) if pieces else None
                    if key and key not in self._cache:
                        self._cache[key] = synth(pieces[0])
                        while len(self._cache) > 12:
                            self._cache.pop(next(iter(self._cache)))
            except Exception as e:  # noqa: BLE001
                log.info("prefetch failed: %s", e)
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ speaking
    def speak(self, text: str, voice: str, rate: int = 0) -> None:
        """Say `text` now. `voice` is "piper:<voice>" or "edge:<voice>"; `rate` is a percentage (-50 .. +100).
        Returns at once."""
        self.stop()
        if not text.strip():
            return
        with self._lock:
            gen = self._gen
        q: queue.Queue = queue.Queue(maxsize=2)       # synthesised audio waiting to be played
        threading.Thread(target=self._produce, args=(gen, _chunks(text), voice, rate, q), daemon=True).start()
        threading.Thread(target=self._play, args=(gen, q), daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            self._gen += 1
        if _can_import("sounddevice"):
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:  # noqa: BLE001
                pass

    def _alive(self, gen: int) -> bool:
        return gen == self._gen

    # ------------------------------------------------------------------ engines
    def _edge_synth(self, voice: str, rate: int):
        import edge_tts
        pct = f"+{int(rate)}%" if rate >= 0 else f"{int(rate)}%"

        async def one(t):
            buf = bytearray()
            async for c in edge_tts.Communicate(t, voice, rate=pct).stream():
                if c["type"] == "audio":
                    buf.extend(c["data"])
            return bytes(buf)

        def synth(t):
            data = asyncio.run(one(t))
            if not data:
                raise RuntimeError("no audio returned")
            return decode_audio(data)
        return synth

    def _piper_synth(self, voice: str, rate: int):
        from piper import PiperVoice
        path = PIPER_DIR / f"{voice}.onnx"
        with NaturalNarrator._load_lock:                  # the warm-up thread and a reading never load it twice
            pv = NaturalNarrator._piper_loaded.get(str(path))
            if pv is None:
                pv = NaturalNarrator._piper_loaded[str(path)] = PiperVoice.load(str(path))
        length_scale = max(0.5, min(2.0, 0.95 / (1 + rate / 100.0)))     # slider +x% = x% faster

        def synth(t):
            try:                                                           # piper-tts >= 1.3
                from piper import SynthesisConfig
                parts = list(pv.synthesize(t, syn_config=SynthesisConfig(length_scale=length_scale)))
                if not parts:
                    raise RuntimeError("no audio returned")
                return np.concatenate([p.audio_float_array for p in parts]).astype(np.float32), parts[0].sample_rate
            except ImportError:                                            # piper-tts 1.2
                from .audio.utils import pcm16_to_float
                raw = b"".join(pv.synthesize_stream_raw(t, length_scale=length_scale))
                return pcm16_to_float(raw), pv.config.sample_rate
        return synth

    def _produce(self, gen, chunks, voice, rate, q):
        kind = PIPER if voice.startswith(PIPER) else EDGE
        name = voice[len(kind):]
        try:
            synth = self._piper_synth(name, rate) if kind == PIPER else self._edge_synth(name, rate)
            for t in chunks:
                if not self._alive(gen):
                    return
                cached = self._cache.get((voice, rate, t))
                audio, sr = cached if cached is not None else synth(t)
                while self._alive(gen):
                    try:
                        q.put((audio, sr), timeout=0.2)
                        break
                    except queue.Full:
                        pass
        except Exception as e:  # noqa: BLE001
            log.warning("%s voice failed: %s", kind.rstrip(":"), e)
            if self._alive(gen) and self.on_error:
                self.on_error(kind, str(e))
        finally:
            while self._alive(gen):                       # tell the player there is nothing more
                try:
                    q.put(None, timeout=0.2)
                    break
                except queue.Full:
                    pass

    def _play(self, gen, q):
        import sounddevice as sd
        while self._alive(gen):
            try:
                item = q.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is None:
                return
            audio, sr = item
            try:
                sd.play(np.asarray(audio, dtype=np.float32), sr)
                n = len(audio) / float(sr)
                waited = 0.0
                while waited < n + 0.3 and self._alive(gen):
                    threading.Event().wait(0.05)
                    waited += 0.05
            except Exception as e:  # noqa: BLE001
                log.warning("could not play: %s", e)
                return
