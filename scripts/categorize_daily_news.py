# scripts/categorize_daily_news.py
# Categorize daily news JSON into coarse domains:
# - security / economy / ai_it / tech / climate / general
#
# Key behavior (important for ops):
# - If a requested dated file is missing, automatically falls back to the most recent
#   daily_news_*.json in data/world_politics/analysis/ (excluding already categorized files).
# - Writes:
#     daily_news_categorized_<DATE>.json
#     daily_news_categorized_latest.json   (when --latest)
#
# Usage:
#   .\.venv\Scripts\python.exe scripts\categorize_daily_news.py --date 2026-02-17 --latest
#   .\.venv\Scripts\python.exe scripts\categorize_daily_news.py --input data/world_politics/analysis/daily_news_2026-02-16.json --latest
#   .\.venv\Scripts\python.exe scripts\categorize_daily_news.py --latest   (auto-pick latest daily_news_*.json)
#
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


@dataclass(frozen=True)
class CategoryRule:
    name: str
    patterns: List[Tuple[re.Pattern, int]]


def build_rules() -> List[CategoryRule]:
    # 最初は粗くてOK。運用しながら育てる前提。
    def rx(words: List[str], weight: int = 2) -> List[Tuple[re.Pattern, int]]:
        return [(re.compile(w, re.IGNORECASE), weight) for w in words]

    security = CategoryRule(
        "security",
        patterns=rx([
            r"\bwar\b", r"\bconflict\b", r"\bceasefire\b", r"\btruce\b",
            r"\bmissile\b", r"\bnuclear\b", r"\bdeterrence\b", r"\balliance\b",
            r"\bnato\b", r"\baukus\b", r"\bquad\b",
            r"sanction", r"military", r"airstrike", r"drone",
            r"国防", r"軍事", r"同盟", r"戦争", r"紛争", r"停戦", r"侵攻", r"攻撃",
            r"ミサイル", r"核", r"抑止", r"防衛", r"自衛隊", r"制裁",
        ], weight=3),
    )

    economy = CategoryRule(
        "economy",
        patterns=rx([
            r"\binflation\b", r"\bgdp\b", r"\brecession\b", r"\brate hike\b", r"\brate cut\b",
            r"\bcentral bank\b", r"\bfed\b", r"\becb\b", r"\bboj\b",
            r"\byield\b", r"\bbond\b", r"\bstock\b", r"\bequity\b", r"\bfx\b",
            r"\busd\b", r"\bjpy\b", r"\beur\b", r"\bthb\b",
            r"interest rate", r"policy rate", r"tariff", r"trade deficit",
            r"金利", r"利上げ", r"利下げ", r"インフレ", r"景気後退", r"景気", r"GDP",
            r"中央銀行", r"日銀", r"FRB", r"ECB",
            r"株価", r"市場", r"債券", r"利回り", r"為替", r"政策", r"関税",
        ], weight=3),
    )

    ai_it = CategoryRule(
        "ai_it",
        patterns=rx([
            r"\bai\b", r"\bartificial intelligence\b", r"\bllm\b", r"\bgpt\b",
            r"\bmachine learning\b", r"\bdeep learning\b",
            r"\bcyber\b", r"\bransomware\b", r"\bmalware\b", r"\bzero day\b",
            r"\btelecom\b", r"\b5g\b", r"\b6g\b", r"\bsatellite internet\b",
            r"\bsemiconductor\b", r"\bchip\b", r"\bgpu\b",
            r"生成AI", r"大規模言語モデル", r"LLM", r"機械学習",
            r"サイバー", r"ランサムウェア", r"マルウェア", r"脆弱性",
            r"通信", r"5G", r"6G", r"衛星通信",
            r"半導体", r"チップ", r"GPU",
        ], weight=3),
    )

    tech = CategoryRule(
        "tech",
        patterns=rx([
            r"\bquantum\b", r"\bfusion\b", r"\bnew material\b", r"\bmaterials\b",
            r"\brobot\b", r"\bautonomous\b", r"\bhypersonic\b",
            r"\bspace\b", r"\blaunch\b", r"\bsatellite\b",
            r"quantum computing", r"battery", r"biotech", r"gene",
            r"量子", r"核融合", r"新素材", r"材料", r"ロボット", r"自律", r"極超音速",
            r"宇宙", r"打ち上げ", r"衛星", r"バッテリー", r"バイオ", r"遺伝子",
        ], weight=2),
    )

    climate = CategoryRule(
        "climate",
        patterns=rx([
            r"\bearthquake\b", r"\btsunami\b", r"\bhurricane\b", r"\btyphoon\b",
            r"\bflood\b", r"\bwildfire\b", r"\bheatwave\b", r"\bdrought\b",
            r"\bclimate\b", r"\bemission\b", r"\bcarbon\b",
            r"\bvolcano\b", r"\bdisaster\b",
            r"地震", r"津波", r"台風", r"洪水", r"豪雨", r"山火事", r"熱波", r"干ばつ",
            r"気候", r"温暖化", r"排出", r"炭素", r"火山", r"災害",
        ], weight=3),
    )

    # 優先度：security / economy / ai_it / climate / tech
    return [security, economy, ai_it, climate, tech]


