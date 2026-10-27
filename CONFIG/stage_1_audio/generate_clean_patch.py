import os
import subprocess
import sys
import difflib

def generate_patch():
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    lt_dir = os.path.join(workspace, "stage_1_audio", "LiveTranslate")
    patch_out = os.path.join(workspace, "CONFIG", "stage_1_audio", "patches", "orchestrator_stage1.patch")
    upstream_commit = "9d392a5"

    files_to_patch = [
        "asr_worker.py",
        "control_panel.py",
        "dialogs.py",
        "main.py",
        "model_manager.py",
        "requirements.txt",
        "start.bat",
        "subtitle_window.py",
        "translator.py",
        "vad_processor.py",
    ]

    all_patch_lines = []

    for fname in files_to_patch:
        # 1. Get original content from git
        git_path = f"{upstream_commit}:stage_1_audio/LiveTranslate/{fname}"
        res = subprocess.run(
            ["git", "show", git_path],
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0:
            print(f"[ERROR] Failed to get original for {fname}: {res.stderr}")
            continue
        orig_lines = res.stdout.splitlines(keepends=True)

        # 2. Get local modified content
        local_path = os.path.join(lt_dir, fname)
        if not os.path.exists(local_path):
            print(f"[ERROR] Local file not found: {local_path}")
            continue
        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
            mod_lines = f.readlines()

        # 3. Generate unified diff
        diff = list(
            difflib.unified_diff(
                orig_lines,
                mod_lines,
                fromfile=f"a/{fname}",
                tofile=f"b/{fname}",
            )
        )
        if diff:
            # Add git diff header
            header = [
                f"diff --git a/{fname} b/{fname}\n",
                f"--- a/{fname}\n",
                f"+++ b/{fname}\n",
            ]
            # Skip difflib fromfile/tofile lines if they duplicate
            body = [line for line in diff if not line.startswith("--- ") and not line.startswith("+++ ")]
            all_patch_lines.extend(header)
            all_patch_lines.extend(body)
            print(f"  [PATCHED] {fname}: {len(body)} diff lines")
        else:
            print(f"  [UNCHANGED] {fname}")

    os.makedirs(os.path.dirname(patch_out), exist_ok=True)
    with open(patch_out, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(all_patch_lines)

    print(f"\n[SUCCESS] Generated clean orchestrator patch: {patch_out} ({os.path.getsize(patch_out)} bytes)")

if __name__ == "__main__":
    generate_patch()
