import json

path = r"C:\Users\SONATO\.gemini\antigravity-ide\brain\391f2124-e7b0-40b8-a867-1bfb7c6fcf44\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f, open("scratch/history.txt", "w", encoding="utf-8") as out:
    for line in f:
        if '"type":"USER_INPUT"' in line:
            obj = json.loads(line)
            c = obj.get("content", "")
            out.write("=== USER ===\n" + c + "\n\n")
