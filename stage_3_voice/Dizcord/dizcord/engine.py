"""The translation engine: two pipelines (incoming + outgoing) sharing providers and outputs.

incoming: Discord audio -> VAD -> STT -> translate -> subtitles + the app voice in my headphones
outgoing: my mic -> VAD/PTT -> STT -> translate -> the app voice into the virtual cable (Discord's microphone)

Each pipeline has three stages on their own threads, so they overlap: recognising sentence 2 while sentence 1 is
being translated while sentence 0 is being spoken. Nothing said in the call is dropped: if recognition falls
behind, the waiting sentences of the same person are recognised together in one request.

"Discord only" listening (listen_mode "app", the default) records just the Discord app (Windows process loopback):
the app's own voice is never captured, so listening never pauses while the app talks, and "Hear people" (hotkey)
can turn the original voices down to silence in the Windows mixer while the app keeps hearing them.

Events are delivered to the GUI through emit(dict).
"""
from __future__ import annotations

import collections
import itertools
import logging
import queue
import re
import threading
import time

import numpy as np

from . import languages as L
from .audio import devices
from .audio.capture import InputDeviceSource, LoopbackSource
from .audio.player import OutputManager
from .audio.vad import Segmenter
from .providers import REGISTRY, ProviderError  # noqa: F401  (REGISTRY re-exported)
from .providers.base import describe_downloads
from .speech import Speaker, Utterance
from .textengine import TextEngine, detect_text_language  # noqa: F401  (re-exported)

log = logging.getLogger("dizcord.engine")

# Things Whisper likes to "hear" in silence/noise.
_HALLUCINATIONS = {
    "thank you", "thanks for watching", "thank you for watching", "thanks for watching and see you next time",
    "please subscribe", "subscribe", "you", "bye", "obrigado", "obrigada", "tchau", "gracias", "merci",
    "ご視聴ありがとうございました", "продолжение следует", "субтитры сделал dimatorzok", "amen",
    "legendas pela comunidade amara.org", "sous-titres réalisés par la communauté d'amara.org",
    "untertitel der amara.org-community", "subtítulos realizados por la comunidad de amara.org",
}
MERGE_MAX_S = 20.0           # waiting sentences recognised together, up to this much audio per request
_VIRTUAL = re.compile(r"cable|voicemeeter|vb-audio|virtual|vaio|voicemod|steelseries sonar", re.I)


def _norm(text: str) -> str:
    return re.sub(r"[^\w\s']", "", text.lower(), flags=re.UNICODE).strip()


def is_garbage(text: str) -> bool:
    t = _norm(text)
    if not t or not re.search(r"\w", t):
        return True
    if t in _HALLUCINATIONS or "amara.org" in text.lower():
        return True
    return False


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def is_echo_of(heard: str, spoken: str) -> bool:
    """True when `heard` (recognised from a microphone/loopback) is the app's own voice saying `spoken`."""
    a, b = _words(heard), set(_words(spoken))
    if len(a) < 2 or not b:
        return bool(a) and len(b) <= 2 and a[0] in b and len(a[0]) > 3
    return sum(1 for w in a if w in b) / len(a) >= 0.7


def cable_recording_side(output_name: str) -> str | None:
    """'CABLE-A Input (VB-Audio Cable A)' -> the matching 'CABLE-A Output …' recording device, if installed."""
    m = re.match(r"^(CABLE(?:-\w+)?) (?:Input|In 16ch)\b", output_name or "", re.I)
    if not m:
        return None
    want = f"{m.group(1)} Output".lower()
    for name in devices.input_devices():
        if name.lower().startswith(want):
            return name
    return None


