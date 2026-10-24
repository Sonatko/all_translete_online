import json

path = r"C:\Users\SONATO\.gemini\antigravity-ide\brain\391f2124-e7b0-40b8-a867-1bfb7c6fcf44\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f, open("scratch/plan_history.txt", "w", encoding="utf-8") as out:
    for line in f:
        if any(w in line for w in ["_on_update_streaming", "stream", "кусочк", "по кусочкам", "моргает"]):
            obj = json.loads(line)
            t = obj.get("type", "")
            if t in ["USER_INPUT", "PLANNER_RESPONSE"]:
                c = obj.get("content", "")
                if c:
                    out.write(f"=== {t} ===\n{c[:500]}\n\n")
