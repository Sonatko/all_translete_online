"""Provider framework.

Every engine (speech-to-text, translation, AI model, text-to-speech) is a
Provider subclass that declares its settings as a list of Field objects.
The GUI builds the settings form from those fields automatically, so adding a
new cloud API is: subclass, declare fields, implement one method, @register.
"""
from __future__ import annotations

import importlib.util
import re
import threading
from dataclasses import dataclass, field
from typing import Any

import requests

from ..config import app_path

REGISTRY: dict[str, dict[str, type["Provider"]]] = {"stt": {}, "translate": {}, "llm": {}, "tts": {}}


class ProviderError(Exception):
    pass


@dataclass
class Field:
    key: str
    label: str
    kind: str = "str"        # str | secret | int | float | bool | choice | combo (editable) | path | text
    default: Any = ""
    options: list = field(default_factory=list)
    help: str = ""
    min: float = 0
    max: float = 100000
    step: float = 1
    key_ref: str = ""        # for kind == "secret": id in the KeyStore (shared between providers)


def register(cls):
    REGISTRY[cls.kind][cls.id] = cls
    return cls


def providers(kind: str) -> dict[str, type["Provider"]]:
    return REGISTRY[kind]


class Provider:
    id = ""
    name = ""
    kind = ""
    local = False                 # runs on this PC (no internet / no key)
    description = ""
    requires: list[str] = []      # importable module names
    pip_hint = ""                 # what to pip install if requires are missing
    fields: list[Field] = []

    def __init__(self, settings: dict | None, keys):
        self.keys = keys
        self.settings = {f.key: f.default for f in self.fields}
        self.update_settings(settings or {})
        self.lock = threading.Lock()
        self.session = requests.Session()

    def update_settings(self, settings: dict) -> None:
        for k, v in settings.items():
            self.settings[k] = v
        for f in self.fields:
            if f.kind == "path":
                self.settings[f.key] = str(app_path(self.settings[f.key], f.default))

    # ---------------------------------------------------------------- helpers
    @classmethod
    def missing_requirements(cls) -> list[str]:
        return [m for m in cls.requires if importlib.util.find_spec(m) is None]

    @classmethod
    def label(cls) -> str:
        tag = " (local)" if cls.local else ""
        return f"{cls.name}{tag}"

    def s(self, key, default=None):
        v = self.settings.get(key, default)
        return default if v is None else v

    def key(self, field_key: str = "api_key") -> str:
        for f in self.fields:
            if f.key == field_key and f.kind == "secret":
                return self.keys.get(f.key_ref or f"{self.id}")
        return ""

    def need_key(self, field_key: str = "api_key") -> str:
        k = self.key(field_key)
        if not k:
            ref = next((f.key_ref for f in self.fields if f.key == field_key), self.id)
            raise ProviderError(f"{self.name}: missing API key '{ref}'. Add it in the API Keys tab.")
        return k

    def http(self, method: str, url: str, timeout: float = 30, **kw) -> requests.Response:
        try:
            r = self.session.request(method, url, timeout=timeout, **kw)
        except requests.RequestException as e:
            raise ProviderError(f"{self.name}: network error: {e}") from e
        if r.status_code >= 400:
            body = r.text
            if "<html" in body[:500].lower():   # don't dump whole HTML error pages
                m = re.search(r"<title>(.*?)</title>", body, re.I | re.S)
                body = m.group(1).strip() if m else "HTML error page"
            body = body[:300].replace("\n", " ")
            hint = {401: " (invalid API key?)", 403: " (no access / wrong region?)", 429: " (rate limited)"}
            raise ProviderError(f"{self.name}: HTTP {r.status_code}{hint.get(r.status_code, '')}: {body}")
        return r

    # ---------------------------------------------------------------- model files (local engines)
    has_downloads = False         # True: downloads_needed()/download() fetch model or voice files once

    def downloads_needed(self, langs: list[str]) -> list[tuple[str, int]]:
        """[(what, bytes)] still to download for these settings and languages - empty when ready."""
        return []

    def download(self, langs: list[str], progress=None, cancelled=lambda: False) -> None:
        """Fetch what downloads_needed() lists into the app folder. progress(done_bytes, total_bytes or 0)."""

    def download_dir(self) -> str:
        from ..config import MODELS_DIR
        return str(MODELS_DIR)

    def warmup(self) -> None:
        """Load models / open connections ahead of time (optional)."""

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass


def describe_downloads(need: list[tuple[str, int]]) -> str:
    """'Piper voice pt_PT-tugão-medium, Piper voice en_US-amy-medium (about 127 MB)'"""
    total = sum(size for _what, size in need)
    return ", ".join(what for what, _size in need) + (f" (about {total / 1e6:,.0f} MB)" if total else "")
