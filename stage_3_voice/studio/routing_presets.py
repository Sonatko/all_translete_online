"""Audio Routing Presets and 1-Click Hardware Setup Wizard.
Provides automated detection and 1-click configuration for:
1. Topping E2x2 OTG (Hardware Zero-Latency DSP Loopback)
2. Virtual Cable / VB-Cable (Universal Software Mode for any PC / Laptop)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sounddevice as sd

log = logging.getLogger("Studio.RoutingPresets")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class RoutingPresets:
    """Manages audio hardware profiles and automated 1-click switching."""

    @staticmethod
    def get_hardware_info() -> Dict[str, bool]:
        """Detect presence of Topping E2x2 and Virtual Audio Cable."""
        has_topping = False
        has_cable = False

        try:
            devs = sd.query_devices()
            for d in devs:
                name = (d.get("name") or "").lower()
                if "e2x2" in name or ("playback 3/4" in name and d.get("max_output_channels", 0) > 0):
                    has_topping = True
                if "cable" in name or "virtual" in name:
                    has_cable = True
        except Exception as e:
            log.warning("Hardware query error: %s", e)

        return {
            "has_topping": has_topping,
            "has_cable": has_cable,
        }

    @classmethod
    def apply_preset(cls, mode: str, cfg: dict) -> Tuple[bool, str]:
        """Apply 1-click preset ('topping' or 'cable') and update configuration."""
        if "audio" not in cfg:
            cfg["audio"] = {}

        devs = sd.query_devices()
        inputs = [d.get("name", "") for d in devs if d.get("max_input_channels", 0) > 0]
        outputs = [d.get("name", "") for d in devs if d.get("max_output_channels", 0) > 0]

        if mode == "topping":
            # 1. Output: Playback 3/4 (Topping Voice)
            out_target = "Playback 3/4"
            for o in outputs:
                if "3/4" in o.lower() or "голос ии" in o.lower() or "topping voice" in o.lower():
                    out_target = o
                    break

            # 2. Sidetone: Playback 1/2 (Topping Headphones)
            side_target = "Playback 1/2"
            for o in outputs:
                if "1/2" in o.lower() or "наушники" in o.lower() or "topping headphones" in o.lower():
                    side_target = o
                    break

            # 3. Input: NVIDIA Broadcast or Analog 1/2
            in_target = "NVIDIA Broadcast"
            for i in inputs:
                if "broadcast" in i.lower():
                    in_target = i
                    break
                elif "analog" in i.lower() or "вход" in i.lower():
                    in_target = i

            cfg["audio"]["output_device"] = out_target
            cfg["audio"]["sidetone_device"] = side_target
            cfg["audio"]["input_device"] = in_target
            cfg["audio"]["routing_mode"] = "topping"

            msg = (
                "Профиль 'Topping E2x2 (Аппаратный)' активирован!\n"
                f"• Микрофон в игре (CS2/Discord): 'ИИ Микрофон' (Loopback 1/2)\n"
                f"• Канал озвучки ИИ: {out_target}\n"
                f"• Наушники: {side_target}"
            )
            log.info("Applied Topping preset: in=%s, out=%s, side=%s", in_target, out_target, side_target)
            return True, msg

        elif mode == "cable":
            # 1. Output: CABLE Input or Virtual Audio
            out_target = None
            for o in outputs:
                if "cable input" in o.lower():
                    out_target = o
                    break
                elif "virtual" in o.lower() and "cable" in o.lower():
                    out_target = o
                    break

            if not out_target:
                for o in outputs:
                    if "virtual" in o.lower():
                        out_target = o
                        break

            if not out_target:
                out_target = "CABLE Input (VB-Audio Virtual Cable)"

            # 2. Sidetone: Default User Headphones / Speakers (not the virtual cable)
            side_target = "Speakers"
            for o in outputs:
                o_low = o.lower()
                if "cable" not in o_low and "virtual" not in o_low and "3/4" not in o_low:
                    if "наушники" in o_low or "speakers" in o_low or "realtek" in o_low or "1/2" in o_low:
                        side_target = o
                        break

            # 3. Input: Default Mic (NVIDIA Broadcast or Realtek or Analog)
            in_target = "NVIDIA Broadcast"
            for i in inputs:
                i_low = i.lower()
                if "cable" not in i_low and "loopback" not in i_low:
                    if "broadcast" in i_low:
                        in_target = i
                        break
                    elif "микрофон" in i_low or "realtek" in i_low or "analog" in i_low:
                        in_target = i

            cfg["audio"]["output_device"] = out_target
            cfg["audio"]["sidetone_device"] = side_target
            cfg["audio"]["input_device"] = in_target
            cfg["audio"]["routing_mode"] = "cable"

            msg = (
                "Профиль 'Виртуальный Кабель (Обычный ПК)' активирован!\n"
                f"• Микрофон в игре (CS2/Discord): 'CABLE Output' (или 'ИИ Микрофон')\n"
                f"• Канал озвучки ИИ: {out_target}\n"
                f"• Наушники: {side_target}"
            )
            log.info("Applied Cable preset: in=%s, out=%s, side=%s", in_target, out_target, side_target)
            return True, msg

        return False, "Неизвестный режим"

