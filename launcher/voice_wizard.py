"""Interactive Voice Cloning Wizard (PySide6).
Allows any user to clone their unique voice timbre in 7 seconds using Kyutai Pocket-TTS,
with automatic studio EQ, latency telemetry, and instant headphone test playback.
"""
from __future__ import annotations

import logging
from pathlib import Path
import shutil
import threading
import time
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from scipy import signal
import sounddevice as sd
import soundfile as sf

log = logging.getLogger("Launcher.VoiceWizard")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "CONFIG" / "stage_3_voice"
MODELS_DIR = PROJECT_ROOT / "stage_3_voice" / "models" / "pocket_tts"
SCRATCH_DIR = PROJECT_ROOT / "stage_3_voice" / "scratch"


class VoiceCloningWizard(QDialog):
    """Step-by-step visual studio for personal voice cloning."""

    # Worker signals
    sig_recording_tick = Signal(int)
    sig_cloning_finished = Signal(str, float)  # wav_path, latency_s
    sig_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Студия обучения и клонирования голоса — Kyutai Pocket-TTS")
        self.resize(680, 560)
        self.setMinimumSize(640, 520)

        self.ref_audio_path: Optional[Path] = None
        self.test_audio_path: Optional[Path] = None
        self.test_audio_data: Optional[np.ndarray] = None
        self.sample_rate = 24000

        self._mon_stream = None
        self._current_mic_peak = 0.0

        self._init_ui()
        self._apply_style()

        # Connect signals
        self.sig_recording_tick.connect(self._on_recording_tick)
        self.sig_cloning_finished.connect(self._on_cloning_finished)
        self.sig_error.connect(self._on_error)

        self._start_mic_monitor()

        # Microphone monitor UI update timer (50 ms, non-blocking)
        self.mic_timer = QTimer(self)
        self.mic_timer.setInterval(50)
        self.mic_timer.timeout.connect(self._poll_mic_level)
        self.mic_timer.start()

    def _start_mic_monitor(self):
        try:
            self._stop_mic_monitor()
            mic_id = self.combo_mic.currentData() if hasattr(self, 'combo_mic') else None
            def _mon_cb(indata, frames, time_info, status):
                peak = float(np.max(np.abs(indata[:, 0])))
                self._current_mic_peak = max(peak, self._current_mic_peak * 0.85)

            self._mon_stream = sd.InputStream(
                device=mic_id,
                channels=1,
                samplerate=48000,
                blocksize=960,
                dtype="float32",
                callback=_mon_cb
            )
            self._mon_stream.start()
        except Exception:
            pass

    def _stop_mic_monitor(self):
        if self._mon_stream:
            try:
                self._mon_stream.stop()
                self._mon_stream.close()
            except Exception:
                pass
            self._mon_stream = None

    def closeEvent(self, event):
        self._stop_mic_monitor()
        super().closeEvent(event)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        title = QLabel("🎙 <b>Обучение нейро-модели под ваш собственный голос</b>")
        title.setStyleSheet("font-size: 16px; color: #ffffff;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Для создания цифрового двойника вашего голоса достаточно прочитать короткую 7-секундную фразу. "
            "Нейросеть Mimi извлечет акустический слепок вашего тембра (Mimi Latents) без нагрузки на видеокарту."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(subtitle)

        # Device Selection Bar
        h_dev = QHBoxLayout()
        h_dev.addWidget(QLabel("Микрофон:"))
        self.combo_mic = QComboBox()
        try:
            for idx, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) > 0:
                    self.combo_mic.addItem(f"[{idx}] {d['name']}", idx)
            # Default to NVIDIA Broadcast or Analog 1/2
            for i in range(self.combo_mic.count()):
                text = self.combo_mic.itemText(i).lower()
                if "broadcast" in text or "analog 1/2" in text:
                    self.combo_mic.setCurrentIndex(i)
                    break
        except Exception:
            pass
        h_dev.addWidget(self.combo_mic, stretch=1)
        layout.addLayout(h_dev)

        # Microphone Live Level Bar
        h_vu = QHBoxLayout()
        h_vu.addWidget(QLabel("Уровень микрофона:"))
        self.vu_bar = QProgressBar()
        self.vu_bar.setRange(0, 100)
        self.vu_bar.setValue(0)
        self.vu_bar.setFixedHeight(12)
        self.vu_bar.setTextVisible(False)
        self.vu_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e2024;
                border: 1px solid #32353b;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 2px;
            }
        """)
        h_vu.addWidget(self.vu_bar, stretch=1)
        layout.addLayout(h_vu)

        # Calibration Prompt Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1c20;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        v_card = QVBoxLayout(card)
        v_card.setSpacing(6)

        card_hint = QLabel("<b>Текст для калибровки (читайте спокойно в микрофон при записи):</b>")
        card_hint.setStyleSheet("color: #60a5fa; font-size: 12px;")
        v_card.addWidget(card_hint)

        self.lbl_text_en = QLabel("«Hello guys, this is my natural voice. I am testing the real-time voice translation for our game.»")
        self.lbl_text_en.setWordWrap(True)
        self.lbl_text_en.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold; font-family: Georgia, serif;")
        v_card.addWidget(self.lbl_text_en)

        card_tip = QLabel("<i>Подсказка: держите микрофон на расстоянии 12–15 см под небольшим углом, чтобы избежать задуваний.</i>")
        card_tip.setStyleSheet("color: #9ca3af; font-size: 11px;")
        v_card.addWidget(card_tip)
        layout.addWidget(card)

        # Progress / Status Section
        self.lbl_status = QLabel("Нажмите кнопку записи, чтобы начать калибровку...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #d1d5db; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.lbl_status)

        self.rec_progress = QProgressBar()
        self.rec_progress.setRange(0, 7)
        self.rec_progress.setValue(0)
        self.rec_progress.setFixedHeight(18)
        self.rec_progress.setTextVisible(True)
        self.rec_progress.setFormat("Готов к записи")
        self.rec_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #ef4444;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.rec_progress)

        # Action Buttons
        h_act = QHBoxLayout()
        self.btn_record = QPushButton("🔴 НАЧАТЬ ЗАПИСЬ (7 СЕКУНД)")
        self.btn_record.setFixedHeight(44)
        self.btn_record.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #ef4444; }
            QPushButton:disabled { background-color: #4b5563; }
        """)
        self.btn_record.clicked.connect(self._on_start_recording)
        h_act.addWidget(self.btn_record, stretch=1)

        self.btn_listen = QPushButton("▶ Прослушать свой клон")
        self.btn_listen.setFixedHeight(44)
        self.btn_listen.setEnabled(False)
        self.btn_listen.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #10b981; }
            QPushButton:disabled { background-color: #374151; color: #6b7280; }
        """)
        self.btn_listen.clicked.connect(self._on_play_sample)
        h_act.addWidget(self.btn_listen)
        layout.addLayout(h_act)

        # Footer
        h_foot = QHBoxLayout()
        h_foot.addStretch()
        self.btn_close = QPushButton("Готово / Закрыть")
        self.btn_close.setFixedHeight(34)
        self.btn_close.clicked.connect(self.accept)
        h_foot.addWidget(self.btn_close)
        layout.addLayout(h_foot)

    def _poll_mic_level(self):
        """Poll input level smoothly without blocking the GUI."""
        self.vu_bar.setValue(min(100, int(self._current_mic_peak * 200)))

    def _on_start_recording(self):
        self.btn_record.setEnabled(False)
        self.btn_listen.setEnabled(False)
        self.rec_progress.setValue(0)
        self.lbl_status.setText("🔴 ИДЕТ ЗАПИСЬ... ЧИТАЙТЕ ТЕКСТ В МИКРОФОН!")
        self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")

        self._stop_mic_monitor()
        mic_id = self.combo_mic.currentData()
        threading.Thread(target=self._recording_worker, args=(mic_id,), daemon=True).start()

    def _recording_worker(self, mic_id: int):
        duration = 7.0
        sr = 48000
        try:
            sr = int(sd.query_devices(mic_id)["default_samplerate"])
        except Exception:
            pass

        # 1. Record audio
        audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32", device=mic_id)

        for sec in range(1, 8):
            time.sleep(1.0)
            self.sig_recording_tick.emit(sec)

        sd.wait()
        audio = audio.flatten()

        # 2. Studio Pre-processing
        # High-pass filter 80Hz (sos)
        sos = signal.butter(2, 80, "hp", fs=sr, output="sos")
        clean_audio = signal.sosfilt(sos, audio)

        # Peak normalization (-1.4 dBFS)
        peak = np.max(np.abs(clean_audio))
        if peak > 0.001:
            clean_audio = clean_audio * (0.85 / peak)

        # Resample to 24000 Hz for Mimi Neural Codec
        num_samples_24k = int(len(clean_audio) * 24000 / sr)
        audio_24k = signal.resample(clean_audio, num_samples_24k).astype(np.float32)

        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        ref_path = SCRATCH_DIR / "my_clean_reference.wav"
        sf.write(str(ref_path), audio_24k, 24000)
        self.ref_audio_path = ref_path

        # 3. Model Conditioning & Latent Extraction
        try:
            import pocket_tts
            from huggingface_hub import hf_hub_download
            import safetensors.torch

            weights_file = hf_hub_download(
                "latent-variable/pocket-tts-cloning-en", "languages/english/model.safetensors"
            )
            m = pocket_tts.TTSModel.load_model()
            state = safetensors.torch.load_file(weights_file)
            m.load_state_dict(state, strict=True)
            m.has_voice_cloning = True

            t0 = time.perf_counter()
            model_state = m.get_state_for_audio_prompt(str(ref_path), truncate=True)
            latency_s = time.perf_counter() - t0

            # Export model state profile to CONFIG and models folders
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            MODELS_DIR.mkdir(parents=True, exist_ok=True)

            prof_config = CONFIG_DIR / "my_pocket_voice.safetensors"
            prof_models = MODELS_DIR / "my_pocket_voice.safetensors"

            pocket_tts.export_model_state(model_state, str(prof_config))
            shutil.copy2(prof_config, prof_models)

            # Generate sample phrase for headphone verification
            test_phrase = "Enemy spotted on B site! Fall back and hold the angles, I am covering you."
            wav_tensor = m.generate_audio(model_state, test_phrase, copy_state=True)
            gen_audio = wav_tensor.squeeze().cpu().numpy()
            peak_gen = np.max(np.abs(gen_audio))
            if peak_gen > 0.001:
                gen_audio = gen_audio * (0.90 / peak_gen)

            test_file = SCRATCH_DIR / "test_cloned_voice.wav"
            sf.write(str(test_file), gen_audio, 24000)
            self.test_audio_path = test_file
            self.test_audio_data = gen_audio

            self.sig_cloning_finished.emit(str(test_file), latency_s)

        except Exception as e:
            self.sig_error.emit(str(e))

    def _on_recording_tick(self, sec: int):
        self.rec_progress.setValue(sec)
        self.rec_progress.setFormat(f"Запись: {sec} / 7 сек")

    def _on_cloning_finished(self, test_wav: str, latency_s: float):
        self.btn_record.setEnabled(True)
        self.btn_listen.setEnabled(True)
        self.lbl_status.setText(f"✔ Обучение завершено за {latency_s:.2f} сек! Слепок вашего тембра успешно сохранен.")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        self.rec_progress.setFormat("Готово! Профиль сохранен.")
        self._start_mic_monitor()

        # Play automatic preview in headphones
        self._on_play_sample()

    def _on_error(self, err_msg: str):
        self.btn_record.setEnabled(True)
        self.lbl_status.setText(f"❌ Ошибка калибровки: {err_msg[:60]}")
        self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold;")
        self._start_mic_monitor()

    def _on_play_sample(self):
        """Play synthesized test phrase into headphones Playback 1/2."""
        if self.test_audio_data is None:
            return
        try:
            # Prefer Playback 1/2
            out_id = None
            for idx, d in enumerate(sd.query_devices()):
                if "playback 1/2" in d["name"].lower() and d["max_output_channels"] > 0:
                    out_id = idx
                    break
            sd.play(self.test_audio_data, samplerate=24000, device=out_id)
        except Exception as e:
            log.warning("Preview playback failed: %s", e)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #131416;
                color: #e5e7eb;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel { color: #e5e7eb; }
            QComboBox {
                background-color: #212328;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #4b5563; }
        """)

