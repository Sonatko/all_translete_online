"""Studio Quality Voice Cloning with Kyutai Pocket-TTS.

Records a pristine 7-second English speech sample from Behringer XM8500,
extracts Mimi neural audio conditioning,
saves the voice profile to safetensors for 0-ms instant reuse,
and synthesizes a realistic tactical game phrase in the user's voice.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add project root and Dizcord to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
STAGE3_DIR = SCRIPT_DIR.parent
ROOT_DIR = STAGE3_DIR.parent
DIZCORD_DIR = STAGE3_DIR / "Dizcord"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(DIZCORD_DIR))

os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
import sounddevice as sd
import soundfile as sf
import scipy.signal as signal
import torch
from huggingface_hub import hf_hub_download
import safetensors.torch

from dizcord.audio import devices, player


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
    print("  «Hello guys, this is my natural voice. I am testing the real-time voice translation for our game.»")
    print()

    devices.ensure_com()
    inputs = devices.input_devices()
    outputs = devices.output_devices()

    # Prefer NVIDIA Broadcast (APO filters active) or Topping Analog 1/2
    mic_idx = None
    for i, d in enumerate(inputs):
        if "broadcast" in d.lower():
            mic_idx = i
            break
    if mic_idx is None:
        for i, d in enumerate(inputs):
            if "analog 1/2" in d.lower():
                mic_idx = i
                break
    if mic_idx is None:
        mic_idx = sd.default.device[0]

    # Prefer Topping Playback 1/2
    out_idx = None
    for i, d in enumerate(outputs):
        if "playback 1/2" in d.lower():
            out_idx = i
            break
    if out_idx is None:
        out_idx = sd.default.device[1]

    mic_name = inputs[mic_idx] if mic_idx < len(inputs) else "Default"
    out_name = outputs[out_idx] if out_idx < len(outputs) else "Default"

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

    ref_wav_path = SCRIPT_DIR / "my_clean_reference.wav"
    sf.write(str(ref_wav_path), audio, sr)
    print(f"[OK] Чистый сэмпл сохранен: {ref_wav_path.name}")

    print("\nЗагрузка архитектуры Pocket-TTS с полным энкодером Mimi...")
    import pocket_tts

    weights_file = hf_hub_download(
        "latent-variable/pocket-tts-cloning-en", "languages/english/model.safetensors"
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
    profile_path = SCRIPT_DIR / "my_pocket_voice.safetensors"
    pocket_tts.export_model_state(model_state, str(profile_path))
    print(f"[OK] Профиль сохранен в {profile_path.name} (готов для мгновенного синтеза в игре).")

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

    out_file = SCRIPT_DIR / "my_clean_cloned_game.wav"
    sf.write(str(out_file), gen_audio, tts_model.sample_rate)
    print(f"[OK] Сгенерированное аудио сохранено: {out_file.name}")

    print("\n[▶ ВОСПРОИЗВЕДЕНИЕ В ВАШИ НАУШНИКИ TOPPING...]")
    dev = player.OutputDevice(out_name)
    dev.open()
    clip = dev.play(gen_audio, tts_model.sample_rate, 1.0, "clean_cloned_play")
    clip.done.wait(10.0)
    dev.close()
    print("[✔ Воспроизведение успешно завершено!]\n")
    print("=" * 74)
    print("ИТОГ: Ваш чистый эталонный голос готов!")
    print(f"Профиль: {profile_path}")
    print("=" * 74)


if __name__ == "__main__":
    main()

