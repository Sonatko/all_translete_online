"""Standalone CLI Model Downloader for Translation Ecosystem.
Can be executed directly on new PCs or in scripts to pre-warm all model weights.
Usage:
    python scripts/download_models.py --profile zh_en --china-mirror
    python scripts/download_models.py --profile ru_en
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from launcher.model_downloader import (
    MODEL_SPECS,
    build_download_urls,
    download_single_file,
    get_pipeline_specs,
    check_spec_status,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DownloadCLI")


def format_bytes(num_bytes: int) -> str:
    """Format bytes into readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="Download AI models for Translation Ecosystem")
    parser.add_argument(
        "--profile",
        choices=["ru_en", "zh_en", "all"],
        default="zh_en",
        help="Model profile to download ('zh_en' for China, 'ru_en' for Russia, 'all' for both)",
    )
    parser.add_argument(
        "--china-mirror",
        action="store_true",
        default=False,
        help="Use Chinese mirror (hf-mirror.com) for high-speed download in mainland China",
    )
    args = parser.parse_args()

    profiles = ["ru_en", "zh_en"] if args.profile == "all" else [args.profile]
    specs_to_download = set()
    for prof in profiles:
        specs_to_download.update(get_pipeline_specs(prof))

    log.info("============================================================")
    log.info("  TRANSLATION ECOSYSTEM - MODEL DOWNLOAD WIZARD")
    log.info("  Profile: %s | China Mirror: %s", args.profile, args.china_mirror)
    log.info("============================================================")

    for spec_key in specs_to_download:
        spec = MODEL_SPECS[spec_key]
        status = check_spec_status(spec_key)

        log.info("\nChecking: %s [%s]", spec["name"], spec["task"])
        if status["is_ready"]:
            log.info("  -> [OK] Already present on disk (%s MB)", status["size_mb"])
            continue

        dest_dir: Path = spec["dest_dir"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file_info in spec["files"]:
            if len(file_info) == 3:
                remote_name = file_info[0]
                exp_size = file_info[1]
                local_name = file_info[2]
            else:
                remote_name = file_info[0]
                exp_size = file_info[1]
                local_name = file_info[0]

            target_file = dest_dir / local_name
            if target_file.is_file() and target_file.stat().st_size >= max(50, int(exp_size * 0.95)):
                log.info("  -> %s: [OK] Present (%s)", local_name, format_bytes(target_file.stat().st_size))
                continue

            urls = build_download_urls(spec["repo"], remote_name, china_mirror=args.china_mirror)
            log.info("  -> Downloading %s (expected %s)...", local_name, format_bytes(exp_size))

            last_pct = [-1]

            def on_progress(down: int, total: int, speed: float):
                pct = int((down / max(total, 1)) * 100)
                if pct != last_pct[0] and pct % 10 == 0:
                    sys.stdout.write(f"\r     [{pct}%] {format_bytes(down)} / {format_bytes(total)} ({speed:.2f} MB/s)  ")
                    sys.stdout.flush()
                    last_pct[0] = pct

            ok = download_single_file(urls, target_file, expected_size=exp_size, progress_cb=on_progress)
            sys.stdout.write("\n")
            if not ok:
                log.error("Failed to download %s. Please check internet connection.", local_name)
                sys.exit(1)

    log.info("\n============================================================")
    log.info("  [SUCCESS] ALL TARGET MODELS DOWNLOADED AND VERIFIED!")
    log.info("============================================================")


if __name__ == "__main__":
    main()

