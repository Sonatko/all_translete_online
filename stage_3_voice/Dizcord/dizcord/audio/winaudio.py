"""Windows per-application audio (Core Audio through comtypes):

- AppLoopbackSource: records ONLY what one app (Discord) plays - WASAPI process loopback, Windows 10 2004+.
  The app's own translated voice, games and music are never captured, so listening never has to pause.
- AppVolume: the app's volume in the Windows volume mixer. "Hear people: off" turns Discord down to 0.1 % and
  the capture is amplified back by the same factor (the mixer volume is applied before the process-loopback tap,
  linearly, in float - measured lossless), so you hear only the translations while the app still hears Discord.
- capture_devices_of(): which recording devices an app is using (is Discord sending your real microphone?).

All COM work runs on threads initialised as multi-threaded apartments (devices.ensure_com).
"""
from __future__ import annotations

import concurrent.futures
import ctypes
import json
import logging
import os
import sys
import threading
import time
from ctypes import POINTER, byref, c_float, c_int, c_uint32, c_uint64, c_void_p, wintypes

import numpy as np

from . import devices
from .capture import Source

log = logging.getLogger("dizcord.winaudio")

DISCORD_EXES = ("discord.exe", "discordptb.exe", "discordcanary.exe", "discorddevelopment.exe")
HEAR_OFF_FACTOR = 0.001          # -60 dB in the mixer: inaudible, still perfectly recoverable from the capture
_SR = 48000


# ============================================================================ processes
class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


def processes() -> list[tuple[int, int, str]]:
    """[(pid, parent pid, exe name lower-case)] of every running process."""
    if os.name != "nt":
        return []
    k32 = ctypes.windll.kernel32
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k32.CreateToolhelp32Snapshot(2, 0)          # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return []
    out = []
    try:
        e = _PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        ok = k32.Process32FirstW(snap, byref(e))
        while ok:
            out.append((int(e.th32ProcessID), int(e.th32ParentProcessID), e.szExeFile.lower()))
            ok = k32.Process32NextW(snap, byref(e))
    finally:
        k32.CloseHandle(snap)
    return out


def app_pids(app: str = "discord") -> tuple[int | None, set[int]]:
    """(root pid, every pid of the app). app = "discord", an exe name ("game.exe") or "pid:1234"."""
    procs = processes()
    if app.startswith("pid:"):
        root = int(app[4:])
        tree, changed = {root}, True
        while changed:                                   # the root and all its children
            changed = False
            for pid, ppid, _ in procs:
                if ppid in tree and pid not in tree:
                    tree.add(pid)
                    changed = True
        return (root if any(p == root for p, _, _ in procs) else None), tree
    names = DISCORD_EXES if app == "discord" else (app.lower(),)
    mine = {pid: ppid for pid, ppid, exe in procs if exe in names}
    roots = [pid for pid, ppid in mine.items() if ppid not in mine]
    return (min(roots) if roots else None), set(mine)


def process_loopback_supported() -> bool:
    if os.name != "nt":
        return False
    try:
        return sys.getwindowsversion().build >= 19041      # Windows 10 2004
    except Exception:
        return False


# ============================================================================ COM interfaces
def _comtypes():
    """Import comtypes from any thread (its import initialises COM and fails if the thread mode differs)."""
    try:
        import comtypes
    except OSError:
        sys.coinit_flags = 0 if getattr(sys, "coinit_flags", 2) == 2 else 2
        import comtypes
    return comtypes


_IFACES: dict = {}


