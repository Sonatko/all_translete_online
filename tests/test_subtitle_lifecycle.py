import sys
import os

# Set headless Qt environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

from PyQt6.QtWidgets import QApplication
from subtitle_window import SubtitleWindow, _SubtitleTextWidget, DEFAULT_SUBTITLE_WIN_SETTINGS

app = QApplication.instance() or QApplication(sys.argv)

def test_subtitle_text_widget_no_flicker():
    w = _SubtitleTextWidget()
    cfg = DEFAULT_SUBTITLE_WIN_SETTINGS["lines"][1]  # translation line
    w.set_config(cfg)
    
    # 1. Stream token 1
    w.set_streaming_text("Привет")
    assert w._text == "Привет"
    assert w._content_opacity_val == 1.0
    
    # 2. Stream token 2
    w.set_streaming_text("Привет, как дела")
    assert w._text == "Привет, как дела"
    
    # 3. Final commit with identical text
    # Track if height_changed was emitted
    emitted = []
    w.height_changed.connect(lambda: emitted.append(True))
    
    # Calling set_text with identical text MUST be a no-op (no flicker/no animate)
    w.set_text("Привет, как дела")
    assert len(emitted) == 0, "set_text with identical text must not emit height_changed!"
    assert w._text == "Привет, как дела"
    print("[PASS] _SubtitleTextWidget: Zero-flicker on identical text commit verified.")

def test_subtitle_window_streaming_commit_in_place():
    settings = dict(DEFAULT_SUBTITLE_WIN_SETTINGS)
    settings["sentences"] = 1
    win = SubtitleWindow(settings)
    
    # 1. First streaming update
    win._on_update_streaming_text("Hello how are you", "Привет")
    assert len(win._sentences) == 1
    assert win._sentences[0][0] == "Hello how are you"
    assert win._sentences[0][1] == {"zh": "Привет"} or list(win._sentences[0][1].values())[0] == "Привет"
    
    # 2. Second streaming update for same original
    win._on_update_streaming_text("Hello how are you", "Привет, как дела")
    assert len(win._sentences) == 1, "Streaming must update in-place, not append!"
    assert list(win._sentences[0][1].values())[0] == "Привет, как дела"
    
    # 3. Final sentence commit
    win._insert_sentence("Hello how are you", {"ru": "Привет, как дела"})
    assert len(win._sentences) == 1, "Final sentence must commit in-place into existing streaming slot!"
    assert win._sentences[0][1]["ru"] == "Привет, как дела"
    
    print("[PASS] SubtitleWindow: In-place streaming commit verified without sentence duplication.")

if __name__ == "__main__":
    test_subtitle_text_widget_no_flicker()
    test_subtitle_window_streaming_commit_in_place()
    print("ALL TESTS PASSED SUCCESSFULLY!")
