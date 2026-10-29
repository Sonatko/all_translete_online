"""Interactive Voice Cloning Tool (XTTS-v2).

Records 5-6 seconds of the user's speech from Behringer XM8500 / Topping E2x2,
extracts neural voice latents (pitch, timbre, resonance),
and synthesizes an English sentence speaking with the user's own voice.
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

# Ensure Coqui terms agreed and soundfile patch for torchaudio
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
import sounddevice as sd
import soundfile as sf
import torch
import torchaudio

# Monkey-patch torchaudio.load to use soundfile (bypasses Windows torchcodec / ffmpeg dll requirement)
torchaudio.load = lambda f, **k: (
    torch.from_numpy(sf.read(f, dtype="float32")[0]).unsqueeze(0)
    if len(sf.read(f, dtype="float32")[0].shape) == 1
    else torch.from_numpy(sf.read(f, dtype="float32")[0].T),
    sf.read(f)[1],
)

from dizcord.audio import devices, player


def main():
    print("=" * 72)
    print("      НЕЙРОННОЕ КЛОНИРОВАНИЕ ВАШЕГО ГОЛОСА (XTTS-v2 Cross-Lingual)")
    print("=" * 72)
    print()
    print("Данный скрипт запишет 5 секунд вашей русской речи с микрофона Behringer XM8500,")
    print("извлечет персональный слепок тембра (форманты, частоты, интонацию)")
    print("и синтезирует английскую речь ВАШИМ СОБСТВЕННЫМ ГОЛОСОМ!")
    print()

    devices.ensure_com()
    inputs = devices.input_devices()
    outputs = devices.output_devices()

    # Pick microphone: prefer NVIDIA Broadcast (APO filters active) or Topping Analog 1/2
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

    # Pick headphones output: Playback 1/2
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

    sr = int(sd.query_devices(mic_idx)["default_samplerate"])
    duration = 5.5

    print("ИНСТРУКЦИЯ:")
    print("1. Нажмите ENTER, когда будете готовы.")
    print("2. Спокойно и уверенно прочитайте следующий текст в микрофон:")
    print()
    print("   «Привет! Я настраиваю систему синхронного перевода для голосового чата и игр.»")
    print()
    input("Нажмите ENTER для начала записи 5.5 секунд >>> ")

    print("\n[🔴 ИДЕТ ЗАПИСЬ... ГОВОРИТЕ В МИКРОФОН!]")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    print("[⏹ ЗАПИСЬ ЗАВЕРШЕНА]\n")

    audio = audio.flatten()
    max_amp = np.max(np.abs(audio))
    print(f"Пиковый уровень сигнала: {max_amp:.4f}")
    if max_amp < 0.03:
        print("[ВНИМАНИЕ] Сигнал слишком тихий! Убедитесь, что регулятор Gain на Topping E2x2 приподнят.")
    else:
        print("[OK] Отличный чистый уровень записи для нейросети.")

    # Save user sample to WAV (resample to 24000 Hz standard for XTTS)
    sample_path = SCRIPT_DIR / "my_voice_sample.wav"
    sf.write(str(sample_path), audio, sr)
    print(f"[OK] Сэмпл вашего голоса сохранен в: {sample_path.name}")

    print("\nЗагрузка нейросети клонирования голоса XTTS-v2 на CPU...")
    from TTS.api import TTS

    t_load = time.perf_counter()
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    print(f"[OK] Модель готова (инициализация: {time.perf_counter() - t_load:.2f} с)")

    print("\nИзвлечение акустического профиля вашего тембра (Conditioning Latents)...")
    t_latent = time.perf_counter()
    gpt_cond_latent, speaker_embedding = tts.synthesizer.tts_model.get_conditioning_latents(
        audio_path=[str(sample_path)]
    )
    latent_time = time.perf_counter() - t_latent
    print(f"[OK] Профиль тембра успешно создан за {latent_time:.2f} с!")

    # Save latents for 0-latency instant reuse
    latents_path = SCRIPT_DIR / "my_voice_latents.pth"
    torch.save(
        {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
        str(latents_path),
    )
    print(f"[OK] Профиль сохранен в {latents_path.name} (теперь не нужно пересчитывать каждый раз).")

    test_english_text = (
        "Hello! This is my own voice cloned in English. "
        "Testing how my natural timbre and pitch sound in the game chat."
    )
    print(f"\nСинтез фразы вашим голосом на английском языке:")
    print(f"  «{test_english_text}»")

    t_synth = time.perf_counter()
    output_wav_path = SCRIPT_DIR / "my_voice_cloned_en.wav"

    tts.tts_to_file(
        text=test_english_text,
        speaker_wav=str(sample_path),
        language="en",
        file_path=str(output_wav_path),
    )
    synth_time = time.perf_counter() - t_synth
    print(f"[OK] Синтез завершен за {synth_time:.2f} с!")

    print("\n[▶ ВОСПРОИЗВЕДЕНИЕ В НАУШНИКИ TOPPING...]")
    cloned_audio, cloned_sr = sf.read(str(output_wav_path), dtype="float32")

    dev = player.OutputDevice(out_name)
    dev.open()
    clip = dev.play(cloned_audio, cloned_sr, 1.0, "cloned_test")
    clip.done.wait(15.0)
    dev.close()
    print("[✔ Воспроизведение завершено!]")
    print()
    print("=" * 72)
    print("ИТОГ: Ваш персональный профиль тембра готов и сохранен.")
    print(f"Аудиофайл результата: {output_wav_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
