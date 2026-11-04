"""Unit test for HTTP Range (206 Partial Content) resumable downloads in model_downloader.py."""
from __future__ import annotations

import hashlib
import http.server
import os
from pathlib import Path
import socketserver
import sys
import tempfile
import threading
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launcher.model_downloader import download_single_file

# Sample test payload (256 KB)
TEST_DATA = os.urandom(256 * 1024)
TEST_MD5 = hashlib.md5(TEST_DATA).hexdigest()


class RangeHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler implementing RFC 7233 byte-range serving."""

    def do_GET(self):
        range_header = self.headers.get("Range")
        data_len = len(TEST_DATA)

        if range_header and range_header.startswith("bytes="):
            # Parse Range: bytes=START-
            range_val = range_header[6:].strip()
            parts = range_val.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else data_len - 1

            if start >= data_len:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{data_len}")
                self.end_headers()
                return

            end = min(end, data_len - 1)
            chunk = TEST_DATA[start : end + 1]

            self.send_response(206)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Range", f"bytes {start}-{end}/{data_len}")
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(data_len))
            self.end_headers()
            self.wfile.write(TEST_DATA)

    def log_message(self, format, *args):
        pass  # Suppress console spam during tests


class TestResumableDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start local test HTTP server on ephemeral port
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), RangeHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.url = f"http://127.0.0.1:{cls.port}/test_model.bin"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_resumable_download_from_partial_file(self):
        """Simulate a download dropped at ~100 KB and resume to 256 KB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_file = Path(tmpdir) / "test_model.bin"
            part_file = dest_file.with_suffix(dest_file.suffix + ".part")

            # 1. Pre-seed partial file with the first 100 KB (simulating dropped connection)
            partial_len = 100 * 1024
            part_file.write_bytes(TEST_DATA[:partial_len])
            self.assertEqual(part_file.stat().st_size, partial_len)

            # 2. Call download_single_file - should resume from 100 KB via Range: bytes=102400-
            progress_history = []
            def on_progress(down, total, speed):
                progress_history.append((down, total))

            ok = download_single_file(
                urls=[self.url],
                dest_path=dest_file,
                expected_size=len(TEST_DATA),
                progress_cb=on_progress,
                max_retries_per_url=2,
            )

            # 3. Verify success and atomic file replacement
            self.assertTrue(ok, "Resumable download should succeed")
            self.assertTrue(dest_file.is_file(), "Final destination file must exist")
            self.assertFalse(part_file.exists(), ".part file must be cleaned up / moved on success")

            # 4. Verify bit-exact integrity
            final_data = dest_file.read_bytes()
            self.assertEqual(len(final_data), len(TEST_DATA))
            self.assertEqual(hashlib.md5(final_data).hexdigest(), TEST_MD5)

            # 5. Verify progress started from partial_len (100 KB), not 0
            self.assertGreater(len(progress_history), 0)
            first_down, total = progress_history[0]
            self.assertEqual(first_down, partial_len, "First progress event must report resumed byte offset")
            self.assertEqual(total, len(TEST_DATA))


if __name__ == "__main__":
    unittest.main()
