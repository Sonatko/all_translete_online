"""Call test - a pretend voice call, no microphone, no Discord call and nothing you can hear.

    runtime\\python.exe tools\\calltest.py  [whisper-model]        (default: base)

A stand-in for Discord (a second process) talks English into the virtual cable while the app translates it:
  1. Discord-only listening: 6 sentences, some while the app voice is still talking. Every sentence must be
     translated, in order, none dropped; the app must never hear its own voice (it plays into the same cable);
     never two app voices at once (chat messages are read in between); listening never pauses;
     "Hear people: off" must turn the stand-in down in the Windows mixer and give its volume back after Stop.
  2. No headphones (worst case): your translated voice goes into the cable your "microphone" records, so the mic
     hears the app's own voice - the echo filter must ignore it (no translation loop).
Prints how long after the end of each sentence the translated voice started.
Uses the free engines (Whisper on this PC, Google free, Edge voices); needs VB-Audio Virtual Cable and internet.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "huggingface"))

SENTENCES = [
    "Hello everyone, can you hear me clearly?",
    "I think we should attack the bomb site together right now.",
    "Wait, there is an enemy behind the wall on the left side.",
    "Okay, I will buy a rifle and some grenades this round.",
    "Nice shot, that was amazing, we won the round.",
    "Let's take a short break after this match, I need some water.",
]


def fake_app(device: str):
    """The stand-in for Discord: plays the files it is told to and reports when each one played."""
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    from dizcord.audio import devices
    from dizcord.audio.utils import resample
    idx = devices.find_device(device, "output")
    sr_out = int(devices.device_info(idx)["default_samplerate"])
    print(json.dumps({"pid": os.getpid()}), flush=True)
    for line in sys.stdin:
        parts = line.split()
        if not parts or parts[0] == "quit":
            break
        x, sr = sf.read(parts[1], dtype="float32")
        x = resample(x.mean(axis=1) if x.ndim > 1 else x, sr, sr_out)
        t0 = time.monotonic()
        sd.play(np.stack([x, x], 1), sr_out, device=idx)
        sd.wait()
        print(json.dumps({"start": t0, "end": time.monotonic()}), flush=True)
        time.sleep(float(parts[2]))


def words(s: str) -> set:
    return set(re.findall(r"[a-z']+", s.lower()))


def which(text: str) -> list[int]:
    return [i for i, s in enumerate(SENTENCES) if len(words(s) & words(text)) >= 0.6 * len(words(s))]


class Run:
    """One engine + one stand-in process; collects events."""

    def __init__(self, prof, feed_device):
        from dizcord import config
        from dizcord.engine import Engine
        self.fake = subprocess.Popen([sys.executable, __file__, "--fake", feed_device], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self.pid = json.loads(self.fake.stdout.readline())["pid"]
        self.played = []
        threading.Thread(target=lambda: [self.played.append(json.loads(ln)) for ln in self.fake.stdout],
                         daemon=True).start()
        self.events, self.lock = [], threading.Lock()
        if prof["input"]["listen_mode"] == "app":
            prof["input"]["listen_app"] = f"pid:{self.pid}"
        self.eng = Engine(prof, config.KeyStore(), self._emit)

    def _emit(self, ev):
        if ev["type"] in ("level", "busy"):
            return
        with self.lock:
            self.events.append(dict(ev, t=time.monotonic()))
        if ev["type"] == "error":
            print(f"   ⚠ {ev['text']}")

    def lines(self):
        with self.lock:
            return [e for e in self.events if e["type"] == "line"]

    def talk(self, wavs, gaps):
        for w, g in zip(wavs, gaps):
            self.fake.stdin.write(f"play {w} {g}\n")
        self.fake.stdin.flush()

    def wait_all(self, direction, n, timeout=150, settle=1.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            got = {i for ln in self.lines() for i in which(ln["original"])}
            if len(got) >= n and self.eng.speaker(direction).backlog() == 0:
                time.sleep(settle)
                return
            time.sleep(0.2)

    def close(self):
        self.eng.stop()
        try:
            self.fake.stdin.write("quit\n")
            self.fake.stdin.flush()
            self.fake.wait(5)
        except Exception:
            self.fake.kill()
        self.eng.shutdown()

    def report(self):
        spoken = {e["id"]: e for e in self.events if e["type"] == "spoken"}
        order = []
        for ln in self.lines():
            hit = which(ln["original"])
            order += hit
            sp = spoken.get(ln["id"])
            ends = [self.played[i]["end"] for i in hit if i < len(self.played)]
            lat = f"{sp['t'] - max(ends):.1f}s after the sentence ended" if sp and ends else "-"
            print(f"   {hit} {ln['original']}\n       → {ln['translated']}   (voice started {lat})")
        return order


def main():
    if "--fake" in sys.argv:
        return fake_app(sys.argv[sys.argv.index("--fake") + 1])
    import soundfile as sf
    from dizcord import config
    from dizcord.audio import devices, winaudio
    from dizcord.providers.tts import EdgeTTS
    from dizcord.speech import Utterance
    model = next((a for a in sys.argv[1:] if not a.startswith("-")), "base")
    cable = devices.find_virtual_cable()
    if not cable:
        print("FAIL: no virtual cable (CABLE Input) found - install VB-Audio Virtual Cable.")
        return 1
    if winaudio.capture_devices_of("discord"):
        print("Discord is recording right now (in a call?) - this test plays into the virtual cable, so it waits "
              "until you leave the call.")
        return 1
    tmp = ROOT / "data" / "calltest"
    tmp.mkdir(parents=True, exist_ok=True)
    edge = EdgeTTS({}, None)
    wavs = []
    for i, s in enumerate(SENTENCES):
        p = tmp / f"sentence{i}.wav"
        if not p.exists():
            a, sr = edge.synthesize(s, "en", "en-US-GuyNeural")
            sf.write(p, a, sr)
        wavs.append(p)

    def profile():
        prof = config.default_profile()
        prof["stt"] = {"provider": "faster_whisper", "settings": {"faster_whisper": {"model": model}}}
        prof["translation"]["provider"] = "google_free"
        prof["tts"]["provider"] = "edge"
        return prof

    ok = True

    def check(name, cond, extra=""):
        nonlocal ok
        ok &= bool(cond)
        print(("  PASS " if cond else "  FAIL ") + name + (f"  {extra}" if extra else ""))

    # ------------------------------------------------------------ 1. Discord-only listening
    print(f"1. Listening to 'Discord' only, Whisper '{model}' (first run downloads it)…")
    prof = profile()
    prof["input"].update(listen_mode="app")
    prof["incoming"].update(output_device=cable, source_lang="en", target_lang="pt", hear_originals=False)
    prof["outgoing"]["enabled"] = False
    r = Run(prof, cable)
    r.eng.start()
    end = time.monotonic() + 600
    while "incoming" not in r.eng.pipelines and r.eng.running and time.monotonic() < end:
        time.sleep(0.2)
    pl = r.eng.pipelines.get("incoming")
    if not pl or not pl.app_capture:
        print("  FAIL: Discord-only listening did not start (needs Windows 10 2004 or newer)")
        r.close()
        return 1
    dev = r.eng.outputs.get(cable)
    stats = {"parallel": 0, "paused": 0, "levels": set(), "t": 0.0}
    stop = threading.Event()

    def monitor():
        while not stop.is_set():
            with dev.lock:
                stats["parallel"] = max(stats["parallel"], sum(1 for c in dev.clips if c.tag == "incoming"))
            stats["paused"] += 1 if pl.segmenter and pl.segmenter.muted else 0
            if r.played and time.monotonic() - stats["t"] > 2:
                stats["t"] = time.monotonic()
                try:
                    stats["levels"] |= {round(v.GetMasterVolume(), 4) for _n, p, _s, v, _i in
                                        winaudio._on_com_thread(winaudio._sessions, 0) if p == r.pid}
                except Exception:
                    pass
            time.sleep(0.005)

    threading.Thread(target=monitor, daemon=True).start()
    time.sleep(1.0)
    r.talk(wavs, [1.0, 0.6, 3.0, 0.6, 0.6, 0.0])

    def chat():
        time.sleep(6)
        for t in ("Mensagem do chat: alguém quer jogar depois?", "Outra mensagem do chat."):
            r.eng.speaker("incoming").say(Utterance(t, "pt", kind="chat", who="Marta"))
            time.sleep(0.3)

    threading.Thread(target=chat, daemon=True).start()
    r.wait_all("incoming", len(SENTENCES))
    stop.set()
    order = r.report()
    lines = r.lines()
    r.eng.stop()
    time.sleep(0.5)
    after = [round(v.GetMasterVolume(), 4) for _n, p, _s, v, _i in winaudio._on_com_thread(winaudio._sessions, 0)
             if p == r.pid]
    r.close()
    check("every sentence translated, none dropped", sorted(set(order)) == list(range(len(SENTENCES))))
    check("in the order they were said", order == sorted(order), order)
    check("the app never heard its own voice", all(which(ln["original"]) for ln in lines))
    check("never two app voices at once (chat messages included)", stats["parallel"] == 1, stats["parallel"])
    check("listening never paused while the app talked", stats["paused"] == 0)
    check("Hear people off: Discord turned down while running", stats["levels"] and max(stats["levels"]) <= 0.0011,
          sorted(stats["levels"]))
    check("Discord's volume given back after Stop", after and min(after) == 1.0, after)

    # ------------------------------------------------------------ 2. echo (no headphones)
    print("\n2. No headphones: the 'microphone' also hears the app's own voice…")
    prof = profile()
    prof["incoming"]["enabled"] = False
    rec = next((n for n in devices.input_devices() if n.lower().startswith("cable output")), "CABLE Output")
    prof["input"].update(mic_device=rec, mic_mode="vad", ignore_mic_while_playing=False)
    prof["outgoing"].update(source_lang="auto", target_lang="es", output_device=cable)
    r = Run(prof, cable)
    r.eng.start()
    while "outgoing" not in r.eng.pipelines and r.eng.running and time.monotonic() < end:
        time.sleep(0.2)
    time.sleep(1.0)
    r.talk(wavs[:4], [6.0, 6.0, 6.0, 0.0])
    r.wait_all("outgoing", 4, settle=8.0)
    order = r.report()
    lines = r.lines()
    r.close()
    check("all 4 sentences translated once, in order", order == [0, 1, 2, 3], order)
    check("its own voice was never translated again (no loop)", all(which(ln["original"]) for ln in lines))
    print("\nPASS" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
