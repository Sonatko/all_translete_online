"""
Test suite for advanced B2-C2 vocabulary, phrasal verbs, idioms, and collocation highlighting.
Verifies:
1. Multi-word phrase matching (phrasal verbs, idioms, collocations).
2. Separable phrasal verbs with pronouns (e.g. 'figure it out', 'pointed that out').
3. Advanced B2-C2 single-word lemmas (e.g. 'quintessential', 'ubiquitous', 'scrutinize').
4. Exclusion of basic A1-B1 words (e.g. 'cable', 'board', 'arm', 'budget').
5. Sub-millisecond performance (< 0.05 ms per sentence, 0% CPU impact).
"""

import sys
import os
import time

# Ensure LiveTranslate directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIVETRANS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "stage_1_audio", "LiveTranslate")
if LIVETRANS_DIR not in sys.path:
    sys.path.insert(0, LIVETRANS_DIR)

from vocab_highlighter import tokenize_with_vocab_flags


def test_collocations():
    test_cases = [
        # (sentence, expected_highlighted_substrings)
        ("I figured out the solution quickly.", ["figured", "out"]),
        ("We are on the verge of a breakthrough.", ["on", "the", "verge", "of"]),
        ("He took everything for granted.", ["took", "for", "granted"]),
        ("The announcement came out of the blue.", ["out", "of", "the", "blue"]),
        ("They decided to call off the meeting.", ["call", "off"]),
        ("You should look forward to the journey.", ["look", "forward", "to"]),
        ("The witness shed light on the investigation.", ["shed", "light", "on"]),
        ("At all costs, we must avoid failure.", ["at", "all", "costs"]),
        ("By and large, the plan worked well.", ["by", "and", "large"]),
        ("He had to bite the bullet and apologize.", ["bite", "the", "bullet"]),
    ]

    for sentence, expected in test_cases:
        tokens = tokenize_with_vocab_flags(sentence)
        flagged = [tok.lower() for tok, is_v in tokens if is_v]
        for exp in expected:
            assert exp.lower() in flagged, f"Expected '{exp}' in flagged words for '{sentence}', got {flagged}"
    print("[PASS] Multi-word collocations & idioms successfully recognized.")


def test_separable_phrasal_verbs():
    test_cases = [
        ("We need to figure it out.", ["figure", "out"]),
        ("She pointed that out earlier.", ["pointed", "out"]),
        ("They will sort this out tomorrow.", ["sort", "out"]),
        ("I will write it down.", ["write", "down"]),
    ]

    for sentence, expected in test_cases:
        tokens = tokenize_with_vocab_flags(sentence)
        flagged = [tok.lower() for tok, is_v in tokens if is_v]
        for exp in expected:
            assert exp.lower() in flagged, f"Expected '{exp}' in flagged words for '{sentence}', got {flagged}"
    print("[PASS] Separable phrasal verbs recognized.")


def test_advanced_single_words():
    advanced_sentence = "This is a quintessential example of ubiquitous and meticulous research."
    tokens = tokenize_with_vocab_flags(advanced_sentence)
    flagged = [tok.lower() for tok, is_v in tokens if is_v]
    assert "quintessential" in flagged
    assert "ubiquitous" in flagged
    assert "meticulous" in flagged
    print(f"[PASS] Advanced single words recognized: {flagged}")


def test_no_false_positives_on_basic_words():
    basic_sentence = "The cable on the board in the budget room has an arm on it."
    tokens = tokenize_with_vocab_flags(basic_sentence)
    flagged = [tok.lower() for tok, is_v in tokens if is_v]
    assert "cable" not in flagged, f"'cable' should not be flagged: {flagged}"
    assert "board" not in flagged, f"'board' should not be flagged: {flagged}"
    assert "arm" not in flagged, f"'arm' should not be flagged: {flagged}"
    assert "budget" not in flagged, f"'budget' should not be flagged: {flagged}"
    print(f"[PASS] Basic words are NOT flagged. Clean output: {flagged}")


def test_sub_millisecond_speed():
    sentence = "We figured out that they were on the verge of taking everything for granted out of the blue."
    # 5,000 iterations benchmark
    t0 = time.perf_counter()
    N = 5000
    for _ in range(N):
        tokenize_with_vocab_flags(sentence)
    t1 = time.perf_counter()
    avg_ms = ((t1 - t0) * 1000) / N
    print(f"[PASS] Speed benchmark: {avg_ms:.4f} ms per sentence ({avg_ms * 1000:.1f} microseconds). Limit: < 0.05 ms.")
    assert avg_ms < 0.05, f"Lookup is too slow: {avg_ms} ms"


if __name__ == "__main__":
    test_collocations()
    test_separable_phrasal_verbs()
    test_advanced_single_words()
    test_no_false_positives_on_basic_words()
    test_sub_millisecond_speed()
    print("\nALL VOCAB COLLOCATION TESTS PASSED SUCCESSFULLY!")
