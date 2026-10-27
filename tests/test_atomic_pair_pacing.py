"""
Test suite for Mimi-standard Atomic Pair Pacing in SubtitleWindow.
Verifies:
1. Window initialized with 2000ms minimum display window and pacing timer.
2. First complete pair displays immediately.
3. Rapid second pair is held in _pending_pair during the 2.0s reading window.
4. Pacing timer timeout fires and displays the pending pair.
5. In-progress streaming text does not overwrite the visible complete pair.
6. clear() cleans up all pending state.
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage_1_audio', 'LiveTranslate'))

from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from subtitle_window import SubtitleWindow

errors = []

try:
    win = SubtitleWindow()
    assert win._min_display_ms == 2000, f"Expected 2000ms, got {win._min_display_ms}"
    assert win._pending_pair is None
    assert win._pacing_timer is not None
    print("[OK] SubtitleWindow initialized with 2000ms pacing timer")

    # 1. Insert Pair 1: Should display immediately
    win._on_update_text("Hello world", json.dumps({"ru": "Привет мир"}))
    assert len(win._sentences) == 1
    assert win._sentences[0][0] == "Hello world"
    assert win._pending_pair is None
    print("[OK] First complete pair displayed immediately")

    # 2. Rapid second pair (10ms later): Must NOT overwrite Pair 1
    win._on_update_text("Second sentence", json.dumps({"ru": "Второе предложение"}))
    assert win._sentences[0][0] == "Hello world", "Pair 1 was prematurely overwritten!"
    assert win._pending_pair is not None
    assert win._pending_pair[0] == "Second sentence"
    assert win._pacing_timer.isActive()
    print("[OK] Rapid second pair held in pending slot; Pair 1 protected")

    # 3. In-progress streaming text during reading window: Must be ignored
    win._on_update_streaming_text("Draft in progress...", "")
    assert win._sentences[0][0] == "Hello world", "Streaming text overwrote protected pair!"
    print("[OK] Streaming partial draft correctly ignored during protected reading window")

    # 4. Fire pacing timer: Pending pair should cleanly replace Pair 1
    win._on_pacing_timer_timeout()
    assert win._sentences[0][0] == "Second sentence"
    assert win._pending_pair is None
    print("[OK] Pacing timer smoothly transitioned to Pair 2")

    # 5. Clear: Resets everything safely
    win.clear()
    assert len(win._sentences) == 0
    assert win._pending_pair is None
    assert not win._pacing_timer.isActive()
    print("[OK] clear() resets all atomic pacing state")

except Exception as e:
    errors.append(f"[FAIL] Atomic pacing: {e}")

print()
if errors:
    print("=== FAILURES ===")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print("=== ALL ATOMIC PAIR PACING CHECKS PASSED ===")
    sys.exit(0)
