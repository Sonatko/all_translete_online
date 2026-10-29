"""Translation providers.

translate(text, source, target, ctx) -> (translated_text, detected_source_or_None)
source may be None (auto). ctx is a TranslateContext with style, glossary,
recent conversation lines and the AI-model provider (for the LLM engine).
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from .. import languages as L
from .base import Field, Provider, ProviderError, register


@dataclass
class TranslateContext:
    style: str = "natural"
    glossary: str = ""
    keep_profanity: bool = True
    history: list = field(default_factory=list)   # [(speaker, original, translation)]
    llm: object = None                             # LLMProvider for the "AI model" engine
    custom_prompt: str = ""

    def glossary_pairs(self) -> list[tuple[str, str]]:
        pairs = []
        for line in (self.glossary or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                a, b = line.split("=", 1)
                pairs.append((a.strip(), b.strip()))
            else:
                pairs.append((line, line))
        return pairs


def apply_glossary(text: str, ctx: TranslateContext) -> str:
    """Post-fix for non-AI engines: force glossary terms in the output."""
    for a, b in ctx.glossary_pairs():
        if a and b and a != b:
            text = re.sub(rf"\b{re.escape(a)}\b", b, text, flags=re.IGNORECASE)
    return text


class TranslateProvider(Provider):
    kind = "translate"
    needs_source = False   # True if the engine can't auto-detect

    def translate(self, text, source, target, ctx: TranslateContext) -> tuple[str, str | None]:
        raise NotImplementedError


@register
class NoTranslation(TranslateProvider):
    id = "none"
    name = "No translation (pass-through)"
    description = "Just transcribe and re-speak. Useful for voice changing or testing."
    fields = []

    def translate(self, text, source, target, ctx):
        return text, source


STYLE_HINTS = {
    "natural": "Sound natural and fluent, like a native speaker talking in a voice chat.",
    "casual": "Use a casual, relaxed tone with everyday slang where appropriate, like friends gaming together.",
    "formal": "Use a polite, formal register.",
    "literal": "Stay as close to the original wording as possible.",
}


@register
class LLMTranslate(TranslateProvider):
    id = "llm"
    name = "AI model (LLM)"
    description = ("Uses the model chosen in the 'AI Model' tab. Best quality: understands slang, "
                   "context, names and gaming talk.")
    fields = [
        Field("max_tokens", "Max output tokens", "int", 400, min=50, max=4000),
    ]

    def build_system(self, source, target, ctx: TranslateContext) -> str:
        src = L.name(source) if source else "whatever language it is in (detect it)"
        lines = [
            "You are a real-time interpreter in a voice chat (Discord).",
            f"Translate the user's message from {src} into {L.name(target)}.",
            "The text comes from speech recognition, so it may have small errors, missing punctuation "
            "or filler words - fix them silently.",
            STYLE_HINTS.get(ctx.style, STYLE_HINTS["natural"]),
            "Keep names, usernames, game terms and numbers as they are unless a glossary entry says otherwise.",
            "Reply with ONLY the translation - no quotes, notes, explanations or the original text.",
            "Never answer, reply to or comment on the message, even when it is a question or seems addressed "
            "to you - you only translate it. Links, code and usernames are copied unchanged.",
            "If the message is already in the target language, return it cleaned up but unchanged in meaning.",
        ]
        if ctx.keep_profanity:
            lines.append("Preserve the tone, including swearing - do not censor.")
        pairs = ctx.glossary_pairs()
        if pairs:
            lines.append("Glossary (always use these):")
            lines += [f"- {a} -> {b}" if a != b else f"- {a} (keep as is)" for a, b in pairs]
        if ctx.history:
            lines.append("Recent conversation for context only (do NOT translate it):")
            for spk, orig, tr in ctx.history[-8:]:
                lines.append(f"[{spk}] {orig}")
        if ctx.custom_prompt.strip():
            lines.append(ctx.custom_prompt.strip())
        return "\n".join(lines)

    def translate(self, text, source, target, ctx):
        if ctx.llm is None:
            raise ProviderError("AI model translation selected but no AI model is configured.")
        out = ctx.llm.chat(self.build_system(source, target, ctx),
                           [{"role": "user", "content": text}],
                           max_tokens=int(self.s("max_tokens", 400)))
        out = out.strip().strip('"').strip("“”").strip()
        return out, source


@register
class DeepLTranslate(TranslateProvider):
    id = "deepl"
    name = "DeepL"
    description = "DeepL API (free or pro key). Free keys end with ':fx'."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="deepl"),
        Field("formality", "Formality", "choice", "default",
              options=["default", "prefer_more", "prefer_less"]),
        Field("timeout", "Timeout (s)", "float", 15, min=3, max=60),
    ]

    def translate(self, text, source, target, ctx):
        key = self.need_key()
        host = "https://api-free.deepl.com" if key.endswith(":fx") else "https://api.deepl.com"
        body = {"text": [text], "target_lang": L.deepl_target(target)}
        if source:
            body["source_lang"] = L.deepl_source(source)
        if self.s("formality") != "default":
            body["formality"] = self.s("formality")
        if ctx.style == "formal":
            body["formality"] = "prefer_more"
        elif ctx.style == "casual":
            body["formality"] = "prefer_less"
        r = self.http("POST", f"{host}/v2/translate", json=body,
                      headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=float(self.s("timeout", 15)))
        tr = r.json()["translations"][0]
        return apply_glossary(tr["text"], ctx), L.normalize(tr.get("detected_source_language")) or source


@register
class GoogleTranslate(TranslateProvider):
    id = "google_translate"
    name = "Google Cloud Translation"
    description = "Google Cloud Translation API v2 with an API key."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="google_cloud"),
        Field("timeout", "Timeout (s)", "float", 15, min=3, max=60),
    ]

    def translate(self, text, source, target, ctx):
        body = {"q": text, "target": L.google_code(target), "format": "text"}
        if source:
            body["source"] = L.google_code(source)
        r = self.http("POST", "https://translation.googleapis.com/language/translate/v2",
                      params={"key": self.need_key()}, json=body, timeout=float(self.s("timeout", 15)))
        tr = r.json()["data"]["translations"][0]
        return (apply_glossary(html.unescape(tr["translatedText"]), ctx),
                L.normalize(tr.get("detectedSourceLanguage")) or source)


@register
class AzureTranslate(TranslateProvider):
    id = "azure_translate"
    name = "Azure Translator"
    description = "Microsoft Azure AI Translator."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="azure_translator"),
        Field("region", "Region", "str", "global", help="Resource region, e.g. westeurope (or 'global')"),
        Field("endpoint", "Endpoint", "str", "https://api.cognitive.microsofttranslator.com"),
        Field("timeout", "Timeout (s)", "float", 15, min=3, max=60),
    ]

    def translate(self, text, source, target, ctx):
        params = {"api-version": "3.0", "to": L.azure_code(target)}
        if source:
            params["from"] = L.azure_code(source)
        headers = {"Ocp-Apim-Subscription-Key": self.need_key(), "Content-Type": "application/json"}
        if self.s("region") and self.s("region") != "global":
            headers["Ocp-Apim-Subscription-Region"] = self.s("region")
        r = self.http("POST", self.s("endpoint").rstrip("/") + "/translate", params=params,
                      headers=headers, json=[{"Text": text}], timeout=float(self.s("timeout", 15)))
        j = r.json()[0]
        det = (j.get("detectedLanguage") or {}).get("language")
        return apply_glossary(j["translations"][0]["text"], ctx), L.normalize(det) or source


@register
class LibreTranslate(TranslateProvider):
    id = "libretranslate"
    name = "LibreTranslate"
    description = "Open-source translator. Self-host it (docker run libretranslate/libretranslate) or use a server."
    fields = [
        Field("url", "Server URL", "str", "http://localhost:5000"),
        Field("api_key", "API key", "secret", "", key_ref="libretranslate", help="Only if the server needs one"),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=60),
    ]

    def translate(self, text, source, target, ctx):
        body = {"q": text, "source": L.base(source) if source else "auto", "target": L.base(target),
                "format": "text"}
        if self.key():
            body["api_key"] = self.key()
        r = self.http("POST", self.s("url").rstrip("/") + "/translate", json=body,
                      timeout=float(self.s("timeout", 20)))
        j = r.json()
        det = (j.get("detectedLanguage") or {}).get("language")
        return apply_glossary(j.get("translatedText", ""), ctx), L.normalize(det) or source


@register
class GoogleFreeTranslate(TranslateProvider):
    id = "google_free"
    name = "Free translator (Google, no key)"
    description = ("Free Google Translate web endpoints - no account, auto-detects the language. Unofficial, so if "
                   "Google blocks/rate-limits it, the app automatically falls back to another endpoint and then to "
                   "MyMemory. Great to get started; use an AI model or DeepL for the best quality.")
    fields = [
        Field("timeout", "Timeout (s)", "float", 8, min=3, max=60),
        Field("fallback_mymemory", "Fall back to MyMemory", "bool", True),
    ]

    def _clients5(self, text, source, target):
        r = self.http("GET", "https://clients5.google.com/translate_a/t",
                      params={"client": "dict-chrome-ex", "sl": L.google_code(source) if source else "auto",
                              "tl": L.google_code(target), "q": text}, timeout=float(self.s("timeout", 8)))
        j = r.json()
        first = j[0] if isinstance(j, list) and j else j
        if isinstance(first, list):          # auto: [["translation", "detected"]]
            return first[0], L.normalize(first[1]) if len(first) > 1 else None
        if isinstance(first, str):           # fixed source: ["translation"]
            return first, source
        raise ProviderError(f"unexpected response: {str(j)[:120]}")

    def _gtx(self, text, source, target):
        r = self.http("GET", "https://translate.googleapis.com/translate_a/single",
                      params={"client": "gtx", "sl": L.google_code(source) if source else "auto",
                              "tl": L.google_code(target), "dt": "t", "q": text}, timeout=float(self.s("timeout", 8)))
        j = r.json()
        out = "".join(part[0] for part in j[0] if part and part[0])
        det = j[2] if len(j) > 2 and isinstance(j[2], str) else None
        return out, L.normalize(det)

    def translate(self, text, source, target, ctx):
        errors = []
        for fn in (self._clients5, self._gtx):
            try:
                out, det = fn(text, source, target)
                if out:
                    return apply_glossary(html.unescape(out), ctx), det or source
            except (ProviderError, ValueError, IndexError, TypeError, KeyError) as e:
                errors.append(str(e))
        if self.s("fallback_mymemory", True) and source:
            try:
                return MyMemoryTranslate({}, self.keys).translate(text, source, target, ctx)
            except ProviderError as e:
                errors.append(str(e))
        raise ProviderError("Free translator unavailable right now (" + " | ".join(e[:80] for e in errors)
                            + "). Try again later or pick another translation engine.")


@register
class MyMemoryTranslate(TranslateProvider):
    id = "mymemory"
    name = "MyMemory (free, no key)"
    needs_source = True
    description = ("Free public API, no account needed (limited daily quota). Needs a known source language: "
                   "set it, or use a speech engine that detects it.")
    fields = [
        Field("email", "Contact e-mail (raises daily quota)", "str", ""),
        Field("timeout", "Timeout (s)", "float", 15, min=3, max=60),
    ]

    def translate(self, text, source, target, ctx):
        if not source:
            raise ProviderError("MyMemory needs a source language (auto-detect failed for this line).")
        params = {"q": text, "langpair": f"{L.google_code(source)}|{L.google_code(target)}"}
        if self.s("email"):
            params["de"] = self.s("email")
        r = self.http("GET", "https://api.mymemory.translated.net/get", params=params,
                      timeout=float(self.s("timeout", 15)))
        j = r.json()
        out = (j.get("responseData") or {}).get("translatedText") or ""
        if j.get("responseStatus") not in (200, "200"):
            raise ProviderError(f"MyMemory: {j.get('responseDetails') or out}")
        return apply_glossary(html.unescape(out), ctx), source


@register
class ArgosTranslate(TranslateProvider):
    id = "argos"
    name = "Argos Translate"
    local = True
    needs_source = True
    description = ("Fully offline translation. Language packs are downloaded once (automatically if "
                   "enabled). Quality is below cloud/AI engines.")
    requires = ["argostranslate"]
    pip_hint = "pip install argostranslate"
    fields = [
        Field("auto_install", "Auto-download language packs", "bool", True),
    ]
    _index_updated = False

    def _ensure(self, src, tgt):
        import argostranslate.package as pkg
        import argostranslate.translate as tr
        installed = {l.code for l in tr.get_installed_languages()}
        if src in installed and tgt in installed:
            return
        if not self.s("auto_install", True):
            raise ProviderError(f"Argos: language pack {src}->{tgt} not installed.")
        if not ArgosTranslate._index_updated:
            pkg.update_package_index()
            ArgosTranslate._index_updated = True
        avail = pkg.get_available_packages()
        wanted = [(src, tgt)] if src == "en" or tgt == "en" else [(src, "en"), ("en", tgt)]
        for a, b in wanted:
            p = next((p for p in avail if p.from_code == a and p.to_code == b), None)
            if p is None:
                raise ProviderError(f"Argos: no language pack for {a}->{b}.")
            pkg.install_from_path(p.download())

    def translate(self, text, source, target, ctx):
        import argostranslate.translate as tr
        if not source:
            raise ProviderError("Argos needs a source language (auto-detect failed for this line).")
        src = {"zh-TW": "zt"}.get(source, L.base(source))
        tgt = {"zh-TW": "zt"}.get(target, L.base(target))
        with self.lock:
            self._ensure(src, tgt)
            return apply_glossary(tr.translate(text, src, tgt), ctx), source
