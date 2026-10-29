"""Turns a continuous audio stream into utterances.

Modes:
  vad    - energy based voice activity detection with an adaptive noise floor
  ptt    - record while the push-to-talk key is held
  toggle - press once to start recording, again to stop
"""
from __future__ import annotations

import collections
import logging
import threading
import time

import numpy as np

from .utils import db_to_gain, resample, rms_db

FRAME_S = 0.03


class Segmenter:
    def __init__(self, samplerate: int, on_utterance, on_level=None, mode: str = "vad", vad_cfg: dict | None = None,
                 gain_db: float = 0.0, target_sr: int = 16000):
        self.sr = int(samplerate)
        self.on_utterance = on_utterance      # fn(np.ndarray float32 @ target_sr, duration_s)
        self.on_level = on_level              # fn(db, is_speech)
        self.mode = mode
        self.target_sr = target_sr
        self.gain = db_to_gain(gain_db)
        self.frame = max(1, int(self.sr * FRAME_S))
        self._buf = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()
        self.muted = False                    # set True to drop audio (echo guard)
        self.update_config(vad_cfg or {})
        self._reset()
        self.noise_floor = -60.0
        self._floor_init = True
        self.ptt_down = False
        self._last_level_emit = 0.0

    def update_config(self, cfg: dict):
        self.auto = bool(cfg.get("auto", True))
        self.threshold_db = float(cfg.get("threshold_db", -45.0))
        self.silence_frames = max(1, int(cfg.get("silence_ms", 700) / 1000 / FRAME_S))
        self.min_speech_frames = max(1, int(cfg.get("min_speech_ms", 300) / 1000 / FRAME_S))
        self.max_frames = max(10, int(float(cfg.get("max_utterance_s", 12)) / FRAME_S))
        self.preroll = collections.deque(maxlen=max(1, int(cfg.get("pre_roll_ms", 300) / 1000 / FRAME_S)))

    def _reset(self):
        self.active = False
        self.frames: list[np.ndarray] = []
        self.speech_frames = 0
        self.silence_run = 0

    @property
    def effective_threshold(self) -> float:
        if self.auto:
            return max(self.noise_floor + 12.0, -58.0)
        return self.threshold_db

    def set_ptt(self, down: bool):
        with self._lock:
            if self.mode == "toggle":
                if down:
                    self.ptt_down = not self.ptt_down
                    if not self.ptt_down:
                        self._flush()
                return
            if self.ptt_down and not down:
                self.ptt_down = False
                self._flush()
            else:
                self.ptt_down = down

    def feed(self, chunk: np.ndarray):
        if self.gain != 1.0:
            chunk = chunk * self.gain
        with self._lock:
            self._buf = np.concatenate([self._buf, chunk]) if len(self._buf) else chunk
            while len(self._buf) >= self.frame:
                f, self._buf = self._buf[:self.frame], self._buf[self.frame:]
                self._process(f)

    def _emit_level(self, db, speech):
        now = time.monotonic()
        if self.on_level and now - self._last_level_emit > 0.05:
            self._last_level_emit = now
            self.on_level(db, speech)

    def _process(self, f: np.ndarray):
        db = rms_db(f)
        if self.muted:
            if self.active and self.mode == "vad":
                self._reset()   # discard: it probably contains our own translated voice
            self._emit_level(db, False)
            return

        if self.mode in ("ptt", "toggle"):
            if self.ptt_down:
                if not self.active:
                    self.active = True
                    self.frames = list(self.preroll)
                self.frames.append(f)
                self.speech_frames += 1
                if len(self.frames) >= self.max_frames * 2:
                    self._flush(keep_active=True)
            else:
                self.preroll.append(f)
            self._emit_level(db, self.ptt_down)
            return

        # ---- VAD
        is_speech = db > self.effective_threshold
        # Noise floor follows quiet levels quickly and loud levels very slowly (~30 s).
        if self._floor_init:
            self.noise_floor = max(db, -100.0)
            self._floor_init = False
        elif db < self.noise_floor:
            self.noise_floor = 0.7 * self.noise_floor + 0.3 * db
        else:
            self.noise_floor = 0.999 * self.noise_floor + 0.001 * db
        self._emit_level(db, is_speech)

        if not self.active:
            self.preroll.append(f)
            if is_speech:
                self.active = True
                self.frames = list(self.preroll)
                self.speech_frames = 1
                self.silence_run = 0
            return

        self.frames.append(f)
        if is_speech:
            self.speech_frames += 1
            self.silence_run = 0
        else:
            self.silence_run += 1
        if self.silence_run >= self.silence_frames:
            self._flush()
        elif len(self.frames) >= self.max_frames:
            self._flush(keep_active=True)

    def _flush(self, keep_active: bool = False):
        frames, speech, trailing = self.frames, self.speech_frames, self.silence_run
        self._reset()
        self.preroll.clear()
        if keep_active and self.mode == "vad":
            self.active = True       # long monologue: cut here and keep listening
            self.speech_frames = 1
        if not frames or speech < self.min_speech_frames:
            return
        # drop most of the trailing silence (VAD hang-over), keep ~150 ms
        drop = max(0, trailing - 5)
        if drop and len(frames) - drop > 3:
            frames = frames[:-drop]
        audio = np.concatenate(frames)
        duration = len(audio) / self.sr
        audio16 = resample(audio, self.sr, self.target_sr)
        peak = float(np.max(np.abs(audio16))) if len(audio16) else 0.0
        if 0 < peak < 0.3:  # normalise quiet speech for better recognition
            audio16 = audio16 * min(0.6 / peak, 10.0)
        try:
            self.on_utterance(audio16.astype(np.float32), duration)
        except Exception:
            logging.getLogger("dizcord.vad").exception("on_utterance failed")