def _ifaces() -> dict:
    if _IFACES:
        return _IFACES
    ct = _comtypes()
    from comtypes import COMMETHOD, GUID, IUnknown, COMObject
    HR = ctypes.HRESULT

    class WAVEFORMATEX(ctypes.Structure):
        _fields_ = [("wFormatTag", wintypes.WORD), ("nChannels", wintypes.WORD), ("nSamplesPerSec", wintypes.DWORD),
                    ("nAvgBytesPerSec", wintypes.DWORD), ("nBlockAlign", wintypes.WORD),
                    ("wBitsPerSample", wintypes.WORD), ("cbSize", wintypes.WORD)]

    class PROPERTYKEY(ctypes.Structure):
        _fields_ = [("fmtid", GUID), ("pid", wintypes.DWORD)]

    class PROPVARIANT(ctypes.Structure):
        _fields_ = [("vt", wintypes.USHORT), ("r1", wintypes.WORD), ("r2", wintypes.WORD), ("r3", wintypes.WORD),
                    ("p", c_void_p), ("p2", c_void_p)]

    class IAudioCaptureClient(IUnknown):
        _iid_ = GUID("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
        _methods_ = [
            COMMETHOD([], HR, "GetBuffer", (["out"], POINTER(POINTER(ctypes.c_byte)), "data"),
                      (["out"], POINTER(c_uint32), "frames"), (["out"], POINTER(wintypes.DWORD), "flags"),
                      (["out"], POINTER(c_uint64), "pos"), (["out"], POINTER(c_uint64), "qpc")),
            COMMETHOD([], HR, "ReleaseBuffer", (["in"], c_uint32, "frames")),
            COMMETHOD([], HR, "GetNextPacketSize", (["out"], POINTER(c_uint32), "frames")),
        ]

    class IAudioClient(IUnknown):
        _iid_ = GUID("{1CB9AD4C-DBFA-4c32-B178-C2F568A703B2}")
        _methods_ = [
            COMMETHOD([], HR, "Initialize", (["in"], c_int, "mode"), (["in"], wintypes.DWORD, "flags"),
                      (["in"], ctypes.c_longlong, "dur"), (["in"], ctypes.c_longlong, "period"),
                      (["in"], POINTER(WAVEFORMATEX), "fmt"), (["in"], POINTER(GUID), "session")),
            COMMETHOD([], HR, "GetBufferSize", (["out"], POINTER(c_uint32), "n")),
            COMMETHOD([], HR, "GetStreamLatency", (["out"], POINTER(ctypes.c_longlong), "n")),
            COMMETHOD([], HR, "GetCurrentPadding", (["out"], POINTER(c_uint32), "n")),
            COMMETHOD([], HR, "IsFormatSupported", (["in"], c_int, "mode"), (["in"], POINTER(WAVEFORMATEX), "fmt"),
                      (["out"], POINTER(POINTER(WAVEFORMATEX)), "closest")),
            COMMETHOD([], HR, "GetMixFormat", (["out"], POINTER(POINTER(WAVEFORMATEX)), "fmt")),
            COMMETHOD([], HR, "GetDevicePeriod", (["out"], POINTER(ctypes.c_longlong), "a"),
                      (["out"], POINTER(ctypes.c_longlong), "b")),
            COMMETHOD([], HR, "Start"),
            COMMETHOD([], HR, "Stop"),
            COMMETHOD([], HR, "Reset"),
            COMMETHOD([], HR, "SetEventHandle", (["in"], wintypes.HANDLE, "h")),
            COMMETHOD([], HR, "GetService", (["in"], POINTER(GUID), "iid"), (["out"], POINTER(c_void_p), "obj")),
        ]

    class IActivateAudioInterfaceAsyncOperation(IUnknown):
        _iid_ = GUID("{72A22D78-CDE4-431D-B8CC-843A71199B6D}")
        _methods_ = [COMMETHOD([], HR, "GetActivateResult", (["out"], POINTER(HR), "hr"),
                               (["out"], POINTER(POINTER(IUnknown)), "iface"))]

    class IActivateAudioInterfaceCompletionHandler(IUnknown):
        _iid_ = GUID("{41D949AB-9862-444A-80F6-C261334DA5EB}")
        _methods_ = [COMMETHOD([], HR, "ActivateCompleted",
                               (["in"], POINTER(IActivateAudioInterfaceAsyncOperation), "op"))]

    class IAgileObject(IUnknown):
        _iid_ = GUID("{94ea2b94-e9cc-49e0-c0ff-ee64ca8f5b90}")
        _methods_ = []

    class Handler(COMObject):
        _com_interfaces_ = [IActivateAudioInterfaceCompletionHandler, IAgileObject]

        def __init__(self):
            super().__init__()
            self.done = threading.Event()
            self.result = None

        def ActivateCompleted(self, op):
            try:
                self.result = op.GetActivateResult()
            except Exception as e:  # noqa: BLE001
                self.result = (e, None)
            self.done.set()
            return 0

    class IPropertyStore(IUnknown):
        _iid_ = GUID("{886d8eeb-8cf2-4446-8d02-cdba1dbdcf99}")
        _methods_ = [
            COMMETHOD([], HR, "GetCount", (["out"], POINTER(wintypes.DWORD), "n")),
            COMMETHOD([], HR, "GetAt", (["in"], wintypes.DWORD, "i"), (["out"], POINTER(PROPERTYKEY), "k")),
            COMMETHOD([], HR, "GetValue", (["in"], POINTER(PROPERTYKEY), "k"), (["out"], POINTER(PROPVARIANT), "v")),
        ]

    class IMMDevice(IUnknown):
        _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
        _methods_ = [
            COMMETHOD([], HR, "Activate", (["in"], POINTER(GUID), "iid"), (["in"], wintypes.DWORD, "ctx"),
                      (["in"], c_void_p, "params"), (["out"], POINTER(c_void_p), "obj")),
            COMMETHOD([], HR, "OpenPropertyStore", (["in"], wintypes.DWORD, "access"),
                      (["out"], POINTER(POINTER(IPropertyStore)), "store")),
            COMMETHOD([], HR, "GetId", (["out"], POINTER(wintypes.LPWSTR), "id")),
            COMMETHOD([], HR, "GetState", (["out"], POINTER(wintypes.DWORD), "state")),
        ]

    class IMMDeviceCollection(IUnknown):
        _iid_ = GUID("{0BD7A1BE-7A1A-44DB-8397-CC5392387B5E}")
        _methods_ = [
            COMMETHOD([], HR, "GetCount", (["out"], POINTER(c_uint32), "n")),
            COMMETHOD([], HR, "Item", (["in"], c_uint32, "i"), (["out"], POINTER(POINTER(IMMDevice)), "dev")),
        ]

    class IMMDeviceEnumerator(IUnknown):
        _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        _methods_ = [
            COMMETHOD([], HR, "EnumAudioEndpoints", (["in"], c_int, "flow"), (["in"], wintypes.DWORD, "mask"),
                      (["out"], POINTER(POINTER(IMMDeviceCollection)), "coll")),
        ]

    class ISimpleAudioVolume(IUnknown):
        _iid_ = GUID("{87CE5498-68D6-44E5-9215-6DA47EF883D8}")
        _methods_ = [
            COMMETHOD([], HR, "SetMasterVolume", (["in"], c_float, "v"), (["in"], POINTER(GUID), "ctx")),
            COMMETHOD([], HR, "GetMasterVolume", (["out"], POINTER(c_float), "v")),
            COMMETHOD([], HR, "SetMute", (["in"], wintypes.BOOL, "m"), (["in"], POINTER(GUID), "ctx")),
            COMMETHOD([], HR, "GetMute", (["out"], POINTER(wintypes.BOOL), "m")),
        ]

    class IAudioSessionControl(IUnknown):
        _iid_ = GUID("{F4B1A599-7266-4319-A8CA-E70ACB11E8CD}")
        _methods_ = [
            COMMETHOD([], HR, "GetState", (["out"], POINTER(c_int), "s")),
            COMMETHOD([], HR, "GetDisplayName", (["out"], POINTER(wintypes.LPWSTR), "n")),
            COMMETHOD([], HR, "SetDisplayName", (["in"], wintypes.LPCWSTR, "n"), (["in"], POINTER(GUID), "c")),
            COMMETHOD([], HR, "GetIconPath", (["out"], POINTER(wintypes.LPWSTR), "n")),
            COMMETHOD([], HR, "SetIconPath", (["in"], wintypes.LPCWSTR, "n"), (["in"], POINTER(GUID), "c")),
            COMMETHOD([], HR, "GetGroupingParam", (["out"], POINTER(GUID), "g")),
            COMMETHOD([], HR, "SetGroupingParam", (["in"], POINTER(GUID), "g"), (["in"], POINTER(GUID), "c")),
            COMMETHOD([], HR, "RegisterAudioSessionNotification", (["in"], c_void_p, "x")),
            COMMETHOD([], HR, "UnregisterAudioSessionNotification", (["in"], c_void_p, "x")),
        ]

    class IAudioSessionControl2(IAudioSessionControl):
        _iid_ = GUID("{bfb7ff88-7239-4fc9-8fa2-07c950be9c6d}")
        _methods_ = [
            COMMETHOD([], HR, "GetSessionIdentifier", (["out"], POINTER(wintypes.LPWSTR), "n")),
            COMMETHOD([], HR, "GetSessionInstanceIdentifier", (["out"], POINTER(wintypes.LPWSTR), "n")),
            COMMETHOD([], HR, "GetProcessId", (["out"], POINTER(wintypes.DWORD), "pid")),
        ]

    class IAudioSessionEnumerator(IUnknown):
        _iid_ = GUID("{E2F5BB11-0570-40CA-ACDD-3AA01277DEE8}")
        _methods_ = [
            COMMETHOD([], HR, "GetCount", (["out"], POINTER(c_int), "n")),
            COMMETHOD([], HR, "GetSession", (["in"], c_int, "i"),
                      (["out"], POINTER(POINTER(IAudioSessionControl)), "s")),
        ]

    class IAudioSessionManager2(IUnknown):
        _iid_ = GUID("{77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F}")
        _methods_ = [
            COMMETHOD([], HR, "GetAudioSessionControl", (["in"], POINTER(GUID), "g"), (["in"], wintypes.DWORD, "f"),
                      (["out"], POINTER(c_void_p), "s")),
            COMMETHOD([], HR, "GetSimpleAudioVolume", (["in"], POINTER(GUID), "g"), (["in"], wintypes.DWORD, "f"),
                      (["out"], POINTER(c_void_p), "s")),
            COMMETHOD([], HR, "GetSessionEnumerator", (["out"], POINTER(POINTER(IAudioSessionEnumerator)), "e")),
        ]

    _IFACES.update(locals())
    _IFACES["ct"] = ct
    return _IFACES


# ============================================================================ process loopback capture
class _ActParams(ctypes.Structure):
    _fields_ = [("ActivationType", c_int), ("TargetProcessId", wintypes.DWORD), ("ProcessLoopbackMode", c_int)]


class _Blob(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.ULONG), ("pBlobData", c_void_p)]


