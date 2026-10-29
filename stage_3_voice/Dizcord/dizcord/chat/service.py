"""Text translation service: Discord chat watcher, select-to-translate, hotkeys,
draft translation and sending text into Discord.

Everything reports to the GUI through emit(dict) events:
  chat_line   {id, channel, author, original, translated, src, tgt, edited}
  chat_status {text, ok}
  chat_window {rect}                      physical-pixel rect of the Discord window
  popup       {original, translated, src, tgt, x, y, kind}
  ocr_request {}                          GUI should open the area selector
"""
from __future__ import annotations

import collections
import concurrent.futures
import ctypes
import logging
import queue
import threading
import time

from .. import languages as L
from ..providers import REGISTRY, ProviderError
from ..speech import Utterance
from . import winutil

log = logging.getLogger("dizcord.chat")

DISCORD_EPOCH_MS = 1420070400000
SPEAK_MAX_AGE_S = 180            # never read out messages older than this (scrolled-to or loaded late)


def message_time(mid: str) -> float | None:
    """When a Discord message was sent (unix seconds), from its id (a snowflake)."""
    try:
        return ((int(mid) >> 22) + DISCORD_EPOCH_MS) / 1000.0
    except (TypeError, ValueError):
        return None


def _snowflake(mid: str) -> int:
    try:
        return int(mid)
    except (TypeError, ValueError):
        return 0


