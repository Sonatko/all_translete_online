import sys
import time
import os
import wave
import psutil
import soundfile as sf
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

import jiwer
from huggingface_hub import hf_hub_download

# Paths
TEST_DIR = "scratch/test_audio"
AUDIO_FILES = {
    "clean_en": {
        "path": os.path.join(TEST_DIR, "en.wav"),
        "gt": "the tribal chieftain called for the boy and presented him with 50 pieces of gold",
        "lang": "en"
    },
    "noisy_broadcast": {
        "path": os.path.join(TEST_DIR, "jfk.wav"),
        "gt": "and so my fellow americans ask not what your country can do for you ask what you can do for your country",
        "lang": "en"
    },
    "noisy_game": {
        "path": os.path.join(TEST_DIR, "noisy_game.wav"),
        "gt": "the tribal chieftain called for the boy and presented him with 50 pieces of gold",
        "lang": "en"
    },
    "chinese_dialogue": {
        "path": os.path.join(TEST_DIR, "zh.wav"),
        "gt": "开放时间早上9点至下午5点",
        "lang": "zh"
    },
    "japanese_speech": {
        "path": os.path.join(TEST_DIR, "ja.wav"),
        "gt": "", # Tested for fluency and stability
        "lang": "ja"
    }
}

def load_audio_16k(path):
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
        sr = 16000
    return data.astype(np.float32), sr, len(data) / sr

def calc_wer(hypothesis: str, reference: str) -> float:
    if not reference:
        return 0.0
    # Normalize punctuation and lowercase
    tr = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip()
    ])
    h_clean = tr(hypothesis)
    r_clean = tr(reference)
    if not r_clean:
        return 0.0
    return jiwer.wer(r_clean, h_clean) * 100.0

# -------------------------------------------------------------
# 1. Faster-Whisper Small
# -------------------------------------------------------------
def bench_whisper_small():
    from faster_whisper import WhisperModel
    print("\n" + "="*60)
    print(" [1/5] FASTER-WHISPER SMALL (INT8) | OpenAI Architecture")
    print("="*60)
    t0 = time.perf_counter()
    model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    print(f"Model Load Time: {time.perf_counter() - t0:.2f} s")
    
    results = {}
    for name, item in AUDIO_FILES.items():
        data, sr, dur = load_audio_16k(item["path"])
        t0 = time.perf_counter()
        segments, info = model.transcribe(data, beam_size=1, language=item["lang"], task="transcribe")
        text = " ".join([s.text for s in segments]).strip()
        elapsed = time.perf_counter() - t0
        rtf = elapsed / dur
        wer = calc_wer(text, item["gt"]) if item["lang"] == "en" else None
        results[name] = {"text": text, "latency_ms": elapsed * 1000, "rtf": rtf, "wer": wer}
        print(f"\n  [{name}] ({dur:.2f}s):")
        print(f"    Recognized: \"{text}\"")
        wer_str = f"| WER: {wer:.1f}%" if wer is not None else ""
        print(f"    Latency:    {elapsed*1000:.1f} ms | RTF: {rtf:.3f} {wer_str}")
    return results

# -------------------------------------------------------------
# 2. Sherpa-ONNX SenseVoice-Small
# -------------------------------------------------------------
def bench_sensevoice():
    import sherpa_onnx
    print("\n" + "="*60)
    print(" [2/5] SHERPA-ONNX SENSEVOICE-SMALL (INT8) | Alibaba Architecture")
    print("="*60)
    m = hf_hub_download(repo_id='csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17', filename='model.int8.onnx')
    tok = hf_hub_download(repo_id='csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17', filename='tokens.txt')
    
    t0 = time.perf_counter()
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=m, tokens=tok, num_threads=2, use_itn=True, language="auto", provider="cpu"
    )
    print(f"Model Load Time: {time.perf_counter() - t0:.2f} s")
    
    results = {}
    for name, item in AUDIO_FILES.items():
        data, sr, dur = load_audio_16k(item["path"])
        stream = rec.create_stream()
        stream.accept_waveform(sr, data)
        t0 = time.perf_counter()
        rec.decode_stream(stream)
        elapsed = time.perf_counter() - t0
        text = stream.result.text
        rtf = elapsed / dur
        wer = calc_wer(text, item["gt"]) if item["lang"] == "en" else None
        results[name] = {"text": text, "latency_ms": elapsed * 1000, "rtf": rtf, "wer": wer}
        print(f"\n  [{name}] ({dur:.2f}s):")
        print(f"    Recognized: \"{text}\"")
        wer_str = f"| WER: {wer:.1f}%" if wer is not None else ""
        print(f"    Latency:    {elapsed*1000:.1f} ms | RTF: {rtf:.3f} {wer_str}")
    return results