class Pipeline:
    def __init__(self, engine: "Engine", direction: str):
        self.engine = engine
        self.dir = direction                  # "incoming" | "outgoing"
        self.source = None
        self.segmenter = None
        self.stt_q: collections.deque = collections.deque()
        self._stt_cv = threading.Condition()
        self.mt_q: queue.Queue = queue.Queue()
        self.running = False
        self.threads: list[threading.Thread] = []
        self._passthrough_ok = False
        self.app_capture = False              # listening to the Discord app only (never hears the app's voice)

    # ------------------------------------------------------------ config
    @property
    def p(self) -> dict:
        return self.engine.profile

    @property
    def cfg(self) -> dict:
        return self.p[self.dir]

    def _listen_device_name(self) -> str:
        return self.p["input"]["listen_device"] or devices.default_name("output")

    # ------------------------------------------------------------ lifecycle
    def start(self):
        inp = self.p["input"]
        if self.dir == "incoming":
            mode = "vad"
            vad_cfg = inp["listen_vad"]
            gain = inp.get("listen_gain_db", 0.0)
            self.source = self._incoming_source(inp)
        else:
            mode = inp["mic_mode"]
            vad_cfg = inp["mic_vad"]
            gain = inp.get("mic_gain_db", 0.0)
            self.source = InputDeviceSource(inp["mic_device"], self._on_audio)

        self.running = True
        self.segmenter = Segmenter(self.source.samplerate, self._on_utterance, self._on_level, mode, vad_cfg, gain)
        if not self.app_capture:              # the Discord-only capture is already running
            self.source.start()
        self._passthrough_ok = self._check_passthrough()
        for fn in (self._stt_worker, self._mt_worker):
            t = threading.Thread(target=fn, name=f"{self.dir}-{fn.__name__}", daemon=True)
            t.start()
            self.threads.append(t)

    def _incoming_source(self, inp):
        if inp["listen_mode"] == "app":
            from .audio.winaudio import AppLoopbackSource
            src = AppLoopbackSource(inp.get("listen_app") or "discord", self._on_audio, self.engine.emit_status)
            try:
                src.start()                    # started here: if Windows can't do it, fall back right away
                self.app_capture = True
                self.engine.app_source = src
                self.engine.emit_status("Listening to the Discord app only (the app's own voice is never heard)")
                return src
            except Exception as e:  # noqa: BLE001
                src.stop()
                self.engine.emit_error(f"Can't listen to the Discord app only ({e}) - listening to everything "
                                       f"that plays on '{self._listen_device_name()}' instead.")
                return LoopbackSource("", self._on_audio)
        cable_out = self._cable_recording_side(inp["listen_device"]) if inp["listen_mode"] == "loopback" else None
        if cable_out:
            # WASAPI loopback of a VB-Audio cable endpoint is silent - record its other side instead.
            self.engine.emit_status(f"Listening to '{cable_out}' (recording side of the virtual cable)")
            return InputDeviceSource(cable_out, self._on_audio)
        if inp["listen_mode"] == "loopback":
            return LoopbackSource(inp["listen_device"], self._on_audio)
        return InputDeviceSource(inp["listen_device"], self._on_audio)

    def stop(self):
        self.running = False
        if self.source:
            self.source.stop()
            self.source = None
        with self._stt_cv:
            self.stt_q.append(None)
            self._stt_cv.notify_all()
        self.mt_q.put(None)

    @staticmethod
    def _cable_recording_side(output_name: str) -> str | None:
        return cable_recording_side(output_name)

    def _check_passthrough(self) -> bool:
        if not self.cfg.get("passthrough") or self.app_capture:
            return False
        if self.dir == "incoming":
            inp = self.p["input"]
            res = self.engine.outputs.resolve
            if inp["listen_mode"] == "loopback" and res(self.cfg["output_device"]) == res(inp["listen_device"]):
                self.engine.emit_error("Pass-through disabled: you can't play the captured device back into "
                                       "itself (feedback loop). Capture a separate device (e.g. CABLE-B / Voicemeeter).")
                return False
        return True

    # ------------------------------------------------------------ audio thread
    def _on_audio(self, chunk: np.ndarray):
        if not self.running or self.segmenter is None:
            return
        if self._passthrough_ok:
            should_pass = True
            if self.dir == "incoming":
                should_pass = self.engine.hears_people()
            else:
                # Outgoing: pass live mic only when NOT translating via PTT and NOT playing AI speech
                is_translating = (self.segmenter.mode in ("ptt", "toggle") and self.segmenter.ptt_down)
                is_ai_speaking = self.engine.outputs.any_playing("outgoing")
                should_pass = not is_translating and not is_ai_speaking

            if should_pass:
                try:
                    self.engine.outputs.get(self.cfg["output_device"]).push_live(
                        chunk, self.source.samplerate, float(self.cfg.get("passthrough_volume", 1.0)))
                except Exception as e:
                    self._passthrough_ok = False
                    self.engine.emit_error(f"Pass-through failed: {e}")
        self.segmenter.muted = self._should_mute()
        self.segmenter.feed(chunk)

    def _should_mute(self) -> bool:
        inp = self.p["input"]
        if not self.cfg.get("enabled", True):
            return True
        if self.dir == "incoming":
            if self.engine.paused_incoming:
                return True
            if self.app_capture:              # only Discord is recorded: the app's voice can't get in
                return False
            if inp.get("pause_listen_while_speaking") and inp["listen_mode"] == "loopback":
                dev = self.engine.outputs.existing(inp["listen_device"])
                return bool(dev and dev.is_playing())
            return False
        # outgoing: don't pick up translations coming out of the speakers
        if self.engine.muted_outgoing:
            return True
        if inp.get("ignore_mic_while_playing"):
            return self.engine.outputs.any_playing("incoming") or self.engine.outputs.any_playing("monitor")
        return False

    def _on_level(self, db, speech):
        self.engine.emit({"type": "level", "dir": self.dir, "db": db, "speech": speech,
                          "threshold": self.segmenter.effective_threshold if self.segmenter else -45})

    def _on_utterance(self, audio16, duration):
        t_end = time.monotonic()
        who = self.engine.who_spoke(t_end - duration, t_end) if self.dir == "incoming" else ""
        with self._stt_cv:
            self.stt_q.append((t_end, audio16, duration, who))
            self._stt_cv.notify_all()

    # ------------------------------------------------------------ workers
    def _next_audio(self):
        """The next sentence to recognise - with the ones waiting behind it by the same person (catch up, drop
        nothing). Returns None when stopping."""
        with self._stt_cv:
            while not self.stt_q:
                self._stt_cv.wait()
            item = self.stt_q.popleft()
            if item is None:
                return None
            t0, audio, duration, who = item
            parts = [audio]
            merged = 1
            while self.stt_q and self.stt_q[0] is not None and self.stt_q[0][3] == who \
                    and duration + self.stt_q[0][2] <= MERGE_MAX_S:
                _t, a, d, _w = self.stt_q.popleft()
                parts += [np.zeros(int(16000 * 0.25), dtype=np.float32), a]
                duration += d
                merged += 1
        if merged > 1:
            log.info("%s: catching up - %d sentences recognised together", self.dir, merged)
        return t0, np.concatenate(parts), who

    def _stt_worker(self):
        while True:
            item = self._next_audio()
            if item is None or not self.running:
                return
            t_captured, audio, who = item
            try:
                self.process_audio(audio, t_captured, who=who)
            except ProviderError as e:
                self.engine.emit_error(str(e))
            except Exception as e:
                log.exception("pipeline error")
                self.engine.emit_error(f"{self.dir}: {e}")
            finally:
                self.engine.emit({"type": "busy", "dir": self.dir, "stage": None})

    def _mt_worker(self):
        while True:
            job = self.mt_q.get()
            if job is None:
                return
            try:
                self.process_text(**job)
            except ProviderError as e:
                self.engine.emit_error(str(e))
            except Exception as e:
                log.exception("translation error")
                self.engine.emit_error(f"{self.dir}: {e}")
            finally:
                self.engine.emit({"type": "busy", "dir": self.dir, "stage": None})

    def process_audio(self, audio, t0=None, who: str = ""):
        eng = self.engine
        t0 = t0 or time.monotonic()
        src_cfg = self.cfg["source_lang"]
        src = None if src_cfg == L.AUTO else src_cfg
        eng.emit({"type": "busy", "dir": self.dir, "stage": "stt"})
        stt = eng.provider("stt")
        if src is None and not getattr(stt, "supports_auto", True):
            src = eng.profile["outgoing"]["source_lang"] if self.dir == "outgoing" else None
        t = time.monotonic()
        text, detected = stt.transcribe(audio, src)
        t_stt = time.monotonic() - t
        if is_garbage(text):
            return
        if eng.is_echo(text, self.dir, self.app_capture, t0 - len(audio) / 16000 - 0.3, t0):
            log.info("%s: ignored the app's own voice: %s", self.dir, text[:80])
            return
        detected = detected or src or detect_text_language(text)
        job = {"text": text, "detected": detected, "t0": t0, "timings": {"stt": t_stt}, "who": who}
        if self.running:
            self.mt_q.put(job)                 # translated on its own thread: the next sentence is recognised now
        else:
            self.process_text(**job)

    def process_text(self, text, detected=None, t0=None, timings=None, typed=False, who: str = ""):
        eng = self.engine
        t0 = t0 or time.monotonic()
        timings = dict(timings or {})
        target = self.target_language()
        if detected is None:
            src_cfg = self.cfg["source_lang"]
            detected = None if src_cfg == L.AUTO else src_cfg
            detected = detected or detect_text_language(text)

        if self.dir == "incoming" and detected and not L.same_language(detected, eng.profile["incoming"]["target_lang"]):
            eng.set_their_language(detected)

        # regional variants (pt-PT vs pt-BR...) still go through translation
        skipped = L.same_language(detected, target) and target not in ("pt-PT", "en-GB", "zh-TW", "es-MX")
        translated = text
        if not skipped:
            eng.emit({"type": "busy", "dir": self.dir, "stage": "translate"})
            t = time.monotonic()
            tr = eng.provider("translate")
            ctx = eng.translate_context(self.dir)
            src_for_mt = detected
            if tr.needs_source and not src_for_mt:
                raise ProviderError(f"{tr.name}: couldn't detect the spoken language for: “{text[:60]}”")
            translated, det2 = tr.translate(text, src_for_mt, target, ctx)
            detected = detected or det2
            timings["mt"] = time.monotonic() - t
            if not translated.strip():
                return

        eng.add_history(who or ("Them" if self.dir == "incoming" else "Me"), text, translated)
        speak = bool(self.cfg.get("speak", True)) and not (skipped and self.dir == "incoming"
                                                           and self.cfg.get("skip_same_language", True))
        line_id = eng.next_line_id()
        eng.emit({"type": "line", "dir": self.dir, "id": line_id, "original": text, "translated": translated,
                  "src": detected, "tgt": target, "timings": timings, "skipped": skipped, "typed": typed,
                  "who": who, "latency": time.monotonic() - t0})
        if speak:
            def started(u, line_id=line_id):
                eng.emit({"type": "spoken", "dir": self.dir, "id": line_id, "timings": u.timings,
                          "latency": u.started_at - u.t0})
            eng.speaker(self.dir).say(Utterance(translated, target, kind="typed" if typed else "voice", who=who,
                                                on_start=started, t0=t0, timings=timings))

    def target_language(self) -> str:
        if self.dir == "outgoing" and self.cfg.get("follow_their_language") and self.engine.their_language:
            return self.engine.their_language
        return self.cfg["target_lang"]


