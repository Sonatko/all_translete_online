"""
Universal Ecosystem Orchestrator: Stage 1 Auto-Patcher & Injector
Applies surgical patches and copies custom modules into stage_1_audio/LiveTranslate.
Guarantees clean idempotency: safe to run repeatedly without breaking code.
"""

import os
import shutil
import subprocess
import sys


def apply_stage1_orchestration():
    config_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(config_dir, "..", ".."))
    target_dir = os.path.join(workspace_root, "stage_1_audio", "LiveTranslate")
    custom_modules_dir = os.path.join(config_dir, "custom_modules")
    patch_file = os.path.join(config_dir, "patches", "orchestrator_stage1.patch")
    settings_src = os.path.join(config_dir, "user_settings.json")
    settings_dst = os.path.join(target_dir, "user_settings.json")

    if not os.path.exists(target_dir):
        print(f"[ERROR] Target directory not found: {target_dir}")
        return False

    print("============================================================")
    print("  STAGE 1: AUDIO ENGINE ORCHESTRATION & INJECTION")
    print("============================================================")

    # 1. Copy authoritative custom modules & modified engine components
    print("\n[1/2] Injecting authoritative Stage 1 engine modules...")
    if os.path.exists(custom_modules_dir):
        for fname in os.listdir(custom_modules_dir):
            if fname.endswith(".py") or fname.endswith(".txt"):
                src = os.path.join(custom_modules_dir, fname)
                dst = os.path.join(target_dir, fname)
                shutil.copy2(src, dst)
                print(f"  [OK] Injected: {fname}")
    else:
        print(f"  [ERROR] Custom modules directory not found: {custom_modules_dir}")
        return False

    # 2. Synchronize authoritative settings
    print("\n[2/2] Synchronizing authoritative user_settings.json...")
    if os.path.exists(settings_src):
        shutil.copy2(settings_src, settings_dst)
        print("  [OK] Synchronized user_settings.json")

    print("\n============================================================")
    print("  STAGE 1 ORCHESTRATION COMPLETE: ENGINE READY")
    print("============================================================")
    return True


if __name__ == "__main__":
    success = apply_stage1_orchestration()
    sys.exit(0 if success else 1)