# -------------------------------------------------------------
# 3. Sherpa-ONNX Zipformer (Next-Gen Kaldi)
# -------------------------------------------------------------
def bench_zipformer():
    import sherpa_onnx
    print("\n" + "="*60)
    print(" [3/5] SHERPA-ONNX ZIPFORMER BILINGUAL (INT8) | Daniel Povey Team")
    print("="*60)
    r = 'csukuangfj/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20'
    enc = hf_hub_download(r, 'encoder-epoch-99-avg-1.int8.onnx')
    dec = hf_hub_download(r, 'decoder-epoch-99-avg-1.int8.onnx')
    join = hf_hub_download(r, 'joiner-epoch-99-avg-1.int8.onnx')
    tok = hf_hub_download(r, 'tokens.txt')

    t0 = time.perf_counter()
    rec = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=tok,
        encoder=enc,
        decoder=dec,
        joiner=join,
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
        provider="cpu"
    )
    print(f"Model Load Time: {time.perf_counter() - t0:.2f} s")

    results = {}
    for name, item in AUDIO_FILES.items():
        if item["lang"] not in ["en", "zh"]:
            continue
        data, sr, dur = load_audio_16k(item["path"])
        stream = rec.create_stream()
        t0 = time.perf_counter()
        stream.accept_waveform(sr, data)
        # Feed audio into online recognizer
        while rec.is_ready(stream):
            rec.decode_stream(stream)
        elapsed = time.perf_counter() - t0
        res = rec.get_result(stream)
        text = res.text if hasattr(res, "text") else str(res)
        rtf = elapsed / dur
        wer = calc_wer(text, item["gt"]) if item["lang"] == "en" else None
        results[name] = {"text": text, "latency_ms": elapsed * 1000, "rtf": rtf, "wer": wer}
        print(f"\n  [{name}] ({dur:.2f}s):")
        print(f"    Recognized: \"{text}\"")
        wer_str = f"| WER: {wer:.1f}%" if wer is not None else ""
        print(f"    Latency:    {elapsed*1000:.1f} ms | RTF: {rtf:.3f} {wer_str}")
    return results

def bench_moonshine():
    import moonshine_voice as mv
    from moonshine_voice.transcriber import Transcriber
    print("\n" + "="*60)
    print(" [4/5] MOONSHINE VOICE (INT8) | UsefulSensors Architecture")
    print("="*60)
    p, a = mv.get_model_for_language("en")
    t0 = time.perf_counter()
    transcriber = Transcriber(model_path=p, model_arch=a)
    print(f"Model Load Time: {time.perf_counter() - t0:.2f} s")
    
    results = {}
    for name, item in AUDIO_FILES.items():
        if item["lang"] != "en":
            continue
        data, sr, dur = load_audio_16k(item["path"])
        t0 = time.perf_counter()
        transcript = transcriber.transcribe_without_streaming(data.tolist(), sample_rate=sr)
        elapsed = time.perf_counter() - t0
        text = " ".join([line.text for line in transcript.lines]).strip()
        rtf = elapsed / dur
        wer = calc_wer(text, item["gt"])
        results[name] = {"text": text, "latency_ms": elapsed * 1000, "rtf": rtf, "wer": wer}
        print(f"\n  [{name}] ({dur:.2f}s):")
        print(f"    Recognized: \"{text}\"")
        print(f"    Latency:    {elapsed*1000:.1f} ms | RTF: {rtf:.3f} | WER: {wer:.1f}%")
    return results

if __name__ == "__main__":
    w_res = bench_whisper_small()
    sv_res = bench_sensevoice()
    zip_res = bench_zipformer()
    moon_res = bench_moonshine()
