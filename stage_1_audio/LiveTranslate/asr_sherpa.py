"""Sherpa-ONNX unified ASR engine supporting dual profiles:
1. Multilingual: Alibaba SenseVoice-Small (INT8)
2. Pure English: NVIDIA Parakeet-TDT 0.6B (INT8)

Optimized for AMD Ryzen 7 7800X3D (AVX-512 VNNI, 2 threads).
"""

import logging
import os
import time
import numpy as np
import sherpa_onnx
from huggingface_hub import hf_hub_download

log = logging.getLogger("LiveTranslate.SherpaASR")

SAMPLE_RATE = 16000

class Profile:
    MULTILINGUAL = "multilingual"
    PURE_ENGLISH = "pure_english"


class SherpaASREngine:
    """Unified ASR Engine powered by Sherpa-ONNX C++ runtime."""

    def __init__(
        self,
        profile: str = Profile.MULTILINGUAL,
        num_threads: int = 2,
        provider: str = "cpu",
        hotwords_file: str = "",
        hotwords_score: float = 1.5,
    ):
        self.profile = profile.lower()
        self.num_threads = max(1, int(num_threads))
        self.provider = provider
        self.hotwords_file = hotwords_file
        self.hotwords_score = hotwords_score
        self._recognizer = None
        self._load_model()

    def _load_model(self):
        t0 = time.perf_counter()
        log.info(
            f"Loading Sherpa-ONNX model | Profile: {self.profile} | "
            f"Threads: {self.num_threads} | Provider: {self.provider}"
        )

        if self.profile == Profile.MULTILINGUAL:
            # Alibaba SenseVoice-Small INT8
            repo_id = "csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
            model_path = hf_hub_download(repo_id=repo_id, filename="model.int8.onnx")
            tokens_path = hf_hub_download(repo_id=repo_id, filename="tokens.txt")

            self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=model_path,
                tokens=tokens_path,
                num_threads=self.num_threads,
                use_itn=True,
                language="auto",
                provider=self.provider,
            )
            log.info(f"SenseVoice-Small INT8 loaded in {time.perf_counter() - t0:.2f}s")

        elif self.profile == Profile.PURE_ENGLISH:
            # NVIDIA Parakeet-TDT 0.6B INT8
            base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scratch", "parakeet_tdt")
            enc = os.path.join(base_dir, "encoder.int8.onnx")
            dec = os.path.join(base_dir, "decoder.int8.onnx")
            join = os.path.join(base_dir, "joiner.int8.onnx")
            tokens = os.path.join(base_dir, "tokens.txt")

            for f, name in [(enc, "encoder"), (dec, "decoder"), (join, "joiner"), (tokens, "tokens")]:
                if not os.path.exists(f):
                    raise FileNotFoundError(f"Parakeet model file missing: {name} at {f}")

            self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=enc,
                decoder=dec,
                joiner=join,
                tokens=tokens,
                num_threads=self.num_threads,
                sample_rate=SAMPLE_RATE,
                feature_dim=128,
                model_type="nemo_transducer",
                blank_penalty=1.5,
                hotwords_file=self.hotwords_file,
                hotwords_score=self.hotwords_score,
                provider=self.provider,
            )
            log.info(f"Parakeet-TDT 0.6B INT8 loaded in {time.perf_counter() - t0:.2f}s")
        else:
            raise ValueError(f"Unknown ASR profile: {self.profile}. Choose 'multilingual' or 'pure_english'.")

    def create_stream(self):
        """Create a decoding stream for incremental/batch audio processing."""
        return self._recognizer.create_stream()

    def decode_stream(self, stream):
        """Execute C++ decoding on an active stream."""
        self._recognizer.decode_stream(stream)

    def transcribe(self, audio: np.ndarray, word_timestamps: bool = False) -> dict | None:
        """Transcribe a 16kHz mono audio buffer into clean text.
        
        Args:
            audio: float32 1D numpy array, 16kHz mono.
            word_timestamps: optional boolean.
            
        Returns:
            dict with 'text', 'language', 'language_name', 'latency_ms' or None.
        """
        if audio is None or audio.size == 0:
            return None

        # Ensure 1D float32
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        t0 = time.perf_counter()
        stream = self.create_stream()
        stream.accept_waveform(SAMPLE_RATE, audio)
        self.decode_stream(stream)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        raw_text = stream.result.text.strip()
        if not raw_text:
            return None

        # Clean tags (e.g. SenseVoice emotion/event tags <|HAPPY|>, <|BGM|>, etc.)
        import re
        clean_text = re.sub(r"<\|.*?\|>", "", raw_text).strip()
        if not clean_text:
            return None

        # Detect language cues
        lang = "en"
        lang_name = "English"
        if self.profile == Profile.MULTILINGUAL:
            if any("\u0400" <= c <= "\u04ff" for c in clean_text):
                lang, lang_name = "ru", "Russian"
            elif any("\u4e00" <= c <= "\u9fff" for c in clean_text):
                lang, lang_name = "zh", "Chinese"
            elif any("\u3040" <= c <= "\u30ff" for c in clean_text):
                lang, lang_name = "ja", "Japanese"

        return {
            "text": clean_text,
            "language": lang,
            "language_name": lang_name,
            "latency_ms": elapsed_ms,
        }

    def unload(self):
        """Release C++ recognizer and free memory."""
        self._recognizer = None
        log.info(f"SherpaASREngine ({self.profile}) unloaded.")
