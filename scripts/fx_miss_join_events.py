import json
from pathlib import Path
import pandas as pd

# ============================
# Settings
# ============================
MISS_CSV = Path("data/fx/usd_jpy_miss_days.csv")
OUT_JSON = Path("data/fx/usd_jpy_miss_events.json")
OUT_MD = Path("data/fx/usd_jpy_miss_events.md")

WINDOW_DAYS = 1              # 0=当日, 1=前後1日も拾う（為替は1推奨）
MAX_EVENTS_PER_DAY = 12       # 1日あたりMDに出す最大件数（読みやすさ優先）

# FX用途のフィルタ
FX_MODE = "macro_only"        # "macro_only" or "all"
MACRO_PREFIX = "macro_"       # category が macro_ で始まるものだけ採用（macro_only時）

EVENTS_GLOB = [
    "data/**/analysis/events_*.jsonl",
    "data/**/analysis/events_*.json",   # 念のため（将来用）
    "data/**/events_*.jsonl",
]

FILTER_EVENTS_BY_MISS_RANGE = True      # True推奨（読み込み高速化）


# ============================
# Utilities
# ============================
def pick_event_date(e: dict):
    """イベント辞書から日付(date)を推定して返す。取れなければNone。"""
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
    """dict/list混在でも安全に文字列化"""
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


def compact_event(e: dict):
    """出力用に最低限のフィールドへ圧縮"""
    title = e.get("title") or e.get("headline") or e.get("name") or "(no title)"
    return {
        "title": as_str(title),
        "source": as_str(e.get("source")),
        "category": as_str(e.get("category")),
        "importance": as_str(e.get("importance")),
        "url": as_str(e.get("url")),
    }


def load_events_from_jsonl(path: Path):
    events = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                events.append(e)
    except Exception:
        return []
    return events


# ============================
# Load miss days
# ============================
if not MISS_CSV.exists():
    raise SystemExit(f"[ERR] miss csv not found: {MISS_CSV}")

miss_df = pd.read_csv(MISS_CSV)
if "date" not in miss_df.columns:
    raise SystemExit("[ERR] miss csv must have 'date' column")

miss_df["date"] = pd.to_datetime(miss_df["date"]).dt.date
miss_dates = sorted(set(miss_df["date"].tolist()))
if not miss_dates:
    raise SystemExit("[ERR] miss dates empty")

miss_min = min(miss_dates)
miss_max = max(miss_dates)

# windowを考慮した読み込み範囲（前後日）
range_min = (pd.to_datetime(miss_min) - pd.Timedelta(days=WINDOW_DAYS)).date()
range_max = (pd.to_datetime(miss_max) + pd.Timedelta(days=WINDOW_DAYS)).date()


# ============================
# Find event files
# ============================
event_files = []
for pat in EVENTS_GLOB:
    event_files.extend(list(Path(".").glob(pat)))

event_files = [p for p in event_files if p.is_file() and p.suffix.lower() in [".jsonl", ".json"]]
event_files = sorted(event_files, key=lambda p: p.stat().st_mtime, reverse=True)

if not event_files:
    raise SystemExit("[ERR] no events jsonl found (searched: " + ", ".join(EVENTS_GLOB) + ")")

used_files = [str(p).replace("\\", "/") for p in event_files]


# ============================
# Load events (ALL files)
# ============================
events = []
skipped_non_macro = 0

for p in event_files:
    # jsonl想定（.jsonでも1行1json形式なら同様に読める）
    for e in load_events_from_jsonl(p):
        d = pick_event_date(e)
        if not d:
            continue

        if FILTER_EVENTS_BY_MISS_RANGE and (d < range_min or d > range_max):
            continue

        # ---- FX filter: macro only (recommended)
        if FX_MODE == "macro_only":
            cat = as_str(e.get("category"))
            if not cat.startswith(MACRO_PREFIX):
                skipped_non_macro += 1
                continue

        e["_date"] = d
        events.append(e)

if not events:
    raise SystemExit(
        "[ERR] events loaded = 0. "
        "If you use FX_MODE='macro_only', ensure macro events exist and category starts with 'macro_'."
    )

# date -> events
by_date = {}
for e in events:
    by_date.setdefault(e["_date"], []).append(e)


# ============================
# Join
# ============================
rows = []

for d in miss_dates:
    # 対象日（当日＋前後）
    hit_days = [d]
    if WINDOW_DAYS >= 1:
        for i in range(1, WINDOW_DAYS + 1):
            hit_days.append((pd.to_datetime(d) - pd.Timedelta(days=i)).date())
            hit_days.append((pd.to_datetime(d) + pd.Timedelta(days=i)).date())

    # 集める
    hits = []
    for hd in hit_days:
        hits.extend(by_date.get(hd, []))

    # ---- dedupe (same event may appear multiple times across files / window)
    seen = set()
    uniq = []
    for x in hits:
        d0 = x.get("_date") or pick_event_date(x) or ""
        title0 = x.get("title") or x.get("headline") or x.get("name") or ""
        k = (
            str(d0),
            as_str(title0),
            as_str(x.get("source")),
            as_str(x.get("url")),
        )
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    hits = uniq

    # 表示用に最大件数を制限
    hits = hits[:MAX_EVENTS_PER_DAY]

    rows.append(
        {
            "miss_date": str(d),
            "events_count": len(hits),
            "events": [compact_event(x) for x in hits],
        }
    )


# ============================
# Save JSON
# ============================
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================
# Save Markdown
# ============================
md = []
md.append("# USDJPY Miss days × Events")
md.append("")
md.append(f"- miss csv: `{MISS_CSV}`")
md.append(f"- events files loaded: {len(used_files)}")
md.append(f"- latest events file: `{used_files[0]}`")
md.append(f"- window_days: {WINDOW_DAYS}")
md.append(f"- FX_MODE: {FX_MODE}")
if FX_MODE == "macro_only":
    md.append(f"- macro filter: category startswith `{MACRO_PREFIX}`")
md.append(f"- miss range: {miss_min} .. {miss_max}")
if FILTER_EVENTS_BY_MISS_RANGE:
    md.append(f"- events date filter: {range_min} .. {range_max}")
else:
    md.append("- events date filter: (disabled)")
md.append("")

for r in rows:
    md.append(f"## {r['miss_date']}  (events: {r['events_count']})")
    if r["events_count"] == 0:
        md.append("- (no events found)")
    else:
        for e in r["events"]:
            line = f"- {e['title']}"
            meta = " / ".join(x for x in [e["source"], e["category"], e["importance"]] if x)
            if meta:
                line += f"  ({meta})"
            md.append(line)
    md.append("")

OUT_MD.write_text("\n".join(md), encoding="utf-8")


# ============================
# Done
# ============================
print("[OK] joined miss days with events")
print(f" - {OUT_JSON}")
print(f" - {OUT_MD}")
print(f"[INFO] events files loaded: {len(used_files)}")
print(f"[INFO] miss range: {miss_min} .. {miss_max}")
if FILTER_EVENTS_BY_MISS_RANGE:
    print(f"[INFO] events date filter: {range_min} .. {range_max}")
else:
    print("[INFO] events date filter: disabled")
if FX_MODE == "macro_only":
    print(f"[INFO] skipped_non_macro: {skipped_non_macro}")
