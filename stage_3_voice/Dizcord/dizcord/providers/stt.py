"""Speech-to-text providers.

transcribe(audio, language) -> (text, detected_language_code_or_None)
audio is mono float32 at 16 kHz. language is one of our codes or None (= auto).
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
import re

import numpy as np

from .. import languages as L
from ..audio.utils import wav_bytes
from ..config import MODELS_DIR
from .base import Field, Provider, ProviderError, register

SR = 16000


class STTProvider(Provider):
    kind = "stt"
    supports_auto = True

    def transcribe(self, audio: np.ndarray, language: str | None) -> tuple[str, str | None]:
        raise NotImplementedError


@register
class FasterWhisperSTT(STTProvider):
    id = "faster_whisper"
    name = "Whisper (faster-whisper)"
    local = True
    description = ("Runs OpenAI Whisper on your PC. Free and private. Uses the GPU automatically "
                   "if CUDA is available. First use downloads the model.")
    requires = ["faster_whisper"]
    pip_hint = "pip install faster-whisper"
    fields = [
        Field("model", "Model", "combo", "small",
              options=["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3",
                       "distil-large-v3"],
              help="Bigger = more accurate but slower. 'large-v3-turbo' is great on a GPU."),
        Field("device", "Device", "choice", "auto", options=["auto", "cuda", "cpu"]),
        Field("compute_type", "Precision", "choice", "auto",
              options=["auto", "int8", "int8_float16", "float16", "float32"]),
        Field("beam_size", "Beam size", "int", 1, min=1, max=10, help="1 = fastest"),
        Field("cpu_threads", "CPU threads", "int", min(8, max(2, (os.cpu_count() or 4) // 2)), min=1, max=64),
        Field("vad_filter", "Built-in VAD filter", "bool", False),
        Field("initial_prompt", "Hint / vocabulary", "str", "",
              help="Names, game terms etc. to help recognition"),
    ]

    _model = None
    _model_key = None
    has_downloads = True
    _SIZES_MB = {"tiny": 75, "base": 145, "small": 484, "medium": 1530, "large-v3-turbo": 1620, "turbo": 1620,
                 "large-v3": 3090, "large": 3090, "distil-large-v3": 1510}

    def _repo(self) -> str | None:
        """The Hugging Face repo of the chosen model, None for a model folder on this PC."""
        from faster_whisper.utils import _MODELS
        name = str(self.s("model"))
        return _MODELS.get(name, name if "/" in name and not os.path.isdir(name) else None)

    def downloads_needed(self, langs):
        repo = self._repo()
        if repo is None:
            return []
        from huggingface_hub import try_to_load_from_cache
        if isinstance(try_to_load_from_cache(repo, "model.bin", cache_dir=str(MODELS_DIR / "whisper")), str):
            return []
        return [(f"Whisper model '{self.s('model')}'", self._SIZES_MB.get(str(self.s("model")), 0) * 1_000_000)]

    def download(self, langs, progress=None, cancelled=lambda: False):
        from faster_whisper.utils import download_model
        if self.downloads_needed(langs):
            download_model(str(self.s("model")), cache_dir=str(MODELS_DIR / "whisper"))

    def download_dir(self):
        return str(MODELS_DIR / "whisper")

    def _load(self):
        from faster_whisper import WhisperModel
        key = (self.s("model"), self.s("device"), self.s("compute_type"))
        if self._model is not None and self._model_key == key:
            return self._model
        device = self.s("device")
        ctype = self.s("compute_type")
        if device == "auto":
            try:
                import ctranslate2
                device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
            except Exception:
                device = "cpu"
        if ctype == "auto":
            ctype = "float16" if device == "cuda" else "int8"
        try:
            self._model = WhisperModel(self.s("model"), device=device, compute_type=ctype,
                                       cpu_threads=int(self.s("cpu_threads", 4)),
                                       download_root=str(MODELS_DIR / "whisper"))
        except Exception as e:
            if device == "cuda":  # CUDA libs missing -> fall back to CPU instead of failing
                self._model = WhisperModel(self.s("model"), device="cpu", compute_type="int8",
                                           cpu_threads=int(self.s("cpu_threads", 4)),
                                           download_root=str(MODELS_DIR / "whisper"))
            else:
                raise ProviderError(f"faster-whisper: could not load model: {e}") from e
        self._model_key = key
        return self._model

    def warmup(self):
        with self.lock:
            self._load()

    def transcribe(self, audio, language):
        with self.lock:
            model = self._load()
            segments, info = model.transcribe(
                audio, language=L.whisper_code(language), beam_size=int(self.s("beam_size", 1)),
                vad_filter=bool(self.s("vad_filter")), condition_on_previous_text=False,
                initial_prompt=self.s("initial_prompt") or None, without_timestamps=True,
            )
            text = " ".join(seg.text.strip() for seg in segments
                            if getattr(seg, "no_speech_prob", 0) < 0.8).strip()
        detected = L.normalize(info.language) if info and info.language else None
        if detected and language is None and getattr(info, "language_probability", 1.0) < 0.4:
            detected = None  # too unsure to trust
        return text, detected or language


class OpenAICompatSTT(STTProvider):
    base_url = ""
    key_ref = "custom_stt"
    default_model = ""
    model_options: list[str] = []
    key_optional = False

    @classmethod
    def build_fields(cls):
        return [
            Field("base_url", "Base URL", "str", cls.base_url),
            Field("api_key", "API key", "secret", "", key_ref=cls.key_ref),
            Field("model", "Model", "combo", cls.default_model, options=cls.model_options),
            Field("prompt", "Hint / vocabulary", "str", ""),
            Field("timeout", "Timeout (s)", "float", 30, min=3, max=300),
        ]

    def transcribe(self, audio, language):
        url = self.s("base_url").rstrip("/") + "/audio/transcriptions"
        key = self.key() if self.key_optional else self.need_key()
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        model = self.s("model")
        # whisper-style models return the detected language with verbose_json; gpt-4o-* only do json.
        fmt = "json" if "gpt-4o" in model else "verbose_json"
        data = {"model": model, "response_format": fmt}
        if language:
            data["language"] = L.whisper_code(language)
        if self.s("prompt"):
            data["prompt"] = self.s("prompt")
        files = {"file": ("speech.wav", wav_bytes(audio, SR), "audio/wav")}
        try:
            r = self.http("POST", url, headers=headers, data=data, files=files,
                          timeout=float(self.s("timeout", 30)))
        except ProviderError as e:
            blocked = self.__dict__.setdefault("_blocked", set())     # models this account was refused
            other = [m for m in self.model_options if m != model and m not in blocked]
            if fmt == "verbose_json" and "response_format" in str(e):
                data["response_format"] = "json"
                files = {"file": ("speech.wav", wav_bytes(audio, SR), "audio/wav")}
                r = self.http("POST", url, headers=headers, data=data, files=files,
                              timeout=float(self.s("timeout", 30)))
            elif other and re.search(r"model_permission_blocked|model_not_found|does not exist|not have access",
                                     str(e)):
                # this account may not use that model: use the provider's other model from now on
                blocked.add(model)
                self.settings["model"] = other[0]
                return self.transcribe(audio, language)
            else:
                raise
        j = r.json()
        return (j.get("text") or "").strip(), L.normalize(j.get("language")) or language


STT_PRESETS = [
    ("openai_stt", "OpenAI", "https://api.openai.com/v1", "openai", "gpt-4o-mini-transcribe",
     ["gpt-4o-mini-transcribe", "gpt-4o-transcribe", "whisper-1"], False),
    ("groq_stt", "Groq Whisper", "https://api.groq.com/openai/v1", "groq", "whisper-large-v3-turbo",
     ["whisper-large-v3-turbo", "whisper-large-v3"], False),
    ("custom_stt", "Custom OpenAI-compatible", "http://localhost:8000/v1", "custom_stt",
     "Systran/faster-whisper-small", [], False),
]

for _pid, _name, _url, _ref, _model, _models, _local in STT_PRESETS:
    _cls = type(f"STT_{_pid}", (OpenAICompatSTT,), {
        "id": _pid, "name": _name, "base_url": _url, "key_ref": _ref, "default_model": _model,
        "model_options": _models, "local": _local, "key_optional": _pid == "custom_stt",
        "description": f"{_name} speech recognition (OpenAI /audio/transcriptions API). "
                       + ("Works with speaches / faster-whisper-server / LocalAI etc."
                          if _pid == "custom_stt" else ""),
    })
    _cls.fields = _cls.build_fields()
    register(_cls)


@register
class DeepgramSTT(STTProvider):
    id = "deepgram"
    name = "Deepgram"
    description = "Deepgram Nova speech recognition. Very fast."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="deepgram"),
        Field("model", "Model", "combo", "nova-3", options=["nova-3", "nova-2", "whisper-large"]),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def transcribe(self, audio, language):
        params = {"model": self.s("model"), "smart_format": "true", "punctuate": "true"}
        if language:
            params["language"] = L.base(language) if language not in ("pt-PT", "en-GB", "zh-TW") else language
        else:
            params["detect_language"] = "true"
        r = self.http("POST", "https://api.deepgram.com/v1/listen", params=params,
                      headers={"Authorization": f"Token {self.need_key()}", "Content-Type": "audio/wav"},
                      data=wav_bytes(audio, SR), timeout=float(self.s("timeout", 20)))
        j = r.json()
        try:
            ch = j["results"]["channels"][0]
            text = ch["alternatives"][0]["transcript"]
        except (KeyError, IndexError):
            return "", language
        return text.strip(), L.normalize(ch.get("detected_language")) or language


@register
class ElevenLabsSTT(STTProvider):
    id = "elevenlabs_stt"
    name = "ElevenLabs Scribe"
    description = "ElevenLabs speech-to-text (Scribe). Accurate, many languages."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="elevenlabs"),
        Field("model", "Model", "combo", "scribe_v1", options=["scribe_v1", "scribe_v2"]),
        Field("timeout", "Timeout (s)", "float", 30, min=3, max=120),
    ]

    def transcribe(self, audio, language):
        data = {"model_id": self.s("model")}
        if language:
            data["language_code"] = L.base(language)
        r = self.http("POST", "https://api.elevenlabs.io/v1/speech-to-text",
                      headers={"xi-api-key": self.need_key()}, data=data,
                      files={"file": ("speech.wav", wav_bytes(audio, SR), "audio/wav")},
                      timeout=float(self.s("timeout", 30)))
        j = r.json()
        return (j.get("text") or "").strip(), L.normalize(j.get("language_code")) or language


@register
class AzureSTT(STTProvider):
    id = "azure_stt"
    name = "Azure Speech"
    supports_auto = False
    description = "Microsoft Azure speech recognition (short audio REST). Needs a source language."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="azure_speech"),
        Field("region", "Region", "str", "eastus"),
        Field("fallback_lang", "Language when 'auto'", "str", "en",
              help="Azure REST can't auto-detect; this code is used when the source is 'Auto'"),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def transcribe(self, audio, language):
        lang = language or L.normalize(self.s("fallback_lang")) or "en"
        url = (f"https://{self.s('region')}.stt.speech.microsoft.com/speech/recognition/"
               "conversation/cognitiveservices/v1")
        r = self.http("POST", url, params={"language": L.locale_tag(lang), "format": "simple"},
                      headers={"Ocp-Apim-Subscription-Key": self.need_key(),
                               "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"},
                      data=wav_bytes(audio, SR), timeout=float(self.s("timeout", 20)))
        j = r.json()
        if j.get("RecognitionStatus") != "Success":
            return "", lang
        return (j.get("DisplayText") or "").strip(), lang


@register
class GoogleSTT(STTProvider):
    id = "google_stt"
    name = "Google Cloud Speech"
    description = "Google Cloud Speech-to-Text v1 (API key). 'Auto' tries the listed candidate languages."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="google_cloud"),
        Field("model", "Model", "combo", "latest_short", options=["latest_short", "latest_long", "default"]),
        Field("auto_candidates", "Auto-detect candidates", "str", "en,pt,es",
              help="Comma-separated codes (max 4) used when the source is 'Auto'"),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def transcribe(self, audio, language):
        if language:
            primary, alts = L.locale_tag(language), []
        else:
            cands = [L.normalize(c) for c in self.s("auto_candidates", "en").split(",") if c.strip()]
            cands = [c for c in cands if c] or ["en"]
            primary, alts = L.locale_tag(cands[0]), [L.locale_tag(c) for c in cands[1:4]]
        cfg = {"encoding": "LINEAR16", "sampleRateHertz": SR, "languageCode": primary,
               "enableAutomaticPunctuation": True, "model": self.s("model")}
        if alts:
            cfg["alternativeLanguageCodes"] = alts
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        body = {"config": cfg, "audio": {"content": base64.b64encode(pcm).decode()}}
        r = self.http("POST", "https://speech.googleapis.com/v1/speech:recognize",
                      params={"key": self.need_key()}, json=body, timeout=float(self.s("timeout", 20)))
        res = r.json().get("results") or []
        text = " ".join(x["alternatives"][0].get("transcript", "") for x in res if x.get("alternatives"))
        det = L.normalize(res[0].get("languageCode")) if res and res[0].get("languageCode") else None
        return text.strip(), det or language


@register
class GigaAMSTT(STTProvider):
    id = "gigaam"
    name = "Sber GigaAM v3 (Fast CTC)"
    local = True
    description = ("Ultra-fast offline Russian speech recognition using SberDevices GigaAM-v3 Conformer CTC "
                   "(sherpa-onnx INT8). 4-5x faster than Whisper on CPU.")
    requires = ["sherpa_onnx"]
    pip_hint = "pip install sherpa-onnx"
    fields = [
        Field("model_path", "Model file", "path", str(MODELS_DIR / "giga-am-v3" / "model.int8.onnx")),
        Field("tokens_path", "Tokens file", "path", str(MODELS_DIR / "giga-am-v3" / "tokens.txt")),
        Field("cpu_threads", "CPU threads", "int", 2, min=1, max=16, help="2 threads allocated for Zen 4"),
    ]
    has_downloads = True
    _recognizer = None
    _recognizer_key = None

    def _files(self):
        out = []
        for key in ("model_path", "tokens_path"):
            p = Path(self.s(key))
            if not p.is_file():
                out.append(p)
        return out

    def downloads_needed(self, langs):
        files = self._files()
        if not files:
            return []
        return [("Sber GigaAM v3 (sherpa-onnx)", 225_000_000)]

    def download(self, langs, progress=None, cancelled=lambda: False):
        from huggingface_hub import snapshot_download
        models_dir = Path(self.s("model_path")).parent
        models_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id="csukuangfj/sherpa-onnx-nemo-ctc-giga-am-v3-russian-2025-12-16",
            local_dir=str(models_dir),
            allow_patterns=["model.int8.onnx", "tokens.txt"]
        )

    def download_dir(self):
        return str(Path(self.s("model_path")).parent)

    def _load(self):
        import sherpa_onnx
        key = (str(self.s("model_path")), str(self.s("tokens_path")), int(self.s("cpu_threads", 2)))
        if self._recognizer is not None and self._recognizer_key == key:
            return self._recognizer
        mp = Path(self.s("model_path"))
        tp = Path(self.s("tokens_path"))
        if not mp.is_file() or not tp.is_file():
            self.download([])
        self._recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
            model=str(mp),
            tokens=str(tp),
            num_threads=int(self.s("cpu_threads", 2)),
            provider="cpu"
        )
        self._recognizer_key = key
        return self._recognizer

    def warmup(self):
        with self.lock:
            self._load()

    def transcribe(self, audio, language):
        with self.lock:
            rec = self._load()
            stream = rec.create_stream()
            stream.accept_waveform(SR, audio)
            rec.decode_stream(stream)
            text = stream.result.text.strip()
        return text, "ru"

