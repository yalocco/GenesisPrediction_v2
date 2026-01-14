#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Postprocess: compute anchors quality score + tags, and write into daily_summary_YYYY-MM-DD.json
- Does NOT change anchors/top_tokens/hints/anchors_detail.
- Only APPENDS/UPDATES "anchors_quality".
- Idempotent: if anchors_quality.version==VERSION and anchors list unchanged, skip.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = 1

# ====== Heuristics (simple & safe; tune later) ======

WEAK_FUNCTION_WORDS = {
    # pronouns / determiners / very common glue words
    "i","you","your","yours","we","they","them","their","theirs","he","she","his","her","its",
    "this","that","these","those","here","there","now","then",
    "a","an","the","and","or","but","if","to","of","in","on","at","for","from","with","as","by",
}

WEAK_DOMAIN_GENERIC = {
    "politics","political","global","international","world","globes",
    "crisis","conflict","attack","security","government","policy","economy",
}

WEAK_GENERIC_NOUNS = {
    "years","year","life","people","thing","things","way","door","back","next","plan","read",
    "most","will","would","might","must","should","could",
}

COMMON_VERBS = {
    "read","say","says","said","make","makes","made","take","takes","took","get","gets","got",
    "go","goes","went","come","comes","came","see","sees","saw","know","knows","knew",
}

MONTHS_DAYS = {
    "jan","january","feb","february","mar","march","apr","april","may","jun","june",
    "jul","july","aug","august","sep","sept","september","oct","october","nov","november","dec","december",
    "monday","tuesday","wednesday","thursday","friday","saturday","sunday",
}

_re_has_digit = re.compile(r"\d")
_re_only_punct = re.compile(r"^[\W_]+$")

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

@dataclass
class ItemScore:
    token: str
    score: float
    tags: List[str]

def score_token(tok: str) -> ItemScore:
    t = (tok or "").strip().lower()
    tags: List[str] = []
    score = 1.0

    if not t:
        return ItemScore(tok, 0.0, ["empty"])

    if _re_only_punct.match(t):
        return ItemScore(tok, 0.0, ["only_punct"])

    # penalties
    if t in WEAK_FUNCTION_WORDS:
        score -= 0.70
        tags.append("weak_function_word")

    if t in WEAK_DOMAIN_GENERIC:
        score -= 0.45
        tags.append("weak_domain_generic")

    if t in WEAK_GENERIC_NOUNS:
        score -= 0.45
        tags.append("weak_generic")

    if t in COMMON_VERBS:
        score -= 0.35
        tags.append("common_verb")

    if t in MONTHS_DAYS:
        score -= 0.35
        tags.append("time_word")

    if _re_has_digit.search(t):
        score -= 0.25
        tags.append("has_digit")

    if len(t) <= 3:
        score -= 0.20
        tags.append("very_short")

    if t.endswith("ing"):
        score -= 0.15
        tags.append("ends_with_ing")

    # light positive hint (doesn't guarantee entity, just "looks specific")
    # If not tagged as weak function/generic and length is decent:
    if (len(t) >= 5) and not any(tag.startswith("weak_") for tag in tags):
        tags.append("entity_like")

    score = clamp01(score)
    return ItemScore(tok, score, tags)

def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def dump_json(p: Path, obj: Dict[str, Any]) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(p)

def anchors_signature(anchors: List[str]) -> str:
    # stable signature for idempotency
    return "|".join((a or "").strip().lower() for a in anchors)

def compute_quality(doc: Dict[str, Any]) -> Tuple[float, List[ItemScore]]:
    anchors = doc.get("anchors") or []
    if not isinstance(anchors, list):
        anchors = []

    items = [score_token(str(a)) for a in anchors]
    if not items:
        return 0.0, []

    overall = sum(it.score for it in items) / len(items)
    overall = round(overall, 4)
    return overall, items

def now_jst_iso() -> str:
    jst = timezone(timedelta(hours=9))
    return datetime.now(tz=jst).isoformat(timespec="seconds")

def should_skip(doc: Dict[str, Any], anchors: List[str]) -> bool:
    aq = doc.get("anchors_quality")
    if not isinstance(aq, dict):
        return False
    if aq.get("version") != VERSION:
        return False
    if aq.get("anchors_sig") != anchors_signature(anchors):
        return False
    return True

def process_file(p: Path) -> bool:
    doc = load_json(p)
    anchors = doc.get("anchors") or []
    if not isinstance(anchors, list):
        anchors = []

    if should_skip(doc, anchors):
        return False

    overall, items = compute_quality(doc)

    weak_tokens = [it.token for it in items if it.score < 0.40]
    flag = "low" if overall < 0.70 else "ok"

    doc["anchors_quality"] = {
        "version": VERSION,
        "anchors_sig": anchors_signature(anchors),
        "overall_score": overall,
        "flag": flag,
        "weak_tokens": weak_tokens,
        "items": [{"token": it.token, "score": round(it.score, 4), "tags": it.tags} for it in items],
        "computed_at": now_jst_iso(),
    }


    dump_json(p, doc)
    return True

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir containing daily_summary_*.json")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (optional) only process that day")
    args = ap.parse_args()

    base = Path(args.dir)
    if not base.exists():
        print(f"[ERR] dir not found: {base}")
        return 2

    if args.date:
        targets = [base / f"daily_summary_{args.date}.json"]
    else:
        targets = sorted(base.glob("daily_summary_*.json"))

    changed = 0
    missing = 0
    for p in targets:
        if not p.exists():
            missing += 1
            continue
        if process_file(p):
            changed += 1

    print(f"[DONE] anchors_quality version={VERSION} updated_files={changed} missing={missing}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