class _BlobVariant(ctypes.Structure):
    _fields_ = [("vt", wintypes.USHORT), ("r1", wintypes.WORD), ("r2", wintypes.WORD), ("r3", wintypes.WORD),
                ("blob", _Blob)]


def _activate_process_loopback(pid: int):
    """IAudioClient that records the process tree of pid (must run on an MTA thread)."""
    I = _ifaces()
    params = _ActParams(1, pid, 0)            # PROCESS_LOOPBACK, INCLUDE_TARGET_PROCESS_TREE
    pv = _BlobVariant()
    pv.vt = 65                                # VT_BLOB
    pv.blob.cbSize = ctypes.sizeof(params)
    pv.blob.pBlobData = ctypes.cast(byref(params), c_void_p)
    handler = I["Handler"]()
    fn = ctypes.windll.Mmdevapi.ActivateAudioInterfaceAsync
    fn.argtypes = [wintypes.LPCWSTR, POINTER(I["GUID"]), POINTER(_BlobVariant),
                   POINTER(I["IActivateAudioInterfaceCompletionHandler"]), POINTER(c_void_p)]
    fn.restype = ctypes.HRESULT
    op = c_void_p()
    fn("VAD\\Process_Loopback", byref(I["IAudioClient"]._iid_), byref(pv),
       handler.QueryInterface(I["IActivateAudioInterfaceCompletionHandler"]), byref(op))
    if not handler.done.wait(5):
        raise RuntimeError("Windows did not answer the app-audio request")
    hr, iface = handler.result
    if isinstance(hr, Exception) or hr != 0 or not iface:
        raise RuntimeError(f"app audio capture refused ({hr})")
    client = iface.QueryInterface(I["IAudioClient"])
    fmt = I["WAVEFORMATEX"](3, 2, _SR, _SR * 8, 8, 32, 0)       # float32 stereo 48 kHz
    # LOOPBACK | AUTOCONVERTPCM | SRC_DEFAULT_QUALITY, 100 ms buffer
    client.Initialize(0, 0x00020000 | 0x80000000 | 0x08000000, 1_000_000, 0, byref(fmt), None)
    cap = ctypes.cast(client.GetService(byref(I["IAudioCaptureClient"]._iid_)), POINTER(I["IAudioCaptureClient"]))
    return client, cap


