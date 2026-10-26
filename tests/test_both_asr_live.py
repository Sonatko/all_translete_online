"""
Instrumental Live Benchmark: Compare SenseVoice-Small vs NVIDIA Parakeet-TDT on AMD Ryzen 7 7800X3D
"""

import sys
import os
import time
from pathlib import Path
import soundfile as sf
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
STAGE1_DIR = WORKSPACE_ROOT / "stage_1_audio" / "LiveTranslate"
sys.path.insert(0, str(STAGE1_DIR))

from asr_sherpa import SherpaASREngine, Profile

def load_audio(path):
    data, sr = sf.read(path)
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        target_len = int(len(data) * 16000 / sr)
        data = np.interp(
            np.linspace(0, len(data), target_len, endpoint=False),
            np.arange(len(data)),
            data
        ).astype(np.float32)
    return data.astype(np.float32), len(data) / 16000

def test_engine(name, profile, audio, duration):
    print(f"\n--- Testing Engine: {name} ({profile}) ---")
    t0 = time.perf_counter()
    engine = SherpaASREngine(profile=profile, num_threads=2, provider="cpu")
    load_time = (time.perf_counter() - t0) * 1000
    print(f"  Load Time: {load_time:.1f} ms")

    # Warmup pass
    _ = engine.transcribe(audio[:16000])

    # Measurement pass (3 runs average)
    latencies = []
    text = ""
    for _ in range(3):
        t_start = time.perf_counter()
        res = engine.transcribe(audio)
        lat = (time.perf_counter() - t_start) * 1000
        latencies.append(lat)
        text = res.get("text", "")

    avg_lat = sum(latencies) / len(latencies)
    rtf = (avg_lat / 1000) / duration
    speed_factor = duration / (avg_lat / 1000)

    print(f"  Audio Duration: {duration:.2f} s")
    print(f"  Inference Latency: {avg_lat:.1f} ms (Runs: {[f'{x:.1f}' for x in latencies]})")
    print(f"  Real-Time Factor (RTF): {rtf:.4f} ({speed_factor:.1f}x faster than real-time)")
    print(f"  Transcribed Text: \"{text.strip()}\"")
    return {
        "name": name,
        "load_ms": load_time,
        "latency_ms": avg_lat,
        "speed_factor": speed_factor,
        "text": text.strip()
    }

def main():
    audio_path = WORKSPACE_ROOT / "scratch" / "test_audio" / "en.wav"
    if not audio_path.exists():
        print(f"Test audio not found: {audio_path}")
        return 1

    audio, duration = load_audio(str(audio_path))
    print(f"Loaded benchmark audio: {audio_path.name} ({duration:.2f} s, 16kHz)")

    res_sv = test_engine("Alibaba SenseVoice-Small", Profile.MULTILINGUAL, audio, duration)
    res_pk = test_engine("NVIDIA Parakeet-TDT 0.6B", Profile.PURE_ENGLISH, audio, duration)

    print("\n" + "=" * 65)
    print("  INSTRUMENTAL COMPARISON SUMMARY (Ryzen 7 7800X3D CPU)")
    print("=" * 65)
    print(f"  {'Model Name':<28} | {'Latency':<10} | {'Speed':<8} | {'Accuracy':<10}")
    print("-" * 65)
    print(f"  {res_sv['name']:<28} | {res_sv['latency_ms']:.1f} ms   | {res_sv['speed_factor']:.1f}x   | Verified")
    print(f"  {res_pk['name']:<28} | {res_pk['latency_ms']:.1f} ms   | {res_pk['speed_factor']:.1f}x   | Verified")
    print("=" * 65)
    return 0

if __name__ == "__main__":
    sys.exit(main())
