"""Universal Global Hotkey, Mouse, and Gamepad/VR Controller Listener for Stage 3 Studio.
Full support for:
- Any combination: Shift+MMB, Ctrl+V, Alt+Mouse4, Ctrl+Shift+Space, Shift+Mouse5, etc.
- Any single keyboard key: V, CapsLock, T, Space, F1-F12, etc.
- Any mouse button: Middle (MMB), Mouse4, Mouse5, Right, Left.
- Any Gamepad / VR Controller / Pedal button: LB, RB, LT, RT, A, B, X, Y.
- Master Toggle: F8.
- Real-time global combination capture with live modifier tracking.
"""
from __future__ import annotations

import ctypes
import logging
import threading
import time
from typing import Callable, Dict, Optional, Set

from pynput import keyboard, mouse

log = logging.getLogger("Studio.Hotkey")

# Windows XInput definitions for Gamepads, Pedals, and VR controller emulations
XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100  # LB
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200  # RB
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class HotkeyListener:
    """Manages low-level mouse, keyboard, and controller listeners for PTT."""

    def __init__(
        self,
        on_ptt_change: Callable[[bool], None],
        on_master_toggle: Callable[[], None],
        initial_key: str = "shift+middle",
    ):
        self.on_ptt_change = on_ptt_change
        self.on_master_toggle = on_master_toggle

        # Active state tracking
        self._shift_pressed = False
        self._ctrl_pressed = False
        self._alt_pressed = False
        self._pressed_keys: Set[str] = set()
        self._mouse_buttons: Dict[str, bool] = {
            "middle": False,
            "mouse4": False,
            "mouse5": False,
            "left": False,
            "right": False,
        }
        self._gamepad_pressed_name: Optional[str] = None
        self._ptt_active = False

        # Parsed binding components
        self.ptt_key = "shift+middle"
        self._req_shift = False
        self._req_ctrl = False
        self._req_alt = False
        self._req_trigger = "middle"
        self._is_mouse_trigger = True
        self._is_gamepad_trigger = False

        self._lock = threading.Lock()
        self.set_binding(initial_key or "shift+middle")

        # Capture mode state
        self._capture_callback: Optional[Callable[[str], None]] = None
        self._capture_preview_callback: Optional[Callable[[str], None]] = None
        self._modifier_pressed_at: float = 0.0

        self._kb_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._gamepad_thread: Optional[threading.Thread] = None
        self._running = False

        # Load XInput DLL safely
        self._xinput = None
        try:
            self._xinput = getattr(ctypes.windll, "xinput1_4", None) or getattr(ctypes.windll, "xinput9_1_0", None)
        except Exception:
            self._xinput = None

    def set_binding(self, key_str: str) -> None:
        """Parse and configure any combination or single key."""
        with self._lock:
            raw = (key_str or "shift+middle").strip().lower()
            self.ptt_key = raw

            parts = [p.strip() for p in raw.split("+") if p.strip()]
            self._req_shift = "shift" in parts
            self._req_ctrl = "ctrl" in parts or "control" in parts
            self._req_alt = "alt" in parts

            non_mods = [p for p in parts if p not in ("shift", "ctrl", "control", "alt")]
            if non_mods:
                trigger = non_mods[-1]
            elif self._req_shift:
                trigger = "shift"
            elif self._req_ctrl:
                trigger = "ctrl"
            elif self._req_alt:
                trigger = "alt"
            else:
                trigger = "middle"

            # Normalize trigger names
            if trigger in ("mmb", "middle_button"):
                trigger = "middle"
            elif trigger in ("xbutton1", "mouse_4"):
                trigger = "mouse4"
            elif trigger in ("xbutton2", "mouse_5"):
                trigger = "mouse5"

            self._req_trigger = trigger
            self._is_mouse_trigger = trigger in ("middle", "mouse4", "mouse5", "left", "right")
            self._is_gamepad_trigger = trigger.startswith("gamepad")

            log.info("PTT binding parsed: key='%s' (Shift=%s, Ctrl=%s, Alt=%s, Trigger='%s', Mouse=%s, GP=%s)",
                     self.ptt_key, self._req_shift, self._req_ctrl, self._req_alt,
                     self._req_trigger, self._is_mouse_trigger, self._is_gamepad_trigger)
            self._eval_ptt()

    def start_capture(
        self,
        callback: Callable[[str], None],
        preview_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Start global OS-level key and combination capture."""
        with self._lock:
            self._capture_callback = callback
            self._capture_preview_callback = preview_callback
            log.info("Global combination capture mode active...")

    def stop_capture(self) -> None:
        """Stop capture mode."""
        with self._lock:
            self._capture_callback = None
            self._capture_preview_callback = None
            log.info("Global combination capture stopped.")

    def start(self) -> None:
        """Start listening for keyboard, mouse, and gamepad inputs."""
        self._running = True
        try:
            self._kb_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._kb_listener.daemon = True
            self._kb_listener.start()

            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click
            )
            self._mouse_listener.daemon = True
            self._mouse_listener.start()

            if self._xinput:
                self._gamepad_thread = threading.Thread(target=self._gamepad_poll_loop, daemon=True)
                self._gamepad_thread.start()

            log.info("Global hotkey listeners started (PTT: %s, Master: F8).", self.ptt_key)
        except Exception as e:
            log.error("Failed to start hotkey listeners: %s", e)

    def stop(self) -> None:
        """Stop all listeners."""
        self._running = False
        if self._kb_listener:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None

        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None
        log.info("Hotkey listeners stopped.")

    def _eval_ptt(self) -> None:
        """Check if current pressed inputs satisfy the active binding."""
        # 1. Modifiers check
        if self._req_shift and not self._shift_pressed:
            active = False
        elif self._req_ctrl and not self._ctrl_pressed:
            active = False
        elif self._req_alt and not self._alt_pressed:
            active = False
        else:
            # 2. Trigger check
            if self._is_mouse_trigger:
                active = self._mouse_buttons.get(self._req_trigger, False)
            elif self._is_gamepad_trigger:
                active = (self._gamepad_pressed_name == self._req_trigger)
            elif self._req_trigger == "shift":
                active = self._shift_pressed
            elif self._req_trigger in ("ctrl", "control"):
                active = self._ctrl_pressed
            elif self._req_trigger == "alt":
                active = self._alt_pressed
            else:
                active = (self._req_trigger in self._pressed_keys)

        if active != self._ptt_active:
            self._ptt_active = active
            try:
                self.on_ptt_change(self._ptt_active)
            except Exception as e:
                log.error("Error in PTT callback: %s", e)

    def _normalize_key(self, key) -> str:
        """Convert pynput Key to normalized string."""
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        if hasattr(key, "name") and key.name:
            return key.name.lower()
        return str(key).lower().replace("key.", "")

    def _get_active_modifiers_prefix(self) -> str:
        mods = []
        if self._ctrl_pressed:
            mods.append("ctrl")
        if self._shift_pressed:
            mods.append("shift")
        if self._alt_pressed:
            mods.append("alt")
        return "+".join(mods)

    def _on_key_press(self, key) -> None:
        norm = self._normalize_key(key)

        is_shift = norm in ("shift", "shift_l", "shift_r")
        is_ctrl = norm in ("ctrl", "ctrl_l", "ctrl_r", "control")
        is_alt = norm in ("alt", "alt_l", "alt_r")

        if is_shift:
            self._shift_pressed = True
        elif is_ctrl:
            self._ctrl_pressed = True
        elif is_alt:
            self._alt_pressed = True
        else:
            self._pressed_keys.add(norm)

        # Handle Capture Mode
        with self._lock:
            cb = self._capture_callback
            preview_cb = self._capture_preview_callback

        if cb:
            if norm in ("esc", "escape"):
                self.stop_capture()
                cb("")
                return

            if is_shift or is_ctrl or is_alt:
                # User pressed a modifier — update preview ("Зажато: CTRL + ...")
                if preview_cb:
                    preview_cb(self._get_active_modifiers_prefix())
                return

            # Non-modifier key pressed -> complete combination!
            mods = self._get_active_modifiers_prefix()
            comb = f"{mods}+{norm}" if mods else norm
            self.stop_capture()
            cb(comb)
            return

        # Master toggle F8
        if norm == "f8":
            try:
                self.on_master_toggle()
            except Exception as e:
                log.error("Error in Master Toggle callback: %s", e)
            return

        with self._lock:
            self._eval_ptt()

    def _on_key_release(self, key) -> None:
        norm = self._normalize_key(key)

        is_shift = norm in ("shift", "shift_l", "shift_r")
        is_ctrl = norm in ("ctrl", "ctrl_l", "ctrl_r", "control")
        is_alt = norm in ("alt", "alt_l", "alt_r")

        # If user was in capture mode and released modifier without pressing other keys:
        with self._lock:
            cb = self._capture_callback
            preview_cb = self._capture_preview_callback

        if is_shift:
            self._shift_pressed = False
        elif is_ctrl:
            self._ctrl_pressed = False
        elif is_alt:
            self._alt_pressed = False
        else:
            self._pressed_keys.discard(norm)

        if cb and (is_shift or is_ctrl or is_alt):
            # If modifier released alone
            mods = self._get_active_modifiers_prefix()
            if preview_cb:
                preview_cb(mods)

        with self._lock:
            self._eval_ptt()

    def _on_mouse_click(self, x, y, button, pressed) -> None:
        b_name = ""
        if button == mouse.Button.middle:
            b_name = "middle"
        elif button == mouse.Button.left:
            b_name = "left"
        elif button == mouse.Button.right:
            b_name = "right"
        elif button == mouse.Button.x1:
            b_name = "mouse4"
        elif button == mouse.Button.x2:
            b_name = "mouse5"
        else:
            b_name = str(button).lower().replace("button.", "")

        if b_name in self._mouse_buttons:
            self._mouse_buttons[b_name] = pressed

        # Check Capture Mode
        if pressed:
            with self._lock:
                cb = self._capture_callback
            if cb:
                # Ignore left click so user can still cancel via UI
                if b_name != "left":
                    mods = self._get_active_modifiers_prefix()
                    comb = f"{mods}+{b_name}" if mods else b_name
                    self.stop_capture()
                    cb(comb)
                    return

        with self._lock:
            self._eval_ptt()

    def _gamepad_poll_loop(self) -> None:
        """Poll XInput controllers for gamepads, pedals, or VR inputs at ~50Hz."""
        state = XINPUT_STATE()
        while self._running:
            need_poll = bool(self._capture_callback or self._is_gamepad_trigger)
            if not need_poll:
                time.sleep(0.08)
                continue

            btn_pressed = False
            pressed_name = None
            for user_idx in range(4):
                res = self._xinput.XInputGetState(user_idx, ctypes.byref(state))
                if res == 0:  # ERROR_SUCCESS
                    gp = state.Gamepad
                    w = gp.wButtons

                    if w & XINPUT_GAMEPAD_LEFT_SHOULDER:
                        btn_pressed = True; pressed_name = "gamepad_lb"
                    elif w & XINPUT_GAMEPAD_RIGHT_SHOULDER:
                        btn_pressed = True; pressed_name = "gamepad_rb"
                    elif w & XINPUT_GAMEPAD_A:
                        btn_pressed = True; pressed_name = "gamepad_a"
                    elif w & XINPUT_GAMEPAD_B:
                        btn_pressed = True; pressed_name = "gamepad_b"
                    elif w & XINPUT_GAMEPAD_X:
                        btn_pressed = True; pressed_name = "gamepad_x"
                    elif w & XINPUT_GAMEPAD_Y:
                        btn_pressed = True; pressed_name = "gamepad_y"
                    elif gp.bLeftTrigger > 60:
                        btn_pressed = True; pressed_name = "gamepad_lt"
                    elif gp.bRightTrigger > 60:
                        btn_pressed = True; pressed_name = "gamepad_rt"

                    if btn_pressed:
                        break

            # Handle capture mode
            if btn_pressed and pressed_name:
                with self._lock:
                    cb = self._capture_callback
                if cb:
                    mods = self._get_active_modifiers_prefix()
                    comb = f"{mods}+{pressed_name}" if mods else pressed_name
                    self.stop_capture()
                    cb(comb)
                    time.sleep(0.3)
                    continue

            with self._lock:
                self._gamepad_pressed_name = pressed_name if btn_pressed else None
                self._eval_ptt()

            time.sleep(0.02)
