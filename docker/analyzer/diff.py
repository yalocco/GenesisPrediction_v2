# docker/analyzer/diff.py
import json
import os
from collections import Counter
from datetime import datetime, timedelta

def read_jsonl(path: str):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows

def _safe_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def extract_axes(event: dict):
    cat = event.get("category") or event.get("categories") or event.get("type")
    categories = [c for c in _safe_list(cat) if isinstance(c, str)]

    kw = event.get("keywords") or event.get("keyphrases") or event.get("tags")
    keywords = [k for k in _safe_list(kw) if isinstance(k, str)]

    ent = event.get("entities") or event.get("countries") or event.get("locations")
    entities = []
    for x in _safe_list(ent):
        if isinstance(x, str):
            entities.append(x)
        elif isinstance(x, dict):
            name = x.get("name") or x.get("text") or x.get("value")
            if isinstance(name, str):
                entities.append(name)

    event_id = event.get("id") or ""
    title = event.get("title") or event.get("summary") or ""
    url = event.get("url") or event.get("link") or ""
    published_at = event.get("published_at") or event.get("date") or None
    source = event.get("source") or event.get("provider") or ""

    if not event_id:
        event_id = (url or title)[:200]

    return categories, keywords, entities, {
        "id": event_id,
        "title": title,
        "url": url,
        "category": categories,
        "entities": entities,
        "keywords": keywords,
        "source": source,
        "published_at": published_at
    }

def build_dimension(items_today, items_base, total_today, total_base, top_n=30):
    c_today = Counter(items_today)
    c_base = Counter(items_base)
    keys = set(c_today.keys()) | set(c_base.keys())

    changed, added, removed = [], [], []

    rank_today = {k:i+1 for i,(k,_) in enumerate(c_today.most_common())}
    rank_base  = {k:i+1 for i,(k,_) in enumerate(c_base.most_common())}

    for k in keys:
        t = c_today.get(k, 0)
        b = c_base.get(k, 0)
        d = t - b
        if t > 0 and b == 0:
            added.append({"key": k, "today": t, "baseline": 0, "delta": d})
        elif t == 0 and b > 0:
            removed.append({"key": k, "today": 0, "baseline": b, "delta": d})
        elif d != 0:
            changed.append({
                "key": k,
                "today": t,
                "baseline": b,
                "delta": d,
                "delta_pct": None if b == 0 else (d / b),
                "share_today": (t / total_today) if total_today else 0.0,
                "share_baseline": (b / total_base) if total_base else 0.0,
                "rank_today": rank_today.get(k),
                "rank_baseline": rank_base.get(k),
                "rank_delta": (rank_today.get(k, 10**9) - rank_base.get(k, 10**9))
            })

    changed.sort(key=lambda x: x["delta"], reverse=True)
    added.sort(key=lambda x: x["today"], reverse=True)
    removed.sort(key=lambda x: x["baseline"], reverse=True)

    return {
        "added": added[:top_n],
        "removed": removed[:top_n],
        "changed": changed[:top_n]
    }

def build_interpretation(out: dict) -> dict:
    date = out["meta"]["date"]
    base = out["meta"]["baseline_date"]
    delta_events = out["summary"]["delta_events"]

    dims = out["diff"]["dimensions"]
    cat_changed = dims["categories"]["changed"]
    kw_changed  = dims["keywords"]["changed"]
    ent_changed = dims["entities"]["changed"]

    added_events = out.get("event_level", {}).get("added", []) or []
    removed_events = out.get("event_level", {}).get("removed", []) or []

    def top_change(lst):
        return lst[0] if lst else None

    top_cat = top_change(cat_changed)
    top_kw  = top_change(kw_changed)
    top_ent = top_change(ent_changed)

    bullets = [
        f"対象: {date} vs {base}",
        f"件数差: {delta_events:+d}（today={out['input']['today']['events_count']} / baseline={out['input']['baseline']['events_count']}）",
    ]

    def fmt(label, item):
        if not item:
            return f"{label}: (変化なし)"
        return f"{label}: {item['key']} {item['delta']:+d}（today={item['today']} / baseline={item['baseline']}）"

    bullets += [
        fmt("カテゴリ差分（最大）", top_cat),
        fmt("キーワード差分（最大）", top_kw),
        fmt("エンティティ差分（最大）", top_ent),
    ]

    if added_events:
        urls = [e.get("url") or e.get("id") for e in added_events[:3]]
        bullets.append("新規URLサンプル: " + " / ".join([u for u in urls if u]))
    if removed_events:
        urls = [e.get("url") or e.get("id") for e in removed_events[:3]]
        bullets.append("消滅URLサンプル: " + " / ".join([u for u in urls if u]))

    if delta_events == 0 and not (top_cat or top_kw or top_ent):
        summary = (
            "全体の件数・主要ディメンションの差分は小さい。"
            "一方でURL単位では入れ替わりがあり、注目テーマが差し替わっている可能性がある。"
        )
    else:
        parts = []
        if delta_events != 0:
            parts.append(f"件数が{delta_events:+d}変化。")
        if top_cat:
            parts.append(f"カテゴリでは「{top_cat['key']}」が{top_cat['delta']:+d}。")
        if top_kw:
            parts.append(f"キーワードでは「{top_kw['key']}」が{top_kw['delta']:+d}。")
        if top_ent:
            parts.append(f"エンティティでは「{top_ent['key']}」が{top_ent['delta']:+d}。")
        summary = " ".join(parts) if parts else "小さな変化だが、差分が観測された。"

    hypotheses = []
    if added_events or removed_events:
        conf = 0.25 + (0.1 if len(added_events) >= 10 else 0) + (0.1 if len(removed_events) >= 10 else 0)
        hypotheses.append({
            "text": "ニュース総量が同程度でも、記事の入れ替わりがあるため、注目テーマが差し替わっている可能性。",
            "confidence": round(min(conf, 0.6), 2),
            "evidence": ["event_level.added", "event_level.removed"]
        })

    return {"summary": summary, "bullets": bullets, "hypotheses": hypotheses}

