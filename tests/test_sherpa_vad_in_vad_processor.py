import os
import sys
import time
import numpy as np
import soundfile as sf

# Ensure path resolution
sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

import sherpa_onnx
import silero_vad

class SherpaOnnxVADBackend:
    """Zero-copy C++ ONNX backend for VADProcessor without PyTorch."""

    def __init__(self, sample_rate=16000, threshold=0.5, silence_duration=0.25):
        onnx_path = os.path.join(os.path.dirname(silero_vad.__file__), "data", "silero_vad.onnx")
        config = sherpa_onnx.VadModelConfig(
            silero_vad=sherpa_onnx.SileroVadModelConfig(
                model=onnx_path,
                threshold=threshold,
                min_silence_duration=silence_duration,
                min_speech_duration=0.20,
                window_size=512,
            ),
            sample_rate=sample_rate,
            num_threads=1,
            provider="cpu",
        )
        self.detector = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        self.window_size = 512

    def get_confidence(self, chunk: np.ndarray) -> float:
        if len(chunk) < self.window_size:
            chunk = np.pad(chunk, (0, self.window_size - len(chunk)))
        else:
            chunk = chunk[: self.window_size]
        self.detector.accept_waveform(chunk)
        return 0.95 if self.detector.is_speech_detected() else 0.05


def test_sherpa_backend_on_speech():
    audio_path = os.path.abspath("scratch/test_audio/en.wav")
    assert os.path.exists(audio_path), f"Audio file not found: {audio_path}"
    data, sr = sf.read(audio_path)
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        target_len = int(len(data) * 16000 / sr)
        audio = np.interp(
            np.linspace(0, len(data), target_len, endpoint=False),
            np.arange(len(data)),
            data
        ).astype(np.float32)
    else:
        audio = data.astype(np.float32)

    backend = SherpaOnnxVADBackend()
    chunk_size = 512
    latencies = []
    speech_chunks = 0
    silence_chunks = 0

    for i in range(0, len(audio) - chunk_size, chunk_size):
        chunk = audio[i : i + chunk_size]
        t0 = time.perf_counter()
        conf = backend.get_confidence(chunk)
        latencies.append((time.perf_counter() - t0) * 1000)

        if conf > 0.5:
            speech_chunks += 1
        else:
            silence_chunks += 1

    avg_lat = sum(latencies) / len(latencies)
    print(f"C++ Sherpa VAD Backend Avg Latency: {avg_lat:.4f} ms per 32ms chunk")
    print(f"Speech Chunks: {speech_chunks}, Silence Chunks: {silence_chunks}")

    assert speech_chunks > 10, "Expected speech chunks to be detected!"
    assert silence_chunks > 5, "Expected silence chunks to be detected!"
    assert avg_lat < 0.3, f"Expected sub-millisecond latency, got {avg_lat:.2f} ms"
    print("\n[SUCCESS] SHERPA ONNX VAD BACKEND READY FOR VADPROCESSOR!")


if __name__ == "__main__":
    test_sherpa_backend_on_speech()
