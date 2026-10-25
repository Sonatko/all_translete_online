import logging
import gc
import os

import numpy as np
from faster_whisper import WhisperModel

from translator import LANGUAGE_DISPLAY

log = logging.getLogger("LiveTranslate.ASR")

SAMPLE_RATE = 16000
DEFAULT_PAD_SECONDS = 0.5
PAD_SECONDS_ENV = "LIVETRANS_WHISPER_PAD_SECONDS"

LANGUAGE_NAMES = {**LANGUAGE_DISPLAY, "auto": "auto"}


class ASREngine:
    """Speech-to-text using faster-whisper."""

    def __init__(
        self,
        model_size="medium",
        device="cuda",
        device_index=0,
        compute_type="float16",
        language="auto",
        download_root=None,
        pad_seconds=None,
        task="transcribe",
    ):
        self.language = language if language != "auto" else None
        self.task = task
        self._model = WhisperModel(
            model_size,
            device=device,
            device_index=device_index,
            compute_type=compute_type,
            download_root=download_root,
        )
        self._set_input_padding(pad_seconds, log_change=False)
        log.info(f"Model loaded: {model_size} on {device} ({compute_type})")
        self._log_input_padding()

    @staticmethod
    def _read_pad_seconds(value=None) -> float:
        if value is None:
            value = os.environ.get(PAD_SECONDS_ENV)
        if value is None:
            return DEFAULT_PAD_SECONDS
        try:
            return float(value)
        except (TypeError, ValueError):
            log.warning(
                f"Invalid Whisper pad seconds={value!r}; "
                f"using default {DEFAULT_PAD_SECONDS:g}s"
            )
            return DEFAULT_PAD_SECONDS

    def _set_input_padding(self, pad_seconds=None, log_change=True):
        self._pad_seconds = self._read_pad_seconds(pad_seconds)
        self._pad_quantum = int(round(SAMPLE_RATE * self._pad_seconds))
        if log_change:
            self._log_input_padding()

    def _log_input_padding(self):
        if self._pad_quantum > 0:
            log.info(
                "Whisper input padding enabled: "
                f"bucket={self._pad_seconds:g}s, quantum={self._pad_quantum} samples"
            )
        else:
            log.info("Whisper input padding disabled")

    def set_language(self, language: str):
        old = self.language
        self.language = language if language != "auto" else None
        log.info(f"ASR language: {old} -> {self.language}")

    def set_input_padding(self, pad_seconds):
        old_quantum = self._pad_quantum
        self._set_input_padding(pad_seconds, log_change=False)
        if self._pad_quantum != old_quantum:
            self._log_input_padding()

    def to_device(self, device: str):
        # ctranslate2 doesn't support device migration; must reload
        return False

    def unload(self):
        model = self._model
        self._model = None
        if model is None:
            return

        for attr in ("model", "feature_extractor", "hf_tokenizer"):
            if hasattr(model, attr):
                try:
                    delattr(model, attr)
                except Exception as e:
                    log.debug(f"Failed to delete WhisperModel.{attr}: {e}")
        del model
        gc.collect()

    def _prepare_audio_input(self, audio: np.ndarray) -> np.ndarray:
        if self._pad_quantum <= 0 or audio.size == 0:
            return audio

        original_samples = audio.shape[0]
        remainder = original_samples % self._pad_quantum
        if remainder == 0:
            return audio

        padded_samples = original_samples + self._pad_quantum - remainder
        padded = np.pad(audio, (0, padded_samples - original_samples), mode="constant")
        log.debug(f"Whisper input padded: {original_samples} -> {padded_samples} samples")
        return padded

    def transcribe(self, audio: np.ndarray, word_timestamps: bool = False) -> dict | None:
        """Transcribe audio segment.

        Args:
            audio: float32 numpy array, 16kHz mono
            word_timestamps: if True, include per-word timestamps in result

        Returns:
            dict with 'text', 'language', 'language_name' (and 'words' if word_timestamps) or None.
        """
        audio_input = self._prepare_audio_input(audio)
        init_prompt = "以下是普通话的句子。" if self.language == "zh" else None
        segments, info = self._model.transcribe(
            audio_input,
            language=self.language,
            task=getattr(self, "task", "transcribe"),
            initial_prompt=init_prompt,
            beam_size=2,
            best_of=2,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=not word_timestamps,
            vad_filter=False,
            word_timestamps=word_timestamps,
            no_speech_threshold=0.6,
        )

        noise_hallucinations = {
            "thank you", "thank you.", "thank you very much", "thank you very much.",
            "thanks for watching", "thanks for watching.", "thank you for watching", "thank you for watching.",
            "subtitles by", "bye", "bye.", "you",
            # Chinese speech hallucinations on silence / weak mic noise
            "谢谢大家", "谢谢大家。", "请订阅", "请订阅。", "关注我", "关注我。",
            "谢谢观看", "谢谢观看。", "大家再见", "大家再见。", "不客气", "不客气。"
        }

        text_parts = []
        words = []
        for seg in segments:
            clean = seg.text.strip().lower()
            if getattr(seg, "no_speech_prob", 0.0) > 0.6:
                log.debug(f"Discarding segment with high no_speech_prob={seg.no_speech_prob:.2f}: '{seg.text}'")
                continue
            if clean in noise_hallucinations and getattr(seg, "no_speech_prob", 0.0) > 0.35:
                log.debug(f"Discarding hallucination on weak speech '{clean}' (prob={seg.no_speech_prob:.2f})")
                continue
            text_parts.append(seg.text.strip())
            if word_timestamps and seg.words:
                for w in seg.words:
                    words.append({"word": w.word, "start": w.start, "end": w.end})

        detected_lang = "en" if getattr(self, "task", "transcribe") == "translate" else info.language
        # Chinese characters do not use whitespace separation
        if detected_lang == "zh":
            full_text = "".join(text_parts).strip()
        else:
            full_text = " ".join(text_parts).strip()

        if not full_text:
            return None

        result = {
            "text": full_text,
            "language": detected_lang,
            "language_name": LANGUAGE_NAMES.get(detected_lang, detected_lang),
        }
        if word_timestamps and words:
            result["words"] = words
        return result
