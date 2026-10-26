"""Sherpa-ONNX native C++ Voice Activity Detector (VAD).
Integrates Silero VAD (ONNX) directly inside C++ runtime for zero-copy audio segmentation
and real-time streaming subtitle generation.
"""

import logging
import os
import time
import numpy as np
import sherpa_onnx

log = logging.getLogger("LiveTranslate.SherpaVAD")

SAMPLE_RATE = 16000


def find_silero_vad_model() -> str:
    """Locate silero_vad.onnx in environment or local paths."""
    try:
        import silero_vad
        pkg_path = os.path.join(os.path.dirname(silero_vad.__file__), "data", "silero_vad.onnx")
        if os.path.exists(pkg_path):
            return pkg_path
    except ImportError:
        pass

    candidates = [
        os.path.join(os.path.dirname(__file__), "silero_vad.onnx"),
        os.path.join(os.path.dirname(__file__), "..", "..", "scratch", "silero_vad.onnx"),
        os.path.join(os.path.dirname(__file__), "..", "..", "models", "silero_vad.onnx"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)

    raise FileNotFoundError("silero_vad.onnx not found. Install silero-vad or place in models/.")


class SherpaVADDetector:
    """High-performance C++ VAD processor using sherpa-onnx VoiceActivityDetector."""

    def __init__(
        self,
        model_path: str = None,
        threshold: float = 0.5,
        min_silence_duration: float = 0.25,
        min_speech_duration: float = 0.20,
        max_speech_duration: float = 10.0,
        window_size: int = 512,
        buffer_size_seconds: float = 30.0,
        streaming_step: float = 0.25,
    ):
        self.model_path = model_path or find_silero_vad_model()
        self.threshold = float(threshold)
        self.min_silence_duration = float(min_silence_duration)
        self.min_speech_duration = float(min_speech_duration)
        self.max_speech_duration = float(max_speech_duration)
        self.window_size = int(window_size)
        self.streaming_step = float(streaming_step)

        self._config = sherpa_onnx.VadModelConfig()
        self._config.silero_vad.model = self.model_path
        self._config.silero_vad.threshold = self.threshold
        self._config.silero_vad.min_silence_duration = self.min_silence_duration
        self._config.silero_vad.min_speech_duration = self.min_speech_duration
        self._config.silero_vad.max_speech_duration = self.max_speech_duration
        self._config.silero_vad.window_size = self.window_size
        self._config.sample_rate = SAMPLE_RATE
        self._config.num_threads = 1
        self._config.provider = "cpu"

        self._vad = sherpa_onnx.VoiceActivityDetector(self._config, buffer_size_in_seconds=buffer_size_seconds)

        # Internal audio tracking for streaming partial previews
        self._stream_buffer = np.array([], dtype=np.float32)
        self._speech_started = False
        self._last_stream_time = 0.0

        log.info(
            f"SherpaVAD initialized with {os.path.basename(self.model_path)} | "
            f"SilenceTimeout: {self.min_silence_duration}s | Window: {self.window_size}"
        )

    def process_chunk(self, chunk: np.ndarray):
        """Feed a new audio chunk into the C++ VAD engine.
        
        Yields:
            ("partial", audio_array) -> intermediate live audio while speaking.
            ("final", audio_array)   -> complete phrase audio after silence detected.
        """
        if chunk is None or chunk.size == 0:
            return

        if len(chunk.shape) > 1:
            chunk = chunk.mean(axis=1)
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)

        # Feed window-by-window into C++ VAD
        offset = 0
        while offset + self.window_size <= len(chunk):
            window = chunk[offset : offset + self.window_size]
            self._vad.accept_waveform(window)
            offset += self.window_size

        # Track speech state
        if self._vad.is_speech_detected():
            if not self._speech_started:
                self._speech_started = True
                self._stream_buffer = chunk.copy()
                self._last_stream_time = time.perf_counter()
            else:
                self._stream_buffer = np.append(self._stream_buffer, chunk)

            # Check if streaming interval elapsed for partial display
            now = time.perf_counter()
            if (now - self._last_stream_time) >= self.streaming_step and len(self._stream_buffer) >= (SAMPLE_RATE * 0.4):
                self._last_stream_time = now
                yield ("partial", self._stream_buffer.copy())
        else:
            if self._speech_started:
                # Speech ended, pop complete segments from VAD
                self._speech_started = False
                self._stream_buffer = np.array([], dtype=np.float32)

                while not self._vad.empty():
                    segment = self._vad.front
                    samples = np.array(segment.samples, dtype=np.float32)
                    self._vad.pop()
                    if len(samples) >= int(SAMPLE_RATE * self.min_speech_duration):
                        yield ("final", samples)

    def flush(self):
        """Force flush all remaining segments in VAD buffer."""
        segments = []
        while not self._vad.empty():
            segment = self._vad.front
            samples = np.array(segment.samples, dtype=np.float32)
            self._vad.pop()
            if len(samples) >= int(SAMPLE_RATE * self.min_speech_duration):
                segments.append(samples)
        self._speech_started = False
        self._stream_buffer = np.array([], dtype=np.float32)
        return segments

    def reset(self):
        """Reset VAD internal state."""
        self._vad.reset()
        self._speech_started = False
        self._stream_buffer = np.array([], dtype=np.float32)
