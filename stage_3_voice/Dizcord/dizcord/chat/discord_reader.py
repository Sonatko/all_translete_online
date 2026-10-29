"""Reads chat messages straight from the Discord desktop window through Windows
UI Automation (the same accessibility interface screen readers use).

No Discord account token, no self-bot, nothing injected into Discord: we only read
what is on the screen. Works for server channels, DMs, group DMs, threads and forum
posts - anything shown as a message list.

Discord (Chromium) only builds its accessibility tree once an assistive client asks
for it, so we "wake" it with WM_GETOBJECT first.
"""
from __future__ import annotations

import ctypes
import logging
import re
import time
from dataclasses import dataclass, field

log = logging.getLogger("dizcord.chat")

_INVISIBLE = re.compile(r"[⁠​‌‍﻿]")
_SPACES = re.compile(r"[ \t]+")


@dataclass
class ChatMessage:
    id: str
    channel_id: str
    author: str
    text: str
    embed: str = ""
    timestamp: str = ""
    list_name: str = ""           # "Messages in #general" (localised)
    rect: tuple = field(default=(0, 0, 0, 0))

    @property
    def full_text(self) -> str:
        squash = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
        if self.embed and squash(self.embed) not in squash(self.text):
            if squash(self.text) and squash(self.text) in squash(self.embed):
                return self.embed      # embed is the longer version of the same text
            return (self.text + "\n" + self.embed).strip() if self.text else self.embed
        return self.text


def clean(text: str) -> str:
    text = _INVISIBLE.sub("", text or "")
    lines = [_SPACES.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln).strip()


def _collect(el, out: list):
    """Visible text of a message part, skipping timestamps/tooltips/buttons."""
    for ch in el.GetChildren():
        t = ch.ControlTypeName
        aid = ch.AutomationId or ""
        if aid.startswith("_r_") or aid.startswith("message-timestamp"):
            continue
        if t == "TextControl":
            if ch.GetChildren():      # <time> wrapper -> it's a timestamp, skip
                continue
            out.append(ch.Name or "")
        elif t == "ButtonControl":
            n = ch.Name or ""
            if n[:1] in "@#":        # mentions
                out.append(n)
        elif t == "ImageControl":
            n = ch.Name or ""
            if n.startswith(":") and n.endswith(":") and len(n) < 40:   # custom emoji
                out.append(n)
        else:
            _collect(ch, out)


def _text_of(el) -> str:
    parts: list[str] = []
    _collect(el, parts)
    return clean("".join(parts))


