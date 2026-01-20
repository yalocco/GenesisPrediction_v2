import json
from pathlib import Path
import pandas as pd

# ============================
# Settings
# ============================
IN_JSON = Path("data/fx/usd_jpy_miss_events.json")
OUT_JSON = Path("data/fx/usd_jpy_miss_events_labeled.json")
OUT_CSV = Path("data/fx/usd_jpy_miss_events_labeled.csv")
OUT_MD = Path("data/fx/usd_jpy_miss_events_summary.md")

MACRO_PREFIX = "macro_"   # fx_miss_join_events.py の設定と合わせる

# ============================
# Helpers
# ============================
def as_str(v):
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    if isinstance(v, dict):
        for k in ["name", "label", "id", "domain"]:
            if v.get(k):
                return str(v[k])
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        parts = []
        for x in v:
            sx = as_str(x)
            if sx:
                parts.append(sx)
        return ", ".join(parts)
    return str(v)

def is_macro_event(e: dict) -> bool:
    cat = as_str(e.get("category"))
    return cat.startswith(MACRO_PREFIX)

def event_key(e: dict) -> str:
    # 集計用の軽いキー
    title = as_str(e.get("title"))
    src = as_str(e.get("source"))
    cat = as_str(e.get("category"))
    imp = as_str(e.get("importance"))
    return f"{title} | {src} | {cat} | {imp}"

# ============================
# Load
# ============================
if not IN_JSON.exists():
    raise SystemExit(f"[ERR] input json not found: {IN_JSON}")

rows = json.loads(IN_JSON.read_text(encoding="utf-8"))
if not isinstance(rows, list):
    raise SystemExit("[ERR] invalid input json format (expected list)")

# ============================
# Label + Flatten
# ============================
flat = []
labeled = []

for r in rows:
    miss_date = r.get("miss_date")
    events = r.get("events") or []
    events_count = int(r.get("events_count") or len(events))

    # macro_only運用でも、念のためmacro判定は残す
    macro_events = [e for e in events if is_macro_event(e)]
    macro_count = len(macro_events)

    # ---- Classify
    # macro_hit: macroイベントが1件以上
    # noise: それ以外（events=0が大半）
    cls = "macro_hit" if macro_count > 0 else "noise"

    # 代表イベント（最初のmacro、なければ空）
    rep = macro_events[0] if macro_events else None
    rep_title = as_str(rep.get("title")) if rep else ""
    rep_cat = as_str(rep.get("category")) if rep else ""
    rep_src = as_str(rep.get("source")) if rep else ""
    rep_imp = as_str(rep.get("importance")) if rep else ""

    r2 = dict(r)
    r2["class"] = cls
    r2["macro_count"] = macro_count
    r2["rep_title"] = rep_title
    r2["rep_category"] = rep_cat
    r2["rep_source"] = rep_src
    r2["rep_importance"] = rep_imp
    labeled.append(r2)

    flat.append(
        {
            "miss_date": miss_date,
            "class": cls,
            "events_count": events_count,
            "macro_count": macro_count,
            "rep_title": rep_title,
            "rep_category": rep_cat,
            "rep_source": rep_src,
            "rep_importance": rep_imp,
        }
    )

# ============================
# Save labeled JSON/CSV
# ============================
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(labeled, ensure_ascii=False, indent=2), encoding="utf-8")

df = pd.DataFrame(flat)
df.to_csv(OUT_CSV, index=False, encoding="utf-8")

# ============================
# Build summary
# ============================
total = len(df)
macro_hit = int((df["class"] == "macro_hit").sum())
noise = int((df["class"] == "noise").sum())

macro_hit_rate = (macro_hit / total) if total else 0.0

# カテゴリ別（macro_hit日の代表カテゴリ）
cat_counts = (
    df[df["class"] == "macro_hit"]
    .groupby("rep_category")
    .size()
    .sort_values(ascending=False)
)

# 代表イベント別（同じイベントが何回出るか）
event_counts = (
    df[df["class"] == "macro_hit"]
    .assign(rep_key=lambda x: x["rep_title"] + " | " + x["rep_source"])
    .groupby("rep_key")
    .size()
    .sort_values(ascending=False)
    .head(20)
)

md = []
md.append("# USDJPY miss 分類サマリ（macro_hit / noise）")
md.append("")
md.append(f"- input: `{IN_JSON}`")
md.append(f"- labeled json: `{OUT_JSON}`")
md.append(f"- labeled csv: `{OUT_CSV}`")
md.append("")
md.append("## 集計")
md.append(f"- total miss days: **{total}**")
md.append(f"- macro_hit: **{macro_hit}**  ({macro_hit_rate:.2%})")
md.append(f"- noise: **{noise}**")
md.append("")
md.append("## macro_hit の代表カテゴリ（rep_category）")
if len(cat_counts) == 0:
    md.append("- (none)")
else:
    for cat, n in cat_counts.items():
        cat2 = cat if cat else "(blank)"
        md.append(f"- {cat2}: {int(n)}")
md.append("")
md.append("## macro_hit の代表イベント上位（rep_title | rep_source）")
if len(event_counts) == 0:
    md.append("- (none)")
else:
    for k, n in event_counts.items():
        md.append(f"- {k}: {int(n)}")
md.append("")
md.append("## macro_hit の日付一覧（先頭30）")
hit_days = df[df["class"] == "macro_hit"]["miss_date"].tolist()[:30]
if not hit_days:
    md.append("- (none)")
else:
    md.append("- " + ", ".join(hit_days))

OUT_MD.write_text("\n".join(md), encoding="utf-8")

# ============================
# Done
# ============================
print("[OK] labeled miss days (macro_hit/noise)")
print(f" - {OUT_JSON}")
print(f" - {OUT_CSV}")
print(f" - {OUT_MD}")
print(f"[INFO] total={total} macro_hit={macro_hit} noise={noise} macro_hit_rate={macro_hit_rate:.2%}")
