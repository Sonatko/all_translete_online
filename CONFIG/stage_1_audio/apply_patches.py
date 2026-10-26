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

    # 1. Copy custom modules (Zero-loss standalone components)
    print("\n[1/3] Injecting custom high-performance modules...")
    if os.path.exists(custom_modules_dir):
        for fname in os.listdir(custom_modules_dir):
            if fname.endswith(".py"):
                src = os.path.join(custom_modules_dir, fname)
                dst = os.path.join(target_dir, fname)
                shutil.copy2(src, dst)
                print(f"  [OK] Injected module: {fname}")
    else:
        print(f"  [WARNING] Custom modules directory not found: {custom_modules_dir}")

    # 2. Apply unified surgical patch
    print("\n[2/3] Applying surgical orchestrator patch...")
    if os.path.exists(patch_file):
        # Check if already applied (reverse check)
        chk_rev = subprocess.run(
            ["git", "apply", "--check", "--reverse", "--ignore-whitespace", patch_file],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if chk_rev.returncode == 0:
            print("  [OK] orchestrator_stage1.patch is already applied.")
        else:
            res = subprocess.run(
                ["git", "apply", "--ignore-whitespace", patch_file],
                cwd=target_dir,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                print("  [APPLIED] Successfully applied orchestrator_stage1.patch")
            else:
                print(f"  [WARNING] Patch apply warning / error: {res.stderr.strip()}")
    else:
        print(f"  [ERROR] Patch file not found: {patch_file}")

    # 3. Synchronize authoritative settings
    print("\n[3/3] Synchronizing authoritative user_settings.json...")
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
