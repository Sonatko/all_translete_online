"""Global Hotkey and Mouse Listener for Stage 3 Studio.
Monitors Shift + Middle Mouse Button (MMB) for PTT and F9 for Master Toggle.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from pynput import keyboard, mouse

log = logging.getLogger("Studio.Hotkey")


class HotkeyListener:
    """Manages low-level mouse and keyboard listeners for PTT and shortcuts."""

    def __init__(self, on_ptt_change: Callable[[bool], None], on_master_toggle: Callable[[], None]):
        self.on_ptt_change = on_ptt_change
        self.on_master_toggle = on_master_toggle

        self._shift_pressed = False
        self._middle_pressed = False
        self._ptt_active = False

        self._kb_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for keyboard and mouse events."""
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

            log.info("Global hotkey listeners initialized (PTT: Shift + MMB, Master: F9).")
        except Exception as e:
            log.error("Failed to initialize hotkey listeners: %s", e)

    def stop(self) -> None:
        """Stop listeners."""
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

    def _update_ptt_state(self) -> None:
        """Determine if PTT condition is satisfied."""
        with self._lock:
            # Shift + Middle Mouse Button
            should_be_active = self._shift_pressed and self._middle_pressed
            if should_be_active != self._ptt_active:
                self._ptt_active = should_be_active
                try:
                    self.on_ptt_change(self._ptt_active)
                except Exception as e:
                    log.error("Error in PTT callback: %s", e)

    def _on_key_press(self, key) -> None:
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_pressed = True
            self._update_ptt_state()
        elif key == keyboard.Key.f9:
            try:
                self.on_master_toggle()
            except Exception as e:
                log.error("Error in Master Toggle callback: %s", e)

    def _on_key_release(self, key) -> None:
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_pressed = False
            self._update_ptt_state()

    def _on_mouse_click(self, x, y, button, pressed) -> None:
        if button == mouse.Button.middle:
            self._middle_pressed = pressed
            self._update_ptt_state()
