"""Real-time Low-Latency Audio Engine for Stage 3 Studio.
Handles WASAPI loopback, mic input, PTT buffering with tail padding,
passthrough to Topping Playback 3/4, sidetone to Playback 1/2, and decoupled telemetry.
"""
from __future__ import annotations

import collections
import logging
import math
import queue
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal
import sounddevice as sd

from .model_manager import ModelManager

log = logging.getLogger("Studio.Audio")

DEFAULT_SR = 48000
BLOCK_SIZE = 480  # 10ms at 48kHz for responsive VU meters and minimal latency


class AudioEngine:
    """Core low-latency audio processing coordinator."""

    def __init__(self, model_manager: ModelManager, config: Dict):
        self.mm = model_manager
        self.config = config

        # Audio streams
        self._in_stream: Optional[sd.InputStream] = None
        self._out_stream: Optional[sd.OutputStream] = None
        self._sidetone_stream: Optional[sd.OutputStream] = None

        # Lock and thread flags
        self._lock = threading.Lock()
        self._running = False
        self._master_enabled = True

        # PTT State
        self._is_ptt_pressed = False
        self._ptt_buffer: List[np.ndarray] = []
        self._tail_frames_left = 0
        self._tail_total_frames = int((self.config.get("ptt", {}).get("tail_ms", 200) / 1000.0) * DEFAULT_SR)

        # Queues for asynchronous playback
        self._out_queue: queue.Queue = queue.Queue(maxsize=100)
        self._sidetone_queue: queue.Queue = queue.Queue(maxsize=100)

        # Inference worker thread
        self._work_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None

        # Decoupled Telemetry (read by UI timer at 30 FPS - zero GUI lag)
        self.mic_peak_db: float = -60.0
        self.mic_rms_db: float = -60.0
        self.out_peak_db: float = -60.0
        self.engine_state: str = "IDLE"  # IDLE, RECORDING, PROCESSING, SPEAKING
        self.last_stt_ms: float = 0.0
        self.last_mt_ms: float = 0.0
        self.last_tts_ms: float = 0.0
        self.last_total_ms: float = 0.0
        self.last_ru_text: str = ""
        self.last_en_text: str = ""

        # Transcript history (max 30 items)
        self.transcript_history: collections.deque = collections.deque(maxlen=30)
        self.on_transcript_callback: Optional[Callable[[Dict], None]] = None

    # =========================================================================
    # Device Discovery & Resolution
    # =========================================================================
    @staticmethod
    def get_devices() -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """Query system audio input and output devices."""
        inputs = []
        outputs = []
        try:
            devs = sd.query_devices()
            for idx, d in enumerate(devs):
                name = d.get("name", f"Device #{idx}")
                if d.get("max_input_channels", 0) > 0:
                    inputs.append((idx, name))
                if d.get("max_output_channels", 0) > 0:
                    outputs.append((idx, name))
        except Exception as e:
            log.error("Failed to query sound devices: %s", e)
        return inputs, outputs

    def _resolve_device_id(self, name_hint: str, is_input: bool) -> Optional[int]:
        """Find best matching device index by substring."""
        if not name_hint:
            return None
        hint_lower = name_hint.lower()
        try:
            devs = sd.query_devices()
            # 1. Exact or close substring match
            for idx, d in enumerate(devs):
                ch = d.get("max_input_channels" if is_input else "max_output_channels", 0)
                if ch > 0 and hint_lower in d.get("name", "").lower():
                    return idx
        except Exception:
            pass
        return None

    # =========================================================================
    # Audio Pipeline Start / Stop
    # =========================================================================
    def start(self) -> bool:
        """Start audio streams and background inference worker."""
        if self._running:
            return True

        self._running = True
        self._tail_total_frames = int((self.config.get("ptt", {}).get("tail_ms", 200) / 1000.0) * DEFAULT_SR)

        # 1. Start worker thread
        self._worker_thread = threading.Thread(target=self._inference_worker, daemon=True, name="S2ST_Worker")
        self._worker_thread.start()

        # 2. Setup audio devices
        audio_cfg = self.config.get("audio", {})
        in_id = self._resolve_device_id(audio_cfg.get("input_device", "NVIDIA Broadcast"), is_input=True)
        out_id = self._resolve_device_id(audio_cfg.get("output_device", "Playback 3/4"), is_input=False)
        side_id = self._resolve_device_id(audio_cfg.get("sidetone_device", "Playback 1/2"), is_input=False)

        try:
            # Input Stream
            self._in_stream = sd.InputStream(
                device=in_id,
                channels=1,
                samplerate=DEFAULT_SR,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=self._in_callback,
            )
            self._in_stream.start()
            log.info("Input audio stream started on device: %s (id=%s)", audio_cfg.get("input_device"), in_id)

            # Main Game Output Stream (Playback 3/4 -> Topping Loopback 1+2)
            self._out_stream = sd.OutputStream(
                device=out_id,
                channels=1,
                samplerate=DEFAULT_SR,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=self._out_callback,
            )
            self._out_stream.start()
            log.info("Output stream started on device: %s (id=%s)", audio_cfg.get("output_device"), out_id)

            # Sidetone Stream (Headphones Playback 1/2)
            if audio_cfg.get("sidetone_enabled", True) and side_id is not None and side_id != out_id:
                self._sidetone_stream = sd.OutputStream(
                    device=side_id,
                    channels=1,
                    samplerate=DEFAULT_SR,
                    blocksize=BLOCK_SIZE,
                    dtype="float32",
                    callback=self._sidetone_callback,
                )
                self._sidetone_stream.start()
                log.info("Sidetone stream started on headphones: %s (id=%s)", audio_cfg.get("sidetone_device"), side_id)

            return True
        except Exception as e:
            log.error("Failed to start audio streams: %s", e)
            self.stop()
            return False

    def stop(self) -> None:
        """Stop all streams cleanly."""
        self._running = False

        if self._in_stream:
            try:
                self._in_stream.stop()
                self._in_stream.close()
            except Exception:
                pass
            self._in_stream = None

        if self._out_stream:
            try:
                self._out_stream.stop()
                self._out_stream.close()
            except Exception:
                pass
            self._out_stream = None

        if self._sidetone_stream:
            try:
                self._sidetone_stream.stop()
                self._sidetone_stream.close()
            except Exception:
                pass
            self._sidetone_stream = None

        # Flush queues
        while not self._work_queue.empty():
            try:
                self._work_queue.get_nowait()
            except Exception:
                break

        log.info("Audio engine stopped.")

    def restart_streams(self) -> bool:
        """Restart audio streams with newly selected devices without stopping the worker thread."""
        if self._in_stream:
            try:
                self._in_stream.stop()
                self._in_stream.close()
            except Exception:
                pass
            self._in_stream = None

        if self._out_stream:
            try:
                self._out_stream.stop()
                self._out_stream.close()
            except Exception:
                pass
            self._out_stream = None

        if self._sidetone_stream:
            try:
                self._sidetone_stream.stop()
                self._sidetone_stream.close()
            except Exception:
                pass
            self._sidetone_stream = None

        audio_cfg = self.config.get("audio", {})
        in_id = self._resolve_device_id(audio_cfg.get("input_device", "NVIDIA Broadcast"), is_input=True)
        out_id = self._resolve_device_id(audio_cfg.get("output_device", "Playback 3/4"), is_input=False)
        side_id = self._resolve_device_id(audio_cfg.get("sidetone_device", "Playback 1/2"), is_input=False)

        try:
            self._in_stream = sd.InputStream(
                device=in_id,
                channels=1,
                samplerate=DEFAULT_SR,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=self._in_callback,
            )
            self._in_stream.start()

            self._out_stream = sd.OutputStream(
                device=out_id,
                channels=1,
                samplerate=DEFAULT_SR,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=self._out_callback,
            )
            self._out_stream.start()

            if audio_cfg.get("sidetone_enabled", True) and side_id is not None and side_id != out_id:
                self._sidetone_stream = sd.OutputStream(
                    device=side_id,
                    channels=1,
                    samplerate=DEFAULT_SR,
                    blocksize=BLOCK_SIZE,
                    dtype="float32",
                    callback=self._sidetone_callback,
                )
                self._sidetone_stream.start()

            log.info("Audio streams restarted successfully with new devices.")
            return True
        except Exception as e:
            log.error("Failed to restart audio streams: %s", e)
            return False

    # =========================================================================
    # Audio Callbacks
    # =========================================================================
    def _in_callback(self, indata, frames, time_info, status):
        """Incoming audio block from microphone (runs in real-time audio thread)."""
        if status:
            pass  # Avoid logging in realtime callback to prevent stutter

        mono = indata[:, 0]

        # Calculate smooth Peak and RMS for UI meters
        peak = float(np.max(np.abs(mono)))
        rms = float(np.sqrt(np.mean(mono ** 2)))

        peak_db = 20.0 * math.log10(peak) if peak > 1e-5 else -60.0
        rms_db = 20.0 * math.log10(rms) if rms > 1e-5 else -60.0

        # Exponential decay smoothing for VU meters
        self.mic_peak_db = max(peak_db, self.mic_peak_db - 1.8)
        self.mic_rms_db = max(rms_db, self.mic_rms_db - 1.5)

        if not self._master_enabled:
            return

        with self._lock:
            # 1. PTT Active: Accumulate speech into recording buffer
            if self._is_ptt_pressed:
                self._ptt_buffer.append(mono.copy())
                self.engine_state = "RECORDING"
            elif self._tail_frames_left > 0:
                # Post-roll tail padding to capture final consonant/word
                self._ptt_buffer.append(mono.copy())
                self._tail_frames_left -= len(mono)
                if self._tail_frames_left <= 0:
                    self._dispatch_ptt_utterance()
            else:
                # 2. PTT UP: Optional passthrough of natural mic to game loopback
                if self.config.get("audio", {}).get("passthrough_enabled", True):
                    gain = float(self.config.get("audio", {}).get("passthrough_volume", 1.0))
                    passthrough_chunk = mono * gain
                    if not self._out_queue.full():
                        self._out_queue.put_nowait(passthrough_chunk)

    def _out_callback(self, outdata, frames, time_info, status):
        """Outgoing playback to Playback 3/4 (Loopback 1+2)."""
        try:
            chunk = self._out_queue.get_nowait()
            if len(chunk) < frames:
                outdata[:len(chunk), 0] = chunk
                outdata[len(chunk):, 0] = 0.0
            else:
                outdata[:, 0] = chunk[:frames]
        except queue.Empty:
            outdata.fill(0.0)

        # Output level telemetry
        peak = float(np.max(np.abs(outdata[:, 0])))
        peak_db = 20.0 * math.log10(peak) if peak > 1e-5 else -60.0
        self.out_peak_db = max(peak_db, self.out_peak_db - 2.0)

    def _sidetone_callback(self, outdata, frames, time_info, status):
        """Headphones monitor playback to Playback 1/2."""
        try:
            chunk = self._sidetone_queue.get_nowait()
            if len(chunk) < frames:
                outdata[:len(chunk), 0] = chunk
                outdata[len(chunk):, 0] = 0.0
            else:
                outdata[:, 0] = chunk[:frames]
        except queue.Empty:
            outdata.fill(0.0)

    # =========================================================================
    # PTT Trigger & Dispatch
    # =========================================================================
    def set_ptt_state(self, pressed: bool) -> None:
        """Called by hotkey listener when Shift+MMB state changes."""
        with self._lock:
            if pressed and not self._is_ptt_pressed:
                # PTT Down
                self._is_ptt_pressed = True
                self._ptt_buffer = []
                self._tail_frames_left = 0
                self.engine_state = "RECORDING"
                log.info("PTT Pressed -> Recording speech buffer...")
            elif not pressed and self._is_ptt_pressed:
                # PTT Released -> start tail countdown
                self._is_ptt_pressed = False
                self._tail_frames_left = self._tail_total_frames
                log.info("PTT Released -> Applying %d ms tail padding...", self.config.get("ptt", {}).get("tail_ms", 200))

    def _dispatch_ptt_utterance(self) -> None:
        """Combine accumulated audio chunks and send to background inference worker."""
        if not self._ptt_buffer:
            self.engine_state = "IDLE"
            return

        full_audio_48k = np.concatenate(self._ptt_buffer)
        self._ptt_buffer = []

        # Minimum speech length check (150 ms)
        if len(full_audio_48k) < int(DEFAULT_SR * 0.15):
            self.engine_state = "IDLE"
            return

        self.engine_state = "PROCESSING"
        self._work_queue.put(full_audio_48k)

    def toggle_master(self) -> bool:
        """Toggle master S2ST translation on/off."""
        self._master_enabled = not self._master_enabled
        if not self._master_enabled:
            self.engine_state = "PAUSED"
        else:
            self.engine_state = "IDLE"
        log.info("Master S2ST toggled: %s", self._master_enabled)
        return self._master_enabled

    # =========================================================================
    # Background S2ST Inference Worker (STT -> MT -> TTS)
    # =========================================================================
    def _inference_worker(self) -> None:
        """Runs in separate thread: Resample -> GigaAM -> Opus-MT -> Pocket-TTS."""
        log.info("Inference worker started.")
        while self._running:
            try:
                audio_48k = self._work_queue.get(timeout=0.2)
            except queue.Empty:
                if self.engine_state == "PROCESSING" and not self._is_ptt_pressed:
                    self.engine_state = "IDLE"
                continue

            try:
                # 1. Resample from 48000 Hz to 16000 Hz for GigaAM STT
                num_samples_16k = int(len(audio_48k) * 16000 / DEFAULT_SR)
                audio_16k = signal.resample(audio_48k, num_samples_16k).astype(np.float32)

                # Step 1: STT Transcription
                ru_text, stt_ms = self.mm.transcribe(audio_16k)
                self.last_stt_ms = round(stt_ms, 1)
                self.last_ru_text = ru_text

                if not ru_text.strip():
                    log.info("STT returned empty transcript (silence/noise).")
                    self.engine_state = "IDLE"
                    continue

                log.info("STT [%.1f ms]: %s", stt_ms, ru_text)

                # Step 2: MT Translation (Russian -> English)
                en_text, mt_ms = self.mm.translate(ru_text)
                self.last_mt_ms = round(mt_ms, 1)
                self.last_en_text = en_text

                if not en_text.strip():
                    log.info("MT returned empty translation.")
                    self.engine_state = "IDLE"
                    continue

                log.info("MT  [%.1f ms]: %s", mt_ms, en_text)

                # Step 3: TTS Synthesis (Pocket-TTS Cloned Voice)
                self.engine_state = "SPEAKING"
                tts_audio_24k, tts_sr, tts_ms = self.mm.synthesize(en_text)
                self.last_tts_ms = round(tts_ms, 1)
                self.last_total_ms = round(stt_ms + mt_ms + tts_ms, 1)

                log.info("TTS [%.1f ms]: Synthesized %d samples. Total Latency: %.1f ms",
                         tts_ms, len(tts_audio_24k) if tts_audio_24k is not None else 0, self.last_total_ms)

                # Step 4: Resample synthesized 24kHz audio to 48kHz and enqueue to streams
                if tts_audio_24k is not None and len(tts_audio_24k) > 0:
                    num_samples_48k = int(len(tts_audio_24k) * DEFAULT_SR / tts_sr)
                    out_48k = signal.resample(tts_audio_24k, num_samples_48k).astype(np.float32)

                    # Chunk and dispatch to Playback 3/4 (Game)
                    chunk_size = BLOCK_SIZE
                    for i in range(0, len(out_48k), chunk_size):
                        chunk = out_48k[i:i + chunk_size]
                        self._out_queue.put(chunk)

                    # Dispatch to Sidetone (Headphones Playback 1/2) with monitor volume
                    if self.config.get("audio", {}).get("sidetone_enabled", True):
                        sidetone_vol = float(self.config.get("audio", {}).get("sidetone_volume", 0.70))
                        sidetone_chunk_arr = out_48k * sidetone_vol
                        for i in range(0, len(sidetone_chunk_arr), chunk_size):
                            chunk = sidetone_chunk_arr[i:i + chunk_size]
                            self._sidetone_queue.put(chunk)

                # Record transcript record
                record = {
                    "time": time.strftime("%H:%M:%S"),
                    "ru": ru_text,
                    "en": en_text,
                    "stt_ms": self.last_stt_ms,
                    "mt_ms": self.last_mt_ms,
                    "tts_ms": self.last_tts_ms,
                    "total_ms": self.last_total_ms,
                }
                self.transcript_history.appendleft(record)
                if self.on_transcript_callback:
                    try:
                        self.on_transcript_callback(record)
                    except Exception:
                        pass

            except Exception as e:
                log.error("Error during S2ST pipeline inference: %s", e)
            finally:
                if not self._is_ptt_pressed:
                    self.engine_state = "IDLE"