class AppLoopbackSource(Source):
    """Records only what one application plays (default: Discord), whatever device it plays on.

    Keeps running when Discord is closed/restarted (feeds silence and re-attaches). `factor` is the volume the app
    was turned down to in the mixer; the capture is divided by it."""

    samplerate = _SR

    def __init__(self, app: str, on_audio, on_status=None):
        super().__init__(on_audio)
        self.app = app or "discord"
        self.on_status = on_status or (lambda _t: None)
        self._stop = threading.Event()
        self._thread = None
        self._ready = threading.Event()
        self._error = None
        self.pid = None
        self.factor = 1.0
        self._blank_until = 0.0
        self.attached = False

    def set_factor(self, factor: float):
        """The app's mixer volume changed by this factor: compensate (and drop the ~100 ms where it changes)."""
        if abs(factor - self.factor) > 1e-6:
            self._blank_until = time.monotonic() + 0.1
            self.factor = max(1e-5, float(factor))

    def blank(self, seconds: float = 0.1):
        self._blank_until = time.monotonic() + seconds

    def start(self):
        if not process_loopback_supported():
            raise RuntimeError("needs Windows 10 version 2004 or newer")
        self._thread = threading.Thread(target=self._run, name="app-capture", daemon=True)
        self._thread.start()
        self._ready.wait(8)
        if self._error:
            raise RuntimeError(self._error)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _feed(self, x: np.ndarray):
        now = time.monotonic()
        if now < self._blank_until:
            x = np.zeros_like(x)
        elif self.factor != 1.0:
            x = x / self.factor
            if len(x) and float(np.max(np.abs(x))) > 1.5:   # a stream that wasn't turned down yet: not usable
                x = np.zeros_like(x)
        try:
            self.on_audio(x.astype(np.float32, copy=False))
        except Exception:
            log.exception("app capture callback failed")

    def _run(self):
        devices.ensure_com()
        client = cap = None
        first = True
        last_check = 0.0
        silence = np.zeros(int(_SR * 0.02), dtype=np.float32)
        try:
            _ifaces()
        except Exception as e:  # noqa: BLE001
            self._error = f"comtypes is missing ({e})"
            self._ready.set()
            return
        while not self._stop.is_set():
            if client is None:
                root, _ = app_pids(self.app)
                if root is None:
                    if first:
                        self.on_status("Waiting for Discord to open…")
                        first = False
                        self._ready.set()
                    self.attached = False
                    self._feed(silence)                     # keep the clock running for voice detection
                    self._stop.wait(0.02)
                    continue
                try:
                    client, cap = _activate_process_loopback(root)
                    client.Start()
                    self.pid, self.attached = root, True
                    log.info("Capturing app audio of pid %s (%s)", root, self.app)
                    if not first:
                        self.on_status("Discord found - listening to it")
                    first = False
                    self._ready.set()
                except Exception as e:  # noqa: BLE001
                    client = cap = None
                    if first:
                        self._error = str(e)
                        self._ready.set()
                        return
                    self._stop.wait(2.0)
                    continue
            try:
                n = cap.GetNextPacketSize()
                got = False
                while n:
                    data, frames, flags, _p, _q = cap.GetBuffer()
                    if frames:
                        if flags & 2:                       # AUDCLNT_BUFFERFLAGS_SILENT
                            x = np.zeros(frames, dtype=np.float32)
                        else:
                            x = np.ctypeslib.as_array(ctypes.cast(data, POINTER(ctypes.c_float)), (frames * 2,))
                            x = x.reshape(-1, 2).mean(axis=1).astype(np.float32)
                        self._feed(x)
                        got = True
                    cap.ReleaseBuffer(frames)
                    n = cap.GetNextPacketSize()
                now = time.monotonic()
                if now - last_check > 3.0:                  # Discord closed/restarted -> attach to the new one
                    last_check = now
                    root, _ = app_pids(self.app)
                    if root != self.pid:
                        raise RuntimeError("target app restarted")
                if not got:
                    self._stop.wait(0.01)
            except Exception as e:  # noqa: BLE001
                log.info("app capture re-attaching: %s", e)
                try:
                    client.Stop()
                except Exception:
                    pass
                client = cap = None
                self.attached = False
        if client is not None:
            try:
                client.Stop()
            except Exception:
                pass


