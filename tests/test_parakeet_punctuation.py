import os
import sys
import time
import soundfile as sf
import numpy as np

sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

from asr_sherpa import SherpaASREngine, Profile

def test_parakeet_with_punctuation():
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

    print("Initializing NVIDIA Parakeet-TDT with C++ OfflinePunctuation...")
    engine = SherpaASREngine(profile=Profile.PURE_ENGLISH, num_threads=2, provider="cpu")
    assert engine._punct is not None, "Expected OfflinePunctuation to be initialized!"

    res = engine.transcribe(audio)
    assert res is not None, "Transcription failed!"
    print(f"\n[PARAKEET OUTPUT]: {res['text']}")
    print(f"[LATENCY]: {res['latency_ms']:.1f} ms")

    # Check that text contains sentence ending punctuation (. or ?) and capital letters
    assert any(c in res['text'] for c in ".!?"), "Expected punctuation to be restored!"
    assert any(c.isupper() for c in res['text']), "Expected capital letters to be restored!"

    print("\n[SUCCESS] PARAKEET C++ PUNCTUATION RESTORATION VERIFIED!")

if __name__ == "__main__":
    test_parakeet_with_punctuation()
