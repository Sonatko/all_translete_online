"""Downloads of offline voices and model files into the app folder (models/...) - each file once.

- download(lang): the natural voice (Piper) of the app language, about 60 MB. After that the tour and the Manual
  are read aloud without internet.
- piper_voice_for(locale) / piper_files(voice): a Piper voice for a language you translate to, picked from the
  official catalogue (voices.json of huggingface.co/rhasspy/piper-voices, kept in models/piper for a month).

fetch() writes <file>.part and renames it at the end, so a half-downloaded file never replaces a good one."""
from __future__ import annotations

import json
import threading
import time
import urllib.parse
from pathlib import Path

from .config import MODELS_DIR
from .i18n import LANGUAGES, PIPER_URL, Language

TIMEOUT = 30
CATALOGUE_DAYS = 30
_QUALITY = {"medium": 0, "high": 1, "low": 2, "x_low": 3}          # medium: natural and fast enough on any CPU
_PREFERRED = {lang.piper.split("-")[0]: lang.piper for lang in LANGUAGES}   # the voices of the app languages
_catalogue: dict | None = None
_catalogue_failed = -1e9                     # time.monotonic() of the last failed catalogue download
_catalogue_lock = threading.Lock()


def fetch(url: str, dst: Path, progress=None, cancelled=lambda: False, base: int = 0, total: int = 0) -> int:
    """Download `url` to `dst`; returns the number of bytes. progress(base + done_bytes, total or file size)."""
    import requests
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_name(dst.name + ".part")
    done = 0
    with requests.get(url, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        size = int(r.headers.get("content-length") or 0)
        with open(part, "wb") as f:
            for block in r.iter_content(1 << 16):
                if cancelled():
                    raise RuntimeError("cancelled")
                f.write(block)
                done += len(block)
                if progress:
                    progress(base + done, total or size)
    if size and done < size:
        raise OSError(f"download incomplete ({done} of {size} bytes): {url}")
    part.replace(dst)
    return done


def fetch_all(files, folder: Path, progress=None, cancelled=lambda: False) -> None:
    """files = [(url, file name, bytes)]: the ones not in `folder` yet are downloaded into it."""
    todo = [f for f in files if not (Path(folder) / f[1]).is_file()]
    total, done = sum(f[2] for f in todo), 0
    for url, name, size in todo:
        done += fetch(url, Path(folder) / name, progress, cancelled, done, total) or size


def download(lang: Language, progress=None, cancelled=lambda: False) -> None:
    """Fetch both files of `lang`'s voice. progress(done_bytes, total_bytes) is called while downloading.
    Raises on failure; a half-downloaded file never replaces a good one."""
    files = []
    for url, name in lang.piper_urls:
        v = piper_catalogue_entry(lang.piper)
        size = next((i["size_bytes"] for p, i in v["files"].items() if p.endswith("/" + name)), 0) if v else 0
        files.append((url, name, size))
    fetch_all(files, MODELS_DIR / "piper", progress, cancelled)


# ------------------------------------------------------------------------------------------- Piper catalogue
def piper_catalogue() -> dict:
    """{voice key: entry} of every Piper voice. Raises when it was never downloaded and there is no internet."""
    global _catalogue, _catalogue_failed
    with _catalogue_lock:
        if _catalogue is None:
            path = MODELS_DIR / "piper" / "voices.json"
            if not path.is_file() or time.time() - path.stat().st_mtime > CATALOGUE_DAYS * 86400:
                if not path.is_file() and time.monotonic() - _catalogue_failed < 600:
                    raise OSError("the list of Piper voices could not be downloaded (no internet?)")
                try:
                    fetch(f"{PIPER_URL}/voices.json", path)
                except Exception:  # noqa: BLE001
                    _catalogue_failed = time.monotonic()
                    if not path.is_file():
                        raise
            _catalogue = json.loads(path.read_text(encoding="utf-8"))
        return _catalogue


def piper_catalogue_entry(key: str) -> dict | None:
    try:
        return piper_catalogue().get(key)
    except Exception:  # noqa: BLE001
        return None


def piper_voice_for(locale: str) -> dict | None:
    """The catalogue voice for a locale like "pt_PT": that country first, else the same language elsewhere
    (e.g. zh_TW -> zh_CN). Medium quality first, the app-language voice of that country preferred."""
    fam = locale.split("_")[0].lower()

    def rank(v):
        code = v["language"]["code"]
        return (code.lower() != locale.lower(), v["key"] != _PREFERRED.get(code), _QUALITY.get(v["quality"], 9),
                v["key"])
    return min((v for v in piper_catalogue().values() if v["language"]["family"].lower() == fam), key=rank,
               default=None)


def piper_files(voice: dict) -> list[tuple[str, str, int]]:
    """[(url, file name, bytes)] of the .onnx model and its .onnx.json of a catalogue voice."""
    return [(f"{PIPER_URL}/{urllib.parse.quote(path)}", path.rsplit("/", 1)[1], info.get("size_bytes", 0))
            for path, info in voice["files"].items() if path.endswith((".onnx", ".onnx.json"))]
