"""Standalone End-to-End Test for Stage 1 Pipeline.
Simulates a live audio stream (32ms frames), feeds it through SherpaVADDetector (C++ Silero VAD),
and verifies real-time subtitle generation through SherpaASREngine (SenseVoice / Parakeet).
"""

import sys
import os
import time
import soundfile as sf
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))
from asr_sherpa import SherpaASREngine, Profile
from vad_sherpa import SherpaVADDetector

TEST_AUDIO = "scratch/test_audio/noisy_game.wav"
GT_TEXT = "the tribal chieftain called for the boy and presented him with 50 pieces of gold"


def test_pipeline_streaming(profile_name):
    print("\n" + "="*75)
    print(f" STANDALONE STAGE 1 E2E TEST | PROFILE: {profile_name.upper()}")
    print("="*75)

    audio_data, sr = sf.read(TEST_AUDIO)
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    if sr != 16000:
        target_len = int(len(audio_data) * 16000 / sr)
        audio_data = np.interp(np.linspace(0, len(audio_data), target_len, endpoint=False), np.arange(len(audio_data)), audio_data).astype(np.float32)

    total_dur = len(audio_data) / 16000
    print(f"Loaded test audio: {TEST_AUDIO} ({total_dur:.2f}s)")

    # 1. Initialize Engines
    t0 = time.perf_counter()
    vad = SherpaVADDetector(min_silence_duration=0.25, streaming_step=0.25)
    asr = SherpaASREngine(profile=profile_name, num_threads=2)
    print(f"Engines initialized in {time.perf_counter() - t0:.2f}s\n")

    # 2. Simulate streaming in 32ms chunks (512 samples at 16kHz)
    frame_size = 512
    partials_count = 0
    finals = []

    print("--- Simulating Live Audio Stream (512 samples / 32ms frames) ---")
    stream_start = time.perf_counter()

    for i in range(0, len(audio_data), frame_size):
        chunk = audio_data[i : i + frame_size]
        for event_type, audio_seg in vad.process_chunk(chunk):
            if event_type == "partial":
                partials_count += 1
                res = asr.transcribe(audio_seg)
                if res and res["text"]:
                    print(f"  [LIVE PARTIAL #{partials_count}] ({len(audio_seg)/16000:.2f}s): \"{res['text']}\" (ASR: {res['latency_ms']:.1f}ms)")
            elif event_type == "final":
                res = asr.transcribe(audio_seg)
                if res and res["text"]:
                    finals.append(res)
                    print(f"\n  >>> [FINAL SUBTITLE] ({len(audio_seg)/16000:.2f}s): \"{res['text']}\"")
                    print(f"      ASR Latency: {res['latency_ms']:.1f} ms | Language: {res['language_name']}\n")

    # Flush any remaining audio after stream ends
    for audio_seg in vad.flush():
        res = asr.transcribe(audio_seg)
        if res and res["text"]:
            finals.append(res)
            print(f"  >>> [FLUSHED SUBTITLE] ({len(audio_seg)/16000:.2f}s): \"{res['text']}\" (ASR: {res['latency_ms']:.1f}ms)")

    total_stream_time = time.perf_counter() - stream_start
    print(f"\n--- Simulation Complete in {total_stream_time:.2f}s ---")
    print(f"Partials generated: {partials_count}")
    print(f"Final phrases recognized: {len(finals)}")

    assert len(finals) > 0, "No final subtitle recognized!"
    final_text = " ".join([f["text"] for f in finals])
    print(f"Combined Result: \"{final_text}\"")

    asr.unload()
    return finals


if __name__ == "__main__":
    test_pipeline_streaming(Profile.MULTILINGUAL)
    test_pipeline_streaming(Profile.PURE_ENGLISH)
    print("\nALL STAGE 1 STANDALONE TESTS PASSED!")
