from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

# ============================================================
# Anchor noise control (E: light, safe, single-source-of-truth)
#
# ✅ Finalize point: anchors.py (single source of truth)
# ✅ STOP is applied at tokenize stage (main) for CORE + WEAK tokens
# ✅ DOMAIN_GENERIC is handled in finalize_anchors():
#    - single-token generic is blocked
#    - rescued only when "specific" anchors exist (context present)
#    - capped to a small max (default 2)
# ✅ analyze.py should NOT re-filter anchors (I/O only)
# ============================================================

# Absolute stopwords: pronouns / function words / boilerplate
STOP_CORE = {
    # pronouns / determiners
    "i", "me", "my", "mine", "we", "us", "our", "ours",
    "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers",
    "they", "them", "their", "theirs",
    "it", "its",
    "this", "that", "these", "those",
    "who", "what", "when", "where", "why", "how",

    # reporting boilerplate
    "said", "says", "say", "told",
    "report", "reports", "reported",
    "update", "updated", "latest", "breaking",
}

# Domain-generic terms (do NOT drop at tokenize; handled in finalize_anchors)
# Rule: single-token generic is blocked; rescued only with "specific" context.
DOMAIN_GENERIC = {
    # generic / news boilerplate
    "global", "world", "politics", "political", "times",
    "initiative", "initiatives",

    # often-too-generic event words (kept only as contextual labels)
    "crisis", "attack",
}

# Weak verbs / weak tokens we want to drop early (tokenize stage)
STOP_WEAK = {
    "running", "walking", "movement",
    "target", "targets", "targeted", "targeting",
    "back", "backs", "backed",
}

# Numbers-as-words (drop early)
STOP_NUMWORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
}

# Tokenize-time stop list (CORE + WEAK + NUMWORDS)
STOP = STOP_CORE | STOP_WEAK | STOP_NUMWORDS


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
    """
    Tokenize with light normalization.
    - Drops STOP (core/weak/numwords) here
    - Keeps DOMAIN_GENERIC here (handled later in finalize_anchors)
    """
    s = _norm_token(s)
    toks: List[str] = []

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
    """Rank + dedup. (Minimal last safety valve for STOP only.)"""
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

        # keep normalized token
        out.append(Anchor(text=key, kind=a.kind, score=a.score))

        if len(out) >= k:
            break

    return out


def finalize_anchors(
    anchors: List[Anchor],
    max_anchors: int,
    max_domain_generic: int = 2,
) -> List[Anchor]:
    """
    Final quality gate (single source of truth).
    DOMAIN_GENERIC:
      - blocked if it's the only kind of content (no "specific" anchors)
      - allowed only as contextual labels when specific anchors exist
      - capped (default 2)
    """
    anchors = anchors or []
    specific: List[Anchor] = []
    generic: List[Anchor] = []

    for a in anchors:
        tok = _norm_token(a.text)
        if not tok:
            continue
        if tok in DOMAIN_GENERIC:
            generic.append(Anchor(text=tok, kind=a.kind, score=a.score))
        else:
            specific.append(Anchor(text=tok, kind=a.kind, score=a.score))

    # If we have no specific anchors, do not emit generics alone.
    if not specific:
        return []

    # Prioritize specifics, then a small number of rescued generics.
    out: List[Anchor] = []
    out.extend(specific)

    if max_domain_generic > 0 and generic:
        out.extend(generic[:max_domain_generic])

    return out[:max_anchors]


def extract_anchors(diff_doc: Dict[str, Any], daily_doc: Dict[str, Any], max_anchors: int = 12) -> List[Anchor]:
    """Extract lexical anchors from available text fields and return ranked anchors."""
    found: List[Anchor] = []

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

    # rank/dedup → final gate
    ranked = _take_top(found, max_anchors * 2)  # small buffer before finalize
    return finalize_anchors(ranked, max_anchors=max_anchors, max_domain_generic=2)


def anchors_to_strings(anchors: List[Anchor], max_n: int = 10) -> List[str]:
    """Stable conversion for daily_summary JSON."""
    return [a.text for a in (anchors or [])[:max_n]
