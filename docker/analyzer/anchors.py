from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "at", "by",
    "today", "yesterday", "tomorrow", "week", "month", "year", "report", "reports",
}

@dataclass(frozen=True)
class Anchor:
    text: str
    kind: str   # "dimension" | "event" | "lexical"
    score: float

def _norm(s: str) -> str:
    return " ".join(str(s).strip().split())

def _tokenize_light(s: str) -> List[str]:
    import re
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-\s]", " ", s)
    toks = [
        t for t in s.split()
        if len(t) >= 3
        and t not in STOP
        and not t.isdigit()
        and not re.fullmatch(r"\d{4}", t)  # year-like token
        and t not in {"world", "politics"}
    ]
    return toks

def _take_top(items: Iterable[Anchor], k: int) -> List[Anchor]:
    xs = sorted(items, key=lambda a: a.score, reverse=True)
    out: List[Anchor] = []
    seen = set()
    for a in xs:
        key = a.text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
        if len(out) >= k:
            break
    return out

def extract_anchors(diff_doc: Dict[str, Any], daily_doc: Dict[str, Any], max_anchors: int = 12) -> List[Anchor]:
    found: List[Anchor] = []

    # 1) dimensions（diff.dimensions が list[dict] 想定）
    dims = diff_doc.get("dimensions") or (diff_doc.get("diff") or {}).get("dimensions") or []
    if isinstance(dims, list):
        for dim in dims:
            if not isinstance(dim, dict):
                continue
            name = dim.get("name") or dim.get("key") or dim.get("dimension")
            if isinstance(name, str) and name.strip():
                delta = dim.get("delta") or dim.get("change") or 0.0
                try:
                    d = float(delta)
                except Exception:
                    d = 0.0
                score = 3.0 + min(abs(d), 5.0)
                found.append(Anchor(text=_norm(name), kind="dimension", score=score))

    # 2) event_level（added/removed の entity/title/country/topic など）
    ev = diff_doc.get("event_level") or {}
    # ev が {"added":[...], "removed":[...]} 形式を想定
    if isinstance(ev, dict):
        for bucket, base in (("added", 6.0), ("removed", 4.5)):
            items = ev.get(bucket) or []
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                # よくあるキー候補（無いならスキップ）
                for k in ("entity", "actor", "country", "topic", "title", "headline", "location"):
                    v = it.get(k)
                    if isinstance(v, str) and v.strip():
                        found.append(Anchor(text=_norm(v), kind="event", score=base))
                    elif isinstance(v, list):
                        for s in v:
                            if isinstance(s, str) and s.strip():
                                found.append(Anchor(text=_norm(s), kind="event", score=base - 0.5))

    # 3) daily_summaryテキストから lexical（headline/bullets/one_liner など）
    texts: List[str] = []
    for key in ("headline", "one_liner", "delta_explanation", "summary"):
        v = daily_doc.get(key)
        if isinstance(v, str) and v.strip():
            texts.append(v)
    bullets = daily_doc.get("bullets")
    if isinstance(bullets, list):
        texts.extend([b for b in bullets if isinstance(b, str)])

    bag: Dict[str, int] = {}
    for t in texts:
        for tok in _tokenize_light(t):
            bag[tok] = bag.get(tok, 0) + 1
    for tok, c in bag.items():
        found.append(Anchor(text=tok, kind="lexical", score=1.0 + c * 0.25))

    return _take_top(found, max_anchors)

def anchors_to_strings(anchors: List[Anchor], max_n: int = 10) -> List[str]:
    out = []
    for a in anchors[:max_n]:
        out.append(a.text)
    return out
