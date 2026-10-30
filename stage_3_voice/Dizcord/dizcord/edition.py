"""Which edition this copy of the app is.

- full (default): everything.
- public (the GitHub release, made by tools/make_public.py): adds the Manual tab and Settings -> Updates.
  Everything (voice, chat translation inside Discord, OCR, subtitles...) runs on the user's own PC.
  Selected by an edition.json next to main.py: {"edition": "public"}
"""
from __future__ import annotations

import json

from .config import ROOT

try:
    _data = json.loads((ROOT / "edition.json").read_text(encoding="utf-8"))
except Exception:
    _data = {}

PUBLIC = _data.get("edition") == "public"
UPDATE_REPO = str(_data.get("update_repo") or "")      # "owner/name" on GitHub; the Updates box needs it
