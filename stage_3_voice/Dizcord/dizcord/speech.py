"""The app's voice: one Speaker per place it talks (your headphones = "incoming", Discord = "outgoing").

Everything said on the same place - voice-call translations, chat messages read aloud, typed messages - goes through
its Speaker, so two things are never said at once (no voice over voice). Speed:
- the next line is synthesised while the current one plays (no gap waiting for the voice engine);
- streaming voices (Edge) start playing ~0.3 s after the request, before the whole sentence exists;
- long texts with other engines are spoken sentence by sentence (the first one starts while the rest is made);
- leading/trailing silence of the voice is cut;
- when lines pile up, the voice speeds up a little (catch-up) instead of falling further behind.
Nothing is dropped from a live conversation; only old chat messages are skipped when chat reading falls behind.
"""
from __future__ import annotations

import collections
import logging
import re
import threading
import time
from dataclasses import dataclass, field

import numpy as np

from .providers import ProviderError

log = logging.getLogger("dizcord.speech")

NAME_STYLES = [("short", "First 2 letters of the name"), ("first", "First name"), ("full", "Full name"),
               ("off", "Don't say who")]


def short_name(name: str, style: str) -> str:
    """How the voice says who is talking: 'short' = first 2 letters ("Jo"), 'first' = first word, 'full', 'off'."""
    name = re.sub(r"[^\w\s'-]", " ", name or "", flags=re.UNICODE).strip()
    if not name or style == "off":
        return ""
    if style == "short":
        letters = re.sub(r"[\W_\d]", "", name, flags=re.UNICODE)
        return (letters[:2] or name[:2]).capitalize()
    if style == "first":
        return name.split()[0]
    return name