def score_categories(text: str, rules: List[CategoryRule]) -> Dict[str, int]:
    scores: Dict[str, int] = {r.name: 0 for r in rules}
    for rule in rules:
        for pat, w in rule.patterns:
            if pat.search(text):
                scores[rule.name] += w
    return scores


def pick_category(text: str, rules: List[CategoryRule]) -> Tuple[str, List[str], Dict[str, int]]:
    scores = score_categories(text, rules)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    best_name, best_score = ranked[0]
    if best_score <= 0:
        return "general", ["general"], scores

    # 同点上位も保持（将来複数タグにしたい時の保険）
    top = [name for name, sc in ranked if sc == best_score and sc > 0]
    primary = best_name
    categories = [primary] if primary in top else [primary]
    return primary, categories, scores


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def infer_date_from_filename(path: Path) -> str | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return m.group(1) if m else None


def normalize_news_items(obj: Any) -> List[Dict[str, Any]]:
    # daily_news JSON の形が多少違っても吸収
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("items", "articles", "news", "data"):
            v = obj.get(key)
            if isinstance(v, list):
                return v
        return [obj]
    raise ValueError("Unsupported JSON structure for daily_news")


def apply_categories_to_items(items: List[Dict[str, Any]], rules: List[CategoryRule]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in items:
        title = str(it.get("title", "") or "")
        desc = str(it.get("description", "") or it.get("summary", "") or "")
        source = str(it.get("source", "") or it.get("publisher", "") or "")
        url = str(it.get("url", "") or it.get("link", "") or "")

        blob = _norm(" | ".join([title, desc, source, url]))
        cat, cats, scores = pick_category(blob, rules)

        it2 = dict(it)
        it2["category"] = cat
        it2["categories"] = cats
        it2["_category_scores"] = scores  # デバッグ用（GUIでは無視してOK）
        out.append(it2)
    return out


def find_latest_daily_news_file() -> Path | None:
    if not ANALYSIS_DIR.exists():
        return None

    # daily_news_YYYY-MM-DD.json を対象（categorized系は除外）
    candidates: List[Path] = []
    for p in ANALYSIS_DIR.glob("daily_news_*.json"):
        name = p.name
        if "categorized" in name:
            continue
        # daily_news_latest.json のような運用があっても拾う（ただし日付抽出できない）
        candidates.append(p)

    if not candidates:
        return None

    # mtimeで最新
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def resolve_input_path(date: str | None, explicit_input: str | None) -> Tuple[Path, str]:
    """
    Returns (input_path, inferred_date_string)
    - If explicit_input exists, use it.
    - Else if date specified and daily_news_<date>.json exists, use it.
    - Else fallback to the newest daily_news_*.json in analysis dir.
    """
    if explicit_input:
        in_path = Path(explicit_input)
        if not in_path.exists():
            raise SystemExit(f"[ERROR] input not found: {in_path}")
        inferred = infer_date_from_filename(in_path) or datetime.now().strftime("%Y-%m-%d")
        return in_path, inferred

    if date:
        dated = ANALYSIS_DIR / f"daily_news_{date}.json"
        if dated.exists():
            return dated, date

    latest = find_latest_daily_news_file()
    if latest is None:
        tried = (ANALYSIS_DIR / f"daily_news_{date}.json") if date else "(no date)"
        raise SystemExit(f"[ERROR] no daily_news file found under: {ANALYSIS_DIR} (tried: {tried})")

    inferred = infer_date_from_filename(latest) or datetime.now().strftime("%Y-%m-%d")
    if date and not (ANALYSIS_DIR / f"daily_news_{date}.json").exists():
        print(f"[WARN] dated input missing for {date}; fallback to latest: {latest.name}")
    else:
        print(f"[INFO] auto-picked latest input: {latest.name}")

    return latest, inferred


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (will read daily_news_YYYY-MM-DD.json if exists)")
    ap.add_argument("--input", default=None, help="input daily_news json path")
    ap.add_argument("--output", default=None, help="output categorized json path")
    ap.add_argument("--latest", action="store_true", help="also write *_latest.json")
    args = ap.parse_args()

    in_path, inferred_date = resolve_input_path(args.date, args.input)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = ANALYSIS_DIR / f"daily_news_categorized_{inferred_date}.json"

    rules = build_rules()
    raw = load_json(in_path)
    items = normalize_news_items(raw)
    cat_items = apply_categories_to_items(items, rules)

    # 元構造を維持
    if isinstance(raw, list):
        out_obj: Any = cat_items
    elif isinstance(raw, dict):
        out_obj = dict(raw)
        placed = False
        for key in ("items", "articles", "news", "data"):
            if isinstance(raw.get(key), list):
                out_obj[key] = cat_items
                placed = True
                break
        if not placed:
            out_obj["items"] = cat_items
    else:
        out_obj = cat_items

    save_json(out_path, out_obj)
    print(f"[OK] categorized: {out_path} (n={len(cat_items)})")

    if args.latest:
        latest_path = ANALYSIS_DIR / "daily_news_categorized_latest.json"
        save_json(latest_path, out_obj)
        print(f"[OK] wrote latest: {latest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
