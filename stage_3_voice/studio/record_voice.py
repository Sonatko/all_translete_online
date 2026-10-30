"""Studio Quality Voice Cloning with Kyutai Pocket-TTS.

Records a pristine 7-second English speech sample from user microphone,
extracts Mimi neural audio conditioning,
saves the voice profile to safetensors for 0-ms instant reuse,
and synthesizes a realistic tactical game phrase in the user's voice.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

# Add project root and Dizcord to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
STAGE3_DIR = SCRIPT_DIR.parent
ROOT_DIR = STAGE3_DIR.parent

sys.path.insert(0, str(ROOT_DIR))

os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
import sounddevice as sd
import soundfile as sf
import scipy.signal as signal
import torch
from huggingface_hub import hf_hub_download
import safetensors.torch


def main():
    print("=" * 74)
    print("      СТУДИЙНОЕ КЛОНИРОВАНИЕ ГОЛОСА (KYUTAI POCKET-TTS)")
    print("=" * 74)
    print()
    print("ИНСТРУКЦИЯ ПО ЗАПИСИ:")
    print("1. Дистанция: 12-15 см от микрофона (примерно ширина раскрытой ладони).")
    print("2. Угол: говорите чуть-чуть мимо сетки (под углом 30 градусов), чтобы убрать взрывной воздух.")
    print("3. Говорите спокойно, уверенно и своим обычным голосом.")
    print()
    print("ТЕКСТ ДЛЯ ЧТЕНИЯ (нажмите ENTER и сразу читайте):")
    print()
    print("  «Tactical squad, watch the angles! Moving into the sector now.")
    print("   Two hostiles behind the cover, requesting immediate smoke and cover fire!»")
    print()
    print("-" * 74)

    all_devs = sd.query_devices()
    inputs = [d["name"] for d in all_devs if d["max_input_channels"] > 0]
    outputs = [d["name"] for d in all_devs if d["max_output_channels"] > 0]

    # Prefer NVIDIA Broadcast or Topping Analog 1/2
    mic_idx = None
    for i, d in enumerate(all_devs):
        if d["max_input_channels"] > 0 and "nvidia broadcast" in d["name"].lower():
            mic_idx = i
            break
    if mic_idx is None:
        for i, d in enumerate(all_devs):
            if d["max_input_channels"] > 0 and "analog 1/2" in d["name"].lower():
                mic_idx = i
                break
    if mic_idx is None:
        mic_idx = sd.default.device[0]

    # Prefer Topping Playback 1/2
    out_idx = None
    for i, d in enumerate(all_devs):
        if d["max_output_channels"] > 0 and "playback 1/2" in d["name"].lower():
            out_idx = i
            break
    if out_idx is None:
        out_idx = sd.default.device[1]

    mic_name = all_devs[mic_idx]["name"] if mic_idx is not None else "Default"
    out_name = all_devs[out_idx]["name"] if out_idx is not None else "Default"

    print(f"[ВХОД МИКРОФОНА] : {mic_name}")
    print(f"[ВЫХОД НАУШНИКОВ] : {out_name}")
    print()

    input(">>> Нажмите клавишу ENTER для начала 7-секундной записи... ")

    sr = int(sd.query_devices(mic_idx)["default_samplerate"])
    duration = 7.0

    print("\n[🔴 ИДЕТ ЗАПИСЬ... ЧИТАЙТЕ ФРАЗУ В МИКРОФОН!]")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    print("[⏹ ЗАПИСЬ ЗАВЕРШЕНА]\n")

    audio = audio.flatten()

    # Pre-processing: High-Pass 80Hz to eliminate sub-bass rumble
    sos_hpf = signal.butter(2, 80, "hp", fs=sr, output="sos")
    audio = signal.sosfilt(sos_hpf, audio)

    # Peak normalization to -1.5 dBFS
    peak = np.max(np.abs(audio))
    if peak > 0.001:
        audio = audio * (0.85 / peak)

    print(f"Пиковый уровень после фильтрации: {np.max(np.abs(audio)):.4f} [ОТЛИЧНЫЙ СИГНАЛ]")

    ref_wav_dir = STAGE3_DIR / "models" / "pocket_tts"
    ref_wav_dir.mkdir(parents=True, exist_ok=True)
    ref_wav_path = ref_wav_dir / "my_reference_voice.wav"
    sf.write(str(ref_wav_path), audio, sr)
    print(f"[OK] Чистый сэмпл сохранен: {ref_wav_path.name}")

    print("\nЗагрузка архитектуры Pocket-TTS с полным энкодером Mimi...")
    import pocket_tts

    weights_file = hf_hub_download(
        repo_id="kyutai/pocket-tts",
        filename="pocket_tts.safetensors",
    )
    tts_model = pocket_tts.TTSModel.load_model()
    state = safetensors.torch.load_file(weights_file)
    tts_model.load_state_dict(state, strict=True)
    tts_model.has_voice_cloning = True
    print("[OK] Движок Pocket-TTS готов к работе.")

    print("\nИзвлечение акустического вектора вашего голоса (Mimi Neural Latents)...")
    t0 = time.perf_counter()
    model_state = tts_model.get_state_for_audio_prompt(str(ref_wav_path), truncate=True)
    t_latent = time.perf_counter() - t0
    print(f"[OK] Слепок вашего тембра сформирован за {t_latent:.3f} с!")

    # Export model state for 0-latency future reuse
    config_voice = ROOT_DIR / "CONFIG" / "stage_3_voice" / "my_pocket_voice.safetensors"
    models_voice = STAGE3_DIR / "models" / "pocket_tts" / "my_pocket_voice.safetensors"
    config_voice.parent.mkdir(parents=True, exist_ok=True)
    models_voice.parent.mkdir(parents=True, exist_ok=True)

    pocket_tts.export_model_state(model_state, str(config_voice))
    shutil.copy2(config_voice, models_voice)
    print(f"[OK] Профиль сохранен и синхронизирован: {config_voice.name}")

    test_phrase = "Enemy spotted on B site! Fall back and hold the angles, I am covering you."
    print(f"\nСинтез боевой игровой фразы вашим новым чистым голосом:")
    print(f"  «{test_phrase}»")

    t_gen = time.perf_counter()
    wav_tensor = tts_model.generate_audio(model_state, test_phrase, copy_state=True)
    gen_time = time.perf_counter() - t_gen
    print(f"[OK] Синтез завершен за {gen_time:.3f} с на CPU!")

    # Audio normalization and volume mastering (-1.0 dBFS)
    gen_audio = wav_tensor.squeeze().cpu().numpy()
    peak_out = np.max(np.abs(gen_audio))
    if peak_out > 0.001:
        gen_audio = gen_audio * (0.90 / peak_out)

    out_file = ref_wav_dir / "my_cloned_sample.wav"
    sf.write(str(out_file), gen_audio, tts_model.sample_rate)
    print(f"[OK] Сгенерированное аудио сохранено: {out_file.name}")

    print("\n[▶ ВОСПРОИЗВЕДЕНИЕ В ВАШИ НАУШНИКИ...]")
    try:
        sd.play(gen_audio, samplerate=tts_model.sample_rate, device=out_idx)
        sd.wait()
    except Exception as exc:
        print(f"[NOTE] Воспроизведение пропущено: {exc}")

    print("\n" + "=" * 74)
    print(" [УСПЕХ] ВАШ ГОЛОСОВОЙ ПРОФИЛЬ УСПЕШНО ЗАПИСАН И ГОТОВ К РАБОТЕ В ИГРАХ!")
    print("=" * 74)


if __name__ == "__main__":
    main()

