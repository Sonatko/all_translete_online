import os
import sys
import time
import numpy as np

# Ensure path resolution
sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

import sherpa_onnx
import silero_vad

def test_sherpa_vad_speed_and_segmentation():
    onnx_path = os.path.join(os.path.dirname(silero_vad.__file__), "data", "silero_vad.onnx")
    assert os.path.exists(onnx_path), f"silero_vad.onnx not found at {onnx_path}"

    config = sherpa_onnx.VadModelConfig(
        silero_vad=sherpa_onnx.SileroVadModelConfig(
            model=onnx_path,
            threshold=0.5,
            min_silence_duration=0.25,
            min_speech_duration=0.20,
            window_size=512,
        ),
        sample_rate=16000,
        num_threads=1,
        provider="cpu",
    )
    detector = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)

    import soundfile as sf
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

    # Feed chunks of 512 samples (~32ms)
    chunk_size = 512
    segments = []
    latencies = []

    for i in range(0, len(audio) - chunk_size, chunk_size):
        chunk = audio[i : i + chunk_size]
        t0 = time.perf_counter()
        detector.accept_waveform(chunk)
        latencies.append((time.perf_counter() - t0) * 1000)

        while not detector.empty():
            seg = detector.front
            segments.append(np.array(seg.samples, dtype=np.float32))
            detector.pop()

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    print(f"[TEST 1] C++ VAD Chunk Latency: Avg={avg_lat:.4f} ms, Max={max_lat:.4f} ms")
    print(f"[TEST 2] Detected Speech Segments: {len(segments)}")

    assert len(segments) >= 1, "Expected at least 1 speech segment to be detected!"
    speech_len = len(segments[0]) / sr
    print(f"[TEST 3] Segment Duration: {speech_len:.2f} seconds (Expected ~2.0s)")
    assert 1.5 <= speech_len <= 2.5, f"Unexpected speech duration: {speech_len}s"

    print("\n[SUCCESS] C++ SHERPA-ONNX VAD FULLY VERIFIED!")

if __name__ == "__main__":
    test_sherpa_vad_speed_and_segmentation()
