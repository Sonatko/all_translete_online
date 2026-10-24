import json

path = r"C:\Users\SONATO\.gemini\antigravity-ide\brain\391f2124-e7b0-40b8-a867-1bfb7c6fcf44\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if "17:41:" in line:
            obj = json.loads(line)
            for c in obj.get("tool_calls", []):
                print(c.get("name"))
                print(json.dumps(c.get("args"), indent=2, ensure_ascii=False))
