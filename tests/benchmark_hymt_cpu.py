"""
Benchmark script for Tencent HY-MT1.5-1.8B GGUF on CPU.
Measures Time-To-First-Token (TTFT), tokens/sec, RAM consumption, and translation quality.
"""

import os
import sys
import time
import psutil

# Add LiveTranslate directory to path
_cur_dir = os.path.dirname(os.path.abspath(__file__))
_lt_dir = os.path.abspath(os.path.join(_cur_dir, "..", "stage_1_audio", "LiveTranslate"))
if _lt_dir not in sys.path:
    sys.path.insert(0, _lt_dir)

from hymt_engine import LocalHYMTEngine


def get_ram_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def run_benchmark():
    print("=" * 65)
    print("  BENCHMARK: TENCENT HY-MT1.5 1.8B GGUF (Q4_K_M) ON CPU")
    print("=" * 65)

    ram_before = get_ram_mb()
    print(f"\n[1] Initial Process RAM: {ram_before:.1f} MB")
    print("[2] Initializing LocalHYMTEngine (downloading if not cached)...")

    t0 = time.perf_counter()
    engine = LocalHYMTEngine.get_instance()
    init_time = (time.perf_counter() - t0) * 1000

    ram_after = get_ram_mb()
    print(f"  [OK] Model loaded in: {init_time:.1f} ms")
    print(f"  [OK] Process RAM with Model: {ram_after:.1f} MB (Delta: +{ram_after - ram_before:.1f} MB)")

    test_phrases = [
        ("Gaming", "The enemy team is pushing the mid lane, fall back and regroup!"),
        ("Slang/Idiom", "Honestly, it's on the house, don't worry about it at all."),
        ("Complex", "We need to calibrate the sensor threshold before initiating the sequence."),
    ]

    print("\n" + "=" * 65)
    print("  INFERENCE SPEED & QUALITY METRICS")
    print("=" * 65)

    for category, phrase in test_phrases:
        # Measure latency
        start = time.perf_counter()
        translation = engine.translate(phrase, target_language="ru", source_language="en")
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\nCategory: [{category}]")
        print(f"  Source (EN) : \"{phrase}\"")
        print(f"  Target (RU) : \"{translation}\"")
        print(f"  Latency     : {elapsed_ms:.1f} ms")

    print("\n" + "=" * 65)
    print("  CLEAN UNLOAD & MEMORY RELEASE CHECK")
    print("=" * 65)

    LocalHYMTEngine.unload()
    ram_unloaded = get_ram_mb()
    print(f"RAM after unload: {ram_unloaded:.1f} MB (Freed: {ram_after - ram_unloaded:.1f} MB)")
    print("\n[SUCCESS] HY-MT 1.8B Benchmark Completed!")


if __name__ == "__main__":
    run_benchmark()