def build_signals(out: dict) -> dict:
    today_count = int(out.get("input", {}).get("today", {}).get("events_count", 0) or 0)
    base_count = int(out.get("input", {}).get("baseline", {}).get("events_count", 0) or 0)
    delta = today_count - base_count

    ev = out.get("event_level", {}) or {}
    added_n = len(ev.get("added", []) or [])
    removed_n = len(ev.get("removed", []) or [])
    churn = (added_n + removed_n) / max(today_count, 1)

    if delta >= 3:
        trend = "increasing"
    elif delta <= -3:
        trend = "decreasing"
    else:
        trend = "flat"

    if churn >= 0.30:
        volatility = "high"
    elif churn >= 0.10:
        volatility = "medium"
    else:
        volatility = "low"

    notes = []
    if trend == "flat" and churn >= 0.20:
        notes.append("Flat volume with high churn suggests topic rotation")

    return {
        "event_count_trend": trend,
        "churn_rate": round(churn, 3),
        "volatility": volatility,
        "notes": notes
    }

def generate_diff(analysis_dir: str, date_str: str, dataset: str = "world_politics", top_n=30, event_sample_n=50):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    base = d - timedelta(days=1)

    today_file = os.path.join(analysis_dir, f"events_{d.isoformat()}.jsonl")
    base_file  = os.path.join(analysis_dir, f"events_{base.isoformat()}.jsonl")

    today_events = read_jsonl(today_file)
    base_events  = read_jsonl(base_file)

    total_today = len(today_events)
    total_base  = len(base_events)

    cats_today, kws_today, ents_today = [], [], []
    cats_base,  kws_base,  ents_base  = [], [], []
    today_sigs, base_sigs = {}, {}

    for e in today_events:
        c,k,en,ev = extract_axes(e)
        cats_today += c; kws_today += k; ents_today += en
        today_sigs[ev["id"]] = ev

    for e in base_events:
        c,k,en,ev = extract_axes(e)
        cats_base += c; kws_base += k; ents_base += en
        base_sigs[ev["id"]] = ev

    added_ids = [i for i in today_sigs if i not in base_sigs]
    removed_ids = [i for i in base_sigs if i not in today_sigs]

    out = {
        "schema": {"name": "genesis.diff", "version": "1.1.0"},
        "meta": {
            "dataset": dataset,
            "date": d.isoformat(),
            "baseline_date": base.isoformat(),
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "generator": {"repo": "GenesisPrediction_v2", "component": "analyzer"}
        },
        "input": {
            "today": {"events_file": os.path.basename(today_file), "events_count": total_today},
            "baseline": {"events_file": os.path.basename(base_file), "events_count": total_base}
        },
        "summary": {"delta_events": total_today - total_base, "topline": []},
        "diff": {
            "dimensions": {
                "categories": build_dimension(cats_today, cats_base, total_today, total_base, top_n),
                "keywords": build_dimension(kws_today, kws_base, total_today, total_base, top_n),
                "entities": build_dimension(ents_today, ents_base, total_today, total_base, top_n)
            }
        },
        "event_level": {
            "added": [today_sigs[i] for i in added_ids[:event_sample_n]],
            "removed": [{"id": i, "title": base_sigs[i].get("title",""), "url": base_sigs[i].get("url","")} for i in removed_ids[:event_sample_n]]
        },
        "quality": {"notes": [], "warnings": []},
        "extensions": {}
    }

    dims = out["diff"]["dimensions"]
    for label, key in [("Categories","categories"),("Keywords","keywords"),("Entities","entities")]:
        ch = dims[key]["changed"]
        if ch:
            x = ch[0]
            out["summary"]["topline"].append(f"{label}: {x['key']} {x['delta']:+d}")

    if not os.path.exists(base_file):
        out["quality"]["notes"].append("baseline file missing: treated as empty baseline")

    out["extensions"]["interpretation"] = build_interpretation(out)
    out["extensions"]["signals"] = build_signals(out)

    out_path = os.path.join(analysis_dir, f"diff_{d.isoformat()}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return out_path
