"""AI model (LLM) providers used by the "AI model" translation engine.

Most cloud LLM APIs speak the OpenAI chat-completions dialect, so one generic
class + a table of presets covers OpenAI, Groq, OpenRouter, Together, Mistral,
DeepSeek, xAI, Fireworks, Cerebras, Gemini, Ollama, LM Studio, vLLM...
Anthropic (Claude) uses its official SDK.
"""
from __future__ import annotations

import json
import re

from . import models_info
from .base import Field, Provider, ProviderError, register
from .models_info import ModelInfo

# Model ids that are not chat models (embeddings, speech, images, moderation…).
_NOT_CHAT = re.compile(r"embed|whisper|tts|dall-e|image|moderation|transcribe|audio|realtime|search-preview|"
                       r"davinci|babbage|sora|computer-use|guard|rerank|speech|^text-|ocr|orpheus|playai", re.I)


def _per_million(v) -> float | None:
    try:
        return float(v) * 1_000_000
    except (TypeError, ValueError):
        return None


class LLMProvider(Provider):
    kind = "llm"
    limits_note = ""     # shown under the model box when no limits have been seen yet

    def chat(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        raise NotImplementedError

    def list_models(self) -> list[ModelInfo]:
        """Models available with the current key/server (free/paid, price and context when the API says)."""
        raise ProviderError(f"{self.name}: listing models is not supported")

    def check_limits(self) -> None:
        """Send one tiny request so the rate-limit headers get recorded for the selected model."""
        self.chat("Reply with the single word OK.", [{"role": "user", "content": "OK"}], max_tokens=5)


class OpenAICompatLLM(LLMProvider):
    base_url = ""
    default_model = ""
    model_options: list[str] = []
    key_ref = "custom_llm"
    key_optional = False

    @classmethod
    def build_fields(cls):
        return [
            Field("base_url", "Base URL", "str", cls.base_url, help="OpenAI-compatible endpoint (…/v1)"),
            Field("api_key", "API key", "secret", "", key_ref=cls.key_ref,
                  help="Optional for local servers" if cls.key_optional else ""),
            Field("model", "Model", "model", cls.default_model, options=cls.model_options),
            Field("temperature", "Temperature", "float", 0.2, min=-1, max=2, step=0.1,
                  help="-1 = don't send (needed for some reasoning models)"),
            Field("timeout", "Timeout (s)", "float", 30, min=3, max=300),
            Field("auth_style", "Auth header", "choice", "bearer", options=["bearer", "api-key", "none"]),
            Field("extra_body", "Extra JSON body", "text", "",
                  help='Merged into every request, e.g. {"reasoning_effort": "minimal"}'),
        ]

    def chat(self, system, messages, max_tokens=1024):
        url = self.s("base_url").rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        key = self.key()
        if not key and not self.key_optional and self.s("auth_style") != "none":
            self.need_key()
        if key:
            if self.s("auth_style") == "api-key":
                headers["api-key"] = key
            elif self.s("auth_style") == "bearer":
                headers["Authorization"] = f"Bearer {key}"
        body = {
            "model": self.s("model"),
            "messages": [{"role": "system", "content": system}] + messages,
        }
        if "api.openai.com" in url:
            body["max_completion_tokens"] = max_tokens
        else:
            body["max_tokens"] = max_tokens
        temp = float(self.s("temperature", 0.2))
        if temp >= 0:
            body["temperature"] = temp
        extra = (self.s("extra_body") or "").strip()
        if extra:
            try:
                body.update(json.loads(extra))
            except json.JSONDecodeError as e:
                raise ProviderError(f"{self.name}: 'Extra JSON body' is not valid JSON: {e}")
        try:
            r = self.http("POST", url, json=body, headers=headers, timeout=float(self.s("timeout", 30)))
        except ProviderError as e:
            # Some reasoning models reject temperature - retry once without it.
            if "temperature" in str(e) and "temperature" in body:
                body.pop("temperature")
                r = self.http("POST", url, json=body, headers=headers, timeout=float(self.s("timeout", 30)))
            else:
                if re.search(r"blocked at the organi[sz]ation|model_permission_blocked", str(e)):
                    models_info.set_blocked(self.id, self.s("model"),
                                            "blocked in your organization's settings on this service")
                raise
        models_info.set_blocked(self.id, self.s("model"), None)
        models_info.record_headers(self.id, self.s("model"), r.headers)
        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError(f"{self.name}: unexpected response: {str(data)[:300]}")
        if isinstance(content, list):  # some servers return content parts
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return (content or "").strip()

    # ------------------------------------------------------------------ model list
    list_needs_key = True     # False when the provider's model list is public

    def _headers(self, listing: bool = False) -> dict:
        key = self.key()
        if not key:
            if not self.key_optional and self.s("auth_style") != "none" and not (listing and not self.list_needs_key):
                self.need_key()
            return {}
        return {"api-key": key} if self.s("auth_style") == "api-key" else {"Authorization": f"Bearer {key}"}

    def list_models(self) -> list[ModelInfo]:
        url = self.s("base_url").rstrip("/") + "/models"
        data = self.http("GET", url, headers=self._headers(listing=True), timeout=20).json()
        rows = data.get("data", data.get("models", [])) if isinstance(data, dict) else data
        out = []
        for m in rows or []:
            if not isinstance(m, dict) or not m.get("id"):
                continue
            mid = m["id"]
            caps = m.get("capabilities")
            if _NOT_CHAT.search(mid) or (isinstance(caps, dict) and caps.get("completion_chat") is False):
                continue
            if m.get("active") is False:
                continue
            info = ModelInfo(id=mid, name=m.get("name") or m.get("display_name") or "",
                             context=m.get("context_length") or m.get("context_window")
                             or m.get("max_context_length"),
                             max_output=m.get("max_completion_tokens")
                             or (m.get("top_provider") or {}).get("max_completion_tokens"))
            self._classify(info, m)
            out.append(info)
        out.sort(key=lambda i: (i.free not in ("free", "local", "free tier"), i.id.lower()))
        return out

    def _classify(self, info: ModelInfo, raw: dict) -> None:
        """Free or paid - from the price when the API gives one, otherwise from what we know of the service."""
        price = raw.get("pricing")
        if isinstance(price, dict) and ("prompt" in price or "input" in price):
            if "prompt" in price:   # OpenRouter: USD per token, as strings
                pin, pout = _per_million(price.get("prompt")), _per_million(price.get("completion"))
            else:                   # Together: USD per 1M tokens
                pin, pout = price.get("input"), price.get("output")
            if pin is not None and float(pin) >= 0:
                info.price_in, info.price_out = float(pin), float(pout or 0)
                if not info.price_in and not info.price_out:
                    info.free = "free"
                else:   # on free-plan services the price only applies after upgrading
                    info.free = "free tier" if self.free_kind(info.id) == "free tier" else "paid"
                return
        info.free = self.free_kind(info.id)

    def free_kind(self, model_id: str) -> str:
        if self.local:
            return "local"
        return "" if self.id == "custom_openai" else "paid"


class _FreeTierLLM(OpenAICompatLLM):
    """Services whose models can all be used on a free plan (with rate limits)."""

    def free_kind(self, model_id):
        return "free tier"


class _GeminiLLM(OpenAICompatLLM):
    limits_note = ("Free tier: Flash, Flash-Lite and Gemma models, with per-minute and per-day limits that "
                   "depend on the model. Pro models need billing.")

    def free_kind(self, model_id):
        return "free tier" if re.search(r"flash|gemma", model_id, re.I) else "paid"

    def list_models(self):
        # Native endpoint: it also gives the token limits (the OpenAI-compatible one only lists ids).
        key = self.need_key()
        r = self.http("GET", "https://generativelanguage.googleapis.com/v1beta/models",
                      params={"key": key, "pageSize": 1000}, timeout=20)
        out = []
        for m in r.json().get("models", []):
            if "generateContent" not in (m.get("supportedGenerationMethods") or []):
                continue
            mid = m.get("name", "").removeprefix("models/")
            if not mid or _NOT_CHAT.search(mid):
                continue
            out.append(ModelInfo(id=mid, name=m.get("displayName", ""), context=m.get("inputTokenLimit"),
                                 max_output=m.get("outputTokenLimit"), free=self.free_kind(mid)))
        out.sort(key=lambda i: (i.free != "free tier", i.id))
        return out


class _OpenRouterLLM(OpenAICompatLLM):
    list_needs_key = False
    limits_note = ("Free (:free) models: 20 requests/min and 50 requests/day (1000/day once you have bought "
                   "at least $10 of credits).")

    def list_models(self):
        out = super().list_models()
        if self.key():   # account info: free-tier key or not, credit used
            try:
                d = self.http("GET", "https://openrouter.ai/api/v1/key", headers=self._headers(),
                              timeout=15).json()
                d = d.get("data", d)
                note = "free-tier key" if d.get("is_free_tier") else "paid key"
                if d.get("limit") is not None:
                    note += f", credit limit ${d['limit']}"
                note += f", used ${float(d.get('usage') or 0):.2f}"
                for m in out:
                    m.note = note
            except (ProviderError, ValueError, TypeError):
                pass
        return out


class _LocalLLM(OpenAICompatLLM):
    limits_note = "Runs on your PC: free and unlimited (speed depends on your hardware)."

    def list_models(self):
        try:
            return super().list_models()
        except ProviderError as e:
            raise ProviderError(f"{self.name}: server not reachable at {self.s('base_url')} - is it running? "
                                f"({e})")


_PRESET_BASE = {"gemini": _GeminiLLM, "openrouter": _OpenRouterLLM, "groq": _FreeTierLLM,
                "cerebras": _FreeTierLLM, "ollama": _LocalLLM, "lmstudio": _LocalLLM}
_PRESET_NOTES = {
    "groq": "Free plan for every model, with per-minute and per-day limits (shown after the first request).",
    "cerebras": "Free plan with per-minute and per-day limits (shown after the first request).",
    "custom_openai": "",
}


# (id, name, base_url, key_ref, default_model, suggestions, local)
LLM_PRESETS = [
    ("openai", "OpenAI", "https://api.openai.com/v1", "openai", "gpt-4.1-mini",
     ["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1", "gpt-5-mini", "gpt-5-nano", "gpt-4o-mini"], False),
    ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini",
     "gemini-2.5-flash", ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"], False),
    ("groq", "Groq", "https://api.groq.com/openai/v1", "groq", "openai/gpt-oss-120b",
     ["openai/gpt-oss-120b", "openai/gpt-oss-20b"], False),
    ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "openrouter", "google/gemini-2.5-flash",
     ["google/gemini-2.5-flash", "openai/gpt-4.1-mini", "anthropic/claude-sonnet-4.5",
      "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat"], False),
    ("together", "Together AI", "https://api.together.xyz/v1", "together",
     "meta-llama/Llama-3.3-70B-Instruct-Turbo", ["meta-llama/Llama-3.3-70B-Instruct-Turbo",
                                                 "Qwen/Qwen2.5-72B-Instruct-Turbo"], False),
    ("mistral", "Mistral", "https://api.mistral.ai/v1", "mistral", "mistral-small-latest",
     ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"], False),
    ("deepseek", "DeepSeek", "https://api.deepseek.com/v1", "deepseek", "deepseek-chat", ["deepseek-chat"], False),
    ("xai", "xAI (Grok)", "https://api.x.ai/v1", "xai", "grok-3-mini", ["grok-3-mini", "grok-3", "grok-4"], False),
    ("fireworks", "Fireworks AI", "https://api.fireworks.ai/inference/v1", "fireworks",
     "accounts/fireworks/models/llama-v3p3-70b-instruct", [], False),
    ("cerebras", "Cerebras", "https://api.cerebras.ai/v1", "cerebras", "llama-3.3-70b",
     ["llama-3.3-70b", "gpt-oss-120b"], False),
    ("ollama", "Ollama", "http://localhost:11434/v1", "custom_llm", "qwen2.5:7b",
     ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "gemma3:12b", "aya-expanse:8b", "mistral-nemo"], True),
    ("lmstudio", "LM Studio", "http://localhost:1234/v1", "custom_llm", "local-model", [], True),
    ("custom_openai", "Custom OpenAI-compatible", "http://localhost:8000/v1", "custom_llm", "", [], False),
]


