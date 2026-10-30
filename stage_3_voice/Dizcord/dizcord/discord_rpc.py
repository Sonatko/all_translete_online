"""Who is talking in your Discord voice channel - from the Discord app itself (its local RPC connection).

Discord tells authorised apps on the same PC when each person in your voice channel starts/stops talking
(SPEAKING_START / SPEAKING_STOP) and their names. Dizcord lines those times up with each sentence it hears, so the
app voice can say "Jo: …" and the subtitles show who said what. Nothing is sent anywhere except the one-time
login (Discord's own OAuth2 endpoint); no audio or messages are read through it.

Needs your own Discord application (free, developer portal): its Application ID + Client Secret, and
http://localhost added as an OAuth2 redirect. The first time, Discord shows an "Authorize" window - click it once.
"""
from __future__ import annotations

import collections
import ctypes
import json
import logging
import msvcrt
import os
import struct
import threading
import time
import uuid

import requests

log = logging.getLogger("dizcord.rpc")

TOKEN_KEY = "discord_rpc_token"         # KeyStore entries (data/keys.json, never in profiles)
SECRET_KEY = "discord_rpc_secret"
SCOPES = ["rpc", "rpc.voice.read"]
REDIRECT = "http://localhost"
_OP_HANDSHAKE, _OP_FRAME, _OP_CLOSE, _OP_PING, _OP_PONG = 0, 1, 2, 3, 4


class RPCError(Exception):
    pass


