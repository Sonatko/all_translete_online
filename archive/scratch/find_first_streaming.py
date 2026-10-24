import json

path = r"C:\Users\SONATO\.gemini\antigravity-ide\brain\391f2124-e7b0-40b8-a867-1bfb7c6fcf44\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if 'def _on_update_streaming' in line:
            obj = json.loads(line)
            print("=== FOUND ===")
            print(obj.get("content", "")[:1000])
            for call in obj.get("tool_calls", []):
                print("TOOL ARGS:", call.get("args", {}))
