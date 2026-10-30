"""Audio device discovery (Windows WASAPI preferred) and name matching."""
from __future__ import annotations

import os
import threading

import sounddevice as sd

_com = threading.local()


def ensure_com():
    """Initialise COM on the calling thread. Without it, WASAPI streams opened from a
    background thread fail with 'Unanticipated host error' (PaErrorCode -9999)."""
    if os.name != "nt" or getattr(_com, "done", False):
        return
    try:
        import ctypes
        ctypes.windll.ole32.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED
    except Exception:
        pass
    _com.done = True


PREFERRED_HOSTAPIS = ("Windows WASAPI", "Core Audio", "ALSA", "PulseAudio", "MME")


def _hostapi_index() -> int | None:
    apis = sd.query_hostapis()
    for want in PREFERRED_HOSTAPIS:
        for i, a in enumerate(apis):
            if a["name"] == want:
                return i
    return None


def _devices(kind: str):
    api = _hostapi_index()
    out = []
    for i, d in enumerate(sd.query_devices()):
        if api is not None and d["hostapi"] != api:
            continue
        ch = d["max_input_channels"] if kind == "input" else d["max_output_channels"]
        if ch > 0:
            out.append((i, d))
    return out


def input_devices() -> list[str]:
    return [d["name"] for _, d in _devices("input")]


def output_devices() -> list[str]:
    return [d["name"] for _, d in _devices("output")]


def default_name(kind: str) -> str:
    api = _hostapi_index()
    try:
        if api is not None:
            idx = sd.query_hostapis(api)["default_input_device" if kind == "input" else "default_output_device"]
        else:
            idx = sd.default.device[0 if kind == "input" else 1]
        return sd.query_devices(idx)["name"] if idx is not None and idx >= 0 else ""
    except Exception:
        return ""


def find_device(name: str, kind: str) -> int | None:
    """Index of the device whose name matches (exact, then prefix, then substring). '' = default."""
    devs = _devices(kind)
    if not name:
        name = default_name(kind)
        if not name:
            return None
    low = name.lower()
    for i, d in devs:
        if d["name"].lower() == low:
            return i
    for i, d in devs:
        if d["name"].lower().startswith(low):
            return i
    for i, d in devs:
        if low in d["name"].lower():
            return i
    return None


def device_info(idx: int) -> dict:
    return sd.query_devices(idx)


def find_virtual_cable() -> str:
    """Name of a virtual-cable *playback* device to feed Discord's microphone, if installed."""
    for name in output_devices():
        low = name.lower()
        if low.startswith("cable input") or "vb-audio virtual cable" in low and "16ch" not in low:
            return name
    for name in output_devices():
        if "voicemeeter" in name.lower() and "aux" in name.lower():
            return name
    return ""


def wasapi_settings():
    """Let WASAPI convert sample rate / channels for us (shared mode)."""
    api = _hostapi_index()
    if api is not None and sd.query_hostapis(api)["name"] == "Windows WASAPI":
        try:
            return sd.WasapiSettings(auto_convert=True)
        except TypeError:
            return None
    return None
