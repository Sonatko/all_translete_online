"""What we know about each AI model: free or paid, price, context size, and rate limits.

- Model lists come from each provider's /models API (refreshed from the AI Model tab).
- Rate limits are read from the response headers of real requests (every translation updates them,
  and "Check limits" sends one tiny request), because no provider has an API that just lists them.

Everything is cached in data/models_cache.json so the lists are there at startup.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass

from ..config import DATA_DIR

CACHE_FILE = DATA_DIR / "models_cache.json"
STALE_SECONDS = 12 * 3600       # re-scan model lists older than this automatically

_lock = threading.Lock()
_cache: dict | None = None


@dataclass
class ModelInfo:
    id: str
    name: str = ""
    free: str = ""               # "free" | "free tier" | "local" | "paid" | "" (unknown)
    price_in: float | None = None   # USD per 1M input tokens
    price_out: float | None = None  # USD per 1M output tokens
    context: int | None = None      # max input tokens
    max_output: int | None = None
    note: str = ""

    def short(self) -> str:
        """Suffix shown in the model list."""
        parts = []
        if self.free:
            parts.append(self.free)
        if self.price_in is not None and self.free == "paid":
            parts.append(f"${_num(self.price_in)}/${_num(self.price_out)} per 1M")
        if self.context:
            parts.append(f"{_tokens(self.context)} ctx")
        return " · ".join(parts)


def _num(v) -> str:
    if v is None:
        return "?"
    return f"{v:.2f}".rstrip("0").rstrip(".") if v < 100 else f"{v:.0f}"


def _tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{round(n / 1_000_000, 1):g}M"
    if n >= 1000:
        return f"{n // 1000}K"
    return str(n)


# ----------------------------------------------------------------------------- cache
def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}
    return _cache


def _save():
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_cache, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CACHE_FILE)


def models(provider_id: str) -> list[ModelInfo]:
    with _lock:
        entry = _load().get(provider_id) or {}
        return [ModelInfo(**m) for m in entry.get("models", [])]


def model(provider_id: str, model_id: str) -> ModelInfo | None:
    return next((m for m in models(provider_id) if m.id == model_id), None)


def is_stale(provider_id: str) -> bool:
    with _lock:
        entry = _load().get(provider_id) or {}
        return time.time() - entry.get("fetched", 0) > STALE_SECONDS


def save_models(provider_id: str, items: list[ModelInfo]) -> None:
    with _lock:
        entry = _load().setdefault(provider_id, {})
        entry["models"] = [asdict(m) for m in items]
        entry["fetched"] = time.time()
        _save()


# ----------------------------------------------------------------------------- rate limits
# header suffix -> (label, default period). Groq reports requests per DAY in x-ratelimit-limit-requests.
_LIMIT_HEADERS = [
    # Anthropic
    ("anthropic-ratelimit-requests-limit", "requests", "min"),
    ("anthropic-ratelimit-input-tokens-limit", "input tokens", "min"),
    ("anthropic-ratelimit-output-tokens-limit", "output tokens", "min"),
    ("anthropic-ratelimit-tokens-limit", "tokens", "min"),
    # Cerebras
    ("x-ratelimit-limit-requests-day", "requests", "day"),
    ("x-ratelimit-limit-tokens-minute", "tokens", "min"),
    ("x-ratelimit-limit-requests-minute", "requests", "min"),
    ("x-ratelimit-limit-tokens-day", "tokens", "day"),
    # OpenAI style (OpenAI, Groq, Together, Mistral, xAI, DeepSeek…)
    ("x-ratelimit-limit-requests", "requests", "min"),
    ("x-ratelimit-limit-tokens", "tokens", "min"),
    ("x-ratelimit-limit", "requests", "min"),        # OpenRouter
]
_PERIOD_OVERRIDES = {("groq", "x-ratelimit-limit-requests"): "day"}


def record_headers(provider_id: str, model_id: str, headers) -> None:
    """Store the rate limits found in a response's headers (if any)."""
    if not headers or not model_id:
        return
    found = []
    low = {str(k).lower(): v for k, v in dict(headers).items()}
    seen = set()
    for h, label, period in _LIMIT_HEADERS:
        v = low.get(h)
        if v is None:
            continue
        period = _PERIOD_OVERRIDES.get((provider_id, h), period)
        if (label, period) in seen:
            continue
        seen.add((label, period))
        remaining = low.get(h.replace("-limit", "-remaining")) if "-limit" in h else None
        found.append({"label": label, "period": period, "limit": str(v), "remaining": remaining})
    if not found:
        return
    with _lock:
        entry = _load().setdefault(provider_id, {})
        entry.setdefault("limits", {})[model_id] = {"time": time.time(), "items": found}
        _save()


def set_blocked(provider_id: str, model_id: str, reason: str | None) -> None:
    """Remember that the account can't use this model (e.g. blocked in the organization's settings)."""
    with _lock:
        entry = _load().setdefault(provider_id, {})
        blocked = entry.setdefault("blocked", {})
        if reason:
            blocked[model_id] = reason
        elif model_id in blocked:
            blocked.pop(model_id)
        else:
            return
        _save()


def blocked(provider_id: str, model_id: str) -> str | None:
    with _lock:
        return ((_load().get(provider_id) or {}).get("blocked") or {}).get(model_id)


def limits(provider_id: str, model_id: str) -> dict | None:
    with _lock:
        return ((_load().get(provider_id) or {}).get("limits") or {}).get(model_id)


def describe(provider_id: str, model_id: str, provider_note: str = "") -> str:
    """One or two lines of HTML for the info label under the model box."""
    m = model(provider_id, model_id)
    bits = []
    why = blocked(provider_id, model_id)
    if why:
        bits.append(f"⛔ {why}")
    if m:
        if m.free:
            bits.append(f"<b>{m.free}</b>")
        if m.price_in is not None and m.free != "free":
            label = "if you upgrade: " if m.free == "free tier" else ""
            bits.append(f"{label}${_num(m.price_in)} in / ${_num(m.price_out)} out per 1M tokens")
        if m.context:
            bits.append(f"context {_tokens(m.context)} tokens")
        if m.max_output:
            bits.append(f"max output {_tokens(m.max_output)}")
        if m.note:
            bits.append(m.note)
    elif model_id and models(provider_id):
        bits.append("⚠ this model is not in the service's current list - pick another one (or ignore this if "
                    "you typed a custom name)")
    lines = [" · ".join(bits)] if bits else []
    lim = limits(provider_id, model_id)
    if lim:
        parts = []
        for it in lim["items"]:
            s = f"{_fmt_int(it['limit'])} {it['label']}/{it['period']}"
            if it.get("remaining") not in (None, ""):
                s += f" ({_fmt_int(it['remaining'])} left)"
            parts.append(s)
        age = time.time() - lim["time"]
        when = "just now" if age < 90 else (f"{int(age // 60)} min ago" if age < 3600 else
                                             time.strftime("%d %b %H:%M", time.localtime(lim["time"])))
        lines.append("Limits: " + " · ".join(parts) + f"  <i>(seen {when})</i>")
    elif provider_note:
        lines.append(provider_note)
    return "<br>".join(lines)


def _fmt_int(v) -> str:
    try:
        return f"{int(float(v)):,}"
    except (TypeError, ValueError):
        return str(v)
