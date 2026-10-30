"""Speed and pitch for any voice engine, applied to the synthesised audio (Voice tab: per direction).

speed  0.5 .. 2.0   (1 = unchanged) - changes the tempo, keeps the pitch (WSOLA time stretching, made for speech)
pitch  -12 .. +12   semitones       - changes the pitch, keeps the tempo (resampling + time stretching)
"""
from __future__ import annotations

import numpy as np


def wsola(x: np.ndarray, rate: float, sr: int) -> np.ndarray:
    """Time-stretch mono float audio: rate > 1 = faster/shorter. Waveform-similarity overlap-add."""
    if abs(rate - 1.0) < 1e-3 or len(x) < sr // 20:
        return x
    frame = max(256, int(sr * 0.030)) & ~1           # 30 ms windows
    hop = frame // 2                                  # synthesis hop (50 % overlap)
    tol = frame // 4                                  # how far the next window may move to match the waveform
    win = np.hanning(frame).astype(np.float32)
    pad = np.concatenate([np.zeros(tol, np.float32), x.astype(np.float32), np.zeros(frame + tol, np.float32)])
    n_out = int(len(x) / rate)
    out = np.zeros(n_out + frame, np.float32)
    norm = np.zeros(n_out + frame, np.float32)
    prev = tol                                        # where the last copied window started (in pad)
    pos_out = 0
    k = 0
    while pos_out < n_out:
        nominal = tol + int(k * hop * rate)
        if nominal + frame + tol >= len(pad):
            break
        if k == 0:
            best = nominal
        else:
            target = pad[prev + hop: prev + hop + frame]   # what naturally follows the last window
            lo, hi = nominal - tol, nominal + tol
            seg = np.lib.stride_tricks.sliding_window_view(pad[lo: hi + frame], frame)
            best = lo + int(np.argmax(seg @ target))
        out[pos_out: pos_out + frame] += pad[best: best + frame] * win
        norm[pos_out: pos_out + frame] += win
        prev = best
        pos_out += hop
        k += 1
    norm[norm < 1e-3] = 1.0
    return (out / norm)[:n_out]


def apply(audio: np.ndarray, sr: int, speed: float = 1.0, pitch: float = 0.0) -> np.ndarray:
    """`audio` with the speed and pitch changed (mono or stereo float32). Unchanged when both are neutral."""
    speed = float(speed or 1.0)
    pitch = float(pitch or 0.0)
    if abs(speed - 1.0) < 1e-3 and abs(pitch) < 0.05:
        return audio
    x = np.asarray(audio, dtype=np.float32)
    if x.ndim > 1:                                    # voices are mono; mix down anything else
        x = x.mean(axis=1)
    factor = 2.0 ** (pitch / 12.0)                    # pitch ratio
    if abs(factor - 1.0) > 1e-3:
        from scipy.signal import resample_poly
        up, down = 1000, int(round(1000 * factor))    # shorter by `factor` = higher by `factor` at the same rate
        x = resample_poly(x, up, down).astype(np.float32)
    y = wsola(x, speed / factor, sr)                  # back to the original length, then the chosen speed
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    return y / peak * 0.99 if peak > 1.0 else y
