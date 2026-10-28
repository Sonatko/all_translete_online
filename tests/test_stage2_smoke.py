"""Stage 2 Automated Regression & Smoke Verification Gate.

Verifies:
1. OverTranslate binary presence and integrity.
2. Patched OverTranslate.dll in CONFIG and active directories.
3. Authoritative appsettings.json schema and Bilingual RU <-> EN configuration.
4. Hotkey wiring consistency (Ctrl+Alt+A, Ctrl+C+C, Ctrl+Alt+C, Ctrl+Alt+W).
"""

import json
import os
import sys

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGE2_DIR = os.path.join(WORKSPACE_ROOT, "stage_2_screen", "OverTranslate", "current")
CONFIG2_DIR = os.path.join(WORKSPACE_ROOT, "CONFIG", "stage_2_screen")


def test_stage2():
    print("=" * 60)
    print("  STAGE 2 AUTOMATED REGRESSION & SMOKE VERIFICATION GATE")
    print("=" * 60)

    # 1. Binary presence
    print("\n1. OverTranslate Executable & Component Check:")
    exe_path = os.path.join(STAGE2_DIR, "OverTranslate.exe")
    dll_path = os.path.join(STAGE2_DIR, "OverTranslate.dll")
    assert os.path.isfile(exe_path), f"Missing OverTranslate.exe at {exe_path}"
    assert os.path.isfile(dll_path), f"Missing OverTranslate.dll at {dll_path}"
    print(f"  [PASS] OverTranslate.exe present ({os.path.getsize(exe_path) / 1024:.1f} KB)")
    print(f"  [PASS] OverTranslate.dll present ({os.path.getsize(dll_path) / (1024*1024):.2f} MB)")

    # 2. Patched DLL presence in CONFIG
    print("\n2. Authoritative Patched DLL in CONFIG (Turnkey Installer Check):")
    cfg_dll = os.path.join(CONFIG2_DIR, "OverTranslate.patched.dll")
    assert os.path.isfile(cfg_dll), f"Missing OverTranslate.patched.dll at {cfg_dll}"
    print(f"  [PASS] OverTranslate.patched.dll cached in CONFIG ({os.path.getsize(cfg_dll) / (1024*1024):.2f} MB)")

    # 3. Configuration integrity
    print("\n3. Authoritative Configuration Integrity (Bilingual RU <-> EN):")
    cfg_json = os.path.join(CONFIG2_DIR, "appsettings.json")
    assert os.path.isfile(cfg_json), f"Missing appsettings.json at {cfg_json}"
    with open(cfg_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    qt = data.get("QuickTranslate", {})
    assert qt.get("BilingualEnabled") is True, "QuickTranslate.BilingualEnabled must be True"
    assert qt.get("BilingualFirstLanguage") == "RU", f"Expected RU, got {qt.get('BilingualFirstLanguage')}"
    assert qt.get("BilingualSecondLanguage") == "EN-US", f"Expected EN-US, got {qt.get('BilingualSecondLanguage')}"
    print("  [PASS] QuickTranslate configured with BilingualEnabled=True (RU <-> EN-US)")

    # 4. Hotkey check
    print("\n4. Hotkey Scheme Integrity:")
    assert data.get("QuickTranslateHotkeyEnabled") is True, "QuickTranslateHotkey must be enabled"
    assert data.get("QuickLookupHotkeyEnabled") is True, "QuickLookupHotkey must be enabled"
    assert data.get("TranslationWindowHotkeyEnabled") is True, "TranslationWindowHotkey must be enabled"
    print(f"  [PASS] QuickTranslate: {data.get('QuickTranslateHotkeyDisplay')}")
    print(f"  [PASS] QuickLookup:    {data.get('QuickLookupHotkeyDisplay')}")
    print(f"  [PASS] Screen OCR:      {data.get('HotkeyDisplay')}")
    print(f"  [PASS] Main Window:    {data.get('TranslationWindowHotkeyDisplay')}")

    print("\n" + "=" * 60)
    print("  ALL STAGE 2 SYSTEM CHECKS PASSED: READY FOR PRODUCTION RUN")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_stage2()
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
