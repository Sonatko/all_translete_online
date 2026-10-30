"""Model Lifecycle and Inference Manager for Stage 3 Studio.
Provides modular load, unload, status checks, and latency telemetry for STT, MT, and TTS.
"""
from __future__ import annotations

import gc
import logging
import os
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import psutil

log = logging.getLogger("Studio.Models")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "stage_3_voice" / "models"
CONFIG_DIR = PROJECT_ROOT / "CONFIG" / "stage_3_voice"


class ModelManager:
    """Manages the lifecycle of STT, MT, and TTS models on CPU."""

    def __init__(self):
        # STT (GigaAM)
        self._stt_model = None
        self._stt_status: str = "unloaded"  # unloaded, loading, ready, error
        self._stt_error: str = ""

        # MT (Opus-MT INT8)
        self._mt_translator = None
        self._mt_sp_src = None
        self._mt_sp_tgt = None
        self._mt_status: str = "unloaded"
        self._mt_error: str = ""

        # TTS (Pocket-TTS Cloned)
        self._tts_model = None
        self._tts_voice_state = None
        self._tts_current_voice: str = "my_pocket_voice"
        self._tts_status: str = "unloaded"
        self._tts_error: str = ""
        self._tts_temperature: float = 0.48
        self._tts_decode_steps: int = 1

    # =========================================================================
    # RAM Telemetry
    # =========================================================================
    _cached_ram_mb: float = 0.0
    _last_ram_check: float = 0.0

    @classmethod
    def get_process_ram_mb(cls) -> float:
        """Return Resident Set Size (RSS) memory in Megabytes with 1-second caching."""
        now = time.monotonic()
        if now - cls._last_ram_check < 1.0:
            return cls._cached_ram_mb
        try:
            cls._cached_ram_mb = psutil.Process(os.getpid()).memory_info().rss / (1024.0 * 1024.0)
            cls._last_ram_check = now
            return cls._cached_ram_mb
        except Exception:
            return cls._cached_ram_mb

    def get_status_summary(self) -> Dict[str, Any]:
        """Return live status and memory footprint."""
        return {
            "stt": self._stt_status,
            "mt": self._mt_status,
            "tts": self._tts_status,
            "ram_mb": round(self.get_process_ram_mb(), 1),
            "voice": self._tts_current_voice,
        }

    # =========================================================================
    # STT: Sber GigaAM v3 CTC (Sherpa-ONNX INT8)
    # =========================================================================
    def load_stt(self, cpu_threads: int = 2) -> bool:
        """Load Sber GigaAM CTC model into RAM."""
        self._stt_status = "loading"
        try:
            import sherpa_onnx

            model_path = MODELS_DIR / "giga-am-v3" / "model.int8.onnx"
            tokens_path = MODELS_DIR / "giga-am-v3" / "tokens.txt"

            if not model_path.is_file() or not tokens_path.is_file():
                # Check alternative Dizcord cache
                alt_model = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / "models" / "giga-am-v3" / "model.int8.onnx"
                alt_tokens = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / "models" / "giga-am-v3" / "tokens.txt"
                if alt_model.is_file() and alt_tokens.is_file():
                    model_path = alt_model
                    tokens_path = alt_tokens
                else:
                    raise FileNotFoundError(f"GigaAM files not found at {model_path}")

            log.info("Loading GigaAM STT from %s (threads=%d)...", model_path, cpu_threads)
            self._stt_model = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
                model=str(model_path),
                tokens=str(tokens_path),
                num_threads=cpu_threads,
                provider="cpu",
            )
            self._stt_status = "ready"
            self._stt_error = ""
            log.info("GigaAM STT loaded successfully.")
            return True
        except Exception as e:
            self._stt_status = "error"
            self._stt_error = str(e)
            log.error("Failed to load GigaAM STT: %s", e)
            return False

    def unload_stt(self) -> None:
        """Unload STT and reclaim memory."""
        self._stt_model = None
        self._stt_status = "unloaded"
        gc.collect()
        log.info("STT unloaded from memory.")

    def transcribe(self, audio_16k_mono: np.ndarray) -> Tuple[str, float]:
        """Transcribe 16kHz mono audio array. Returns (text, elapsed_ms)."""
        if self._stt_model is None or self._stt_status != "ready":
            return "", 0.0

        t0 = time.perf_counter()
        stream = self._stt_model.create_stream()
        stream.accept_waveform(16000, audio_16k_mono)
        self._stt_model.decode_stream(stream)
        text = stream.result.text.strip()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return text, elapsed_ms

    # =========================================================================
    # MT: Helsinki Opus-MT RU->EN (CTranslate2 INT8)
    # =========================================================================
    def load_mt(self, cpu_threads: int = 2) -> bool:
        """Load Opus-MT INT8 translation model."""
        self._mt_status = "loading"
        try:
            import ctranslate2
            import sentencepiece as spm

            model_dir = MODELS_DIR / "opus-mt-ru-en-ct2"
            if not (model_dir / "model.bin").is_file():
                alt_dir = PROJECT_ROOT / "stage_3_voice" / "Dizcord" / "models" / "opus-mt-ru-en-ct2"
                if (alt_dir / "model.bin").is_file():
                    model_dir = alt_dir
                else:
                    raise FileNotFoundError(f"Opus-MT not found at {model_dir}")

            log.info("Loading Opus-MT from %s...", model_dir)
            self._mt_translator = ctranslate2.Translator(
                str(model_dir),
                device="cpu",
                compute_type="int8",
                intra_threads=cpu_threads,
                inter_threads=1,
            )
            self._mt_sp_src = spm.SentencePieceProcessor(str(model_dir / "source.spm"))
            self._mt_sp_tgt = spm.SentencePieceProcessor(str(model_dir / "target.spm"))
            self._mt_status = "ready"
            self._mt_error = ""
            log.info("Opus-MT loaded successfully.")
            return True
        except Exception as e:
            self._mt_status = "error"
            self._mt_error = str(e)
            log.error("Failed to load Opus-MT: %s", e)
            return False

    def unload_mt(self) -> None:
        """Unload MT model."""
        self._mt_translator = None
        self._mt_sp_src = None
        self._mt_sp_tgt = None
        self._mt_status = "unloaded"
        gc.collect()
        log.info("MT unloaded from memory.")

    def translate(self, text: str) -> Tuple[str, float]:
        """Translate Russian text to English. Returns (translated_text, elapsed_ms)."""
        if not text.strip() or self._mt_translator is None or self._mt_status != "ready":
            return "", 0.0

        t0 = time.perf_counter()
        tokens = self._mt_sp_src.encode(text, out_type=str) + ["</s>"]
        results = self._mt_translator.translate_batch(
            [tokens],
            beam_size=1,  # Greedy search for lowest latency
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
            max_decoding_length=128,
        )
        translated = self._mt_sp_tgt.decode(results[0].hypotheses[0])
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return translated.strip(), elapsed_ms

    # =========================================================================
    # TTS: Kyutai Pocket-TTS (Mimi Codec + Flow Matching)
    # =========================================================================
    def load_tts(self, voice_name: str = "my_pocket_voice") -> bool:
        """Load Pocket-TTS model and prepare voice state."""
        self._tts_status = "loading"
        self._tts_current_voice = voice_name
        try:
            import pocket_tts
            from huggingface_hub import hf_hub_download
            import safetensors.torch

            local_weights = MODELS_DIR / "pocket_tts" / "model.safetensors"
            if local_weights.is_file():
                log.info("Loading Pocket-TTS backbone weights from local SSD (%s)...", local_weights)
                weights_file = str(local_weights)
            else:
                log.info("Loading Pocket-TTS backbone weights from cache...")
                weights_file = hf_hub_download(
                    "latent-variable/pocket-tts-cloning-en",
                    "languages/english/model.safetensors",
                    local_files_only=True,
                )
            model = pocket_tts.TTSModel.load_model()
            state = safetensors.torch.load_file(weights_file)
            model.load_state_dict(state, strict=True)
            model.has_voice_cloning = True
            model.temp = self._tts_temperature
            model.sampler_decode_steps = self._tts_decode_steps
            self._tts_model = model

            # Setup voice state
            self.set_voice(voice_name)
            self._tts_status = "ready"
            self._tts_error = ""
            log.info("Pocket-TTS loaded successfully with voice '%s'.", voice_name)
            return True
        except Exception as e:
            self._tts_status = "error"
            self._tts_error = str(e)
            log.error("Failed to load Pocket-TTS: %s", e)
            return False

    def set_voice(self, voice_name: str) -> bool:
        """Switch active voice profile without reloading the neural backbone."""
        if self._tts_model is None:
            self._tts_current_voice = voice_name
            return False
        try:
            import pocket_tts

            self._tts_current_voice = voice_name
            if voice_name == "my_pocket_voice":
                # Check permanent CONFIG or local models
                clone_path = CONFIG_DIR / "my_pocket_voice.safetensors"
                if not clone_path.is_file():
                    clone_path = MODELS_DIR / "pocket_tts" / "my_pocket_voice.safetensors"
                if not clone_path.is_file():
                    raise FileNotFoundError(f"Voice clone file not found at {clone_path}")

                self._tts_voice_state = pocket_tts.models.tts_model._import_model_state(
                    str(clone_path), self._tts_model.device
                )
                log.info("Voice state loaded from user clone: %s", clone_path)
            elif voice_name in ("alba", "marius", "juergen", "fantine", "paul", "charles", "george", "michael"):
                self._tts_voice_state = self._tts_model.get_state_for_audio_prompt(voice_name)
                log.info("Voice state loaded from stock voice: %s", voice_name)
            else:
                self._tts_voice_state = self._tts_model.get_state_for_audio_prompt("alba")
            return True
        except Exception as e:
            log.error("Failed to set voice '%s': %s", voice_name, e)
            return False

    def unload_tts(self) -> None:
        """Unload TTS model and release memory."""
        self._tts_model = None
        self._tts_voice_state = None
        self._tts_status = "unloaded"
        gc.collect()
        log.info("TTS unloaded from memory.")

    def set_tts_temperature(self, temp: float) -> None:
        """Set stochastic sampling temperature for expressive prosody (0.2=strict, 0.48=human, 0.7=expressive)."""
        self._tts_temperature = max(0.1, min(1.0, float(temp)))
        if self._tts_model is not None:
            self._tts_model.temp = self._tts_temperature
            log.info("Pocket-TTS temperature updated to %.2f", self._tts_temperature)

    def set_tts_decode_steps(self, steps: int) -> None:
        """Set flow matching decode steps (1=ultra-fast, 2=higher acoustic purity)."""
        self._tts_decode_steps = max(1, min(4, int(steps)))
        if self._tts_model is not None:
            self._tts_model.sampler_decode_steps = self._tts_decode_steps
            log.info("Pocket-TTS decode steps updated to %d", self._tts_decode_steps)

    def synthesize(self, text: str) -> Tuple[Optional[np.ndarray], int, float]:
        """Synthesize English text to 24kHz audio. Returns (audio_np, sample_rate, elapsed_ms)."""
        if not text.strip() or self._tts_model is None or self._tts_voice_state is None:
            return None, 24000, 0.0

        t0 = time.perf_counter()
        wav_tensor = self._tts_model.generate_audio(self._tts_voice_state, text, copy_state=True)
        audio = wav_tensor.squeeze().cpu().numpy()
        peak = np.max(np.abs(audio))
        if peak > 0.001:
            audio = audio * (0.90 / peak)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return audio.astype(np.float32), int(self._tts_model.sample_rate), elapsed_ms

    # =========================================================================
    # Batch Lifecycle
    # =========================================================================
    def load_all(self, stt_threads: int = 2, mt_threads: int = 2, voice: str = "my_pocket_voice") -> bool:
        """Load all three models into RAM."""
        ok_stt = self.load_stt(cpu_threads=stt_threads)
        ok_mt = self.load_mt(cpu_threads=mt_threads)
        ok_tts = self.load_tts(voice_name=voice)
        return ok_stt and ok_mt and ok_tts

    def unload_all(self) -> None:
        """Unload all models and run garbage collection."""
        self.unload_stt()
        self.unload_mt()
        self.unload_tts()
        gc.collect()
        log.info("All models unloaded. Memory cleared.")

