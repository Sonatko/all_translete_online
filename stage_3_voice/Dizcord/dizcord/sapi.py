"""Offline narrator using the voices built into Windows (SAPI) - no AI, no internet, no download.

Used by the Manual tab. If SAPI is not available (not Windows, broken COM), `available` is False and every call
is a harmless no-op, so the manual still shows its text.
"""
from __future__ import annotations

import logging

log = logging.getLogger("dizcord.sapi")

_ASYNC = 1             # SVSFlagsAsync: return at once, speak in the background
_PURGE = 2             # SVSFPurgeBeforeSpeak: cut whatever is being said first
_RUNNING = 2           # SRSEIsSpeaking
_ENGLISH = ("409", "809", "c09", "1009", "1409")        # en-US, en-GB, en-AU, en-CA, en-NZ language ids


def _lang_code(lcid_hex: str) -> str:
    """SAPI language id (hex LCID, e.g. "416") -> language code ("pt")."""
    if lcid_hex in _ENGLISH:
        return "en"
    try:
        import locale
        return (locale.windows_locale.get(int(lcid_hex, 16)) or "").split("_")[0]
    except ValueError:
        return ""


class Narrator:
    def __init__(self):
        self._v = None
        self.available = False
        try:
            import comtypes.client
            self._v = comtypes.client.CreateObject("SAPI.SpVoice")
            self.available = True
        except Exception as e:  # noqa: BLE001
            log.info("Windows speech (SAPI) not available: %s", e)

    # ------------------------------------------------------------------ voices
    def voices(self) -> list[tuple[int, str, str]]:
        """[(index, name, language id)] of the installed voices."""
        out = []
        if not self.available:
            return out
        try:
            items = self._v.GetVoices()
            for i in range(items.Count):
                tok = items.Item(i)
                try:
                    lang = tok.GetAttribute("Language").split(";")[0].strip().lower()
                except Exception:  # noqa: BLE001
                    lang = ""
                out.append((i, tok.GetDescription(), lang))
        except Exception as e:  # noqa: BLE001
            log.warning("could not list the voices: %s", e)
        return out

    def default_voice(self, code: str = "en") -> int:
        """Index of the first voice of the language `code` (the app language), else 0."""
        for i, _name, lang in self.voices():
            if _lang_code(lang) == code:
                return i
        return 0

    def has_voice(self, code: str = "en") -> bool:
        return any(_lang_code(lang) == code for _i, _n, lang in self.voices())

    def has_english_voice(self) -> bool:
        return self.has_voice("en")

    def set_voice(self, index: int) -> None:
        if not self.available:
            return
        try:
            self._v.Voice = self._v.GetVoices().Item(int(index))
        except Exception as e:  # noqa: BLE001
            log.warning("could not select voice %s: %s", index, e)

    def set_rate(self, rate: int) -> None:
        """-10 (slow) .. +10 (fast), 0 = normal."""
        if self.available:
            self._v.Rate = max(-10, min(10, int(rate)))

    def set_volume(self, volume: int) -> None:
        """0 .. 100."""
        if self.available:
            self._v.Volume = max(0, min(100, int(volume)))

    # ------------------------------------------------------------------ speaking
    def speak(self, text: str) -> None:
        """Say `text` now: whatever was being said is cut first, this call returns immediately."""
        if not self.available or not text.strip():
            return
        try:
            self._v.Speak(text, _ASYNC | _PURGE)
        except Exception as e:  # noqa: BLE001
            log.warning("speak failed: %s", e)

    def stop(self) -> None:
        if self.available:
            try:
                self._v.Speak("", _ASYNC | _PURGE)
            except Exception:  # noqa: BLE001
                pass

    def speaking(self) -> bool:
        try:
            return bool(self.available and self._v.Status.RunningState == _RUNNING)
        except Exception:  # noqa: BLE001
            return False
