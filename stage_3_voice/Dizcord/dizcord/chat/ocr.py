"""Screen capture + Windows built-in OCR (no extra models needed).

Windows ships OCR for each language pack installed in Settings → Time & Language →
Language (add the language, include "Optical character recognition").
Coordinates are PHYSICAL screen pixels.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import numpy as np


@dataclass
class OcrLine:
    text: str
    rect: tuple[int, int, int, int]   # x, y, w, h in screen pixels


def available() -> bool:
    try:
        from winrt.windows.media.ocr import OcrEngine  # noqa: F401
        return True
    except Exception:
        return False


def languages() -> list[str]:
    try:
        from winrt.windows.media.ocr import OcrEngine
        return [l.language_tag for l in OcrEngine.available_recognizer_languages]
    except Exception:
        return []


def grab(x: int, y: int, w: int, h: int) -> np.ndarray:
    """BGRA uint8 image of a screen rectangle (physical pixels)."""
    import mss
    cls = getattr(mss, "MSS", None) or mss.mss
    with cls() as s:
        shot = s.grab({"left": int(x), "top": int(y), "width": max(1, int(w)), "height": max(1, int(h))})
        return np.array(shot, dtype=np.uint8).reshape(shot.height, shot.width, 4)


def _upscale(img: np.ndarray, factor: float) -> np.ndarray:
    """Smooth upscale (bilinear) - OCR reads small anti-aliased text much better this way."""
    if factor <= 1:
        return img
    try:
        from scipy.ndimage import zoom
        return np.clip(zoom(img.astype(np.float32), (factor, factor, 1), order=1), 0, 255).astype(np.uint8)
    except ImportError:
        f = int(round(factor))
        return np.repeat(np.repeat(img, f, axis=0), f, axis=1)


def estimate_text_height(img_bgra: np.ndarray) -> float:
    """Rough height of text rows in pixels (from runs of rows that contain ink)."""
    g = img_bgra[..., :3].mean(axis=2)
    bg = np.median(g)
    ink = (np.abs(g - bg) > 40).any(axis=1)
    runs, n = [], 0
    for v in ink:
        if v:
            n += 1
        elif n:
            runs.append(n)
            n = 0
    if n:
        runs.append(n)
    runs = [r for r in runs if r >= 3]
    return float(np.median(runs)) if runs else 20.0


def recognize(img_bgra: np.ndarray, lang_tag: str | None = None) -> list[OcrLine]:
    """OCR a BGRA image. Small text is upscaled first (much better results on low resolutions)."""
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter

    h, w = img_bgra.shape[:2]
    # aim for ~40 px tall glyphs; never exceed the OCR engine's size limit
    text_px = estimate_text_height(img_bgra)
    factor = min(4.0, max(1.0, 40.0 / max(text_px, 1)))
    factor = min(factor, OcrEngine.max_image_dimension / max(w, h))
    img = np.ascontiguousarray(_upscale(img_bgra, factor))
    h2, w2 = img.shape[:2]
    if max(h2, w2) > OcrEngine.max_image_dimension:
        raise RuntimeError("Selected area is too large for OCR.")

    if lang_tag and lang_tag != "auto":
        engine = OcrEngine.try_create_from_language(Language(lang_tag))
    else:
        engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError(f"No Windows OCR for '{lang_tag}'. Add the language in Windows Settings → Language.")

    writer = DataWriter()
    writer.write_bytes(img.tobytes())
    bmp = SoftwareBitmap.create_copy_from_buffer(writer.detach_buffer(), BitmapPixelFormat.BGRA8, w2, h2)

    async def run():
        return await engine.recognize_async(bmp)
    result = asyncio.run(run())
    lines = []
    for ln in result.lines:
        words = list(ln.words)
        if not words:
            continue
        xs = [wd.bounding_rect.x for wd in words]
        ys = [wd.bounding_rect.y for wd in words]
        x2 = [wd.bounding_rect.x + wd.bounding_rect.width for wd in words]
        y2 = [wd.bounding_rect.y + wd.bounding_rect.height for wd in words]
        rect = (int(min(xs) / factor), int(min(ys) / factor), int((max(x2) - min(xs)) / factor),
                int((max(y2) - min(ys)) / factor))
        lines.append(OcrLine(ln.text, rect))
    return lines


def paragraphs(lines: list[OcrLine]) -> str:
    """Join OCR lines into text, keeping paragraph breaks where there are vertical gaps."""
    if not lines:
        return ""
    out, prev = [], None
    for ln in sorted(lines, key=lambda l: (l.rect[1], l.rect[0])):
        if prev is not None:
            gap = ln.rect[1] - (prev.rect[1] + prev.rect[3])
            out.append("\n" if gap > prev.rect[3] * 0.8 else " ")
        out.append(ln.text)
        prev = ln
    return "".join(out).strip()