def split_sentences(text: str, first_max: int = 90, rest_min: int = 60) -> list[str]:
    """Pieces to synthesise one after another: a short first piece (starts sooner), then fuller pieces."""
    text = text.strip()
    if len(text) <= first_max:
        return [text]
    parts = [p for p in re.split(r"(?<=[.!?…。！？;:])\s+|\n+", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if out and (len(out[-1]) < (first_max // 3 if len(out) == 1 else rest_min)):
            out[-1] = f"{out[-1]} {p}"
        else:
            out.append(p)
    return out or [text]


@dataclass
class Utterance:
    text: str
    lang: str
    kind: str = "voice"              # voice (call translation) | chat (chat message) | typed | test
    who: str = ""                    # who said it - spoken according to Settings ("Jo: …")
    on_start: object = None          # fn(utterance) when the sound starts
    on_done: object = None           # fn(utterance) when it has been said (or skipped)
    t0: float = field(default_factory=time.monotonic)
    timings: dict = field(default_factory=dict)
    # filled by the Speaker
    spoken_text: str = ""
    speed: float = 1.0
    chunks: list = field(default_factory=list)     # [(float32 audio, sample rate)]
    finished: bool = False
    cancelled: bool = False
    error: str = ""
    started_at: float = 0.0
    done_called: bool = False
    cv: threading.Condition = field(default_factory=threading.Condition)

    def push(self, audio: np.ndarray, sr: int):
        if len(audio):
            with self.cv:
                self.chunks.append((np.asarray(audio, dtype=np.float32), int(sr)))
                self.cv.notify_all()

    def finish(self, error: str = ""):
        with self.cv:
            self.finished = True
            self.error = error
            self.cv.notify_all()

    def seconds(self) -> float:
        return sum(len(a) / sr for a, sr in self.chunks)


class _SilenceTrim:
    """Cuts the silence a voice engine puts before and after the speech, while the audio streams in."""

    def __init__(self, out, thresh: float = 10 ** (-50 / 20), pad_s: float = 0.03, max_hold_s: float = 0.6):
        self.out, self.thresh, self.pad_s, self.max_hold_s = out, thresh, pad_s, max_hold_s
        self.started = False
        self.hold = np.zeros(0, dtype=np.float32)
        self.sr = 24000

    def push(self, x: np.ndarray, sr: int):
        self.sr = sr
        pad = int(self.pad_s * sr)
        if not self.started:
            loud = np.flatnonzero(np.abs(x) > self.thresh)
            if not len(loud):
                return
            x = x[max(0, loud[0] - pad):]
            self.started = True
        buf = np.concatenate([self.hold, x])
        loud = np.flatnonzero(np.abs(buf) > self.thresh)
        cut = (loud[-1] + pad + 1) if len(loud) else 0              # keep everything up to the last sound
        if len(buf) - cut > int(self.max_hold_s * sr):               # a real pause in the speech: let it through
            cut = len(buf) - int(self.max_hold_s * sr)
        if cut > 0:
            self.out(buf[:cut], sr)
        self.hold = buf[cut:]

    def close(self):
        pad = int(self.pad_s * self.sr)
        if len(self.hold) and pad:
            self.out(self.hold[:pad], self.sr)
        self.hold = np.zeros(0, dtype=np.float32)


class Speaker:
    PREPARE_AHEAD = 2           # lines synthesised in advance
    START_BUFFER_S = 0.25       # streamed audio buffered before playback starts (no stutter)
    MAX_CHAT_WAITING = 3        # chat reading falling behind: the oldest waiting chat message is skipped

    def __init__(self, engine, direction: str):
        self.engine = engine
        self.dir = direction
        self._cv = threading.Condition()
        self._waiting: collections.deque[Utterance] = collections.deque()
        self._ready: collections.deque[Utterance] = collections.deque()   # being prepared / prepared, in order
        self._current: Utterance | None = None
        self._clips: list = []
        self._last_who = ("", 0.0)
        # [start, end or None, text] of what was said lately - the echo filter compares the microphone with it
        self.recent: collections.deque = collections.deque(maxlen=30)
        self._threads: list[threading.Thread] = []

    # ------------------------------------------------------------------ API
    def say(self, utt: Utterance, interrupt_kind: str | None = None):
        """Queue a line. Call translations go before chat messages that are still waiting.
        interrupt_kind: first cut/skip everything of that kind (chat "interrupt" mode)."""
        self._ensure_threads()
        with self._cv:
            if interrupt_kind:
                self._drop(interrupt_kind)
            if utt.kind == "voice":
                idx = next((i for i, u in enumerate(self._waiting) if u.kind == "chat"), len(self._waiting))
                self._waiting.insert(idx, utt)
            else:
                self._waiting.append(utt)
            if utt.kind == "chat":
                chats = [u for u in self._waiting if u.kind == "chat"]
                for old in chats[:-self.MAX_CHAT_WAITING]:
                    self._waiting.remove(old)
                    self._skip(old)
            self._cv.notify_all()

    def cancel(self, kind: str | None = None):
        """Stop what is being said (of this kind, or anything) and forget what is waiting."""
        with self._cv:
            self._drop(kind)
            self._cv.notify_all()

    def backlog(self) -> int:
        with self._cv:
            return len(self._waiting) + len(self._ready) + (1 if self._current else 0)

    @property
    def speaking(self) -> bool:
        return self._current is not None

    def wait_idle(self, timeout: float = 30.0) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if not self.backlog():
                return True
            time.sleep(0.05)
        return False

    # ------------------------------------------------------------------ internals
    def _drop(self, kind):
        for q in (self._waiting, self._ready):
            for u in [u for u in q if kind is None or u.kind == kind]:
                q.remove(u)
                self._skip(u)
        cur = self._current
        if cur is not None and (kind is None or cur.kind == kind):
            cur.cancelled = True
            for dev, clip in list(self._clips):
                dev.fade_out(clip)
            with cur.cv:
                cur.cv.notify_all()

    @staticmethod
    def _skip(u: Utterance):
        u.cancelled = True
        u.finish()
        Speaker._done(u)

    @staticmethod
    def _done(u: Utterance):
        if u.on_done and not u.done_called:
            u.done_called = True
            try:
                u.on_done(u)
            except Exception:  # noqa: BLE001
                log.exception("on_done")

    def _ensure_threads(self):
        if self._threads and all(t.is_alive() for t in self._threads):
            return
        self._threads = [threading.Thread(target=self._prepare_loop, name=f"speak-{self.dir}-prep", daemon=True),
                         threading.Thread(target=self._play_loop, name=f"speak-{self.dir}-play", daemon=True)]
        for t in self._threads:
            t.start()

    def _catchup_speed(self) -> float:
        if not self.engine.profile.get("speech", {}).get("catchup", True):
            return 1.0
        behind = len(self._waiting) + len(self._ready) + (1 if self._current else 0)
        return {0: 1.0, 1: 1.0, 2: 1.12, 3: 1.22}.get(behind, 1.3)

    def _spoken_text(self, utt: Utterance) -> str:
        sp = self.engine.profile.get("speech", {})
        style = sp.get("names", "short")
        label = ", ".join(n for n in (short_name(w, style) for w in utt.who.split(" & ")) if n) if utt.who else ""
        if label and not sp.get("repeat_names", False):
            last, when = self._last_who
            if last == utt.who and time.monotonic() - when < 45:
                label = ""                      # the same person goes on talking: don't repeat the name
        if utt.who:
            self._last_who = (utt.who, time.monotonic())
        return f"{label}: {utt.text}" if label else utt.text

    def _prepare_loop(self):
        while True:
            with self._cv:
                while not self._waiting or len(self._ready) >= self.PREPARE_AHEAD:
                    self._cv.wait()
                utt = self._waiting.popleft()
                utt.speed = self._catchup_speed()
                utt.spoken_text = self._spoken_text(utt)
                self._ready.append(utt)
                self._cv.notify_all()
            t = time.monotonic()
            try:
                self._synthesize(utt)
                utt.timings.setdefault("tts", time.monotonic() - t)
                utt.finish()
            except ProviderError as e:
                self.engine.emit_error(str(e))
                utt.finish(str(e))
            except Exception as e:  # noqa: BLE001
                log.exception("speech synthesis failed")
                self.engine.emit_error(f"Voice: {e}")
                utt.finish(str(e))

    def _synthesize(self, utt: Utterance):
        from .audio import voicefx
        from .audio.utils import trim_silence
        eng = self.engine
        tts = eng.provider("tts")
        cfg = eng.profile.get(self.dir, {})
        voice = eng.voice_for(self.dir)
        gender = eng.profile["tts"].get("gender", "female")
        speed = float(cfg.get("voice_speed", 1.0)) * utt.speed
        pitch = float(cfg.get("voice_pitch", 0.0))
        t_req = time.monotonic()

        def first_audio(audio, sr):
            if "tts" not in utt.timings:
                utt.timings["tts"] = time.monotonic() - t_req      # time to the first sound
            utt.push(audio, sr)

        if getattr(tts, "streams", False) and abs(pitch) < 0.05:
            trim = _SilenceTrim(first_audio)
            tts.synthesize_stream(utt.spoken_text, utt.lang, voice, gender,
                                  lambda a, sr: None if utt.cancelled else trim.push(a, sr), speed=speed)
            trim.close()
            return
        for part in split_sentences(utt.spoken_text):
            if utt.cancelled:
                return
            audio, sr = tts.synthesize(part, utt.lang, voice, gender)
            if audio is None or len(audio) == 0:
                raise ProviderError(f"{tts.name}: no audio returned")
            audio = trim_silence(np.asarray(audio, dtype=np.float32), sr)
            first_audio(voicefx.apply(audio, sr, speed, pitch), sr)

    def _sinks(self):
        """[(output device, volume, tag)] where this Speaker plays."""
        eng = self.engine
        cfg = eng.profile[self.dir]
        out = [(eng.outputs.get(cfg["output_device"]), float(cfg.get("volume", 1.0)), self.dir)]
        if self.dir == "outgoing" and cfg.get("monitor"):
            try:
                out.append((eng.outputs.get(cfg.get("monitor_device", "")), float(cfg.get("monitor_volume", 0.5)),
                            "monitor"))
            except Exception as e:  # noqa: BLE001
                eng.emit_error(f"Monitor output: {e}")
        return out

    def _play_loop(self):
        while True:
            with self._cv:
                while not self._ready:
                    self._cv.wait()
                utt = self._ready[0]
            with utt.cv:                      # wait for enough audio (or the end) before starting
                while not (utt.finished or utt.cancelled or utt.seconds() >= self.START_BUFFER_S):
                    utt.cv.wait(0.5)
            with self._cv:
                if self._ready and self._ready[0] is utt:
                    self._ready.popleft()
                self._current = utt
                self._cv.notify_all()
            try:
                if not utt.cancelled and utt.chunks:
                    self._play(utt)
            except Exception as e:  # noqa: BLE001
                log.exception("speech playback failed")
                self.engine.emit_error(f"Voice output: {e}")
            finally:
                with self._cv:
                    self._current = None
                    self._clips = []
                    self._cv.notify_all()
                self._done(utt)

    def _play(self, utt: Utterance):
        from .audio.utils import BlockResampler
        sinks = self._sinks()
        clips = [(dev, dev.play_stream(vol, tag, utt.kind), {}) for dev, vol, tag in sinks]
        with self._cv:
            self._clips = [(dev, clip) for dev, clip, _ in clips]
        fed = 0
        total = 0.0
        while True:
            with utt.cv:
                while fed >= len(utt.chunks) and not (utt.finished or utt.cancelled):
                    utt.cv.wait(0.2)
                new = utt.chunks[fed:]
                fed = len(utt.chunks)
                done = utt.finished or utt.cancelled
            if utt.cancelled:
                break
            for audio, sr in new:
                total += len(audio) / sr
                for dev, clip, rs in clips:
                    r = rs.get(sr) or rs.setdefault(sr, BlockResampler(sr, dev.samplerate))
                    dev.append(clip, r.process(audio))
            if new and not utt.started_at:
                utt.started_at = time.monotonic()
                said = [utt.started_at, None, utt.text]
                self.recent.append(said)
                if utt.on_start:
                    try:
                        utt.on_start(utt)
                    except Exception:  # noqa: BLE001
                        log.exception("on_start")
            if done:
                break
        for dev, clip, rs in clips:
            for r in rs.values():
                dev.append(clip, r.flush())
            dev.finish(clip)
        limit = time.monotonic() + total + 10
        for dev, clip, _ in clips:
            while not clip.done.wait(0.1):
                if time.monotonic() > limit or dev.stream is None:
                    break
        if utt.started_at:
            said[1] = time.monotonic()
