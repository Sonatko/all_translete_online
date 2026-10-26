"""
Applies surgical patches from CONFIG/stage_1_audio/patches/ to stage_1_audio/LiveTranslate.
Checks idempotency: if patches are already applied, skips gracefully without error.
"""

import os
import subprocess
import sys


def apply_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    patches_dir = os.path.join(base_dir, "patches")
    rel_target = os.path.join("stage_1_audio", "LiveTranslate")

    patches = [
        "control_panel.patch",
        "main.patch",
        "subtitle_window.patch",
        "translator.patch",
    ]

    for p in patches:
        patch_path = os.path.join(patches_dir, p)
        if not os.path.exists(patch_path):
            continue

        # Check if already applied
        chk_rev = subprocess.run(
            ["git", "apply", "--check", "--reverse", "--ignore-whitespace", f"--directory={rel_target}", patch_path],
            cwd=workspace_root,
            capture_output=True,
        )
        if chk_rev.returncode == 0:
            print(f"  [OK] {p} is already applied in {rel_target}.")
            continue

        # Apply patch
        res = subprocess.run(
            ["git", "apply", "--ignore-whitespace", f"--directory={rel_target}", patch_path],
            cwd=workspace_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print(f"  [APPLIED] Successfully applied {p}")
        else:
            print(f"  [WARNING] Failed to apply {p}: {res.stderr.strip()}")


if __name__ == "__main__":
    apply_all()
