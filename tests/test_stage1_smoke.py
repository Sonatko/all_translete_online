"""
Stage 1.1 + 1.2 Regression & Smoke Verification Gate
Tests runtime dependencies, model cache presence, and Golden Control Scheme wiring.
Run:
    stage_1_audio\\.venv\\Scripts\\python.exe tests\\test_stage1_smoke.py
"""

import sys
import os
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
STAGE1_DIR = WORKSPACE_ROOT / "stage_1_audio" / "LiveTranslate"
sys.path.insert(0, str(STAGE1_DIR))

PASS = "[PASS]"
FAIL = "[FAIL]"

def run_smoke_tests():
    print("=" * 60)
    print("  STAGE 1 AUTOMATED REGRESSION & SMOKE VERIFICATION GATE")
    print("=" * 60)
    all_passed = True

    # 1. Dependency Imports
    print("\n1. Core Engine Imports:")
    try:
        import torch
        import PyQt6
        import sherpa_onnx
        import ctranslate2
        import transformers
        print(f"  {PASS} PyTorch ({torch.__version__}), PyQt6, Sherpa-ONNX, CTranslate2, Transformers")
    except Exception as e:
        print(f"  {FAIL} Failed to import core dependencies: {e}")
        all_passed = False

    # 2. Sherpa-ONNX Model Cache Verification
    print("\n2. Physical Speech-to-Text Model Presence (Zero-Download Gate):")
    sensevoice_path = STAGE1_DIR / "models" / "sherpa-onnx" / "sensevoice" / "model.int8.onnx"
    tokens_path = STAGE1_DIR / "models" / "sherpa-onnx" / "sensevoice" / "tokens.txt"
    if sensevoice_path.is_file() and tokens_path.is_file():
        size_mb = sensevoice_path.stat().st_size / (1024 * 1024)
        print(f"  {PASS} SenseVoice Small INT8 cached: {size_mb:.1f} MB ({sensevoice_path.name})")
    else:
        print(f"  {FAIL} Missing SenseVoice model files in {sensevoice_path.parent}")
        all_passed = False

    # 3. NLLB Offline Translation Model Presence
    print("\n3. Physical Offline Translation Model Presence:")
    nllb_600m = WORKSPACE_ROOT / "stage_1_audio" / "nllb_server" / "models" / "nllb-200-600m-int8" / "model.bin"
    nllb_13b = WORKSPACE_ROOT / "stage_1_audio" / "nllb_server" / "models" / "nllb-200-1.3b-int8" / "model.bin"
    if nllb_600m.is_file():
        print(f"  {PASS} Meta NLLB-200 600M INT8 cached: {nllb_600m.stat().st_size / (1024 * 1024):.1f} MB")
    else:
        print(f"  {FAIL} Missing NLLB-200 600M INT8 model: {nllb_600m}")
        all_passed = False

    if nllb_13b.is_file():
        print(f"  {PASS} Meta NLLB-200 1.3B INT8 cached: {nllb_13b.stat().st_size / (1024 * 1024):.1f} MB")

    # 4. Configuration Sanity Check
    print("\n4. Authoritative Configuration Integrity:")
    config_file = WORKSPACE_ROOT / "CONFIG" / "stage_1_audio" / "user_settings.json"
    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            asr_engine = data.get("asr_engine")
            active_model = data.get("active_model", 0)
            models = data.get("models", [])
            print(f"  {PASS} authorative config valid: ASR='{asr_engine}', Active Model={active_model} ('{models[active_model]['name']}')")
        except Exception as e:
            print(f"  {FAIL} Configuration corrupted: {e}")
            all_passed = False
    else:
        print(f"  {FAIL} Missing authoritative config at {config_file}")
        all_passed = False

    # 5. Golden Control Scheme Wiring Verification
    print("\n5. Golden Control Scheme Wiring Check:")
    try:
        from subtitle_window import SubtitleWindow
        from subtitle_overlay import SubtitleOverlay
        print(f"  {PASS} SubtitleWindow and SubtitleOverlay modules successfully loaded")
    except Exception as e:
        print(f"  {FAIL} UI components failed to import: {e}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ALL CORE SYSTEM CHECKS PASSED: READY FOR PRODUCTION RUN")
    else:
        print("  SYSTEM REGRESSION DETECTED: PLEASE FIX REPORTED ISSUES")
    print("=" * 60)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_smoke_tests())
