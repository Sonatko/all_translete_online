import json

path = r"C:\Users\SONATO\Dev\active\all_translete_online\.system_generated\logs\transcript.jsonl"
# check real transcript path
path = r"C:\Users\SONATO\.gemini\antigravity-ide\brain\391f2124-e7b0-40b8-a867-1bfb7c6fcf44\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f, open("scratch/hour_ago.txt", "w", encoding="utf-8") as out:
    for line in f:
        obj = json.loads(line)
        created = obj.get("created_at", "")
        # Look for entries between 16:00 and 18:00 UTC (which is 21:00 - 23:00 local time)
        if "2026-10-24T16:" in created or "2026-10-24T17:" in created:
            t = obj.get("type", "")
            if t == "USER_INPUT":
                out.write(f"\n=== USER [{created}] ===\n" + obj.get("content", "") + "\n")
            elif t == "PLANNER_RESPONSE":
                calls = obj.get("tool_calls", [])
                for c in calls:
                    name = c.get("name", "")
                    if name in ["replace_file_content", "multi_replace_file_content", "write_to_file"]:
                        args = c.get("args", {})
                        target = args.get("TargetFile", "")
                        desc = args.get("Description", "")
                        out.write(f"EDIT [{created}]: {target} -> {desc}\n")