# ============================================================================ sessions (mixer)
_pool = concurrent.futures.ThreadPoolExecutor(1, thread_name_prefix="audio-sessions", initializer=devices.ensure_com)


def _on_com_thread(fn, *args, timeout: float = 5.0):
    return _pool.submit(fn, *args).result(timeout)


def _sessions(flow: int):
    """[(device name, pid, state, ISimpleAudioVolume, session id)] for every session of every active device."""
    I = _ifaces()
    ct = I["ct"]
    en = ct.CoCreateInstance(I["GUID"]("{BCDE0395-E52F-467C-8E3D-C4579291692E}"), I["IMMDeviceEnumerator"],
                             ct.CLSCTX_ALL)
    key = I["PROPERTYKEY"](I["GUID"]("{a45c254e-df1c-4efd-8020-67d146a850e0}"), 14)   # friendly name
    coll = en.EnumAudioEndpoints(flow, 1)
    out = []
    for i in range(coll.GetCount()):
        try:
            dev = coll.Item(i)
            v = dev.OpenPropertyStore(0).GetValue(byref(key))
            name = ctypes.wstring_at(v.p) if v.vt == 31 and v.p else ""
            mgr = ctypes.cast(dev.Activate(byref(I["IAudioSessionManager2"]._iid_), ct.CLSCTX_ALL, None),
                              POINTER(I["IAudioSessionManager2"]))
            se = mgr.GetSessionEnumerator()
            for j in range(se.GetCount()):
                ctl = se.GetSession(j)
                c2 = ctl.QueryInterface(I["IAudioSessionControl2"])
                out.append((name, int(c2.GetProcessId()), int(ctl.GetState()),
                            ctl.QueryInterface(I["ISimpleAudioVolume"]), c2.GetSessionIdentifier() or ""))
        except Exception as e:  # noqa: BLE001 - one broken device must not hide the others
            log.debug("audio sessions of device %d: %s", i, e)
    return out


