"""
Local in-process Tencent HY-MT1.5-1.8B translation engine for LiveTranslate.
Executes quantized GGUF (Q4_K_M) inference on CPU via llama-cpp-python with
sub-400ms latency on modern AVX2/AVX-512 CPUs (e.g. AMD Ryzen Zen 4).
"""

import collections
import gc
import logging
import os
import threading
from typing import Optional

log = logging.getLogger("LiveTranslate.HYMT")

_cur_dir = os.path.dirname(os.path.abspath(__file__))

# ISO 639-1 code to English language display names expected by HY-MT prompt
HYMT_LANG_NAMES = {
    "ru": "Russian",
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "uk": "Ukrainian",
    "pl": "Polish",
    "tr": "Turkish",
    "ar": "Arabic",
    "hi": "Hindi",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "cs": "Czech",
    "ro": "Romanian",
    "el": "Greek",
    "hu": "Hungarian",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "he": "Hebrew",
}


def to_hymt_lang_name(code: str) -> str:
    """Map 2-letter language code to full English name for prompt instruction."""
    clean = str(code or "").strip().lower()
    return HYMT_LANG_NAMES.get(clean, clean.capitalize() or "Russian")


class LRUCache:
    """Thread-safe LRU cache with bounded capacity for instant 0ms translations."""

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

    def clear(self):
        with self.lock:
            self.cache.clear()


