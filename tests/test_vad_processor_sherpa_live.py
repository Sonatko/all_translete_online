import os
import sys
import time
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

from vad_processor import VADProcessor

def test_vad_processor_sherpa():
    vad = VADProcessor(
        sample_rate=16000,
        threshold=0.50,
        min_speech_duration=0.25,
        max_speech_duration=10.0,
    )
    print("VAD initialized. Uses Sherpa-ONNX C++:", vad._use_sherpa_vad)
    assert vad._use_sherpa_vad is True, "Expected VADProcessor to use C++ Sherpa-ONNX backend!"

    audio_path = os.path.abspath("scratch/test_audio/en.wav")
    assert os.path.exists(audio_path), f"Audio missing: {audio_path}"
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

    # Stream 512-sample chunks
    chunk_size = 512
    latencies = []
    completed_segments = []

    for i in range(0, len(audio) - chunk_size, chunk_size):
        chunk = audio[i : i + chunk_size]
        t0 = time.perf_counter()
        seg = vad.process_chunk(chunk)
        latencies.append((time.perf_counter() - t0) * 1000)
        if seg is not None:
            completed_segments.append(seg)

    # Flush remaining
    flushed = vad.flush()
    if flushed is not None:
        completed_segments.append(flushed)

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    print(f"VADProcessor Chunk Latency: Avg={avg_lat:.4f} ms, Max={max_lat:.4f} ms")
    print(f"Completed Segments: {len(completed_segments)}")

    assert len(completed_segments) >= 1, "Expected at least 1 speech segment!"
    assert avg_lat < 0.25, f"Expected sub-0.25ms latency, got {avg_lat:.4f} ms"

    print("\n[SUCCESS] VADPROCESSOR C++ SHERPA-ONNX INTEGRATION VERIFIED 100%!")

if __name__ == "__main__":
    test_vad_processor_sherpa()
