"""Small Windows helpers: clipboard text, foreground window info, key sending, focusing a window."""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

user32.GetClipboardData.restype = wt.HANDLE
kernel32.GlobalLock.restype = wt.LPVOID
kernel32.GlobalLock.argtypes = [wt.HGLOBAL]
kernel32.GlobalUnlock.argtypes = [wt.HGLOBAL]
kernel32.GlobalAlloc.restype = wt.HGLOBAL
user32.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
user32.SetClipboardData.restype = wt.HANDLE

# Windows whose Ctrl+C means "interrupt", not "copy"
TERMINAL_CLASSES = {"ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS", "mintty", "PuTTY", "VirtualConsoleClass"}


def _open_clipboard(retries=10) -> bool:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.02)
    return False


def get_clipboard_text() -> str:
    if not _open_clipboard():
        return ""
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        p = kernel32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p) if p else ""
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text: str) -> bool:
    if not _open_clipboard():
        return False
    try:
        user32.EmptyClipboard()
        data = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(data)
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        p = kernel32.GlobalLock(h)
        ctypes.memmove(p, data, size)
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
        return True
    finally:
        user32.CloseClipboard()


def clipboard_sequence() -> int:
    return user32.GetClipboardSequenceNumber()


def foreground() -> tuple[int, str, int]:
    """(hwnd, class name, process id) of the foreground window."""
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return hwnd, buf.value, pid.value


def foreground_is_own_app() -> bool:
    return foreground()[2] == os.getpid()


def window_title(hwnd: int) -> str:
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def cursor_pos() -> tuple[int, int]:
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def focus_window(hwnd: int) -> bool:
    SW_RESTORE = 9
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    if user32.SetForegroundWindow(hwnd) and user32.GetForegroundWindow() == hwnd:
        return True
    # Foreground lock: Windows lets a process take focus right after it received input,
    # so tap Alt (harmless) and retry, attached to the current foreground thread.
    VK_MENU, KEYUP = 0x12, 0x0002
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    other = user32.GetWindowThreadProcessId(fg, None)
    user32.AttachThreadInput(cur, other, True)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYUP, 0)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    user32.AttachThreadInput(cur, other, False)
    time.sleep(0.05)
    return user32.GetForegroundWindow() == hwnd


def wait_modifiers_released(timeout=1.5):
    """After a hotkey fires, wait until Ctrl/Alt/Shift/Win are up before sending our own keys."""
    try:
        import keyboard
    except ImportError:
        time.sleep(0.3)
        return
    end = time.monotonic() + timeout
    while time.monotonic() < end and any(keyboard.is_pressed(k) for k in ("ctrl", "alt", "shift", "windows")):
        time.sleep(0.02)


def send(keys: str):
    import keyboard
    keyboard.send(keys)


def copy_selection_via_clipboard(timeout=0.6) -> str:
    """Press Ctrl+C in the foreground app, return the copied text and restore the old clipboard."""
    old = get_clipboard_text()
    seq = clipboard_sequence()
    send("ctrl+c")
    end = time.monotonic() + timeout
    while time.monotonic() < end and clipboard_sequence() == seq:
        time.sleep(0.02)
    text = get_clipboard_text() if clipboard_sequence() != seq else ""
    if clipboard_sequence() != seq:
        set_clipboard_text(old)
    return text
