import urllib.request
import json
import time
import sys

prompt = """You are an English-to-Russian subtitle translator and language tutor.
Translate the input sentence into natural, fluent Russian and explain key vocabulary.

RULES:
1. Line 1: Output ONLY the complete, fluent Russian translation. Never leave untranslated English words.
2. Line 2+ (Optional): Educational vocabulary hints ONLY if the sentence contains phrasal verbs, idioms, slang, or B2+ words.
3. STRICTLY FORBIDDEN to create hints for basic words (e.g. 'you', 'see', 'two seconds', 'cool', 'maybe', 'speak', 'good').
4. NEVER repeat the translation of the whole sentence on the 💡 line.
5. If the sentence is simple (A1/A2), output ONLY Line 1 with ZERO 💡 lines.

FORMAT:
<Russian translation>
💡 <base infinitive / word> — <meaning in this context>

EXAMPLES:
Input: We need to figure this out before sunset.
Нам нужно разобраться с этим до заката.
💡 figure out — понять, разобраться

Input: Over here is where we rig every American election. Eh.
Вот здесь мы и подтасовываем каждые американские выборы. Да уж.
💡 rig — подтасовывать, фальсифицировать

Input: He totally blew me off yesterday.
Он вчера меня просто продинамил.
💡 blow off — забить на кого-то, продинамить

Input: Two seconds.
Две секунды."""

test_sentences = [
    "I can speak difficult English, I don't know.",
    "Two seconds.",
    "He totally blew me off yesterday.",
    "She decided to turn down the offer because it was shady."
]

for s in test_sentences:
    data = {
        "model": "llama-3.2-3b-instruct-q4_k_m",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": s}
        ],
        "temperature": 0.1,
        "max_tokens": 96
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8080/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        data=json.dumps(data).encode("utf-8")
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            dt = time.time() - t0
            content = res["choices"][0]["message"]["content"]
            sys.stdout.buffer.write(f"\n--- Input: {s} ({dt*1000:.0f} ms) ---\n".encode("utf-8"))
            sys.stdout.buffer.write((content + "\n").encode("utf-8"))
    except Exception as e:
        sys.stdout.buffer.write(f"Error: {e}\n".encode("utf-8"))
