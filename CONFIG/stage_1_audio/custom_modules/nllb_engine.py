"""
Local in-process NLLB-200 translation engine for LiveTranslate.
Eliminates external server.py and port 8080 dependencies by executing
CTranslate2 INT8 inference directly in-process with LRU caching.
"""

import collections
import ctypes
import logging
import os
import sys
import threading
from typing import Optional

log = logging.getLogger("LiveTranslate.NLLB")

# Preload CUDA 12 runtime DLLs from torch/lib if available so CTranslate2 runs on modern GPUs
_cur_dir = os.path.dirname(os.path.abspath(__file__))
_torch_lib = os.path.abspath(os.path.join(_cur_dir, ".venv", "Lib", "site-packages", "torch", "lib"))
if os.path.exists(_torch_lib):
    os.environ["PATH"] = _torch_lib + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(_torch_lib)
        except Exception:
            pass
    for _dll in ("cublasLt64_12.dll", "cublas64_12.dll"):
        _p = os.path.join(_torch_lib, _dll)
        if os.path.exists(_p):
            try:
                ctypes.CDLL(_p)
            except Exception:
                pass

# ISO 639-1 to NLLB Flores-200 language code mapping
NLLB_LANG_MAP = {
    "ru": "rus_Cyrl",
    "en": "eng_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "de": "deu_Latn",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "uk": "ukr_Cyrl",
    "pl": "pol_Latn",
    "tr": "tur_Latn",
    "ar": "ara_Arab",
    "hi": "hin_Deva",
    "vi": "vie_Latn",
}


def to_nllb_lang(code: str) -> str:
    """Map common 2-letter language code to Flores-200 format."""
    clean = str(code or "").strip().lower()
    return NLLB_LANG_MAP.get(clean, clean if "_" in clean else "rus_Cyrl")


def detect_src_lang(text: str) -> str:
    """Fast rule-based language detection for NLLB."""
    # Check for Chinese (Hanzi)
    if any("\u4e00" <= c <= "\u9fff" for c in text):
        return "zho_Hans"
    # Check for Japanese (Hiragana / Katakana)
    if any("\u3040" <= c <= "\u30ff" for c in text):
        return "jpn_Jpan"
    # Check for Korean (Hangul)
    if any("\uac00" <= c <= "\ud7af" for c in text):
        return "kor_Hang"
    # Check if purely Russian / Cyrillic
    if any("\u0400" <= c <= "\u04ff" for c in text) and not any("a" <= c.lower() <= "z" for c in text):
        return "rus_Cyrl"
    return "eng_Latn"


