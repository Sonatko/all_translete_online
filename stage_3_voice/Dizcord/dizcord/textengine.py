"""Text-only part of the engine: translation providers + context, and language detection.

No audio imports, so it also runs without the audio libraries - the desktop Engine (engine.py) builds on top of it.
"""
from __future__ import annotations

import collections
import threading

from . import languages as L
from .providers import REGISTRY, ProviderError
from .providers.translate import TranslateContext


def detect_text_language(text: str) -> str | None:
    try:
        from langdetect import DetectorFactory, detect
        DetectorFactory.seed = 0
        if len(text) < 12:
            return None
        return L.normalize(detect(text))
    except Exception:
        return None


class TextEngine:
    def __init__(self, profile: dict, keys):
        self.profile = profile
        self.keys = keys
        self._providers: dict[tuple[str, str], object] = {}
        self._plock = threading.Lock()
        self.history = collections.deque(maxlen=50)

    def provider(self, kind: str):
        """Cached provider instance for the profile's current choice (settings refreshed in place)."""
        section = {"stt": "stt", "translate": "translation", "llm": "ai", "tts": "tts"}[kind]
        pid = self.profile[section]["provider"]
        cls = REGISTRY[kind].get(pid)
        if cls is None:
            raise ProviderError(f"Unknown {kind} provider '{pid}'")
        missing = cls.missing_requirements()
        if missing:
            raise ProviderError(f"{cls.name} needs extra packages: {cls.pip_hint or ', '.join(missing)} "
                                f"(run install_extras.bat)")
        settings = self.profile[section]["settings"].get(pid, {})
        with self._plock:
            inst = self._providers.get((kind, pid))
            if inst is None:
                inst = self._providers[(kind, pid)] = cls(settings, self.keys)
            else:
                inst.update_settings({f.key: settings[f.key] for f in cls.fields if f.key in settings})
        return inst

    def translate_context(self, direction: str) -> TranslateContext:
        tcfg = self.profile["translation"]
        n = int(tcfg.get("context_lines", 4))
        llm = None
        if tcfg["provider"] == "llm":
            llm = self.provider("llm")
        return TranslateContext(style=tcfg.get("style", "natural"), glossary=tcfg.get("glossary", ""),
                                keep_profanity=bool(tcfg.get("keep_profanity", True)),
                                history=list(self.history)[-n:] if n > 0 else [], llm=llm,
                                custom_prompt=self.profile["ai"].get("custom_prompt", ""))

    def add_history(self, speaker, original, translated):
        self.history.append((speaker, original, translated))