class DiscordReader:
    """Call poll() repeatedly from ONE thread; it returns the messages currently loaded."""

    def __init__(self):
        import uiautomation as auto   # noqa: F401  (imported here so the app runs without it)
        self.auto = auto
        self.window = None
        self.lists: list = []
        self._lists_checked = 0.0
        self._title = None
        self._woken: set[int] = set()
        # inline translations: message id -> (message-content element, its message list)
        self.content_els: dict[str, tuple] = {}

    # ------------------------------------------------------------------ window
    def find_window(self):
        auto = self.auto
        if self.window is not None:
            try:
                if self.window.Exists(0, 0):
                    return self.window
            except Exception:
                pass
        self.window = None
        w = auto.WindowControl(searchDepth=1, ClassName="Chrome_WidgetWin_1", SubName="Discord")
        if w.Exists(0, 0):
            self.window = w
            self._wake(w.NativeWindowHandle)
        return self.window

    def _wake(self, hwnd: int):
        """Ask Chromium to enable its accessibility tree."""
        if hwnd in self._woken:
            return
        self._woken.add(hwnd)
        user32 = ctypes.windll.user32
        WM_GETOBJECT = 0x003D
        handles = [hwnd]
        cb_t = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def cb(h, _lp):
            handles.append(h)
            return True
        user32.EnumChildWindows(hwnd, cb_t(cb), 0)
        for h in handles:
            for obj in (-4, -25):   # OBJID_CLIENT, UiaRootObjectId
                try:
                    user32.SendMessageTimeoutW(h, WM_GETOBJECT, 0, obj, 0x0002, 500, None)
                except Exception:
                    pass
        time.sleep(0.8)

    def window_rect(self):
        w = self.find_window()
        if not w:
            return None
        r = w.BoundingRectangle
        return (r.left, r.top, r.right, r.bottom)

    def is_foreground(self) -> bool:
        w = self.find_window()
        return bool(w) and ctypes.windll.user32.GetForegroundWindow() == w.NativeWindowHandle

    def hwnd(self) -> int | None:
        w = self.find_window()
        return w.NativeWindowHandle if w else None

    # ------------------------------------------------------------------ lists
    def _find_lists(self):
        found = []
        for c, _d in self.auto.WalkControl(self.window, maxDepth=40):
            if c.ControlTypeName != "ListControl":
                continue
            kids = c.GetChildren()
            if any((k.AutomationId or "").startswith("chat-messages-") for k in kids[:6] + kids[-6:]):
                found.append(c)
        return found

    def _lists(self):
        title = self.window.Name
        now = time.monotonic()
        stale = title != self._title or now - self._lists_checked > 10 or not self.lists
        if not stale:
            try:
                for lst in self.lists:
                    lst.BoundingRectangle  # raises if the element is gone
            except Exception:
                stale = True
        if stale:
            self.lists = self._find_lists()
            self._title = title
            self._lists_checked = now
            if not self.lists:   # tree may still be building right after waking
                self._woken.discard(self.window.NativeWindowHandle)
                self._wake(self.window.NativeWindowHandle)
        return self.lists

    @property
    def title(self) -> str:
        t = (self._title or "")
        return t[:-10] if t.endswith(" - Discord") else t

    # ------------------------------------------------------------------ messages
    def message_items(self):
        """[(list_name, ListItem element)] for every loaded message, oldest first."""
        if not self.find_window():
            return []
        out = []
        self._item_list = {}
        for lst in self._lists():
            try:
                name = lst.Name or ""
                for it in lst.GetChildren():
                    if (it.AutomationId or "").startswith("chat-messages-"):
                        out.append((name, it))
                        self._item_list[id(it)] = lst
            except Exception:
                self.lists = []
        return out

    # ------------------------------------------------------------------ positions (inline translations)
    @staticmethod
    def rect_of(el) -> tuple | None:
        """Physical (left, top, right, bottom) or None when the element is gone / not rendered."""
        try:
            r = el.BoundingRectangle
        except Exception:
            return None
        if r.right - r.left <= 0 or r.bottom - r.top <= 0:
            return None
        return (r.left, r.top, r.right, r.bottom)

    def track(self, item, content_el=None):
        """Remember where the text of this message is, to draw its translation on top of it."""
        _, mid = self.ids_of(item)
        if content_el is None:
            content_el = self._find_content(item)
        if content_el is not None:
            self.content_els[mid] = (content_el, getattr(self, "_item_list", {}).get(id(item)))

    @staticmethod
    def _find_content(item):
        stack = list(item.GetChildren())
        while stack:
            el = stack.pop(0)
            aid = el.AutomationId or ""
            if aid.startswith("message-content-"):
                return el
            if aid.startswith(("message-accessories-", "message-reply-context")):
                continue
            if el.ControlTypeName == "GroupControl":
                stack[0:0] = el.GetChildren()
        return None

    def positions(self, ids) -> list[tuple[str, tuple, tuple]]:
        """[(message id, text rect, visible list rect)] for the tracked messages that are on screen."""
        out = []
        lists: dict[int, tuple | None] = {}
        for mid in list(ids):
            entry = self.content_els.get(mid)
            if entry is None:
                continue
            el, lst = entry
            r = self.rect_of(el)
            if r is None:
                self.content_els.pop(mid, None)   # re-rendered or scrolled out of the loaded range
                continue
            if lst is None:
                clip = self.window_rect()
            else:
                if id(lst) not in lists:
                    lists[id(lst)] = self.viewport(lst)
                clip = lists[id(lst)]
            if clip is None or r[3] <= clip[1] or r[1] >= clip[3]:
                continue   # scrolled out of view
            out.append((mid, r, clip))
        return out

    def viewport(self, lst) -> tuple | None:
        """The part of a message list that is actually visible: the list itself is as tall as all loaded
        messages, so intersect it with its scroll containers (no Discord class names needed)."""
        cache = self.__dict__.setdefault("_ancestors", {})
        chain = cache.get(id(lst))
        if chain is None:
            chain, el = [lst], lst
            for _ in range(4):
                try:
                    el = el.GetParentControl()
                except Exception:
                    el = None
                if not el:
                    break
                chain.append(el)
            cache[id(lst)] = chain
            if len(cache) > 20:
                cache.pop(next(iter(cache)))
        box = None
        for el in chain:
            r = self.rect_of(el)
            if r is None:
                continue
            box = r if box is None else (max(box[0], r[0]), max(box[1], r[1]), min(box[2], r[2]), min(box[3], r[3]))
        if box is None or box[2] <= box[0] or box[3] <= box[1]:
            return None
        return box

    def is_visible_foreground(self) -> bool:
        """Discord is the active window and not minimised (only then are inline translations drawn)."""
        w = self.find_window()
        if not w:
            return False
        hwnd = w.NativeWindowHandle
        user32 = ctypes.windll.user32
        return user32.GetForegroundWindow() == hwnd and not user32.IsIconic(hwnd)

    @staticmethod
    def ids_of(item) -> tuple[str, str]:
        parts = (item.AutomationId or "").split("-")
        return (parts[2] if len(parts) > 3 else "", parts[-1])

    def read(self, item, list_name: str = "", previous_author: str = "") -> ChatMessage:
        channel_id, msg_id = self.ids_of(item)
        author, text, embed, ts = "", "", "", ""
        stack = list(item.GetChildren())
        while stack:
            el = stack.pop(0)
            aid = el.AutomationId or ""
            if aid.startswith("message-username-"):
                author = clean(" ".join(c.Name for c in el.GetChildren()
                                        if c.ControlTypeName in ("ButtonControl", "TextControl") and c.Name))
            elif aid.startswith("message-content-"):
                text = _text_of(el)
                self.content_els[msg_id] = (el, getattr(self, "_item_list", {}).get(id(item)))
            elif aid.startswith("message-accessories-"):
                embed = _text_of(el)
            elif aid.startswith("message-timestamp-"):
                ts = clean(" ".join(c.Name for c in el.GetChildren() if c.Name))
            elif aid.startswith("message-reply-context"):
                continue
            elif el.ControlTypeName in ("GroupControl", "TextControl"):
                stack[0:0] = el.GetChildren()
        r = item.BoundingRectangle
        return ChatMessage(msg_id, channel_id, author or previous_author, text, embed, ts, list_name,
                           (r.left, r.top, r.right, r.bottom))
