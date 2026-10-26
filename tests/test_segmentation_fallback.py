import sys
import os

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure LiveTranslate is in Python path
sys.path.insert(0, os.path.abspath("stage_1_audio/LiveTranslate"))

from main import LiveTranslateApp

def test_regex_sentence_segmenter():
    app = LiveTranslateApp.__new__(LiveTranslateApp)

    # Test 1: Multiple English sentences with punctuation
    text1 = "Hello world. This is the second sentence! And the third one?"
    res1 = app._split_sentences(text1, "en")
    print("TEST 1 (En punctuation):", res1)
    assert len(res1) == 3, f"Expected 3 sentences, got {len(res1)}"
    assert res1[0] == "Hello world."
    assert res1[1] == "This is the second sentence!"
    assert res1[2] == "And the third one?"

    # Test 2: Long sentence with comma fallback (>60 chars)
    text2 = "This is a very long introductory sentence without dots, and here is the second part of it."
    res2 = app._split_sentences(text2, "en")
    print("TEST 2 (Comma fallback):", res2)
    assert len(res2) == 2, f"Expected 2 parts, got {len(res2)}"

    # Test 3: Short utterance (single sentence)
    text3 = "Just a single short phrase."
    res3 = app._split_sentences(text3, "en")
    print("TEST 3 (Single sentence):", res3)
    assert len(res3) == 1, f"Expected 1 part, got {len(res3)}"

    # Test 4: CJK punctuation without spaces
    text4 = "こんにちは。これはテストです！第三の文？"
    res4 = app._split_sentences(text4, "ja")
    print("TEST 4 (CJK punctuation):", res4)
    assert len(res4) == 3, f"Expected 3 parts, got {len(res4)}"

    print("\n[SUCCESS] ALL ZERO-DEPENDENCY FALLBACK TESTS PASSED!")

if __name__ == "__main__":
    test_regex_sentence_segmenter()
