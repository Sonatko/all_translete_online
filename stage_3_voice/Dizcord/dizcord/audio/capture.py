"""Audio capture: microphones/input devices (sounddevice) and WASAPI loopback of
an output device (PyAudioWPatch) - the latter is how we "hear" Discord."""
from __future__ import annotations

import logging

import numpy as np
import sounddevice as sd

from . import devices
from .utils import to_mono

log = logging.getLogger("dizcord.capture")


class Source:
    """Calls on_audio(mono_float32_chunk) from an audio thread. .samplerate is set after start()."""

    samplerate = 48000

    def __init__(self, on_audio):
        self.on_audio = on_audio

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class InputDeviceSource(Source):
    def __init__(self, device_name: str, on_audio):
        super().__init__(on_audio)
        self.device_name = device_name
        self.stream = None

    def start(self):
        devices.ensure_com()
        idx = devices.find_device(self.device_name, "input")
        if idx is None:
            raise RuntimeError(f"Input device not found: '{self.device_name or 'default'}'")
        info = devices.device_info(idx)
        self.samplerate = int(info["default_samplerate"])
        channels = min(2, int(info["max_input_channels"])) or 1

        def cb(indata, frames, t, status):
            try:
                self.on_audio(to_mono(indata.copy()))
            except Exception:
                log.exception("capture callback failed")

        last = None
        for extra in (devices.wasapi_settings(), None):
            try:
                self.stream = sd.InputStream(device=idx, samplerate=self.samplerate, channels=channels,
                                             dtype="float32", blocksize=int(self.samplerate * 0.03),
                                             callback=cb, extra_settings=extra)
                self.stream.start()
                log.info("Capturing input '%s' @ %d Hz", info["name"], self.samplerate)
                return
            except Exception as e:
                last = e
        raise RuntimeError(f"Could not open input '{info['name']}': {last}")

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None


class LoopbackSource(Source):
    """Records what is being *played* on an output device (e.g. your headphones where Discord plays)."""

    def __init__(self, output_name: str, on_audio):
        super().__init__(on_audio)
        self.output_name = output_name
        self.pa = None
        self.stream = None

    @staticmethod
    def available() -> bool:
        try:
            import pyaudiowpatch  # noqa: F401
            return True
        except ImportError:
            return False

    def _find(self, pa):
        import pyaudiowpatch as pyaudio
        want = (self.output_name or devices.default_name("output")).lower()
        loops = list(pa.get_loopback_device_info_generator())
        if not loops:
            raise RuntimeError("No WASAPI loopback devices found.")
        for d in loops:
            if d["name"].lower().replace(" [loopback]", "") == want:
                return d
        for d in loops:
            if d["name"].lower().startswith(want) or want in d["name"].lower():
                return d
        try:  # default speakers
            wasapi = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
            spk = pa.get_device_info_by_index(wasapi["defaultOutputDevice"])
            for d in loops:
                if spk["name"] in d["name"]:
                    return d
        except Exception:
            pass
        return loops[0]

    def start(self):
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            raise RuntimeError("Loopback capture needs PyAudioWPatch (pip install PyAudioWPatch).")
        devices.ensure_com()
        self.pa = pyaudio.PyAudio()
        dev = self._find(self.pa)
        self.samplerate = int(dev["defaultSampleRate"])
        channels = max(1, int(dev["maxInputChannels"]))

        def cb(in_data, frame_count, time_info, status):
            try:
                x = np.frombuffer(in_data, dtype=np.float32)
                if channels > 1:
                    x = x.reshape(-1, channels).mean(axis=1)
                self.on_audio(x.astype(np.float32))
            except Exception:
                log.exception("loopback callback failed")
            return (None, pyaudio.paContinue)

        self.stream = self.pa.open(format=pyaudio.paFloat32, channels=channels, rate=self.samplerate,
                                   input=True, input_device_index=dev["index"],
                                   frames_per_buffer=int(self.samplerate * 0.03), stream_callback=cb)
        self.stream.start_stream()
        log.info("Capturing loopback of '%s' @ %d Hz", dev["name"], self.samplerate)

    def stop(self):
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
        except Exception:
            pass
        self.stream = None
        try:
            if self.pa is not None:
                self.pa.terminate()
        except Exception:
            pass
        self.pa = None