def _make_preset(pid, pname, url, key_ref, model, models, local):
    base = _PRESET_BASE.get(pid, OpenAICompatLLM)
    cls = type(f"LLM_{pid}", (base,), {
        "id": pid, "name": pname, "base_url": url, "key_ref": key_ref, "default_model": model,
        "model_options": models, "local": local, "key_optional": local or pid == "custom_openai",
        "description": f"{pname} chat model via the OpenAI-compatible API.",
        "limits_note": _PRESET_NOTES.get(pid, base.limits_note
                                         or "Paid per token. Your rate limits appear after the first request."),
    })
    cls.fields = cls.build_fields()
    return register(cls)


for _p in LLM_PRESETS:
    _make_preset(*_p)


# Models that accept the server-side refusal fallback ("default" form).
_FALLBACK_MODELS = ("claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5")


@register
class AnthropicLLM(LLMProvider):
    id = "anthropic"
    name = "Anthropic (Claude)"
    description = "Claude models through the official Anthropic SDK."
    requires = ["anthropic"]
    pip_hint = "pip install anthropic"
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="anthropic"),
        Field("model", "Model", "model", "claude-opus-5-5",
              options=["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-4-5", "claude-fable-5-1"]),
        Field("effort", "Effort", "choice", "low", options=["low", "medium", "high", "default"],
              help="Low keeps translation latency down. Ignored on Haiku."),
        Field("fallbacks", "Refusal fallback", "bool", True,
              help="If the model declines a line, let the API retry it on a fallback model"),
        Field("timeout", "Timeout (s)", "float", 30, min=3, max=300),
    ]

    limits_note = "Paid per token. Your rate limits appear after the first request (or press Check limits)."
    # USD per 1M tokens (input, output) - the Models API doesn't return prices.
    PRICES = {"claude-fable-5-1": (10, 50), "claude-fable-5": (10, 50), "claude-opus-5-5": (4, 20),
              "claude-opus-5": (5, 25), "claude-opus-4-8": (5, 25), "claude-opus-4-7": (5, 25),
              "claude-opus-4-6": (5, 25), "claude-sonnet-5-5": (2, 10), "claude-sonnet-5": (2, 10),
              "claude-sonnet-4-6": (3, 15), "claude-haiku-4-5": (1, 5)}

    def list_models(self):
        import anthropic
        try:
            items = list(self._client().models.list())
        except anthropic.AuthenticationError as e:
            raise ProviderError(f"Claude: invalid API key ({e.message})")
        except anthropic.APIStatusError as e:
            raise ProviderError(f"Claude: HTTP {e.status_code}: {e.message}")
        except anthropic.APIConnectionError as e:
            raise ProviderError(f"Claude: connection error: {e}")
        out = []
        for m in items:
            price = self.PRICES.get(m.id)
            out.append(ModelInfo(id=m.id, name=m.display_name or "", free="paid",
                                 price_in=price[0] if price else None, price_out=price[1] if price else None,
                                 context=getattr(m, "max_input_tokens", None),
                                 max_output=getattr(m, "max_tokens", None)))
        return out

    def _client(self):
        import anthropic
        if getattr(self, "_cli", None) is None or self._cli_key != self.need_key():
            self._cli_key = self.need_key()
            self._cli = anthropic.Anthropic(api_key=self._cli_key, timeout=float(self.s("timeout", 30)))
        return self._cli

    def chat(self, system, messages, max_tokens=1024):
        import anthropic
        model = self.s("model")
        kwargs = dict(model=model, max_tokens=max(max_tokens, 1024), system=system, messages=messages)
        extra_body = {}
        betas = []
        effort = self.s("effort", "low")
        if effort != "default" and "haiku" not in model:
            kwargs["output_config"] = {"effort": effort}
        if self.s("fallbacks", True) and model.startswith(_FALLBACK_MODELS):
            betas.append("server-side-fallback-2026-07-01")
            extra_body["fallbacks"] = "default"
        try:
            if betas:
                raw = self._client().beta.messages.with_raw_response.create(betas=betas, extra_body=extra_body,
                                                                           **kwargs)
            else:
                raw = self._client().messages.with_raw_response.create(**kwargs)
            models_info.record_headers(self.id, model, raw.headers)
            resp = raw.parse()
        except anthropic.AuthenticationError as e:
            raise ProviderError(f"Claude: invalid API key ({e.message})")
        except anthropic.NotFoundError as e:
            raise ProviderError(f"Claude: model not found '{model}' ({e.message})")
        except anthropic.RateLimitError as e:
            raise ProviderError(f"Claude: rate limited ({e.message})")
        except anthropic.APIStatusError as e:
            raise ProviderError(f"Claude: HTTP {e.status_code}: {e.message}")
        except anthropic.APIConnectionError as e:
            raise ProviderError(f"Claude: connection error: {e}")
        if resp.stop_reason == "refusal":
            raise ProviderError("Claude declined to translate this line.")
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