class _Pipe:
    """Discord's local IPC pipe. Reads only what is available (PeekNamedPipe) so writes never wait on a read."""

    def __init__(self):
        self.f = None
        for i in range(10):
            try:
                self.f = open(rf"\\?\pipe\discord-ipc-{i}", "r+b", buffering=0)
                break
            except OSError:
                continue
        if self.f is None:
            raise RPCError("Discord is not running (no RPC pipe)")
        self.h = msvcrt.get_osfhandle(self.f.fileno())
        self.buf = b""
        self.wlock = threading.Lock()

    def send(self, op: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        with self.wlock:
            self.f.write(struct.pack("<II", op, len(data)) + data)

    def _available(self) -> int:
        avail = ctypes.c_ulong(0)
        if not ctypes.windll.kernel32.PeekNamedPipe(self.h, None, 0, None, ctypes.byref(avail), None):
            raise RPCError("Discord closed the connection")
        return avail.value

    def recv(self, timeout: float) -> tuple[int, dict] | None:
        end = time.monotonic() + timeout
        while True:
            if len(self.buf) >= 8:
                op, n = struct.unpack("<II", self.buf[:8])
                if len(self.buf) >= 8 + n:
                    body, self.buf = self.buf[8:8 + n], self.buf[8 + n:]
                    return op, json.loads(body.decode("utf-8") or "{}")
            n = self._available()
            if n:
                self.buf += self.f.read(n)
                continue
            if time.monotonic() >= end:
                return None
            time.sleep(0.02)

    def close(self):
        try:
            self.f.close()
        except Exception:  # noqa: BLE001
            pass


class SpeakingTracker:
    """Keeps a connection to Discord and a timeline of who talked when (time.monotonic())."""

    def __init__(self, client_id: str, keys, on_status=None):
        self.client_id = (client_id or "").strip()
        self.keys = keys
        self.on_status = on_status or (lambda text, ok: None)
        self.names: dict[str, str] = {}                     # user id -> name shown in the channel
        self.me = ""
        self.channel = None
        self.timeline: dict[str, collections.deque] = {}    # user id -> [start, end|None] intervals
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._pipe = None
        self._pending: dict[str, dict] = {}
        self._thread = threading.Thread(target=self._run, name="discord-rpc", daemon=True)
        self.connected = False

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._pipe:
            self._pipe.close()

    # ------------------------------------------------------------------ who talked
    def speakers_between(self, t0: float, t1: float, min_overlap: float = 0.15) -> list[str]:
        """Names of the people who talked between t0 and t1, most talking first (you are never included)."""
        out = []
        now = time.monotonic()
        with self._lock:
            for uid, spans in self.timeline.items():
                if uid == self.me:
                    continue
                talk = sum(max(0.0, min(t1, e if e is not None else now) - max(t0, s)) for s, e in spans)
                if talk >= min_overlap:
                    out.append((talk, self.names.get(uid, "?")))
        return [n for _t, n in sorted(out, reverse=True)]

    def _speaking(self, uid: str, on: bool):
        now = time.monotonic()
        with self._lock:
            spans = self.timeline.setdefault(uid, collections.deque(maxlen=200))
            if on:
                if not spans or spans[-1][1] is not None:
                    spans.append([now, None])
            elif spans and spans[-1][1] is None:
                spans[-1][1] = now
            for s in list(self.timeline.values()):          # forget what is older than 2 minutes
                while s and s[0][1] is not None and now - s[0][1] > 120:
                    s.popleft()

    # ------------------------------------------------------------------ connection
    def _run(self):
        delay = 2.0
        while not self._stop.is_set():
            try:
                self._session()
                delay = 2.0
            except RPCError as e:
                self.connected = False
                self.on_status(str(e), False)
                if any(w in str(e).lower() for w in ("authoriz", "secret", "application", "login failed")):
                    return                             # needs the user: no new Authorize windows until settings change
            except Exception as e:  # noqa: BLE001
                self.connected = False
                log.exception("Discord RPC")
                self.on_status(f"Discord connection: {e}", False)
            if self._pipe:
                self._pipe.close()
                self._pipe = None
            self._stop.wait(delay)
            delay = min(delay * 2, 30.0) if delay < 60 else delay

    def _cmd(self, cmd: str, args: dict | None = None, evt: str | None = None, timeout: float = 10.0) -> dict:
        nonce = str(uuid.uuid4())
        msg = {"cmd": cmd, "args": args or {}, "nonce": nonce}
        if evt:
            msg["evt"] = evt
        slot = {"event": threading.Event(), "reply": None}
        self._pending[nonce] = slot
        self._pipe.send(_OP_FRAME, msg)
        end = time.monotonic() + timeout
        while not slot["event"].is_set():          # read here until our reply comes (events are handled too)
            if time.monotonic() > end:
                self._pending.pop(nonce, None)
                raise RPCError(f"Discord did not answer {cmd}")
            self._pump(0.2)
        reply = slot["reply"]
        if reply.get("evt") == "ERROR":
            raise RPCError(f"{cmd}: {reply.get('data', {}).get('message', 'error')}")
        return reply.get("data") or {}

    def _pump(self, timeout: float):
        got = self._pipe.recv(timeout)
        if got is None:
            return
        op, msg = got
        if op == _OP_PING:
            self._pipe.send(_OP_PONG, msg)
            return
        if op == _OP_CLOSE:
            raise RPCError(f"Discord closed the connection: {msg.get('message', '')}")
        nonce = msg.get("nonce")
        if nonce and nonce in self._pending:
            slot = self._pending.pop(nonce)
            slot["reply"] = msg
            slot["event"].set()
            return
        if msg.get("cmd") == "DISPATCH":
            self._event(msg.get("evt"), msg.get("data") or {})

    def _event(self, evt: str, data: dict):
        if evt == "SPEAKING_START":
            self._speaking(str(data.get("user_id")), True)
        elif evt == "SPEAKING_STOP":
            self._speaking(str(data.get("user_id")), False)
        elif evt in ("VOICE_STATE_CREATE", "VOICE_STATE_UPDATE"):
            self._remember(data)
        elif evt == "VOICE_CHANNEL_SELECT":
            self._channel_changed = (data.get("channel_id"),)      # a tuple: "left the channel" is (None,)

    def _remember(self, vs: dict):
        user = vs.get("user") or {}
        uid = str(user.get("id") or "")
        if uid:
            self.names[uid] = vs.get("nick") or user.get("global_name") or user.get("username") or "?"

    def _session(self):
        if not self.client_id:
            raise RPCError("Add your Discord Application ID (Output tab → Who is talking)")
        self._pipe = _Pipe()
        self._pipe.send(_OP_HANDSHAKE, {"v": 1, "client_id": self.client_id})
        got = self._pipe.recv(10)
        if got is None:
            raise RPCError("Discord did not answer")
        op, msg = got
        if op == _OP_CLOSE or msg.get("evt") != "READY":
            raise RPCError(f"Discord refused the application id: {msg.get('message') or msg}")
        self._authenticate()
        self.connected = True
        self._channel_changed = None
        self._cmd("SUBSCRIBE", evt="VOICE_CHANNEL_SELECT")
        self._watch((self._cmd("GET_SELECTED_VOICE_CHANNEL") or {}))
        while not self._stop.is_set():
            self._pump(0.5)
            if self._channel_changed is not None:
                (cid,), self._channel_changed = self._channel_changed, None
                self._watch(self._cmd("GET_CHANNEL", {"channel_id": cid}) if cid else {})

    def _watch(self, channel: dict):
        """Follow the speaking events of the voice channel you are in (or none)."""
        old = self.channel
        if old:
            for evt in ("SPEAKING_START", "SPEAKING_STOP", "VOICE_STATE_CREATE", "VOICE_STATE_UPDATE"):
                try:
                    self._cmd("UNSUBSCRIBE", {"channel_id": old}, evt=evt)
                except RPCError:
                    pass
        cid = channel.get("id") if channel else None
        self.channel = cid
        with self._lock:
            self.timeline.clear()
        if not cid:
            self.on_status("Connected to Discord - join a voice channel to see who is talking", True)
            return
        for vs in channel.get("voice_states") or []:
            self._remember(vs)
        for evt in ("SPEAKING_START", "SPEAKING_STOP", "VOICE_STATE_CREATE", "VOICE_STATE_UPDATE"):
            self._cmd("SUBSCRIBE", {"channel_id": cid}, evt=evt)
        self.on_status(f"Who is talking: following {channel.get('name') or 'the voice channel'} "
                       f"({len(channel.get('voice_states') or [])} people)", True)

    # ------------------------------------------------------------------ login
    def _token(self) -> dict:
        try:
            return json.loads(self.keys.get(TOKEN_KEY) or "{}")
        except ValueError:
            return {}

    def _save_token(self, tok: dict):
        tok = dict(tok, expires_at=time.time() + float(tok.get("expires_in", 604800)) - 60)
        self.keys.set(TOKEN_KEY, json.dumps({k: tok[k] for k in ("access_token", "refresh_token", "expires_at")
                                             if k in tok}))
        self.keys.save()

    def _oauth(self, data: dict) -> dict:
        secret = self.keys.get(SECRET_KEY)
        if not secret:
            raise RPCError("Add your Discord application's Client Secret (Output tab → Who is talking)")
        base = {"client_id": self.client_id, "client_secret": secret}
        last = ""
        for extra in ({"redirect_uri": REDIRECT}, {}):
            r = requests.post("https://discord.com/api/oauth2/token", data={**base, **data, **extra}, timeout=15)
            if r.ok:
                return r.json()
            last = r.text[:200]
            if "redirect" not in last.lower():
                break
        raise RPCError(f"Discord login failed: {last}")

    def _authenticate(self):
        tok = self._token()
        if tok.get("refresh_token") and tok.get("expires_at", 0) < time.time():
            try:
                tok = self._oauth({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]})
                self._save_token(tok)
            except RPCError:
                tok = {}
        if tok.get("access_token"):
            try:
                me = self._cmd("AUTHENTICATE", {"access_token": tok["access_token"]})
                self.me = str((me.get("user") or {}).get("id") or "")
                return
            except RPCError:
                pass                                       # expired/revoked: authorise again
        self.on_status("Click 'Authorize' in the Discord window that just opened…", True)
        try:
            data = self._cmd("AUTHORIZE", {"client_id": self.client_id, "scopes": SCOPES}, timeout=180)
        except RPCError as e:
            raise RPCError(f"Not authorized in Discord ({e})") from e
        tok = self._oauth({"grant_type": "authorization_code", "code": data.get("code", "")})
        self._save_token(tok)
        me = self._cmd("AUTHENTICATE", {"access_token": tok["access_token"]})
        self.me = str((me.get("user") or {}).get("id") or "")


def available() -> bool:
    return os.name == "nt"
