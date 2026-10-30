"""End-to-end self-test - no microphone or speaking needed.

Plays a synthetic English sentence into the virtual cable ("CABLE Input"), then:
  incoming pipeline: loopback of CABLE Input  -> Whisper -> translate -> voice
  outgoing pipeline: CABLE Output (as "mic")  -> Whisper -> translate -> voice
Translated voices are captured in memory (not played), so you hear nothing.

Usage:  runtime\\python.exe tools\\selftest.py  [whisper-model]
"""
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "huggingface"))

from dizcord import config  # noqa: E402
from dizcord.audio import devices  # noqa: E402
from dizcord.audio.player import OutputDevice  # noqa: E402
from dizcord.engine import Engine  # noqa: E402

SENTENCE = "Hello everyone, I think we should attack the bomb site together right now."


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "small"
    cable = devices.find_virtual_cable()
    if not cable:
        print("FAIL: no virtual cable (CABLE Input) found - install VB-Audio Virtual Cable.")
        return 1
    print(f"Virtual cable: {cable}")

    prof = config.default_profile()
    prof["input"].update({"listen_mode": "loopback", "listen_device": cable, "mic_device": "CABLE Output",
                          "mic_mode": "vad", "pause_listen_while_speaking": False,
                          "ignore_mic_while_playing": False})
    prof["incoming"].update({"source_lang": "auto", "target_lang": "pt"})
    prof["outgoing"].update({"source_lang": "auto", "target_lang": "es"})
    prof["stt"] = {"provider": "faster_whisper", "settings": {"faster_whisper": {"model": model}}}
    prof["translation"]["provider"] = "google_free"
    prof["tts"]["provider"] = "edge"

    events, done = [], threading.Event()

    def emit(ev):
        if ev["type"] in ("level", "busy"):
            return
        events.append(ev)
        if ev["type"] == "line":
            print(f"  [{ev['dir']}] {ev['src']}->{ev['tgt']}: '{ev['original']}'  =>  '{ev['translated']}'")
        elif ev["type"] in ("error", "status"):
            print(f"  {ev['type']}: {ev['text']}")
        if sum(1 for e in events if e["type"] == "spoken") >= 2:
            done.set()

    eng = Engine(prof, config.KeyStore(), emit)
    spoken = []

    class SilentSpeaker:
        """Synthesises each translation in memory instead of playing it (so you hear nothing)."""

        def __init__(self, direction):
            self.dir, self.recent = direction, []

        def say(self, utt, interrupt_kind=None):
            audio, sr = eng.synthesize(utt.text, utt.lang, self.dir)
            spoken.append((self.dir, round(len(audio) / sr, 1)))
            utt.started_at = time.monotonic()
            if utt.on_start:
                utt.on_start(utt)

        def backlog(self):
            return 0

        def cancel(self, kind=None):
            pass

    eng.speakers = {d: SilentSpeaker(d) for d in ("incoming", "outgoing")}

    print(f"Loading Whisper '{model}' (first run downloads it into models\\)…")
    eng.start()
    t0 = time.time()
    while not eng.pipelines and eng.running and time.time() - t0 < 600:
        time.sleep(0.2)
    if not eng.pipelines:
        print("FAIL: pipelines did not start")
        return 1
    time.sleep(1.0)

    print("Synthesizing test sentence…")
    audio, sr = eng.provider("tts").synthesize(SENTENCE, "en", "auto")
    print(f"Playing {len(audio) / sr:.1f}s of speech into {cable}…")
    out = OutputDevice(cable)
    out.open()
    out.play(audio, sr).done.wait(30)
    out.close()

    ok = done.wait(90)
    eng.shutdown()
    lines = [e for e in events if e["type"] == "line"]
    print()
    print(f"Lines: {len(lines)}   synthesized voices: {spoken}")
    dirs = {e["dir"] for e in lines}
    if ok and dirs == {"incoming", "outgoing"}:
        print("PASS: both directions recognized, translated and voiced.")
        return 0
    print("FAIL: expected a translated + spoken line in both directions.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
