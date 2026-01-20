import json
from pathlib import Path
import pandas as pd

# ============================
# Settings
# ============================
MISS_CSV = Path("data/fx/usd_jpy_miss_days.csv")

# さっき作ったラベル結果
IN_LABELED_JSON = Path("data/fx/usd_jpy_miss_events_labeled.json")

# world_politics 側の events（分析で出ている日次ファイル群）
WP_GLOB = "data/world_politics/analysis/events_*.jsonl"

# 出力
OUT_JSON = Path("data/fx/usd_jpy_miss_events_labeled3.json")
OUT_CSV = Path("data/fx/usd_jpy_miss_events_labeled3.csv")
OUT_MD = Path("data/fx/usd_jpy_miss_events_regime_summary.md")

WINDOW_DAYS = 1          # FXの前後日
REGIME_THRESHOLD = 6     # この件数以上なら「regime_break」扱い（まずは6）
MAX_EVENTS_PER_DAY = 12  # 参照用（読みやすさ）

# ============================
# Helpers
# ============================
def load_jsonl(path: Path):
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

def pick_date(e: dict):
    for k in ["date", "day", "event_date"]:
        if e.get(k):
            try:
                return pd.to_datetime(e[k]).date()
            except Exception:
                pass
    for k in ["ts", "timestamp", "published_at", "created_at", "time"]:
        if e.get(k):
            try:
                return pd.to_datetime(e[k], utc=True).date()
            except Exception:
                try:
                    return pd.to_datetime(e[k]).date()
                except Exception:
                    pass
    return None

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
        return ", ".join([as_str(x) for x in v if as_str(x)])
    return str(v)

def compact(e: dict):
    title = e.get("title") or e.get("headline") or e.get("name") or "(no title)"
    return {
        "title": as_str(title),
        "source": as_str(e.get("source")),
        "category": as_str(e.get("category")),
        "url": as_str(e.get("url")),
    }

# ============================
# Load miss dates
# ============================
if not MISS_CSV.exists():
    raise SystemExit(f"[ERR] miss csv not found: {MISS_CSV}")
miss_df = pd.read_csv(MISS_CSV)
miss_df["date"] = pd.to_datetime(miss_df["date"]).dt.date
miss_dates = sorted(set(miss_df["date"].tolist()))
miss_min = min(miss_dates)
miss_max = max(miss_dates)

range_min = (pd.to_datetime(miss_min) - pd.Timedelta(days=WINDOW_DAYS)).date()
range_max = (pd.to_datetime(miss_max) + pd.Timedelta(days=WINDOW_DAYS)).date()

# ============================
# Load labeled JSON (macro_hit/noise)
# ============================
if not IN_LABELED_JSON.exists():
    raise SystemExit(f"[ERR] labeled json not found: {IN_LABELED_JSON}")
labeled = json.loads(IN_LABELED_JSON.read_text(encoding="utf-8"))

# index by miss_date
by_day = {x["miss_date"]: x for x in labeled}

# ============================
# Load world_politics events and build index
# ============================
wp_files = sorted(list(Path(".").glob(WP_GLOB)))
if not wp_files:
    raise SystemExit(f"[ERR] no world_politics events found: {WP_GLOB}")

wp_events = []
for p in wp_files:
    for e in load_jsonl(p):
        d = pick_date(e)
        if not d:
            continue
        if d < range_min or d > range_max:
            continue
        e["_date"] = d
        wp_events.append(e)

wp_by_date = {}
for e in wp_events:
    wp_by_date.setdefault(e["_date"], []).append(e)

# ============================
# Apply regime flag + 3-class label
# ============================
out_rows = []
flat = []

for d in miss_dates:
    d_str = str(d)
    base = by_day.get(d_str, {"miss_date": d_str, "class": "noise", "events": [], "events_count": 0, "macro_count": 0})
    base = dict(base)

    # window hit days
    hit_days = [d]
    for i in range(1, WINDOW_DAYS + 1):
        hit_days.append((pd.to_datetime(d) - pd.Timedelta(days=i)).date())
        hit_days.append((pd.to_datetime(d) + pd.Timedelta(days=i)).date())

    wp_hits = []
    for hd in hit_days:
        wp_hits.extend(wp_by_date.get(hd, []))

    # dedupe
    seen = set()
    uniq = []
    for e in wp_hits:
        k = (str(e.get("_date")), as_str(e.get("title") or e.get("headline") or e.get("name")), as_str(e.get("source")), as_str(e.get("url")))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    wp_hits = uniq[:MAX_EVENTS_PER_DAY]

    wp_count = len(wp_hits)
    regime_break = wp_count >= REGIME_THRESHOLD

    base["wp_count"] = wp_count
    base["regime_break"] = bool(regime_break)
    base["wp_events"] = [compact(e) for e in wp_hits]

    # 3-class
    if base.get("class") == "macro_hit":
        cls3 = "macro_hit"
    elif regime_break:
        cls3 = "regime_break"
    else:
        cls3 = "noise"
    base["class3"] = cls3

    out_rows.append(base)

    flat.append(
        {
            "miss_date": d_str,
            "class": base.get("class"),
            "class3": cls3,
            "macro_count": int(base.get("macro_count") or 0),
            "events_count": int(base.get("events_count") or 0),
            "wp_count": wp_count,
            "regime_break": int(regime_break),
        }
    )

# ============================
# Save
# ============================
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")

df = pd.DataFrame(flat)
df.to_csv(OUT_CSV, index=False, encoding="utf-8")

# summary
total = len(df)
n_macro = int((df["class3"] == "macro_hit").sum())
n_regime = int((df["class3"] == "regime_break").sum())
n_noise = int((df["class3"] == "noise").sum())

md = []
md.append("# USDJPY miss 3分類サマリ（macro_hit / regime_break / noise）")
md.append("")
md.append(f"- threshold: wp_count >= {REGIME_THRESHOLD}")
md.append(f"- window_days: {WINDOW_DAYS}")
md.append("")
md.append("## counts")
md.append(f"- total: **{total}**")
md.append(f"- macro_hit: **{n_macro}**")
md.append(f"- regime_break: **{n_regime}**")
md.append(f"- noise: **{n_noise}**")
md.append("")
md.append("## regime_break top 20 (by wp_count)")
top = df.sort_values("wp_count", ascending=False).head(20)
for _, r in top.iterrows():
    if int(r["wp_count"]) <= 0:
        break
    md.append(f"- {r['miss_date']}: wp_count={int(r['wp_count'])}, class3={r['class3']}")
OUT_MD.write_text("\n".join(md), encoding="utf-8")

print("[OK] labeled miss days with regime_break + 3-class")
print(f" - {OUT_JSON}")
print(f" - {OUT_CSV}")
print(f" - {OUT_MD}")
print(f"[INFO] total={total} macro_hit={n_macro} regime_break={n_regime} noise={n_noise} threshold={REGIME_THRESHOLD}")
