import json
from pathlib import Path
from typing import Dict, List, Tuple, Any


HISTORY_PATH = Path("resources/history/seed_events_10.json")


# --- 設定: タグの同義語・近縁語マップ（最小）
# 例: 現在タグに debt_cycle が入っていても、イベント側が debt_overhang なら一致扱いにする
TAG_EQUIV: Dict[str, List[str]] = {
    "debt_cycle": ["debt_overhang"],
    "debt_overhang": ["debt_cycle"],
}

# --- 設定: 重要タグの重み（最小）
TAG_WEIGHT: Dict[str, float] = {
    "bloc_polarization": 2.0,
    "financial_regime": 2.0,
    "arms_race": 1.5,
    "debt_cycle": 1.5,
    "debt_overhang": 1.5,
    # ここは後から自由に増やしてOK
}


def load_history_events() -> List[Dict[str, Any]]:
    with HISTORY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def expand_tags(tags: List[str]) -> List[str]:
    """タグ集合を、近縁語も含めた集合に拡張する（重複は後で集合化する）"""
    expanded = list(tags)
    for t in tags:
        expanded.extend(TAG_EQUIV.get(t, []))
    return expanded


def score_event(current_tags: List[str], event_tags: List[str]) -> Tuple[float, List[str]]:
    """
    スコア: (一致したタグの重み合計)
    matched_tags: 実際に一致と見なしたタグ一覧（表示用）
    """
    cur_set = set(expand_tags(current_tags))
    ev_set = set(expand_tags(event_tags))

    matched = sorted(list(cur_set & ev_set))

    score = 0.0
    for t in matched:
        score += TAG_WEIGHT.get(t, 1.0)

    return score, matched


def find_historical_analogs(current_tags: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
    events = load_history_events()
    scored: List[Tuple[float, Dict[str, Any], List[str]]] = []

    for e in events:
        tags = e.get("analog_tags", [])
        s, matched = score_event(current_tags, tags)
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
            "summary": e.get("summary", "")
        })
    return results


if __name__ == "__main__":
    # --- テスト用：あなたが先ほど使った「今日の状況タグ」
    current_tags = [
        "bloc_polarization",
        "financial_regime",
        "arms_race",
        "debt_cycle"
    ]

    analogs = find_historical_analogs(current_tags, top_k=5)

    print("Historical Analog Top:")
    for a in analogs:
        print(f"- score={a['score']}: {a['title']} ({a['matched_tags']})")