def capture_devices_of(app: str = "discord") -> list[str]:
    """Recording devices the app is actively using right now (e.g. Discord's microphone while in a call)."""
    def work():
        _, pids = app_pids(app)
        return sorted({name for name, pid, state, _v, _s in _sessions(1) if pid in pids and state == 1})
    try:
        return _on_com_thread(work)
    except Exception as e:  # noqa: BLE001
        log.debug("capture_devices_of: %s", e)
        return []


def render_devices_of(app: str = "discord") -> list[str]:
    def work():
        _, pids = app_pids(app)
        return sorted({name for name, pid, state, _v, _s in _sessions(0) if pid in pids and state == 1})
    try:
        return _on_com_thread(work)
    except Exception as e:  # noqa: BLE001
        log.debug("render_devices_of: %s", e)
        return []


class AppVolume:
    """Turns an app (Discord) down/up in the Windows volume mixer, remembering the user's own levels.

    The original levels are also written to a small file, so if Dizcord is closed abruptly they are restored the
    next time it starts (Windows remembers mixer levels per app)."""

    def __init__(self, app: str = "discord", restore_file=None):
        self.app = app
        self.factor = 1.0
        self.restore_file = restore_file
        self._orig: dict[str, float] = {}       # session id -> the user's level
        self.muted_by_user = False

    def apply(self, factor: float) -> bool:
        """Set every session of the app to (its own level x factor). Returns True if a session had to change."""
        self.factor = factor
        try:
            return _on_com_thread(self._apply)
        except Exception as e:  # noqa: BLE001
            log.debug("app volume: %s", e)
            return False

    def _apply(self) -> bool:
        _, pids = app_pids(self.app)
        changed, muted = False, False
        for _name, pid, _state, vol, sid in _sessions(0):
            if pid not in pids:
                continue
            key = sid or f"{pid}"
            cur = float(vol.GetMasterVolume())
            if key not in self._orig:
                # a level that looks like ours (left over after a crash) is not the user's own level
                self._orig[key] = cur if cur > HEAR_OFF_FACTOR * 1.5 else 1.0
                self._save()
            want = max(0.0, min(1.0, self._orig[key] * self.factor))
            if abs(cur - want) > 1e-4:
                vol.SetMasterVolume(want, None)
                changed = True
            muted = muted or bool(vol.GetMute())
        self.muted_by_user = muted
        return changed

    def restore(self):
        self.factor = 1.0
        try:
            _on_com_thread(self._restore)
        except Exception as e:  # noqa: BLE001
            log.debug("app volume restore: %s", e)

    def _restore(self):
        _, pids = app_pids(self.app)
        saved = self._load()
        saved.update(self._orig)
        left = dict(saved)
        for _name, pid, _state, vol, sid in _sessions(0):
            if pid in pids and (sid in saved or not sid):
                level = saved.get(sid, 1.0)
                vol.SetMasterVolume(level, None)
                left.pop(sid, None)
        self._orig.clear()
        if pids:          # Discord is running: everything it has now is restored
            left = {}
        self._save(left)

    def _save(self, data=None):
        if not self.restore_file:
            return
        try:
            data = self._orig if data is None else data
            if data:
                self.restore_file.write_text(json.dumps(data), encoding="utf-8")
            elif self.restore_file.exists():
                self.restore_file.unlink()
        except Exception as e:  # noqa: BLE001
            log.debug("app volume save: %s", e)

    def _load(self) -> dict:
        try:
            return {k: float(v) for k, v in json.loads(self.restore_file.read_text(encoding="utf-8")).items()}
        except Exception:
            return {}

    def pending_restore(self) -> bool:
        return bool(self.restore_file and self.restore_file.exists())
