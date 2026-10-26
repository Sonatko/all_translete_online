import os
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import psutil

sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

from nllb_engine import LocalNLLBEngine
from translator import Translator

def get_process_ram_mb():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

def test_nllb_lifecycle():
    initial_ram = get_process_ram_mb()
    print(f"[TEST 1] Initial Process RAM: {initial_ram:.1f} MB")

    # 1. Load Local NLLB Engine
    print("\n--- Initializing Local NLLB Engine ---")
    engine = LocalNLLBEngine.get_instance()
    assert engine is not None
    loaded_ram = get_process_ram_mb()
    print(f"[TEST 2] Loaded Process RAM: {loaded_ram:.1f} MB (Delta: +{loaded_ram - initial_ram:.1f} MB)")

    res = engine.translate("Hello world, this is a test.", target_language="ru")
    print(f"[TEST 3] Translation Result: {res}")
    assert len(res) > 0

    # 2. Test Translator switching to API (triggers unload)
    print("\n--- Switching Translator to API Model (Testing Unload) ---")
    api_translator = Translator(
        api_base="https://api.openai.com/v1",
        api_key="test-key",
        model="gpt-4o",
    )
    assert api_translator._is_local_nllb is False
    assert LocalNLLBEngine._instance is None, "Expected LocalNLLBEngine._instance to be None after unload!"

    unloaded_ram = get_process_ram_mb()
    print(f"[TEST 4] RAM after API switch & unload: {unloaded_ram:.1f} MB (Freed: -{loaded_ram - unloaded_ram:.1f} MB)")

    # 3. Test Reloading Local NLLB when switching back
    print("\n--- Switching Translator Back to Local NLLB (Testing Reload) ---")
    local_translator = Translator(
        api_base="local",
        api_key="local",
        model="nllb-200-1.3b",
    )
    assert local_translator._is_local_nllb is True
    reloaded_engine = LocalNLLBEngine.get_instance()
    assert reloaded_engine is not None
    res2 = local_translator.translate("Good morning!", source_language="en")
    print(f"[TEST 5] Translation after reload: {res2}")
    assert len(res2) > 0

    print("\n[SUCCESS] NLLB MEMORY LIFECYCLE (LOAD -> UNLOAD -> RELOAD) FULLY VERIFIED!")

if __name__ == "__main__":
    test_nllb_lifecycle()
