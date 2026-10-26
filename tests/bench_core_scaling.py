import sys
import time
import os
import soundfile as sf
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

from faster_whisper import WhisperModel
import sherpa_onnx
from huggingface_hub import hf_hub_download

# Prepare 3 different audio lengths:
# 1. Short (1.2s): "Look out!"
# 2. Medium (4.0s): "The tribal chieftain called for the boy."
# 3. Long (11.0s): JFK Address

FULL_AUDIO_PATH = "scratch/test_audio/en.wav"
JFK_AUDIO_PATH = "scratch/test_audio/jfk.wav"

data_en, sr_en = sf.read(FULL_AUDIO_PATH)
if len(data_en.shape) > 1:
    data_en = data_en.mean(axis=1)
if sr_en != 16000:
    target_len = int(len(data_en) * 16000 / sr_en)
    data_en = np.interp(np.linspace(0, len(data_en), target_len, endpoint=False), np.arange(len(data_en)), data_en).astype(np.float32)

short_audio = data_en[:int(16000 * 1.5)]
med_audio = data_en[:int(16000 * 4.0)]

data_jfk, sr_jfk = sf.read(JFK_AUDIO_PATH)
if len(data_jfk.shape) > 1:
    data_jfk = data_jfk.mean(axis=1)
if sr_jfk != 16000:
    target_len = int(len(data_jfk) * 16000 / sr_jfk)
    data_jfk = np.interp(np.linspace(0, len(data_jfk), target_len, endpoint=False), np.arange(len(data_jfk)), data_jfk).astype(np.float32)
long_audio = data_jfk

TEST_SLICES = [
    ("1. Короткая реплика (1.5 сек)", short_audio, 1.5),
    ("2. Средняя фраза (4.0 сек)", med_audio, 4.0),
    ("3. Длинный монолог (11.0 сек)", long_audio, 11.0)
]

THREADS_TO_TEST = [1, 2, 4, 6]

def run_scaling_benchmark():
    print("="*75)
    print(" МАТРИЦА МНОГОПОТОЧНОСТИ И ДЛИНЫ ФРАЗ (AMD Ryzen 7 7800X3D)")
    print("="*75)
    
    # SenseVoice Model paths
    m_sv = hf_hub_download(repo_id='csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17', filename='model.int8.onnx')
    tok_sv = hf_hub_download(repo_id='csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17', filename='tokens.txt')

    print("\n" + "#"*75)
    print(" [ЧАСТЬ 1] SHERPA-ONNX SENSEVOICE-SMALL (INT8) - МАСШТАБИРОВАНИЕ ЯДЕР")
    print("#"*75)
    
    for n_threads in THREADS_TO_TEST:
        print(f"\n>>> Потоков процессора: {n_threads}")
        rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=m_sv, tokens=tok_sv, num_threads=n_threads, use_itn=True, language="auto", provider="cpu"
        )
        for label, audio, dur in TEST_SLICES:
            stream = rec.create_stream()
            stream.accept_waveform(16000, audio)
            t0 = time.perf_counter()
            rec.decode_stream(stream)
            elapsed = time.perf_counter() - t0
            rtf = elapsed / dur
            print(f"  {label}: Задержка = {elapsed*1000:6.1f} мс | RTF = {rtf:6.3f} ({dur/elapsed:4.1f}x real-time)")

    print("\n" + "#"*75)
    print(" [ЧАСТЬ 2] FASTER-WHISPER SMALL (INT8) - МАСШТАБИРОВАНИЕ ЯДЕР")
    print("#"*75)
    
    for n_threads in THREADS_TO_TEST:
        print(f"\n>>> Потоков процессора: {n_threads}")
        model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=n_threads)
        for label, audio, dur in TEST_SLICES:
            t0 = time.perf_counter()
            segments, info = model.transcribe(audio, beam_size=1, language="en")
            text = " ".join([s.text for s in segments]).strip()
            elapsed = time.perf_counter() - t0
            rtf = elapsed / dur
            print(f"  {label}: Задержка = {elapsed*1000:6.1f} мс | RTF = {rtf:6.3f} ({dur/elapsed:4.1f}x real-time)")

if __name__ == "__main__":
    run_scaling_benchmark()