class LRUCache:
    """Thread-safe LRU cache with bounded size."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = collections.OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: str):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)


class LocalNLLBEngine:
    """Thread-safe singleton managing the CTranslate2 NLLB model in-process."""

    _instance: Optional["LocalNLLBEngine"] = None
    _init_lock = threading.Lock()

    @classmethod
    def get_instance(cls, requested_variant: str = "auto") -> "LocalNLLBEngine":
        with cls._init_lock:
            req_str = str(requested_variant or "").lower()
            if cls._instance is not None and requested_variant != "auto":
                cur_is_600m = "600m" in cls._instance.model_name.lower()
                req_is_600m = "600m" in req_str
                if cur_is_600m != req_is_600m:
                    log.info(f"Model variant switch requested: {cls._instance.model_name} -> {requested_variant}")
                    cls.unload()
            if cls._instance is None:
                cls._instance = LocalNLLBEngine(variant=requested_variant)
            return cls._instance

    @classmethod
    def unload(cls):
        """Cleanly unload model from RAM and release GPU/CPU memory."""
        with cls._init_lock:
            if cls._instance is not None:
                log.info(f"Unloading {cls._instance.model_name} from memory...")
                try:
                    if hasattr(cls._instance, "translator"):
                        del cls._instance.translator
                    if hasattr(cls._instance, "tokenizer"):
                        del cls._instance.tokenizer
                    if hasattr(cls._instance, "cache"):
                        cls._instance.cache.cache.clear()
                except Exception as e:
                    log.warning(f"Error while releasing NLLB components: {e}")
                cls._instance = None
                import gc
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                log.info("LocalNLLBEngine unloaded successfully. RAM released.")

    @classmethod
    def get_candidate_dirs(cls, variant: str = "auto") -> list:
        is_600m = "600m" in str(variant).lower()
        if is_600m:
            return [
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-600m-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-600m-int8"),
                os.path.join(_cur_dir, "..", "models", "nllb-200-600m-int8"),
            ]
        else:
            return [
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-1.3b-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-1.3b-int8"),
                os.path.join(_cur_dir, "..", "models", "nllb-200-1.3b-int8"),
            ]

    @classmethod
    def is_cached(cls, variant: str = "auto") -> bool:
        """Check if local NLLB weights exist without loading or network access."""
        for p in cls.get_candidate_dirs(variant):
            resolved = os.path.abspath(p)
            if os.path.exists(resolved) and os.path.exists(os.path.join(resolved, "model.bin")):
                return True
        return False

    @classmethod
    def download_model(cls, variant: str = "600m") -> str:
        """Download requested NLLB model variant explicitly in background thread."""
        is_600m = "600m" in str(variant).lower()
        sub = "nllb-200-600m-int8" if is_600m else "nllb-200-1.3b-int8"
        repo_id = (
            "haoranxu/nllb-200-600M-ctranslate2-int8"
            if is_600m
            else "haoranxu/nllb-200-1.3B-ctranslate2-int8"
        )
        target_dir = os.path.abspath(os.path.join(_cur_dir, "..", "nllb_server", "models", sub))
        os.makedirs(target_dir, exist_ok=True)
        log.info(f"Downloading NLLB {variant} ({repo_id}) to {target_dir}...")
        from huggingface_hub import snapshot_download

        try:
            return snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
        except Exception as e:
            log.warning(f"Direct HF download failed ({e}), trying mirror...")
            old_ep = os.environ.get("HF_ENDPOINT")
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            try:
                return snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
            finally:
                if old_ep:
                    os.environ["HF_ENDPOINT"] = old_ep
                else:
                    os.environ.pop("HF_ENDPOINT", None)

    def __init__(self, variant: str = "auto"):
        import ctranslate2
        import transformers

        self.cache = LRUCache(1000)
        self.variant = str(variant or "auto").lower()
        self.model_dir = self._find_model_dir(self.variant)
        self.model_name = os.path.basename(self.model_dir)

        # Attempt CUDA first with INT8_FLOAT16; fallback gracefully to CPU INT8
        try:
            log.info(f"Loading {self.model_name} (int8) in-process on CUDA...")
            self.translator = ctranslate2.Translator(
                self.model_dir,
                device="cuda",
                device_index=0,
                compute_type="int8_float16",
                inter_threads=1,
                intra_threads=4,
            )
            log.info(f"{self.model_name} loaded and ready in-process on CUDA!")
        except Exception as e:
            log.warning(f"CUDA initialization failed ({e}). Falling back to CPU...")
            self.translator = ctranslate2.Translator(
                self.model_dir,
                device="cpu",
                compute_type="int8",
                inter_threads=2,
                intra_threads=4,
            )
            log.info(f"{self.model_name} loaded and ready in-process on CPU!")

        self.tokenizer = transformers.NllbTokenizer.from_pretrained(
            self.model_dir, src_lang="eng_Latn", local_files_only=True
        )
        self.translate_lock = threading.Lock()

        # Warmup kernels once so first user translation has 0ms cold start
        try:
            w_toks = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode("warmup"))
            self.translator.translate_batch([w_toks], target_prefix=[["rus_Cyrl"]], beam_size=1, max_decoding_length=8)
            log.info(f"{self.model_name} warmup completed (0ms user cold start)!")
        except Exception as we:
            log.debug(f"Warmup notice: {we}")

    def _find_model_dir(self, variant: str = "auto") -> str:
        is_600m = "600m" in str(variant).lower()
        if is_600m:
            candidates = [
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-600m-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-600m-int8"),
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-1.3b-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-1.3b-int8"),
            ]
        else:
            candidates = [
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-1.3b-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-1.3b-int8"),
                os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-600m-int8"),
                os.path.join(_cur_dir, "models", "nllb-200-600m-int8"),
            ]
        for p in candidates:
            resolved = os.path.abspath(p)
            if os.path.exists(resolved) and os.path.exists(os.path.join(resolved, "model.bin")):
                return resolved

        # On-Demand Auto-Download: download Meta NLLB-200 1.3B INT8 automatically if missing!
        target_dir = os.path.abspath(os.path.join(_cur_dir, "..", "nllb_server", "models", "nllb-200-1.3b-int8"))
        os.makedirs(target_dir, exist_ok=True)
        log.info(f"NLLB-200 model weights missing locally. Auto-downloading 1.3B INT8 on-demand to {target_dir}...")
        repo_id = "haoranxu/nllb-200-1.3B-ctranslate2-int8"
        try:
            from huggingface_hub import snapshot_download

            try:
                snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
            except Exception as e:
                log.warning(f"Direct HuggingFace download failed ({e}). Retrying via hf-mirror.com...")
                old_endpoint = os.environ.get("HF_ENDPOINT")
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                try:
                    snapshot_download(repo_id=repo_id, local_dir=target_dir, local_dir_use_symlinks=False)
                finally:
                    if old_endpoint:
                        os.environ["HF_ENDPOINT"] = old_endpoint
                    else:
                        os.environ.pop("HF_ENDPOINT", None)
            return target_dir
        except Exception as err:
            raise FileNotFoundError(f"Failed to auto-download NLLB model: {err}")

    def translate(self, text: str, target_language: str = "ru", source_language: Optional[str] = None) -> str:
        clean = (text or "").strip()
        if not clean:
            return ""

        tgt_code = to_nllb_lang(target_language)
        src_code = to_nllb_lang(source_language) if source_language else detect_src_lang(clean)

        if src_code == tgt_code:
            return clean

        cache_key = f"{src_code}:{tgt_code}:{clean}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        with self.translate_lock:
            self.tokenizer.src_lang = src_code
            tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(clean))
            res = self.translator.translate_batch(
                [tokens],
                target_prefix=[[tgt_code]],
                beam_size=1,
                length_penalty=1.0,
                repetition_penalty=1.1,
                max_decoding_length=64,
            )
            tgt = res[0].hypotheses[0]
            if tgt and tgt[0] == tgt_code:
                tgt = tgt[1:]
            translated = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(tgt))

        self.cache.put(cache_key, translated)
        return translated
