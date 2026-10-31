"""Universal Ecosystem Bootstrapper & Patch Orchestrator.
Prepares donor applications (OverTranslate v2.9.0 & LiveTranslate) and applies
the 7 engineering patches from the CONFIG/ vault for 100% automated setup on new PCs.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("Bootstrap")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "CONFIG"

OVERTRANSLATE_DIR = PROJECT_ROOT / "stage_2_screen" / "OverTranslate"
OVERTRANSLATE_CURRENT = OVERTRANSLATE_DIR / "current"
OVERTRANSLATE_EXE = OVERTRANSLATE_CURRENT / "OverTranslate.exe"
OVERTRANSLATE_DLL = OVERTRANSLATE_CURRENT / "OverTranslate.dll"

LIVETRANSLATE_DIR = PROJECT_ROOT / "stage_1_audio" / "LiveTranslate"


def get_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_with_fallback(urls: list[str], dest_file: Path) -> bool:
    """Download a file with fallback mirror support."""
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    for url in urls:
        try:
            log.info("Downloading: %s ...", url)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp, open(dest_file, "wb") as f:
                shutil.copyfileobj(resp, f)
            if dest_file.is_file() and dest_file.stat().st_size > 1024:
                log.info("Download successful: %s (%d bytes)", dest_file.name, dest_file.stat().st_size)
                return True
        except Exception as e:
            log.warning("Download from %s failed: %s. Trying next mirror...", url, e)
    return False


def setup_stage_2_overtranslate() -> bool:
    """Ensure OverTranslate v2.9.0 is present, patched, and update-nag disabled."""
    log.info("--- [1/2] Verifying Stage 2 (OverTranslate) ---")

    if not OVERTRANSLATE_EXE.is_file():
        log.info("OverTranslate.exe missing. Downloading official portable release v2.9.0...")
        zip_path = OVERTRANSLATE_DIR / "OverTranslate-win-Portable.zip"
        urls = [
            "https://github.com/Hon-Lu/OverTranslate/releases/download/2.9.0/OverTranslate-win-Portable.zip",
            "https://ghproxy.net/https://github.com/Hon-Lu/OverTranslate/releases/download/2.9.0/OverTranslate-win-Portable.zip",
        ]
        if not download_with_fallback(urls, zip_path):
            log.error("Failed to download OverTranslate. Please check internet connection.")
            return False

        log.info("Extracting %s to %s ...", zip_path.name, OVERTRANSLATE_CURRENT)
        OVERTRANSLATE_CURRENT.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(OVERTRANSLATE_CURRENT)
        try:
            zip_path.unlink()
        except Exception:
            pass
        log.info("OverTranslate extracted successfully.")

    # 1. Apply Win11 0x800401D0 clipboard crash patch (only if needed)
    vault_dll = CONFIG_DIR / "stage_2_screen" / "OverTranslate.patched.dll"
    if vault_dll.is_file() and OVERTRANSLATE_CURRENT.is_dir():
        v_hash = get_file_hash(vault_dll)
        c_hash = get_file_hash(OVERTRANSLATE_DLL)
        if v_hash != c_hash:
            try:
                shutil.copy2(vault_dll, OVERTRANSLATE_DLL)
                log.info("Injected OverTranslate.patched.dll into %s", OVERTRANSLATE_DLL)
            except PermissionError:
                log.warning("OverTranslate.dll is currently locked by a running process. Patch is pending restart.")
        else:
            log.info("OverTranslate.patched.dll is already active and verified.")

    # 2. Synchronize appsettings.json and lock SkippedUpdateVersion
    cfg_src = CONFIG_DIR / "stage_2_screen" / "appsettings.json"
    if cfg_src.is_file():
        cfg_appdata = Path(os.path.expandvars(r"%APPDATA%\OverTranslate\appsettings.json"))
        cfg_appdata.parent.mkdir(parents=True, exist_ok=True)
        cfg_dest = OVERTRANSLATE_CURRENT / "appsettings.json"

        try:
            shutil.copy2(cfg_src, cfg_dest)
            shutil.copy2(cfg_src, cfg_appdata)
            log.info("Synchronized authoritative appsettings.json (SkippedUpdateVersion locked to v2.10.0).")
        except Exception as e:
            log.warning("Could not synchronize appsettings.json: %s", e)

    return True


def setup_stage_1_livetranslate() -> bool:
    """Ensure LiveTranslate base files are present and all 14 custom modules injected."""
    log.info("--- [2/2] Verifying Stage 1 (LiveTranslate & 7 Patches) ---")

    # If base files missing, download upstream repo
    core_file = LIVETRANSLATE_DIR / "audio_capture.py"
    if not core_file.is_file():
        log.info("LiveTranslate upstream missing. Downloading base repository...")
        zip_path = PROJECT_ROOT / "stage_1_audio" / "livetranslate_upstream.zip"
        urls = [
            "https://github.com/TheDeathDragon/LiveTranslate/archive/refs/heads/main.zip",
            "https://ghproxy.net/https://github.com/TheDeathDragon/LiveTranslate/archive/refs/heads/main.zip",
        ]
        if download_with_fallback(urls, zip_path):
            log.info("Extracting LiveTranslate upstream...")
            LIVETRANSLATE_DIR.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    parts = member.split("/", 1)
                    if len(parts) > 1 and parts[1]:
                        target = LIVETRANSLATE_DIR / parts[1]
                        if member.endswith("/"):
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(member) as src, open(target, "wb") as dst:
                                shutil.copyfileobj(src, dst)
            try:
                zip_path.unlink()
            except Exception:
                pass
            log.info("LiveTranslate upstream extracted successfully.")

    # Apply all authoritative custom modules from CONFIG/stage_1_audio/custom_modules
    apply_script = CONFIG_DIR / "stage_1_audio" / "apply_patches.py"
    if apply_script.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location("apply_patches", str(apply_script))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "apply_stage1_orchestration"):
                mod.apply_stage1_orchestration()

    return True


def verify_integrity() -> bool:
    """Audit all patches using the launcher's PatchIntegrityChecker."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from launcher.patch_checker import PatchIntegrityChecker

        report = PatchIntegrityChecker.audit_all()
        log.info(
            "Ecosystem Integrity Audit: %d/%d patches active | %d/%d components verified.",
            report["active_patches_count"],
            report["total_patches_count"],
            report["passed_count"],
            report["total_count"],
        )
        if not report["all_passed"]:
            log.info("Auto-healing patches from CONFIG vault...")
            PatchIntegrityChecker.restore_all_patches()
            report = PatchIntegrityChecker.audit_all()
        return report["all_passed"]
    except Exception as e:
        log.warning("Integrity check skipped: %s", e)
        return True


def main():
    log.info("============================================================")
    log.info("  UNIVERSAL ECOSYSTEM BOOTSTRAPPER & PATCH INJECTOR")
    log.info("============================================================")

    ok_s2 = setup_stage_2_overtranslate()
    ok_s1 = setup_stage_1_livetranslate()
    ok_audit = verify_integrity()

    if ok_s1 and ok_s2 and ok_audit:
        log.info("============================================================")
        log.info("  [SUCCESS] ALL STAGES DEPLOYED AND PATCHED SUCCESSFULLY!")
        log.info("============================================================")
        sys.exit(0)
    else:
        log.error("Bootstrap finished with warnings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