class ChatService:
    def __init__(self, engine, emit):
        self.engine = engine
        self.emit = emit
        self._reader_thread = None
        self._reader_stop = threading.Event()
        self._tq: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._translate_worker, name="chat-translate", daemon=True)
        self._worker.start()
        # Chat messages: translated up to 4 at a time, shown in their original order, spoken one at a time.
        self._pool = concurrent.futures.ThreadPoolExecutor(4, thread_name_prefix="chat-tr")
        self._ordered: queue.Queue = queue.Queue()
        threading.Thread(target=self._emit_in_order, name="chat-emit", daemon=True).start()
        # newest message id each chat had when we first saw it: only messages written after that are read out,
        # so scrolling up (Discord loads older messages) or switching chats never reads old messages aloud
        self.newest: dict[str, int] = {}
        self._cache: collections.OrderedDict = collections.OrderedDict()   # (text, target, engine) -> (out, det)
        self._cache_lock = threading.Lock()
        self._providers: dict = {}
        self._mouse = None
        self._hotkeys = []
        self._press = None
        self._last_click = (0.0, 0, 0)
        self._last_selection = ("", 0.0)
        self._busy_selection = threading.Lock()
        self.lang_counts = collections.Counter()
        self.history = collections.deque(maxlen=12)
        self.discord_hwnd = None
        self._clip_seq = None
        self._clip_thread = None
        self._translate_visible = threading.Event()
        self.inline_ids: dict[str, bool] = {}      # translated messages whose translation is drawn inline
        self._inline_last = None                   # last positions sent to the GUI
        self._inline_state = "hide"
        self._discord_fg = None                    # is Discord (or our own window) in front - last value sent

    # ------------------------------------------------------------------ helpers
    @property
    def cfg(self) -> dict:
        return self.engine.profile["chat"]

    @property
    def chat_language(self) -> str | None:
        """Most common foreign language seen in the chat recently."""
        if not self.lang_counts:
            return None
        return self.lang_counts.most_common(1)[0][0]

    def translate(self, text: str, target: str, source: str | None = None,
                  engine_override: bool = True) -> tuple[str, str | None]:
        tr, pid = self._provider(engine_override)
        ctx = self.engine.translate_context("incoming")
        ctx.history = list(self.history)[-int(self.engine.profile["translation"].get("context_lines", 4)):]
        if pid == "llm" and ctx.llm is None:
            ctx.llm = self.engine.provider("llm")
        if source is None and getattr(tr, "needs_source", False):
            from ..textengine import detect_text_language
            source = detect_text_language(text)
        out, det = tr.translate(text, source, target, ctx)
        return out.strip(), det or source

    def _provider(self, override: bool):
        """The app's translation engine, or the Text tab's 'engine for chat messages' when override is set."""
        p = self.engine.profile
        pid = (self.cfg.get("engine") or "") if override else ""
        if not pid or pid == p["translation"]["provider"]:
            return self.engine.provider("translate"), p["translation"]["provider"]
        cls = REGISTRY["translate"].get(pid)
        if cls is None or cls.missing_requirements():
            return self.engine.provider("translate"), p["translation"]["provider"]
        settings = p["translation"]["settings"].get(pid, {})
        inst = self._providers.get(pid)
        if inst is None:
            inst = self._providers[pid] = cls(settings, self.engine.keys)
        return inst, pid

    def _cached_translate(self, text, target):
        key = (text, target, self.cfg.get("engine") or self.engine.profile["translation"]["provider"])
        with self._cache_lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        res = self.translate(text, target, engine_override=True)
        with self._cache_lock:
            self._cache[key] = res
            while len(self._cache) > 1000:
                self._cache.popitem(last=False)
        return res

    def translate_async(self, text: str, target: str, kind: str, **meta):
        self._tq.put(("adhoc", text, target, kind, meta))

    # ================================================================== Discord reader
    @property
    def reader_running(self) -> bool:
        return self._reader_thread is not None and self._reader_thread.is_alive()

    def start_reader(self):
        if self.reader_running:
            return
        self._reader_stop.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, name="discord-reader", daemon=True)
        self._reader_thread.start()

    def stop_reader(self):
        self._reader_stop.set()
        self.emit({"type": "chat_status", "text": "Chat translation off", "ok": False})

    def translate_visible_now(self):
        self._translate_visible.set()
        if not self.reader_running:
            self.start_reader()

    def _reader_loop(self):
        try:
            import uiautomation as auto
            from .discord_reader import DiscordReader
        except ImportError:
            self.emit({"type": "chat_status", "text": "Needs the 'uiautomation' package (run setup.bat)", "ok": False})
            return
        with auto.UIAutomationInitializerInThread():
            reader = DiscordReader()
            seen: dict[str, str] = {}
            authors: dict[str, str] = {}
            newest = self.newest
            channel = None
            last_rect = None
            missing_since = None
            while not self._reader_stop.is_set():
                try:
                    if not reader.find_window():
                        if missing_since is None:
                            missing_since = time.monotonic()
                            self.emit({"type": "chat_status", "text": "Discord window not found - is Discord open?",
                                       "ok": False})
                        self._reader_stop.wait(2.0)
                        continue
                    missing_since = None
                    self.discord_hwnd = reader.hwnd()
                    rect = reader.window_rect()
                    if rect != last_rect:
                        last_rect = rect
                        self.emit({"type": "chat_window", "rect": rect})
                    items = reader.message_items()
                    if reader.title != channel:
                        channel = reader.title
                        seen.clear()
                        self.history.clear()
                        self.inline_ids.clear()
                        reader.content_els.clear()
                        self._inline_emit("hide")
                        self.emit({"type": "chat_status", "text": f"Reading: {channel or 'Discord'}", "ok": True})
                        self.emit({"type": "chat_channel", "channel": channel})
                        n = int(self.cfg.get("history", 5))
                        backlog = {id(it) for _, it in items[-n:]} if n > 0 else set()
                    else:
                        backlog = None
                    force = self._translate_visible.is_set()
                    if force:
                        self._translate_visible.clear()
                        seen.clear()
                        backlog = {id(it) for _, it in items[-15:]}
                    prev_author = ""
                    recent = {id(it) for _, it in items[-3:]}
                    first_look: dict[str, int] = {}
                    for _n, it in items:
                        cid, mid = reader.ids_of(it)
                        if cid not in newest:
                            first_look[cid] = max(first_look.get(cid, 0), _snowflake(mid))
                    newest.update(first_look)        # what is on screen when a chat is first seen is "old"
                    for list_name, it in items:
                        cid, mid = reader.ids_of(it)
                        if mid in self.inline_ids and mid not in reader.content_els:
                            reader.track(it)     # Discord re-rendered it: find its text element again
                        if mid in seen and id(it) not in recent:
                            prev_author = authors.get(mid, prev_author)
                            continue
                        if backlog is not None and id(it) not in backlog and mid not in seen:
                            # old messages when opening a channel: remember, don't translate
                            seen[mid] = ""
                            authors[mid] = prev_author
                            continue
                        msg = reader.read(it, list_name, prev_author)
                        prev_author = msg.author
                        authors[mid] = msg.author
                        text = msg.full_text if self.cfg.get("include_embeds", True) else msg.text
                        if seen.get(mid) == text:
                            continue
                        edited = mid in seen and seen[mid] != "" and seen[mid] != text
                        seen[mid] = text
                        # read aloud only brand-new messages: newer than anything seen in this chat, sent in the last
                        # minutes, not an edit (a link preview loading also changes the text) and not a backlog
                        sent = message_time(mid)
                        speak = (_snowflake(mid) > newest.get(cid, 0) and backlog is None and not edited
                                 and (sent is None or time.time() - sent < SPEAK_MAX_AGE_S))
                        newest[cid] = max(newest.get(cid, 0), _snowflake(mid))
                        if text:
                            fut = self._pool.submit(self._chat_translate, msg, text, edited)
                            self._ordered.put((fut, channel, speak))
                except Exception as e:  # Discord re-rendering, element vanished...
                    log.debug("reader: %s", e)
                    reader.lists = []
                # Between full reads, follow where the translated messages are (~10x per second).
                next_poll = time.monotonic() + max(0.3, int(self.cfg.get("poll_ms", 1200)) / 1000)
                while not self._reader_stop.is_set() and time.monotonic() < next_poll:
                    try:
                        self._focus_tick(reader)
                        self._inline_tick(reader)
                    except Exception as e:
                        log.debug("inline: %s", e)
                    self._reader_stop.wait(0.1)
            self._inline_emit("hide")
            self._discord_fg = None
            self.emit({"type": "discord_focus", "on": False})

    def _focus_tick(self, reader):
        """Tell the GUI when Discord comes to the front / goes to the back (our windows only show over it)."""
        fg = reader.is_visible_foreground() or winutil.foreground_is_own_app()
        if fg != self._discord_fg:
            self._discord_fg = fg
            self.emit({"type": "discord_focus", "on": fg})

    # ================================================================== inline translations
    def _inline_emit(self, state, **data):
        if state == self._inline_state and state != "show":
            return
        self._inline_state = state
        if state == "hide":
            self._inline_last = None
        self.emit({"type": "chat_inline", "state": state, **data})

    def _inline_tick(self, reader):
        """Send the positions of translated messages; hide while they move (scrolling/resizing)."""
        if self.cfg.get("display", "inline") not in ("inline", "both") or not self.inline_ids or not reader.is_visible_foreground():
            self._inline_emit("hide")
            return
        pos = reader.positions(self.inline_ids)
        win = reader.window_rect()
        snapshot = (win, tuple(pos))
        if snapshot == self._inline_last:
            if self._inline_state == "moving":
                self._inline_emit("show", window=win, items=[{"id": m, "rect": r, "clip": c} for m, r, c in pos])
            return
        prev = self._inline_last
        self._inline_last = snapshot
        first = prev is None
        if not first and self._inline_state == "show" and prev[0] == win:
            old = {m: r for m, r, _c in prev[1]}
            new = {m: r for m, r, _c in pos}
            first = all(new.get(m) == r for m, r in old.items())   # only new translations appeared
        if first:   # nothing moved: show right away
            self._inline_emit("show", window=win, items=[{"id": m, "rect": r, "clip": c} for m, r, c in pos])
        else:
            self._inline_emit("moving")

    # ================================================================== translation worker
    def _translate_worker(self):
        while True:
            job = self._tq.get()
            try:
                if job[0] == "adhoc":
                    _, text, target, kind, meta = job
                    out, det = self.translate(text, target)
                    self.emit({"type": "popup", "original": text, "translated": out, "src": det, "tgt": target,
                               "kind": kind, **meta})
            except ProviderError as e:
                self.emit({"type": "chat_error", "text": str(e)})
            except Exception as e:
                log.exception("chat translation failed")
                self.emit({"type": "chat_error", "text": f"Text translation: {e}"})

    def _chat_translate(self, msg, text, edited):
        """Runs in the pool (several at once). Returns the chat_line event, or None to skip the message."""
        cfg = self.cfg
        me = (cfg.get("my_name") or "").strip().lower()
        if me and msg.author.strip().lower() == me:
            return None
        target = cfg.get("target_lang") or self.engine.profile["incoming"]["target_lang"]
        text = text[:2000]
        quick = None
        try:
            from ..textengine import detect_text_language
            quick = detect_text_language(text)
        except Exception:
            pass
        if cfg.get("skip_same_language", True) and quick and L.same_language(quick, target) and len(text) > 25:
            return None
        out, det = self._cached_translate(text, target)
        det = det or quick
        return {"type": "chat_line", "id": msg.id, "author": msg.author or "?", "original": text,
                "translated": out, "src": det, "tgt": target, "edited": edited, "timestamp": msg.timestamp}

    def _emit_in_order(self):
        """Shows translations in the order the messages were written, as soon as each one is ready."""
        while True:
            fut, channel, speak = self._ordered.get()
            try:
                ev = fut.result()
            except ProviderError as e:
                self.emit({"type": "chat_error", "text": str(e)})
                continue
            except Exception as e:
                log.exception("chat translation failed")
                self.emit({"type": "chat_error", "text": f"Text translation: {e}"})
                continue
            if ev is None:
                continue
            text, out, det, target = ev["original"], ev["translated"], ev["src"], ev["tgt"]
            if det and not L.same_language(det, target):
                self.lang_counts[det] += 1
                if sum(self.lang_counts.values()) > 30:   # keep it recent
                    self.lang_counts = collections.Counter(dict(self.lang_counts.most_common(3)))
            self.history.append((ev["author"], text, out))
            same = L.same_language(det, target) or out.strip().lower() == text.strip().lower()
            if same and self.cfg.get("skip_same_language", True):
                continue
            self.inline_ids[ev["id"]] = True
            self.emit(dict(ev, channel=channel))
            if self.cfg.get("speak") and speak:
                self.speak(ev["author"], out, target)

    def speak(self, author: str, text: str, lang: str):
        """Read a chat message out loud with the app voice, in your headphones. It shares the voice with the call
        translations, so two things are never said at the same time. Mode (Text tab):
        queue     - one after the other (when falling behind, the oldest waiting chat messages are skipped)
        interrupt - a new message cuts the chat message that is being read"""
        interrupt = self.cfg.get("speak_mode", "queue") == "interrupt"
        who = author if author and author != "?" else ""
        self.engine.speaker("incoming").say(Utterance(text, lang, kind="chat", who=who),
                                            interrupt_kind="chat" if interrupt else None)

    # ================================================================== selection
    def start_selection(self):
        """Global mouse hook (select-to-translate) + hotkeys."""
        self.stop_selection()
        if self.cfg.get("select_translate", True):
            try:
                from pynput import mouse
                self._mouse = mouse.Listener(on_click=self._on_click)
                self._mouse.daemon = True
                self._mouse.start()
            except Exception as e:
                self.emit({"type": "chat_error", "text": f"Select-to-translate unavailable: {e}"})
        self._install_hotkeys()
        if self.cfg.get("clipboard_watch"):
            self._clip_seq = winutil.clipboard_sequence()
            self._clip_thread = threading.Thread(target=self._clipboard_loop, daemon=True)
            self._clip_thread.start()

    def stop_selection(self):
        if self._mouse is not None:
            try:
                self._mouse.stop()
            except Exception:
                pass
            self._mouse = None
        self._remove_hotkeys()
        self._clip_seq = None

    def _on_click(self, x, y, button, pressed):
        from pynput.mouse import Button
        if button != Button.left:
            return
        now = time.monotonic()
        if pressed:
            self._press = (x, y, now)
            return
        if not self._press:
            return
        px, py, pt = self._press
        self._press = None
        dragged = abs(x - px) + abs(y - py) >= 8
        lt, lx, ly = self._last_click
        double = now - lt < 0.45 and abs(x - lx) + abs(y - ly) < 6
        self._last_click = (now, x, y)
        if dragged or double:
            threading.Thread(target=self._selection_job, args=(x, y, "select"), daemon=True).start()

    def _selection_job(self, x, y, kind, force=False):
        if not self._busy_selection.acquire(blocking=False):
            return
        try:
            time.sleep(0.12)   # let the app finish updating its selection
            if winutil.foreground_is_own_app():
                return
            text = self.get_selected_text(force_clipboard=force)
            text = (text or "").replace("￼", "").strip()
            if len(text) < 2 or len(text) > 4000:
                return
            last, t = self._last_selection
            if text == last and time.monotonic() - t < 3 and not force:
                return
            self._last_selection = (text, time.monotonic())
            target = self.cfg.get("target_lang") or self.engine.profile["incoming"]["target_lang"]
            self.translate_async(text, target, kind, x=x, y=y)
        finally:
            self._busy_selection.release()

    def get_selected_text(self, force_clipboard=False) -> str:
        """Selected text in the foreground app: Discord via UI Automation, others via UIA or the clipboard."""
        hwnd, cls, _pid = winutil.foreground()
        title = winutil.window_title(hwnd)
        is_discord = cls == "Chrome_WidgetWin_1" and title.endswith("Discord")
        scope = self.cfg.get("select_scope", "discord")
        if not is_discord and scope != "everywhere" and not force_clipboard:
            return ""
        text = self._uia_selection(hwnd, is_discord)
        if text or is_discord and not force_clipboard:
            return text
        if cls in winutil.TERMINAL_CLASSES:
            return ""
        return winutil.copy_selection_via_clipboard()

    @staticmethod
    def _uia_selection(hwnd, is_discord) -> str:
        try:
            import uiautomation as auto
        except ImportError:
            return ""
        with auto.UIAutomationInitializerInThread():
            try:
                if is_discord:
                    win = auto.ControlFromHandle(hwnd)
                    doc = win.DocumentControl(searchDepth=10, AutomationId="RootWebArea")
                    if not doc.Exists(0, 0):
                        return ""
                    sel = doc.GetTextPattern().GetSelection()
                    return sel[0].GetText(5000) if sel else ""
                el = auto.GetFocusedControl()
                for _ in range(8):   # walk up to the element that owns a text pattern
                    if el is None:
                        break
                    try:
                        if el.GetPattern(auto.PatternId.TextPattern):
                            sel = el.GetTextPattern().GetSelection()
                            txt = sel[0].GetText(5000) if sel else ""
                            if txt:
                                return txt
                    except Exception:
                        pass
                    el = el.GetParentControl()
            except Exception as e:
                log.debug("uia selection: %s", e)
        return ""

    def _clipboard_loop(self):
        while self._clip_seq is not None:
            time.sleep(0.4)
            seq = winutil.clipboard_sequence()
            if self._clip_seq is None or seq == self._clip_seq:
                continue
            self._clip_seq = seq
            if winutil.foreground_is_own_app():
                continue
            text = winutil.get_clipboard_text().strip()
            if 2 <= len(text) <= 4000 and text != self._last_selection[0]:
                self._last_selection = (text, time.monotonic())
                x, y = winutil.cursor_pos()
                target = self.cfg.get("target_lang") or self.engine.profile["incoming"]["target_lang"]
                self.translate_async(text, target, "clipboard", x=x, y=y)

    # ================================================================== hotkeys
    def _install_hotkeys(self):
        try:
            import keyboard
        except ImportError:
            return
        actions = [("hotkey_selection", self.hotkey_translate_selection),
                   ("hotkey_draft", self.hotkey_translate_draft),
                   ("hotkey_ocr", lambda: self.emit({"type": "ocr_request"})),
                   ("hotkey_inline", lambda: self.emit({"type": "inline_toggle"}))]
        for key, fn in actions:
            combo = (self.cfg.get(key) or "").strip()
            if not combo:
                continue
            try:
                self._hotkeys.append(keyboard.add_hotkey(combo, lambda fn=fn: threading.Thread(target=fn,
                                                                                               daemon=True).start()))
            except Exception as e:
                self.emit({"type": "chat_error", "text": f"Hotkey '{combo}': {e}"})

    def _remove_hotkeys(self):
        if not self._hotkeys:
            return
        try:
            import keyboard
            for h in self._hotkeys:
                keyboard.remove_hotkey(h)
        except Exception:
            pass
        self._hotkeys = []

    def hotkey_translate_selection(self):
        winutil.wait_modifiers_released()
        x, y = winutil.cursor_pos()
        self._selection_job(x, y, "hotkey", force=True)

    def compose_target(self) -> str:
        lang = self.cfg.get("compose_lang", "auto")
        if lang == "auto":
            return self.chat_language or self.engine.their_language or self.engine.profile["outgoing"]["target_lang"]
        return lang

    def hotkey_translate_draft(self):
        """Translate the text you typed in the focused message box (Discord or anything) in place."""
        winutil.wait_modifiers_released()
        hwnd, cls, _ = winutil.foreground()
        if cls in winutil.TERMINAL_CLASSES or winutil.foreground_is_own_app():
            return
        old = winutil.get_clipboard_text()
        winutil.send("ctrl+a")
        time.sleep(0.05)
        text = winutil.copy_selection_via_clipboard()
        if not text.strip():
            return
        target = self.compose_target()
        try:
            out, det = self.translate(text, target)
        except Exception as e:
            self.emit({"type": "chat_error", "text": f"Draft translation: {e}"})
            return
        if winutil.foreground()[0] != hwnd:   # user switched windows meanwhile - don't paste somewhere else
            self.emit({"type": "popup", "original": text, "translated": out, "src": det, "tgt": target,
                       "kind": "draft", "x": winutil.cursor_pos()[0], "y": winutil.cursor_pos()[1]})
            return
        winutil.set_clipboard_text(out)
        winutil.send("ctrl+a")
        time.sleep(0.03)
        winutil.send("ctrl+v")
        time.sleep(0.15)
        if self.cfg.get("draft_send"):
            winutil.send("enter")
        time.sleep(0.3)
        winutil.set_clipboard_text(old)
        self.emit({"type": "chat_status", "text": f"Draft translated to {L.name(target)}", "ok": True})

    # ================================================================== send
    def send_to_discord(self, text: str, press_enter: bool) -> str | None:
        """Paste text into Discord's message box (Discord focuses it automatically). Returns an error or None."""
        hwnd = self.discord_hwnd or self._find_discord_hwnd()
        if not hwnd:
            return "Discord window not found."
        old = winutil.get_clipboard_text()
        winutil.set_clipboard_text(text)
        if not winutil.focus_window(hwnd):
            return "Couldn't bring Discord to the front - click Discord once and use Ctrl+V."
        time.sleep(0.25)
        winutil.send("ctrl+v")
        time.sleep(0.15)
        if press_enter:
            winutil.send("enter")
        time.sleep(0.3)
        winutil.set_clipboard_text(old)
        return None

    @staticmethod
    def _find_discord_hwnd():
        found = []
        cb_t = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def cb(h, _):
            if winutil.user32.IsWindowVisible(h) and winutil.window_title(h).endswith("- Discord"):
                found.append(h)
            return True
        winutil.user32.EnumWindows(cb_t(cb), 0)
        return found[0] if found else None

    def shutdown(self):
        self._reader_stop.set()
        self.stop_selection()
