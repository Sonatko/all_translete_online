"""Small audio helpers: resampling, WAV encode/decode, levels."""
from __future__ import annotations

import io
import math
import wave

import numpy as np

try:
    from scipy.signal import resample_poly as _resample_poly
except Exception:  # scipy is optional
    _resample_poly = None


def to_mono(x: np.ndarray) -> np.ndarray:
    if x.ndim == 2:
        x = x.mean(axis=1)
    return np.ascontiguousarray(x, dtype=np.float32)


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """High-quality one-shot resample of a whole clip."""
    if sr_in == sr_out or len(x) == 0:
        return x.astype(np.float32, copy=False)
    if _resample_poly is not None:
        g = math.gcd(int(sr_in), int(sr_out))
        return _resample_poly(x, int(sr_out) // g, int(sr_in) // g).astype(np.float32)
    n_out = int(round(len(x) * sr_out / sr_in))
    t_out = np.linspace(0, len(x) - 1, n_out)
    return np.interp(t_out, np.arange(len(x)), x).astype(np.float32)


class StreamResampler:
    """Linear-interpolation resampler that keeps state between chunks (for live pass-through)."""

    def __init__(self, sr_in: int, sr_out: int):
        self.ratio = sr_in / sr_out
        self.pos = 0.0
        self.prev = np.zeros(1, dtype=np.float32)
        self.same = sr_in == sr_out

    def process(self, x: np.ndarray) -> np.ndarray:
        if self.same or len(x) == 0:
            return x
        buf = np.concatenate([self.prev, x])
        n = int((len(buf) - 1 - self.pos) / self.ratio)
        if n <= 0:
            self.prev = buf
            return np.zeros(0, dtype=np.float32)
        idx = self.pos + np.arange(n) * self.ratio
        out = np.interp(idx, np.arange(len(buf)), buf).astype(np.float32)
        consumed = self.pos + n * self.ratio
        keep_from = int(consumed)
        self.pos = consumed - keep_from
        self.prev = buf[keep_from:]
        return out


class BlockResampler:
    """High-quality resampling of audio that arrives in pieces (streamed voices): the same polyphase filter as
    resample(), run on blocks with some context on both sides and cut on exact sample boundaries, so the joined
    output equals resampling the whole clip at once."""

    CONTEXT = 64       # input samples of context each side (the filter is ~10 input samples long)

    def __init__(self, sr_in: int, sr_out: int):
        g = math.gcd(int(sr_in), int(sr_out))
        self.up, self.down = int(sr_out) // g, int(sr_in) // g
        self.same = self.up == self.down
        self.pad = -(-self.CONTEXT // self.down) * self.down        # context, a multiple of `down`
        self.buf = np.zeros(self.pad, dtype=np.float32)            # left context: silence before the start
        self.done = 0                                               # input samples already turned into output

    def _run(self, end: int, right_pad: int) -> np.ndarray:
        """Output for input [done, end) of the stream; buf starts at input index done - pad."""
        seg = self.buf[: self.pad + (end - self.done) + right_pad]
        if right_pad > len(seg) - self.pad - (end - self.done):
            seg = np.concatenate([seg, np.zeros(right_pad, dtype=np.float32)])
        y = resample(seg, self.down, self.up) if _resample_poly is not None else np.interp(
            np.arange(len(seg) * self.up // self.down) * self.down / self.up, np.arange(len(seg)), seg)
        a = self.pad * self.up // self.down
        b = a + (end - self.done) * self.up // self.down
        out = np.asarray(y[a:b], dtype=np.float32)
        drop = end - self.done                                       # keep `pad` samples of left context
        self.buf = self.buf[drop:]
        self.done = end
        return out

    def process(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        if self.same:
            return x
        self.buf = np.concatenate([self.buf, x])
        have = self.done + len(self.buf) - self.pad                  # input samples received so far
        end = ((have - self.pad) // self.down) * self.down           # leave `pad` samples of right context
        if end <= self.done:
            return np.zeros(0, dtype=np.float32)
        return self._run(end, self.pad)

    def flush(self) -> np.ndarray:
        if self.same:
            return np.zeros(0, dtype=np.float32)
        have = self.done + len(self.buf) - self.pad
        end = -(-have // self.down) * self.down                      # round up: the tail is padded with silence
        if end <= self.done:
            return np.zeros(0, dtype=np.float32)
        self.buf = np.concatenate([self.buf, np.zeros(end - have, dtype=np.float32)])
        return self._run(end, self.pad)


def rms_db(x: np.ndarray) -> float:
    if len(x) == 0:
        return -100.0
    r = float(np.sqrt(np.mean(np.square(x, dtype=np.float64))))
    return 20 * math.log10(r) if r > 1e-9 else -100.0


def db_to_gain(db: float) -> float:
    return 10 ** (db / 20.0)


def wav_bytes(x: np.ndarray, sr: int) -> bytes:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def pcm16_to_float(data: bytes) -> np.ndarray:
    return (np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0)


def decode_audio(data: bytes) -> tuple[np.ndarray, int]:
    """Decode WAV/MP3/OGG/FLAC bytes -> (mono float32, sample_rate)."""
    if data[:4] == b"RIFF":
        try:
            with wave.open(io.BytesIO(data), "rb") as w:
                sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
                frames = w.readframes(w.getnframes())
            if sw == 2:
                x = pcm16_to_float(frames)
                if ch > 1:
                    x = x.reshape(-1, ch).mean(axis=1)
                return x.astype(np.float32), sr
        except (wave.Error, EOFError):
            pass  # e.g. float WAV or streaming header -> let soundfile try
    try:
        import soundfile as sf
        x, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=False)
        return to_mono(x), int(sr)
    except Exception as e:
        raise RuntimeError(f"Could not decode audio ({len(data)} bytes): {e}") from e


def trim_silence(x: np.ndarray, sr: int, thresh_db: float = -50.0) -> np.ndarray:
    """Remove leading/trailing near-silence from a TTS clip (cuts latency a bit)."""
    if len(x) == 0:
        return x
    thr = db_to_gain(thresh_db)
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    pad = int(0.03 * sr)
    return x[max(0, idx[0] - pad): min(len(x), idx[-1] + pad)]