class LocalHYMTEngine:
    """Thread-safe singleton managing the Tencent HY-MT1.5-1.8B GGUF model."""

    _instance: Optional["LocalHYMTEngine"] = None
    _init_lock = threading.Lock()

    @classmethod
    def get_instance(cls, requested_variant: str = "auto") -> "LocalHYMTEngine":
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = LocalHYMTEngine(variant=requested_variant)
            return cls._instance

    @classmethod
    def get_candidate_paths(cls) -> list:
        target_filename = "HY-MT1.5-1.8B-Q4_K_M.gguf"
        return [
            os.path.join(_cur_dir, "..", "nllb_server", "models", "hy-mt1.5-1.8b-gguf", target_filename),
            os.path.join(_cur_dir, "models", "hy-mt1.5-1.8b-gguf", target_filename),
            os.path.join(_cur_dir, "..", "models", target_filename),
        ]

    @classmethod
    def is_cached(cls) -> bool:
        """Check if local GGUF weights exist on disk and are non-empty."""
        for p in cls.get_candidate_paths():
            resolved = os.path.abspath(p)
            if os.path.exists(resolved) and os.path.getsize(resolved) > 500 * 1024 * 1024:
                return True
        return False

    @classmethod
    def download_model(cls) -> str:
        """Download HY-MT 1.8B GGUF weights explicitly in background thread."""
        target_dir = os.path.abspath(os.path.join(_cur_dir, "..", "nllb_server", "models", "hy-mt1.5-1.8b-gguf"))
        os.makedirs(target_dir, exist_ok=True)
        target_filename = "HY-MT1.5-1.8B-Q4_K_M.gguf"
        repo_id = "tencent/HY-MT1.5-1.8B-GGUF"
        log.info(f"Downloading {target_filename} from {repo_id} to {target_dir}...")
        from huggingface_hub import hf_hub_download

        try:
            return hf_hub_download(
                repo_id=repo_id,
                filename=target_filename,
                local_dir=target_dir,
                local_dir_use_symlinks=False,
            )
        except Exception as e:
            log.warning(f"Direct HuggingFace download failed ({e}). Retrying via hf-mirror.com...")
            old_ep = os.environ.get("HF_ENDPOINT")
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            try:
                return hf_hub_download(
                    repo_id=repo_id,
                    filename=target_filename,
                    local_dir=target_dir,
                    local_dir_use_symlinks=False,
                )
            finally:
                if old_ep:
                    os.environ["HF_ENDPOINT"] = old_ep
                else:
                    os.environ.pop("HF_ENDPOINT", None)

    @classmethod
    def is_loaded(cls) -> bool:
        with cls._init_lock:
            return cls._instance is not None

    @classmethod
    def unload(cls):
        """Cleanly unload GGUF model and C++ context from RAM."""
        with cls._init_lock:
            if cls._instance is not None:
                log.info(f"Unloading {cls._instance.model_name} from memory...")
                try:
                    if hasattr(cls._instance, "llm"):
                        del cls._instance.llm
                    if hasattr(cls._instance, "cache"):
                        cls._instance.cache.clear()
                except Exception as e:
                    log.warning(f"Error while releasing HY-MT components: {e}")
                cls._instance = None
                gc.collect()
                log.info("LocalHYMTEngine unloaded successfully. RAM released.")

    def __init__(self, variant: str = "auto"):
        import llama_cpp

        self.cache = LRUCache(1000)
        self.variant = str(variant or "auto").lower()
        self.model_path = self._find_or_download_model()
        self.model_name = os.path.basename(self.model_path)

        log.info(f"Initializing Tencent HY-MT1.5-1.8B ({self.model_name}) via llama_cpp on CPU...")
        # Optimal CPU configuration:
        # - n_ctx=1024: compact context saves attention calculation latency
        # - n_threads=8: matches physical cores on Ryzen 7 7800X3D
        # - n_gpu_layers=0: pure CPU execution
        self.llm = llama_cpp.Llama(
            model_path=self.model_path,
            n_ctx=1024,
            n_threads=8,
            n_gpu_layers=0,
            verbose=False,
        )
        self.translate_lock = threading.Lock()

        # Warmup forward pass once to eliminate first-sentence cold start
        try:
            log.info("Warming up HY-MT forward pass (0ms user cold start)...")
            self._infer("Hello", target_lang_name="Russian")
            log.info("HY-MT warmup completed successfully!")
        except Exception as we:
            log.debug(f"HY-MT warmup notice: {we}")

    def _find_or_download_model(self) -> str:
        """Find local GGUF weights or perform on-demand download from HuggingFace."""
        target_filename = "HY-MT1.5-1.8B-Q4_K_M.gguf"
        candidates = [
            os.path.join(_cur_dir, "..", "nllb_server", "models", "hy-mt1.5-1.8b-gguf", target_filename),
            os.path.join(_cur_dir, "models", "hy-mt1.5-1.8b-gguf", target_filename),
            os.path.join(_cur_dir, "..", "models", target_filename),
        ]
        for p in candidates:
            resolved = os.path.abspath(p)
            if os.path.exists(resolved) and os.path.getsize(resolved) > 500 * 1024 * 1024:
                log.info(f"Found existing HY-MT GGUF model at: {resolved}")
                return resolved

        # On-Demand Auto-Download: download official Tencent GGUF Q4_K_M if missing
        target_dir = os.path.abspath(os.path.join(_cur_dir, "..", "nllb_server", "models", "hy-mt1.5-1.8b-gguf"))
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, target_filename)

        repo_id = "tencent/HY-MT1.5-1.8B-GGUF"
        log.info(f"HY-MT GGUF model missing locally. Auto-downloading {target_filename} on-demand to {target_dir}...")

        try:
            from huggingface_hub import hf_hub_download

            try:
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=target_filename,
                    local_dir=target_dir,
                    local_dir_use_symlinks=False,
                )
            except Exception as e:
                log.warning(f"Direct HuggingFace download failed ({e}). Retrying via hf-mirror.com...")
                old_endpoint = os.environ.get("HF_ENDPOINT")
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                try:
                    downloaded_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=target_filename,
                        local_dir=target_dir,
                        local_dir_use_symlinks=False,
                    )
                finally:
                    if old_endpoint:
                        os.environ["HF_ENDPOINT"] = old_endpoint
                    else:
                        os.environ.pop("HF_ENDPOINT", None)
            return downloaded_path
        except Exception as err:
            raise FileNotFoundError(f"Failed to auto-download HY-MT GGUF model: {err}")

    def _infer(self, text: str, target_lang_name: str) -> str:
        """Internal LLM inference with official Tencent translation prompt format."""
        prompt = f"Translate the following segment into {target_lang_name}, without additional explanation:\n\n{text}"
        response = self.llm.create_completion(
            prompt=prompt,
            max_tokens=64,
            temperature=0.1,  # Low temperature prevents hallucination & language drift
            stop=["\n", "</s>", "<|endoftext|>"],
            echo=False,
        )
        raw_text = response["choices"][0]["text"].strip()
        # Clean potential quotation marks
        if raw_text.startswith('"') and raw_text.endswith('"') and len(raw_text) > 2:
            raw_text = raw_text[1:-1].strip()
        return raw_text

    def translate(self, text: str, target_language: str = "ru", source_language: Optional[str] = None) -> str:
        """Translate source text into target language with caching and safety checks."""
        clean = (text or "").strip()
        if not clean:
            return ""

        tgt_clean = str(target_language or "ru").strip().lower()
        src_clean = str(source_language or "").strip().lower()

        # Same-language fast path: 0ms delay, no LLM inference needed
        if src_clean and src_clean == tgt_clean:
            return clean

        target_lang_name = to_hymt_lang_name(tgt_clean)

        cache_key = f"{src_clean}:{tgt_clean}:{clean}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        with self.translate_lock:
            translated = self._infer(clean, target_lang_name=target_lang_name)

        self.cache.put(cache_key, translated)
        return translated
