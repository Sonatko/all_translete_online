import sys
import os
sys.path.insert(0, os.path.abspath("bin/LiveTranslate"))
import time
from translator import Translator

t = Translator(
    api_base="http://127.0.0.1:8080/v1",
    api_key="not-needed",
    model="saiga_llama3_8b_q4_k",
    target_language="ru",
    max_tokens=48,
    temperature=0.3,
    streaming=True,
)

print("Starting translate_iter test...")
start = time.perf_counter()
chunks = []
for partial in t.translate_iter("You will. Yes indeed.", "en"):
    now = time.perf_counter() - start
    chunks.append((now, partial))
    print(f"[{now*1000:.1f}ms] chunk: '{partial}'")

print("Total chunks:", len(chunks))
