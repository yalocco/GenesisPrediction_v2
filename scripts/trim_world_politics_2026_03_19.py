import json
from pathlib import Path

p = Path(r"data/world_politics/2026-03-19.json")
bak = Path(r"data/world_politics/2026-03-19.json.cut_fix.bak")

raw = p.read_text(encoding="utf-8-sig")

if not bak.exists():
    bak.write_text(raw, encoding="utf-8")

decoder = json.JSONDecoder()
obj, end = decoder.raw_decode(raw)

fixed = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
p.write_text(fixed, encoding="utf-8")

print(f"trimmed: {p}")
print(f"json_end_offset={end}")
print(f"kept_chars={len(fixed)}")
print(f"removed_chars={len(raw) - end}")
if isinstance(obj, dict):
    print(f"articles={len(obj.get('articles', []))}")