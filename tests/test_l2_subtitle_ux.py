"""
Smoke test for L2 English Learner subtitle UX changes.
Verifies vocab highlighting, typography hierarchy, and ASR latency thresholds.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage_1_audio', 'LiveTranslate'))

errors = []

# --- Test 1: vocab_highlighter ---
try:
    from vocab_highlighter import tokenize_with_vocab_flags
    tokens = tokenize_with_vocab_flags("The investigation revealed significant evidence of corruption")
    vocab_words = [t for t, is_v in tokens if is_v]
    assert len(vocab_words) > 0, f"Expected B2-C1 flags, got: {vocab_words}"
    print(f"[OK] tokenize_with_vocab_flags: vocab_words = {vocab_words}")
except Exception as e:
    errors.append(f"[FAIL] vocab_highlighter: {e}")

# --- Test 2: subtitle_window default settings ---
try:
    from subtitle_window import DEFAULT_SUBTITLE_WIN_SETTINGS
    lines = DEFAULT_SUBTITLE_WIN_SETTINGS["lines"]
    orig = next(l for l in lines if l["type"] == "original")
    trans = next(l for l in lines if l["type"] == "translation")

    assert orig["font_family"] == "Segoe UI", f"Wrong font: {orig['font_family']}"
    assert orig["font_size"] == 24, f"Wrong size: {orig['font_size']}"
    assert orig.get("vocab_color") == "#FFB86C", f"Wrong vocab_color: {orig.get('vocab_color')}"
    assert trans["font_size"] == 15, f"Wrong trans size: {trans['font_size']}"
    assert trans["color"] == "#7AA2F7", f"Wrong trans color: {trans['color']}"
    print("[OK] DEFAULT_SUBTITLE_WIN_SETTINGS: L2 typography hierarchy verified")
    print(f"     Line 1 (EN): {orig['font_family']} {orig['font_size']}px #FFFFFF + vocab #{orig.get('vocab_color','?')[1:]}")
    print(f"     Line 2 (RU): {trans['font_family']} {trans['font_size']}px {trans['color']}")
except Exception as e:
    errors.append(f"[FAIL] DEFAULT_SUBTITLE_WIN_SETTINGS: {e}")

# --- Test 3: subtitle_window imports vocab_highlighter ---
try:
    from subtitle_window import tokenize_with_vocab_flags as twvf
    result = twvf("test word")
    assert isinstance(result, list)
    print("[OK] subtitle_window re-exports tokenize_with_vocab_flags successfully")
except Exception as e:
    errors.append(f"[FAIL] subtitle_window vocab import: {e}")

# --- Test 4: main.py latency thresholds ---
try:
    main_path = os.path.join(os.path.dirname(__file__), '..', 'stage_1_audio', 'LiveTranslate', 'main.py')
    with open(main_path, encoding='utf-8') as f:
        src = f.read()
    assert 'self._interim_interval = 0.35' in src, "interim_interval not set to 0.35"
    assert 'if duration < 0.4:' in src, "duration threshold not set to 0.4"
    assert 'cooldown >= 0.35' in src, "cooldown threshold not set to 0.35"
    print("[OK] main.py: all three ASR latency thresholds correctly lowered")
    print("     interim_interval: 2.0s -> 0.35s")
    print("     duration filter:  1.5s -> 0.4s")
    print("     cooldown:         1.0s -> 0.35s")
except Exception as e:
    errors.append(f"[FAIL] main.py thresholds: {e}")

# --- Test 5: user_settings.json ---
try:
    import json
    settings_path = os.path.join(os.path.dirname(__file__), '..', 'stage_1_audio', 'LiveTranslate', 'user_settings.json')
    with open(settings_path, encoding='utf-8') as f:
        settings = json.load(f)
    assert settings.get("interim_interval") == 0.35, f"interim_interval: {settings.get('interim_interval')}"
    sub_lines = settings.get("subtitle_mode", {}).get("lines", [])
    orig_cfg = next((l for l in sub_lines if l.get("type") == "original"), None)
    trans_cfg = next((l for l in sub_lines if l.get("type") == "translation"), None)
    assert orig_cfg and orig_cfg.get("vocab_color") == "#FFB86C", f"vocab_color: {orig_cfg}"
    assert trans_cfg and trans_cfg.get("font_size") in (15, 16), f"trans font_size: {trans_cfg}"
    assert trans_cfg and trans_cfg.get("color") == "#7AA2F7", f"trans color: {trans_cfg}"
    assert trans_cfg and trans_cfg.get("opacity") in (200, 255), f"trans opacity: {trans_cfg}"
    print("[OK] user_settings.json: all L2 parameters persisted correctly")
except Exception as e:
    errors.append(f"[FAIL] user_settings.json: {e}")

print()
if errors:
    print("=== FAILURES ===")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print("=== ALL 5 CHECKS PASSED ===")
    sys.exit(0)
