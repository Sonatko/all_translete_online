"""Model Lifecycle and Inference Manager for Stage 3 Studio.
Provides modular load, unload, status checks, and latency telemetry for STT, MT, and TTS.
"""
from __future__ import annotations

import gc
import json
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

    def __init__(self, pipeline: str = "ru_en"):
        # Pipeline Selection: "ru_en" (Russian -> English) or "zh_en" (Chinese -> English)
        self.pipeline: str = pipeline

        # STT (GigaAM for RU, SenseVoice for ZH)
        self._stt_model = None
        self._stt_status: str = "unloaded"  # unloaded, loading, ready, error
        self._stt_error: str = ""

        # MT (Opus-MT INT8: RU->EN or ZH->EN)
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
        self.tts_speed: float = 1.0  # 1.0 = Pure neural synthesis (zero robotic / comb-filtering artifacts)

    def set_pipeline(self, pipeline: str, auto_reload: bool = False) -> bool:
        """Switch language pipeline between "ru_en" and "zh_en"."""
        if pipeline not in ("ru_en", "zh_en"):
            log.warning("Unknown pipeline '%s', defaulting to 'ru_en'", pipeline)
            pipeline = "ru_en"
        if self.pipeline == pipeline and self._stt_status == "ready" and self._mt_status == "ready":
            return True
        log.info("Switching pipeline from '%s' to '%s' (auto_reload=%s)...", self.pipeline, pipeline, auto_reload)
        self.pipeline = pipeline
        self.unload_stt()
        self.unload_mt()
        if auto_reload:
            ok_stt = self.load_stt()
            ok_mt = self.load_mt()
            return ok_stt and ok_mt
        return True

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
        """Return live status, active pipeline, and memory footprint."""
        return {
            "pipeline": self.pipeline,
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
        """Load STT model into RAM according to active pipeline (GigaAM or SenseVoice)."""
        self._stt_status = "loading"
        try:
            import sherpa_onnx

            if self.pipeline == "zh_en":
                model_path = MODELS_DIR / "sensevoice" / "model.int8.onnx"
                tokens_path = MODELS_DIR / "sensevoice" / "tokens.txt"
                if not model_path.is_file() or not tokens_path.is_file():
                    raise FileNotFoundError(f"SenseVoice Chinese ASR not found at {model_path}")
                log.info("Loading SenseVoice Chinese STT from %s (threads=%d)...", model_path, cpu_threads)
                self._stt_model = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=str(model_path),
                    tokens=str(tokens_path),
                    language="zh",
                    use_itn=True,
                    num_threads=cpu_threads,
                    provider="cpu",
                )
            else:
                model_path = MODELS_DIR / "giga-am-v3" / "model.int8.onnx"
                tokens_path = MODELS_DIR / "giga-am-v3" / "tokens.txt"
                if not model_path.is_file() or not tokens_path.is_file():
                    raise FileNotFoundError(f"GigaAM Russian STT not found at {model_path}")
                log.info("Loading GigaAM Russian STT from %s (threads=%d)...", model_path, cpu_threads)
                self._stt_model = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
                    model=str(model_path),
                    tokens=str(tokens_path),
                    num_threads=cpu_threads,
                    provider="cpu",
                )
            self._stt_status = "ready"
            self._stt_error = ""
            log.info("STT (%s) loaded successfully.", self.pipeline)
            return True
        except Exception as e:
            self._stt_status = "error"
            self._stt_error = str(e)
            log.error("Failed to load STT (%s): %s", self.pipeline, e)
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
        """Load Opus-MT INT8 translation model (RU->EN or ZH->EN)."""
        self._mt_status = "loading"
        try:
            import ctranslate2
            import sentencepiece as spm

            if self.pipeline == "zh_en":
                model_dir = MODELS_DIR / "opus-mt-zh-en-ct2"
            else:
                model_dir = MODELS_DIR / "opus-mt-ru-en-ct2"

            if not (model_dir / "model.bin").is_file():
                raise FileNotFoundError(f"Opus-MT ({self.pipeline}) not found at {model_dir}")

            # Auto-healing: Handle accidental config.json.txt created via Windows Explorer
            txt_cfg = model_dir / "config.json.txt"
            cfg_file = model_dir / "config.json"
            if txt_cfg.is_file() and not cfg_file.is_file():
                try:
                    txt_cfg.rename(cfg_file)
                except Exception:
                    pass

            # Auto-healing: if config.json missing, 0-byte, or invalid JSON, write authoritative config
            need_rewrite_cfg = False
            if not cfg_file.is_file() or cfg_file.stat().st_size < 10:
                need_rewrite_cfg = True
            else:
                try:
                    json.loads(cfg_file.read_text(encoding="utf-8"))
                except Exception:
                    need_rewrite_cfg = True

            if need_rewrite_cfg:
                log.info("Auto-healing config.json for %s...", model_dir.name)
                default_cfg = {
                    "add_source_bos": False,
                    "add_source_eos": False,
                    "bos_token": "<s>",
                    "decoder_start_token": "</s>",
                    "eos_token": "</s>",
                    "layer_norm_epsilon": None,
                    "unk_token": "<unk>",
                    "model_type": "marian",
                }
                cfg_file.write_text(json.dumps(default_cfg, indent=2), encoding="utf-8")

            # Auto-healing: generation_config.json
            gen_cfg = model_dir / "generation_config.json"
            if not gen_cfg.is_file() or gen_cfg.stat().st_size < 10:
                default_gen = {
                    "bad_words_ids": [[65000]],
                    "bos_token_id": 0,
                    "decoder_start_token_id": 65000,
                    "eos_token_id": 0,
                    "forced_eos_token_id": 0,
                    "max_length": 512,
                    "num_beams": 6,
                    "pad_token_id": 65000,
                    "renormalize_logits": True,
                    "transformers_version": "4.32.0.dev0",
                }
                gen_cfg.write_text(json.dumps(default_gen, indent=2), encoding="utf-8")

            log.info("Loading Opus-MT (%s) from %s...", self.pipeline, model_dir)
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
            log.info("Opus-MT (%s) loaded successfully.", self.pipeline)
            return True
        except Exception as e:
            self._mt_status = "error"
            self._mt_error = str(e)
            log.error("Failed to load Opus-MT (%s): %s", self.pipeline, e)
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
    @staticmethod
    def _ensure_pocket_tts_config(models_dir: Path, config_dir: Path) -> Path:
        """Ensure tokenizer.json and offline config.yaml exist for 100% offline Pocket-TTS."""
        tts_dir = models_dir / "pocket_tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        local_tok = tts_dir / "tokenizer.json"
        if not local_tok.is_file():
            config_tok = config_dir / "tokenizer.json"
            if config_tok.is_file():
                import shutil
                shutil.copy(config_tok, local_tok)
                log.info("Provisioned tokenizer.json from CONFIG to %s", local_tok)

        weights_file = tts_dir / "model.safetensors"
        cfg_path = tts_dir / "config.yaml"
        w_posix = weights_file.resolve().as_posix()
        t_posix = local_tok.resolve().as_posix()

        needs_rewrite = True
        if cfg_path.is_file():
            try:
                existing_text = cfg_path.read_text(encoding="utf-8")
                if f"weights_path: {w_posix}" in existing_text and f"tokenizer_path: {t_posix}" in existing_text:
                    needs_rewrite = False
                else:
                    log.info("Detected outdated or foreign absolute paths in Pocket-TTS config.yaml. Auto-regenerating for current PC...")
            except Exception:
                needs_rewrite = True

        if needs_rewrite and weights_file.is_file() and local_tok.is_file():
            yaml_content = f"""weights_path: {w_posix}
default_temperature: 0.3

replace_characters:
  '’': "'"
  '‘': "'"

flow_lm:
  insert_bos_before_voice: true
  dtype: float32
  flow:
    depth: 6
    dim: 512
  transformer:
    d_model: 1024
    hidden_scale: 4
    max_period: 10000
    num_heads: 16
    num_layers: 6
  lookup_table:
    dim: 1024
    n_bins: 4000
    tokenizer: tokenizers
    tokenizer_path: {t_posix}

mimi:
  dtype: float32
  sample_rate: 24000
  inner_dim: 32
  outer_dim: 512
  channels: 1
  frame_rate: 12.5
  seanet:
    dimension: 512
    channels: 1
    n_filters: 64
    n_residual_layers: 1
    ratios:
    - 6
    - 5
    - 4
    kernel_size: 7
    residual_kernel_size: 3
    last_kernel_size: 3
    dilation_base: 2
    pad_mode: constant
    compress: 2
  transformer:
    d_model: 512
    num_heads: 8
    num_layers: 2
    layer_scale: 0.01
    context: 250
    dim_feedforward: 2048
    input_dimension: 512
    output_dimensions:
    - 512
  quantizer:
    dimension: 32
    output_dimension: 512
"""
            cfg_path.write_text(yaml_content, encoding="utf-8")
            log.info("Created offline Pocket-TTS config.yaml at %s", cfg_path)
        return cfg_path

    def load_tts(self, voice_name: str = "my_pocket_voice") -> bool:
        """Load Pocket-TTS model and prepare voice state with 100% offline support."""
        self._tts_status = "loading"
        self._tts_current_voice = voice_name
        try:
            import pocket_tts
            import safetensors.torch
            from huggingface_hub import hf_hub_download

            local_weights = MODELS_DIR / "pocket_tts" / "model.safetensors"
            cfg_path = self._ensure_pocket_tts_config(MODELS_DIR, CONFIG_DIR)

            if not local_weights.is_file():
                log.warning("Pocket-TTS weights missing at %s - download required", local_weights)
                self._tts_status = "not_downloaded"
                self._tts_error = "Model weights not downloaded. Please click 'Скачать недостающие модели' first."
                return False

            if cfg_path.is_file():
                log.info("Loading Pocket-TTS 100% offline from local config: %s", cfg_path)
                model = pocket_tts.TTSModel.load_model(config=cfg_path)
                model.origin = pocket_tts.models.tts_model.CONFIGS_DIR / "english.yaml"
            else:
                log.error("Pocket-TTS config generation failed at %s", cfg_path)
                self._tts_status = "error"
                self._tts_error = f"Config file not found: {cfg_path}"
                return False

            model.has_voice_cloning = True
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

    def get_available_voices(self) -> List[Tuple[str, str]]:
        """Scan CONFIG, custom voices directory, and stock voices."""
        voices = []
        voices_dir = CONFIG_DIR / "voices"
        voices_dir.mkdir(parents=True, exist_ok=True)

        is_zh = (self.pipeline == "zh_en")

        # 1. Author's Pre-trained Voice (Always present as primary standard)
        author_label = "⭐ 作者原声 (my_pocket_voice)" if is_zh else "⭐ Голос автора (my_pocket_voice)"
        voices.append(("my_pocket_voice", author_label))

        # 2. Standard Built-in Voices
        stock = [
            ("juergen", "标准音色: Juergen (男声, 稳重)" if is_zh else "Стандартный: Juergen (Мужской, уверенный)"),
            ("marius", "标准音色: Marius (男声, 沉着)" if is_zh else "Стандартный: Marius (Мужской, спокойный)"),
            ("alba", "标准音色: Alba (女声, 温暖)" if is_zh else "Стандартный: Alba (Женский, теплый)"),
            ("fantine", "标准音色: Fantine (女声, 柔和)" if is_zh else "Стандартный: Fantine (Женский, мягкий)"),
            ("paul", "标准音色: Paul (男声, 叙事)" if is_zh else "Стандартный: Paul (Мужской, баритон)"),
            ("charles", "标准音色: Charles (男声, 深沉)" if is_zh else "Стандартный: Charles (Мужской, глубокий)"),
        ]
        voices.extend(stock)

        # 3. User Trained Voices in CONFIG/stage_3_voice/voices/
        for p in sorted(voices_dir.glob("*.safetensors")):
            v_id = f"custom:{p.name}"
            v_title = p.stem.replace("_", " ").title()
            prefix = "👤 我的克隆: " if is_zh else "👤 Свой клон: "
            voices.append((v_id, f"{prefix}{v_title}"))

        return voices

    def set_voice(self, voice_name: str) -> bool:
        """Switch active voice profile without reloading the neural backbone."""
        if self._tts_model is None:
            self._tts_current_voice = voice_name
            return False
        try:
            import pocket_tts

            self._tts_current_voice = voice_name
            if voice_name.startswith("custom:"):
                fname = voice_name.split(":", 1)[1]
                custom_path = CONFIG_DIR / "voices" / fname
                if custom_path.is_file():
                    self._tts_voice_state = pocket_tts.models.tts_model._import_model_state(
                        str(custom_path), self._tts_model.device
                    )
                    log.info("Voice state loaded from custom profile: %s", custom_path)
                    return True
                else:
                    log.warning("Custom voice not found at %s", custom_path)

            if voice_name == "my_pocket_voice":
                clone_path = CONFIG_DIR / "my_pocket_voice.safetensors"
                if not clone_path.is_file():
                    clone_path = MODELS_DIR / "pocket_tts" / "my_pocket_voice.safetensors"

                # If missing locally on clean PC, download on-demand from GitHub / China mirror
                if not clone_path.is_file():
                    log.info("Author's voice missing locally. Downloading via high-speed mirror...")
                    clone_path = CONFIG_DIR / "my_pocket_voice.safetensors"
                    clone_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        from launcher.model_downloader import download_single_file
                        urls = [
                            "https://ghproxy.net/https://github.com/Sonatko/all_translete_online/raw/main/CONFIG/stage_3_voice/my_pocket_voice.safetensors",
                            "https://github.com/Sonatko/all_translete_online/raw/main/CONFIG/stage_3_voice/my_pocket_voice.safetensors",
                        ]
                        download_single_file(urls, clone_path, expected_size=4_425_520)
                    except Exception as dle:
                        log.warning("On-demand author voice download error: %s", dle)

                if clone_path.is_file():
                    # Sync to models folder
                    models_copy = MODELS_DIR / "pocket_tts" / "my_pocket_voice.safetensors"
                    models_copy.parent.mkdir(parents=True, exist_ok=True)
                    if not models_copy.is_file():
                        try:
                            shutil.copy2(clone_path, models_copy)
                        except Exception:
                            pass
                    self._tts_voice_state = pocket_tts.models.tts_model._import_model_state(
                        str(clone_path), self._tts_model.device
                    )
                    log.info("Voice state loaded from author voice: %s", clone_path)
                    return True
                else:
                    log.warning("Voice clone file not found at %s, falling back to stock voice 'juergen'", clone_path)
                    voice_name = "juergen"

            if voice_name in ("alba", "marius", "juergen", "fantine", "paul", "charles", "george", "michael"):
                # 1. Try local offline embeddings first (instant, 0ms, zero network)
                local_emb = MODELS_DIR / "pocket_tts" / "embeddings" / f"{voice_name}.safetensors"
                if not local_emb.is_file():
                    local_emb = CONFIG_DIR / "embeddings" / f"{voice_name}.safetensors"
                if local_emb.is_file():
                    self._tts_voice_state = pocket_tts.models.tts_model._import_model_state(
                        str(local_emb), self._tts_model.device
                    )
                    log.info("Voice state loaded locally offline from %s", local_emb)
                    return True

                # 2. On-demand mirror download for this specific single voice if missing
                try:
                    from launcher.model_downloader import download_single_file, build_download_urls
                    urls = build_download_urls(
                        "kyutai/pocket-tts-without-voice-cloning",
                        f"languages/english/embeddings/{voice_name}.safetensors",
                        china_mirror=True,
                    )
                    dest_file = MODELS_DIR / "pocket_tts" / "embeddings" / f"{voice_name}.safetensors"
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    log.info("Downloading voice '%s' on-demand via mirror...", voice_name)
                    if download_single_file(urls, dest_file):
                        self._tts_voice_state = pocket_tts.models.tts_model._import_model_state(
                            str(dest_file), self._tts_model.device
                        )
                        log.info("Voice state '%s' downloaded and activated.", voice_name)
                        return True
                except Exception as dl_e:
                    log.warning("On-demand mirror download for voice '%s' failed: %s", voice_name, dl_e)

                # 3. Upstream fallback
                try:
                    self._tts_voice_state = self._tts_model.get_state_for_audio_prompt(voice_name)
                    log.info("Voice state loaded from stock voice: %s", voice_name)
                    return True
                except Exception as ve:
                    log.warning("Stock voice '%s' unavailable offline: %s", voice_name, ve)
                    return False
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

    @staticmethod
    def time_stretch_sola(audio: np.ndarray, speed: float = 0.92, sample_rate: int = 24000) -> np.ndarray:
        """Natural, phase-coherent time-stretching via Synchronized Overlap-Add (SOLA).

        Operates strictly in the time-domain to preserve vocal tract formants and pitch
        without introducing metallic/flanged robotic artifacts common in phase vocoders.
        Benchmark: ~3ms latency on CPU for 2s audio.
        """
        if abs(speed - 1.0) < 0.01 or len(audio) < int(0.05 * sample_rate):
            return audio

        win_size = int(0.025 * sample_rate)  # 25ms window (~600 samples at 24kHz)
        hop_out = win_size // 2
        hop_in = int(round(hop_out * speed))
        window = np.hanning(win_size).astype(np.float32)

        num_hops = (len(audio) - win_size) // hop_in
        if num_hops <= 1:
            return audio

        out_len = num_hops * hop_out + win_size
        output = np.zeros(out_len, dtype=np.float32)
        norm = np.zeros(out_len, dtype=np.float32)

        max_shift = win_size // 4
        half_win = win_size // 2

        padded = np.pad(audio, (max_shift, max_shift + win_size), mode='reflect')

        for i in range(num_hops):
            in_pos = i * hop_in + max_shift
            out_pos = i * hop_out

            best_offset = 0
            if i > 0:
                ref = output[out_pos:out_pos + half_win]
                cand_region = padded[in_pos - max_shift : in_pos + half_win + max_shift]
                xcorr = np.correlate(cand_region, ref, mode='valid')
                best_offset = int(np.argmax(xcorr)) - max_shift

            pos = in_pos + best_offset
            chunk = padded[pos:pos + win_size] * window
            output[out_pos:out_pos + win_size] += chunk
            norm[out_pos:out_pos + win_size] += window

        norm[norm < 1e-4] = 1.0
        stretched = output / norm
        return stretched.astype(np.float32)

    def synthesize(self, text: str, speed: Optional[float] = None) -> Tuple[Optional[np.ndarray], int, float]:
        """Synthesize English text to 24kHz audio with natural pacing. Returns (audio_np, sample_rate, elapsed_ms)."""
        if not text.strip() or self._tts_model is None or self._tts_voice_state is None:
            return None, 24000, 0.0

        target_speed = speed if speed is not None else self.tts_speed
        t0 = time.perf_counter()
        wav_tensor = self._tts_model.generate_audio(self._tts_voice_state, text, copy_state=True)
        audio = wav_tensor.squeeze().cpu().numpy()

        # Apply time-domain SOLA pacing if speed != 1.0 (preserves 100% natural timbre and pitch)
        if abs(target_speed - 1.0) >= 0.01:
            audio = self.time_stretch_sola(audio, speed=target_speed, sample_rate=int(self._tts_model.sample_rate))

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

