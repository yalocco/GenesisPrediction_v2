import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# docker-compose で ./resources を /app/resources にマウントする想定
HISTORY_PATH = Path("/app/resources/history/seed_events_10.json")

TAG_EQUIV: Dict[str, List[str]] = {
    "debt_cycle": ["debt_overhang"],
    "debt_overhang": ["debt_cycle"],
}

TAG_WEIGHT: Dict[str, float] = {
    "bloc_polarization": 2.0,
    "financial_regime": 2.0,
    "arms_race": 1.5,
    "debt_cycle": 1.5,
    "debt_overhang": 1.5,
}


def _load_history_events() -> List[Dict[str, Any]]:
    with HISTORY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _expand_tags(tags: List[str]) -> List[str]:
    expanded = list(tags)
    for t in tags:
        expanded.extend(TAG_EQUIV.get(t, []))
    return expanded


def _score_event(current_tags: List[str], event_tags: List[str]) -> Tuple[float, List[str]]:
    cur = set(_expand_tags(current_tags))
    ev = set(_expand_tags(event_tags))
    matched = sorted(list(cur & ev))
    score = 0.0
    for t in matched:
        score += TAG_WEIGHT.get(t, 1.0)
    return score, matched


def derive_current_tags(anchors: List[str] | None = None, regime: str | None = None) -> List[str]:
    # v1: anchors/regime → tags は後で強化。今は fallback を使うため空を返す。
    _ = anchors, regime
    return []


def find_historical_analogs(current_tags: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
    events = _load_history_events()
    scored: List[Tuple[float, Dict[str, Any], List[str]]] = []

    for e in events:
        event_tags = e.get("analog_tags", [])
        s, matched = _score_event(current_tags, event_tags)
        if s > 0:
            scored.append((s, e, matched))

    scored.sort(key=lambda x: x[0], reverse=True)

    results: List[Dict[str, Any]] = []
    for s, e, matched in scored[:top_k]:
        results.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "score": round(s, 3),
            "matched_tags": matched,
            "summary": e.get("summary", ""),
            "notes": e.get("notes", ""),
        })
    return results
