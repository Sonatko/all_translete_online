"""Output mixer: one always-open stream per output device.

Several clips (and a live pass-through stream) can play at once; they are
mixed in the audio callback. Opening the stream once avoids clicks and the
~100 ms cost of opening a device per sentence.
"""
from __future__ import annotations

import logging
import threading
import time

import numpy as np
import sounddevice as sd

from . import devices
from .utils import StreamResampler, resample

log = logging.getLogger("dizcord.player")


class _Clip:
    __slots__ = ("data", "pos", "volume", "tag", "done", "growing", "kind")

    def __init__(self, data, volume, tag, growing=False, kind=""):
        self.data, self.pos, self.volume, self.tag = data, 0, volume, tag
        self.done = threading.Event()
        self.growing = growing        # streamed: more audio is still coming (plays silence if it runs dry)
        self.kind = kind              # what is speaking ("voice" / "chat"), for the speech queue


class OutputDevice:
    def __init__(self, name: str):
        self.name = name
        self.lock = threading.Lock()
        self.clips: list[_Clip] = []
        self.live = np.zeros(0, dtype=np.float32)   # pass-through ring
        self.live_volume = 1.0
        self.duck = 1.0                              # live volume multiplier while clips play
        self.stream = None
        self.samplerate = 48000
        self.channels = 2
        self._live_resamplers: dict[int, StreamResampler] = {}
        self.tag_last: dict[str, float] = {}         # tag -> last time a clip with that tag played

    def open(self):
        devices.ensure_com()
        idx = devices.find_device(self.name, "output")
        if idx is None:
            raise RuntimeError(f"Output device not found: '{self.name or 'default'}'")
        info = devices.device_info(idx)
        self.samplerate = int(info["default_samplerate"])
        self.channels = min(2, int(info["max_output_channels"])) or 1
        last = None
        for extra in (devices.wasapi_settings(), None):
            try:
                self.stream = sd.OutputStream(device=idx, samplerate=self.samplerate, channels=self.channels,
                                              dtype="float32", blocksize=int(self.samplerate * 0.02),
                                              callback=self._callback, extra_settings=extra)
                self.stream.start()
                log.info("Opened output '%s' @ %d Hz", info["name"], self.samplerate)
                return
            except Exception as e:
                last = e
        raise RuntimeError(f"Could not open output '{info['name']}': {last}")

    def close(self):
        with self.lock:
            for c in self.clips:
                c.done.set()
            self.clips.clear()
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    # ------------------------------------------------------------------ API
    def play(self, audio: np.ndarray, sr: int, volume: float = 1.0, tag: str = "") -> _Clip:
        data = resample(audio.astype(np.float32), sr, self.samplerate)
        clip = _Clip(data, volume, tag)
        with self.lock:
            self.clips.append(clip)
        return clip

    def play_stream(self, volume: float = 1.0, tag: str = "", kind: str = "") -> _Clip:
        """A clip that starts empty and grows with append() (audio already at self.samplerate) until finish()."""
        clip = _Clip(np.zeros(0, dtype=np.float32), volume, tag, growing=True, kind=kind)
        with self.lock:
            self.clips.append(clip)
        return clip

    def append(self, clip: _Clip, data: np.ndarray):
        with self.lock:
            if clip.growing:
                clip.data = np.concatenate([clip.data[clip.pos:], data.astype(np.float32, copy=False)])
                clip.pos = 0

    def finish(self, clip: _Clip):
        with self.lock:
            clip.growing = False
            if clip not in self.clips:
                clip.done.set()

    def push_live(self, chunk: np.ndarray, sr: int, volume: float = 1.0):
        rs = self._live_resamplers.get(sr)
        if rs is None:
            rs = self._live_resamplers[sr] = StreamResampler(sr, self.samplerate)
        data = rs.process(chunk)
        with self.lock:
            self.live_volume = volume
            self.live = np.concatenate([self.live, data])
            maxlen = int(self.samplerate * 0.25)  # never let pass-through lag behind > 250 ms
            if len(self.live) > maxlen:
                self.live = self.live[-maxlen:]

    def is_playing(self, tag: str | None = None, tail: float = 0.35) -> bool:
        """True while a clip (optionally with this tag) plays, plus a short tail for device latency."""
        now = time.monotonic()
        with self.lock:
            if any(tag is None or c.tag == tag for c in self.clips):
                return True
            if tag is None:
                return any(now - t < tail for t in self.tag_last.values())
            return now - self.tag_last.get(tag, 0.0) < tail

    def fade_out(self, clip: _Clip, ms: int = 40):
        """Stop one clip quickly with a short fade (no click); its done event fires when the fade ends."""
        with self.lock:
            clip.growing = False
            if clip not in self.clips:
                clip.done.set()
                return
            n = int(self.samplerate * ms / 1000)
            tail = clip.data[clip.pos:clip.pos + n].copy()
            tail *= np.linspace(1.0, 0.0, len(tail), dtype=np.float32)
            clip.data = np.concatenate([clip.data[:clip.pos], tail])

    def stop_clips(self, tag: str | None = None):
        with self.lock:
            keep = []
            for c in self.clips:
                if tag is None or c.tag == tag:
                    c.done.set()
                else:
                    keep.append(c)
            self.clips = keep

    # ------------------------------------------------------------- callback
    def _callback(self, outdata, frames, t, status):
        mix = np.zeros(frames, dtype=np.float32)
        with self.lock:
            has_clips = bool(self.clips)
            if len(self.live):
                n = min(frames, len(self.live))
                mix[:n] += self.live[:n] * self.live_volume * (self.duck if has_clips else 1.0)
                self.live = self.live[n:]
            finished = []
            for c in self.clips:
                n = min(frames, len(c.data) - c.pos)
                if n > 0:
                    mix[:n] += c.data[c.pos:c.pos + n] * c.volume
                    c.pos += n
                if c.pos >= len(c.data) and not c.growing:
                    finished.append(c)
            for c in finished:
                self.clips.remove(c)
                c.done.set()
            if has_clips:
                now = time.monotonic()
                for c in self.clips + finished:
                    self.tag_last[c.tag] = now
        np.clip(mix, -1.0, 1.0, out=mix)
        outdata[:] = mix[:, None] if self.channels > 1 else mix.reshape(-1, 1)


class OutputManager:
    """Shares one OutputDevice per physical device between pipelines."""

    def __init__(self):
        self._devs: dict[str, OutputDevice] = {}
        self._lock = threading.Lock()
        self._resolved: dict[str, str] = {}

    def resolve(self, name: str) -> str:
        """'' / partial name -> the real device name (lower-case), cached."""
        key = (name or "").strip().lower()
        if key not in self._resolved:
            idx = devices.find_device(name, "output")
            self._resolved[key] = devices.device_info(idx)["name"].lower() if idx is not None else key
        return self._resolved[key]

    def get(self, name: str) -> OutputDevice:
        key = self.resolve(name)
        with self._lock:
            dev = self._devs.get(key)
            if dev is None:
                dev = OutputDevice(name)
                dev.open()
                self._devs[key] = dev
            return dev

    def existing(self, name: str) -> OutputDevice | None:
        return self._devs.get(self.resolve(name))

    def any_playing(self, tag: str) -> bool:
        with self._lock:
            devs = list(self._devs.values())
        return any(d.is_playing(tag) for d in devs)

    def close_all(self):
        with self._lock:
            devs = list(self._devs.values())
            self._devs.clear()
        for d in devs:
            d.close()
        self._resolved.clear()

    def all(self) -> list[OutputDevice]:
        with self._lock:
            return list(self._devs.values())
