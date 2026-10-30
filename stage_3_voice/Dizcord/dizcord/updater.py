"""Self-update from GitHub releases (used by the public edition: Settings -> Updates).

The repo comes from edition.json: {"edition": "public", "update_repo": "owner/name"}.
check()  - asks GitHub for the latest release and says whether it is newer than this copy.
apply()  - downloads that release, copies its files over this folder (never touching data\\, models\\, runtime\\
           or edition.json) and reinstalls the Python packages if requirements.txt changed.
The app has to be restarted afterwards.
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import __version__
from .config import ROOT
from .edition import UPDATE_REPO

PROTECTED = {"data", "models", "runtime", "dist", ".git", ".venv", "__pycache__", "edition.json"}
TIMEOUT = 20
API = "https://api.github.com/repos/{repo}"


@dataclass
class Release:
    tag: str
    version: tuple
    notes: str
    zip_url: str
    newer: bool


@dataclass
class UpdateResult:
    files: int = 0
    skipped: list = field(default_factory=list)       # files that were in use and could not be replaced
    packages_updated: bool = False
    pip_error: str = ""


def parse_version(text: str) -> tuple:
    """'v0.5.1' -> (0, 5, 1); anything unparsable -> ()."""
    nums = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in nums[:4])


def _get(url: str, **kw):
    r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/vnd.github+json",
                                                    "User-Agent": "Dizcord-updater"}, **kw)
    r.raise_for_status()
    return r


def check(repo: str = "") -> Release:
    repo = (repo or UPDATE_REPO).strip()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise RuntimeError("No update source configured (edition.json needs \"update_repo\": \"owner/name\").")
    api = API.format(repo=repo)
    try:
        data = _get(f"{api}/releases/latest").json()
        tag = data["tag_name"]
        notes = data.get("body") or ""
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code != 404:
            raise
        tags = _get(f"{api}/tags").json()               # no release published: fall back to the newest tag
        if not tags:
            raise RuntimeError("The repository has no releases or tags yet.") from None
        tag, notes = tags[0]["name"], ""
    version = parse_version(tag)
    if not version:
        raise RuntimeError(f"Could not read a version number from '{tag}'.")
    return Release(tag, version, notes, f"{api}/zipball/{tag}", version > parse_version(__version__))


def _copy_tree(src_root: Path, result: UpdateResult) -> None:
    for src in src_root.rglob("*"):
        rel = src.relative_to(src_root)
        if src.is_dir() or any(part in PROTECTED for part in rel.parts) or src.suffix in (".pyc", ".tmp"):
            continue
        dst = ROOT / rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            result.files += 1
        except OSError:
            result.skipped.append(rel.as_posix())         # e.g. Dizcord.exe while it is running


def apply(release: Release) -> UpdateResult:
    result = UpdateResult()
    old_req = (ROOT / "requirements.txt").read_text(encoding="utf-8") if (ROOT / "requirements.txt").exists() else ""
    with tempfile.TemporaryDirectory(prefix="dizcord-update-") as tmp:
        blob = _get(release.zip_url, stream=False).content
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            z.extractall(tmp)
        tops = [p for p in Path(tmp).iterdir() if p.is_dir()]
        src_root = tops[0] if len(tops) == 1 else Path(tmp)    # GitHub zips have one top folder
        if not (src_root / "main.py").exists():
            raise RuntimeError("The downloaded release does not look like Dizcord (no main.py) - nothing changed.")
        _copy_tree(src_root, result)
    new_req = (ROOT / "requirements.txt").read_text(encoding="utf-8") if (ROOT / "requirements.txt").exists() else ""
    if new_req != old_req:
        try:
            out = subprocess.run([sys.executable, "-m", "pip", "install", "--no-build-isolation",
                                  "-r", str(ROOT / "requirements.txt")],
                                 capture_output=True, text=True, timeout=900)
            result.packages_updated = out.returncode == 0
            if out.returncode:
                result.pip_error = (out.stderr or out.stdout)[-300:]
        except (OSError, subprocess.SubprocessError) as e:
            result.pip_error = str(e)
    return result