class Engine(TextEngine):
    def __init__(self, profile: dict, keys, emit):
        super().__init__(profile, keys)
        self._emit = emit
        self.outputs = OutputManager()
        self.pipelines: dict[str, Pipeline] = {}
        self.speakers: dict[str, Speaker] = {}
        self.their_language: str | None = None
        self.running = False
        self.paused_incoming = False
        self.muted_outgoing = False
        self.hear_originals = bool(profile.get("incoming", {}).get("hear_originals", False))
        self.app_source = None                # the Discord-only capture while it runs
        self.app_volume = None
        self.rpc = None                       # who is talking (Discord RPC), when set up
        self._ids = itertools.count(1)
        self._hotkey_hooks = []
        self._ptt_down = False
        self._watch_stop = threading.Event()
        self._warned: dict[str, str] = {}
        threading.Thread(target=self._restore_discord_volume, name="restore-volume", daemon=True).start()
        self._update_rpc()

    # --------------------------------------------------------------- events
    def emit(self, ev: dict):
        try:
            self._emit(ev)
        except Exception:
            pass

    def emit_status(self, text):
        log.info(text)
        self.emit({"type": "status", "text": text})

    def emit_error(self, text):
        log.error(text)
        self.emit({"type": "error", "text": text})

    def _warn_once(self, key: str, text: str):
        """An error shown once per situation (not every few seconds while it lasts)."""
        if self._warned.get(key) != text:
            self._warned[key] = text
            if text:
                self.emit_error(text)

    def next_line_id(self) -> int:
        return next(self._ids)

    def set_their_language(self, lang):
        if lang and lang != self.their_language:
            self.their_language = lang
            self.emit({"type": "their_lang", "lang": lang})

    # --------------------------------------------------------------- voice
    def speaker(self, direction: str) -> Speaker:
        sp = self.speakers.get(direction)
        if sp is None:
            sp = self.speakers[direction] = Speaker(self, direction)
        return sp

    def voice_for(self, direction: str) -> str:
        tts = self.profile["tts"]
        return (tts.get("voices", {}).get(tts["provider"], {}) or {}).get(direction, "auto") or "auto"

    def synthesize(self, text, lang, direction):
        """Whole clip at once (Voice tab test). Live speech goes through speaker(direction)."""
        tts = self.provider("tts")
        audio, sr = tts.synthesize(text, lang, self.voice_for(direction), self.profile["tts"].get("gender", "female"))
        if audio is None or len(audio) == 0:
            raise ProviderError(f"{tts.name}: no audio returned")
        from .audio import voicefx
        from .audio.utils import trim_silence
        cfg = self.profile.get(direction, {})
        audio = trim_silence(np.asarray(audio, dtype=np.float32), sr)
        return voicefx.apply(audio, sr, cfg.get("voice_speed", 1.0), cfg.get("voice_pitch", 0.0)), sr

    def is_echo(self, text: str, direction: str, app_capture: bool = False, t_start: float | None = None,
                t_end: float | None = None) -> bool:
        """The microphone (or a loopback) heard the app's own voice: it was heard WHILE the app was saying the same
        words (so you can still repeat what you heard a moment later)."""
        if direction == "incoming" and app_capture:
            return False
        now = time.monotonic()
        t_end = t_end or now
        t_start = t_start if t_start is not None else t_end - 30
        for sp in self.speakers.values():
            for start, end, said in list(sp.recent):
                if t_start < (end or now) + 0.8 and t_end > start and is_echo_of(text, said):
                    return True
        return False

    # --------------------------------------------------------------- who is talking
    def _update_rpc(self):
        sp = self.profile.get("speakers", {})
        want = bool(sp.get("enabled")) and bool((sp.get("client_id") or "").strip())
        cid = (sp.get("client_id") or "").strip()
        if self.rpc and (not want or self.rpc.client_id != cid):
            self.rpc.stop()
            self.rpc = None
        if want and self.rpc is None:
            try:
                from .discord_rpc import SpeakingTracker
                self.rpc = SpeakingTracker(cid, self.keys, lambda text, ok: self.emit(
                    {"type": "rpc_status", "text": text, "ok": ok}))
                self.rpc.start()
            except Exception as e:  # noqa: BLE001
                self.emit_error(f"Who is talking: {e}")

    def who_spoke(self, t0: float, t1: float) -> str:
        if not self.rpc:
            return ""
        names = self.rpc.speakers_between(t0 - 0.3, t1)
        return " & ".join(names[:2])

    # --------------------------------------------------------------- hear the original voices
    def hears_people(self) -> bool:
        """The original voices of the call are heard: 'Hear people' is on, or the translations are not spoken
        (text only - turning Discord down would leave you with silence)."""
        return self.hear_originals or not self.profile["incoming"].get("speak", True)

    def toggle_hear(self):
        self.set_hear(not self.hear_originals)

    def set_hear(self, on: bool):
        self.hear_originals = bool(on)
        self.emit({"type": "hear", "on": self.hear_originals})
        pl = self.pipelines.get("incoming")
        if pl and not pl.app_capture and not pl._passthrough_ok and self.running:
            self.emit_status("Hear people: works with 'Discord only' listening (Input tab), or with pass-through.")
        elif on:
            self.emit_status("Hear people: ON - you hear their voices and the translations")
        else:
            self.emit_status("Hear people: OFF - you hear only the translations")
        if self.running:
            self._beep(on)

    def _beep(self, on: bool):
        """A tiny sound so you know the hotkey worked (high = on, low = off)."""
        try:
            sr = 48000
            t = np.arange(int(sr * 0.07)) / sr
            tone = 0.12 * np.sin(2 * np.pi * (880 if on else 440) * t) * np.hanning(len(t))
            self.outputs.get(self.profile["incoming"]["output_device"]).play(tone.astype(np.float32), sr, 1.0, "beep")
        except Exception:  # noqa: BLE001
            pass

    def _restore_discord_volume(self):
        """If Dizcord was closed while Discord was turned down, give Discord its volume back."""
        try:
            from .audio.winaudio import AppVolume
            from .config import DATA_DIR
            vol = AppVolume("discord", DATA_DIR / "discord_volume.json")
            if vol.pending_restore() and not self.running:
                vol.restore()
                log.info("Discord volume restored after an abrupt exit")
        except Exception as e:  # noqa: BLE001
            log.debug("restore volume: %s", e)

    def _watch(self):
        """While running: Discord's mixer volume (hear people on/off + ducking) and the microphone check."""
        from .audio import winaudio
        from .config import DATA_DIR
        devices.ensure_com()
        last_factor, last_apply, last_mic = None, 0.0, 0.0
        while not self._watch_stop.wait(0.1):
            pl = self.pipelines.get("incoming")
            now = time.monotonic()
            try:
                if pl and pl.app_capture and self.app_source:
                    if self.app_volume is None:
                        self.app_volume = winaudio.AppVolume(self.profile["input"].get("listen_app") or "discord",
                                                             DATA_DIR / "discord_volume.json")
                    if self.hears_people():
                        duck = float(self.profile["incoming"].get("duck_passthrough", 0.25))
                        factor = duck if duck < 0.99 and self.outputs.any_playing("incoming") else 1.0
                    else:
                        factor = winaudio.HEAR_OFF_FACTOR
                    if factor != last_factor or now - last_apply > 1.0:   # new Discord streams appear any time
                        changed = self.app_volume.apply(factor)
                        if factor != last_factor:
                            self.app_source.set_factor(factor)
                        elif changed:                  # a new Discord stream was just turned down: drop its start
                            self.app_source.blank()
                        last_factor, last_apply = factor, now
                        self._warn_once("muted", "Discord is muted in the Windows volume mixer - the app can't hear "
                                        "it. Unmute Discord there (the app turns it down by itself)."
                                        if self.app_volume.muted_by_user else "")
                if now - last_mic > 10 and "outgoing" in self.pipelines:
                    last_mic = now
                    self._check_discord_mic()
            except Exception as e:  # noqa: BLE001
                log.debug("watch: %s", e)
        if self.app_volume is not None:
            self.app_volume.restore()
            self.app_volume = None

    def _check_discord_mic(self):
        """People must hear only the app voice: Discord's microphone has to be the virtual cable."""
        from .audio import winaudio
        mics = winaudio.capture_devices_of(self.profile["input"].get("listen_app") or "discord")
        if not mics:
            return                              # Discord is not recording right now (not in a call)
        out = self.profile["outgoing"]["output_device"]
        want = cable_recording_side(out)
        real = [m for m in mics if not _VIRTUAL.search(m)]
        if real:
            msg = (f"Discord is using your real microphone ('{real[0]}') - people hear your own voice, not only the "
                   f"translation. In Discord → Settings → Voice & Video → Input Device choose "
                   f"'{want or 'CABLE Output'}'.")
        elif want and want not in mics:
            msg = (f"Discord's microphone is '{mics[0]}', but the translated voice goes to '{out}'. In Discord → "
                   f"Settings → Voice & Video → Input Device choose '{want}'.")
        else:
            msg = ""
        self._warn_once("mic", msg)
        self.emit({"type": "discord_mic", "ok": not msg, "devices": mics})

    def play(self, direction, audio, sr, wait=True):
        """Play a finished clip where this direction's voice goes (kept for tools/tests)."""
        cfg = self.profile[direction]
        clip = self.outputs.get(cfg["output_device"]).play(audio, sr, float(cfg.get("volume", 1.0)), direction)
        if wait:
            clip.done.wait(timeout=len(audio) / sr + 5)

    # --------------------------------------------------------------- control
    def start(self):
        if self.running:
            return
        self.running = True
        self.emit({"type": "state", "running": True})
        threading.Thread(target=self._start_bg, daemon=True).start()

    def _start_bg(self):
        try:
            self.emit_status("Loading engines…")
            for kind in ("stt", "translate", "tts"):
                self.provider(kind)
            if self.profile["translation"]["provider"] == "llm":
                self.provider("llm")
            stt = self.provider("stt")
            need = stt.downloads_needed([])
            if need:
                self.emit_status(f"Downloading {describe_downloads(need)} into {stt.download_dir()} - once, this "
                                 "can take a few minutes…")
            elif stt.local:
                self.emit_status(f"Loading {stt.name} model…")
            stt.warmup()
            threading.Thread(target=self._prepare_tts, name="tts-warmup", daemon=True).start()
            if stt.local and self.profile["incoming"]["source_lang"] == L.AUTO:
                self.emit_status("Tip: on the Live tab, choose the language they speak instead of Auto-detect - "
                                 "speech recognition on this PC gets about twice as fast.")
            started = []
            self.emit({"type": "hear", "on": self.hear_originals})
            for d in ("incoming", "outgoing"):
                if not self.profile[d].get("enabled", True):
                    continue
                pl = Pipeline(self, d)
                try:
                    pl.start()
                    self.pipelines[d] = pl
                    started.append(d)
                except Exception as e:
                    pl.stop()
                    self.emit_error(f"Could not start {d} audio: {e}")
            # open outputs now so the first sentence isn't delayed
            for name in {self.profile["incoming"]["output_device"], self.profile["outgoing"]["output_device"]}:
                try:
                    self.outputs.get(name)
                except Exception as e:
                    self.emit_error(str(e))
            self._check_outgoing_device()
            self._install_hotkeys()
            self._watch_stop.clear()
            self._warned.clear()
            threading.Thread(target=self._watch, name="engine-watch", daemon=True).start()
            if not self.running:   # stopped while we were loading
                self._teardown()
                return
            if started:
                self.emit_status("Running: " + " + ".join(started))
            else:
                self.emit_error("Nothing started - check the Input tab.")
                self.stop()
        except ProviderError as e:
            self.emit_error(str(e))
            self.stop()
        except Exception as e:
            log.exception("start failed")
            self.emit_error(f"Start failed: {e}")
            self.stop()

    def _prepare_tts(self):
        """Download the voices of the languages spoken (once), then load the voice engine."""
        tts = self.provider("tts")
        langs = [self.profile[d]["target_lang"] for d in ("incoming", "outgoing")
                 if self.profile[d].get("enabled", True) and self.profile[d].get("speak", True)]
        try:
            need = tts.downloads_needed(langs)
            if need:
                self.emit_status(f"Downloading {describe_downloads(need)} into {tts.download_dir()} - once…")
                tts.download(langs)
                self.emit_status(f"{tts.name}: download finished.")
            tts.warmup()
        except Exception as e:  # noqa: BLE001
            self.emit_error(f"{tts.name}: {e}")

    def _check_outgoing_device(self):
        if not self.profile["outgoing"].get("enabled", True):
            return
        out = self.profile["outgoing"]["output_device"] or devices.default_name("output")
        if not _VIRTUAL.search(out or ""):
            self.emit_error(f"Your translated voice plays on '{out}', which Discord can't use as a microphone. "
                            "Output tab → 'Send to': choose the virtual cable (CABLE Input).")

    def stop(self):
        self.running = False
        self._teardown()
        self.emit({"type": "state", "running": False})
        self.emit_status("Stopped")

    def _teardown(self):
        self._remove_hotkeys()
        self._watch_stop.set()
        for pl in list(self.pipelines.values()):
            try:
                pl.stop()
            except Exception:
                pass
        self.pipelines.clear()
        self.app_source = None
        for sp in self.speakers.values():
            sp.cancel()
        if self.app_volume is not None:          # the watch thread restores it too; this covers a dead thread
            try:
                self.app_volume.restore()
            except Exception:  # noqa: BLE001
                pass
        self.outputs.close_all()

    def shutdown(self):
        self.stop()
        if self.rpc:
            self.rpc.stop()
            self.rpc = None
        for p in self._providers.values():
            try:
                p.close()
            except Exception:
                pass

    def apply_profile(self, profile: dict):
        """Live-update settings that don't need a restart (languages, voices, volumes, VAD...)."""
        hear = bool(profile.get("incoming", {}).get("hear_originals", False))
        if hear != bool(self.profile.get("incoming", {}).get("hear_originals", False)):
            self.hear_originals = hear          # the "when Dizcord starts" box was just changed
            self.emit({"type": "hear", "on": hear})
        if self.profile["incoming"].get("speak", True) and not profile["incoming"].get("speak", True) \
                and "incoming" in self.speakers:
            self.speakers["incoming"].cancel()  # text only from now on: stop what is being said
        self.profile = profile
        for d, pl in self.pipelines.items():
            if pl.segmenter:
                inp = profile["input"]
                pl.segmenter.update_config(inp["listen_vad"] if d == "incoming" else inp["mic_vad"])
                if d == "outgoing":
                    pl.segmenter.mode = inp["mic_mode"]
        self._update_rpc()

    # --------------------------------------------------------------- manual input
    def say(self, text: str):
        """Typed message -> translate -> speak into Discord."""
        def run():
            pl = self.pipelines.get("outgoing") or Pipeline(self, "outgoing")
            try:
                pl.process_text(text, typed=True)
            except ProviderError as e:
                self.emit_error(str(e))
            except Exception as e:
                log.exception("say failed")
                self.emit_error(f"Say: {e}")
        threading.Thread(target=run, daemon=True).start()

    def set_ptt(self, down: bool):
        pl = self.pipelines.get("outgoing")
        if pl and pl.segmenter:
            pl.segmenter.set_ptt(down)
            self.emit({"type": "ptt", "down": pl.segmenter.ptt_down})

    def stop_speaking(self):
        for sp in self.speakers.values():
            sp.cancel()
        for d in self.outputs.all():
            d.stop_clips()

    # --------------------------------------------------------------- hotkeys
    def _install_hotkeys(self):
        try:
            import keyboard
        except ImportError:
            self.emit_status("Global hotkeys unavailable (pip install keyboard) - use the on-screen buttons.")
            return
        hear = (self.profile["input"].get("hear_key") or "").strip()
        if hear:
            try:
                self._hotkey_hooks.append(("hotkey", keyboard.add_hotkey(
                    hear, lambda: threading.Thread(target=self.toggle_hear, daemon=True).start())))
            except Exception as e:
                self.emit_error(f"Could not register hotkey '{hear}': {e}")
        key = (self.profile["input"].get("ptt_key") or "").strip()
        if self.profile["input"]["mic_mode"] not in ("ptt", "toggle") or not key:
            return
        try:
            def on_down(_e):
                if not self._ptt_down:
                    self._ptt_down = True
                    self.set_ptt(True)

            def on_up(_e):
                if self._ptt_down:
                    self._ptt_down = False
                    if self.profile["input"]["mic_mode"] == "ptt":
                        self.set_ptt(False)
            self._hotkey_hooks += [("hook", keyboard.on_press_key(key, on_down)),
                                   ("hook", keyboard.on_release_key(key, on_up))]
        except Exception as e:
            self.emit_error(f"Could not register hotkey '{key}': {e}")

    def _remove_hotkeys(self):
        if not self._hotkey_hooks:
            return
        try:
            import keyboard
            for kind, h in self._hotkey_hooks:
                try:
                    keyboard.remove_hotkey(h) if kind == "hotkey" else keyboard.unhook(h)
                except Exception:  # noqa: BLE001
                    pass
        except Exception:
            pass
        self._hotkey_hooks = []
