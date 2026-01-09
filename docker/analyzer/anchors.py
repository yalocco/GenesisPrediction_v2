from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

# ============================================================
# Anchor noise control (E: light, safe, single-source-of-truth)
#   - STOP is applied at tokenize stage (main)
#   - _take_top has a minimal "last safety valve"
#   - analyze.py should NOT re-filter anchors (I/O only)
# ============================================================

# Absolute stopwords: pronouns / function words / boilerplate
STOP_CORE = {
    # pronouns / determiners
    "i","me","my","mine","we","us","our","ours",
    "you","your","yours",
    "he","him","his","she","her","hers",
    "they","them","their","theirs",
    "it","its",
    "this","that","these","those",
    "who","what","when","where","why","how",

    # reporting boilerplate
    "said","says","say","told",
    "report","reports","reported",
    "update","updated","latest","breaking",
}

# Domain stopwords: dataset-wide generic terms (tune as needed)
STOP_DOMAIN = {
    # generic / news boilerplate
    "global","world","politics","political","times",
    "initiative","initiatives",

    # weak verbs / nouns commonly surfacing as noise
    "running","walking","movement",
    "target","targets","targeted","targeting",
    "back","backs","backed",

    # often-too-generic event words (keep if you prefer)
    "crisis","attack",

    # numbers-as-words
    "one","two","three","four","five","six","seven","eight","nine","ten",
}

STOP = STOP_CORE | STOP_DOMAIN


@dataclass(frozen=True)
class Anchor:
    text: str
    kind: str      # "dimension" | "event" | "lexical" (current usage: lexical)
    score: float


def _norm(s: str) -> str:
    return " ".join(str(s).strip().split())


def _norm_token(s: str) -> str:
    """Normalize token for STOP/dup checks."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = " ".join(s.split())
    return s


def _tokenize_light(s: str) -> List[str]:
    s = _norm_token(s)
    toks = []
    for t in s.split():
        if len(t) < 3:
            continue
        if t in STOP:
            continue
        if t.isdigit():
            continue
        if re.fullmatch(r"\d{4}", t):  # year-like token
            continue
        toks.append(t)
    return toks


def _take_top(items: Iterable[Anchor], k: int) -> List[Anchor]:
    """Rank + dedup. (Minimal last safety valve for STOP.)"""
    xs = sorted(items, key=lambda a: a.score, reverse=True)
    out: List[Anchor] = []
    seen = set()

    for a in xs:
        key = _norm_token(a.text)

        if not key or len(key) < 3:
            continue
        if key in STOP:               # last safety valve
            continue
        if key.isdigit():
            continue
        if re.fullmatch(r"\d{4}", key):
            continue

        if key in seen:
            continue
        seen.add(key)

        # keep original text (but normalized casing tends to be nicer)
        out.append(Anchor(text=key, kind=a.kind, score=a.score))

        if len(out) >= k:
            break

    return out


def extract_anchors(diff_doc: Dict[str, Any], daily_doc: Dict[str, Any], max_anchors: int = 12) -> List[Anchor]:
    """Extract lexical anchors from available text fields and return ranked anchors."""
    found: List[Anchor] = []

    # You can expand these fields safely; empty/missing is fine.
    texts: List[str] = []

    # diff summary-ish
    if isinstance(diff_doc, dict):
        s = diff_doc.get("summary") or {}
        if isinstance(s, dict):
            for key in ("headline", "bullets", "watch", "uncertainty", "note"):
                v = s.get(key)
                if isinstance(v, str) and v.strip():
                    texts.append(v)
                elif isinstance(v, list):
                    texts.extend([str(x) for x in v if str(x).strip()])

    # daily summary-ish
    if isinstance(daily_doc, dict):
        for key in ("headline", "one_liner", "delta_explanation"):
            v = daily_doc.get(key)
            if isinstance(v, str) and v.strip():
                texts.append(v)

    # Build bag-of-words (after tokenize filtering)
    bag: Dict[str, int] = {}
    for t in texts:
        for tok in _tokenize_light(t):
            bag[tok] = bag.get(tok, 0) + 1

    for tok, c in bag.items():
        found.append(Anchor(text=tok, kind="lexical", score=1.0 + c * 0.25))

    return _take_top(found, max_anchors)


def anchors_to_strings(anchors: List[Anchor], max_n: int = 10) -> List[str]:
    """Stable conversion for daily_summary JSON."""
    return [a.text for a in (anchors or [])[:max_n]]
