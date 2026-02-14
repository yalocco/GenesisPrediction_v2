# scripts/diagnose_sentiment_join.py
# Diagnose why Sentiment join results in "missing" (no sentiment numbers in table).
#
# Reads:
# - data/world_politics/analysis/view_model_latest.json
# - data/world_politics/analysis/sentiment_latest.json
#
# Prints:
# - counts
# - exact URL overlap
# - normalized URL overlap (strip #, ?, trailing slash, www)
# - sample URLs from each
# - title overlap (basic normalization)

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
VM_PATH = ROOT / "data" / "world_politics" / "analysis" / "view_model_latest.json"
SENT_PATH = ROOT / "data" / "world_politics" / "analysis" / "sentiment_latest.json"


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    # remove fragment
    parts = urlsplit(u)
    scheme = (parts.scheme or "").lower()
    netloc = (parts.netloc or "").lower()
    path = parts.path or ""
    query = parts.query or ""

    # normalize netloc: drop leading www.
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # drop common tracking query entirely (safe for join; we only need identity)
    # If you want stricter behavior, change to keep query.
    query = ""

    # strip trailing slash
    if path.endswith("/") and path != "/":
        path = path[:-1]

    return urlunsplit((scheme, netloc, path, query, ""))


_title_ws = re.compile(r"\s+")
_title_nonword = re.compile(r"[^\w]+", re.UNICODE)


def norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    t = _title_nonword.sub(" ", t)
    t = _title_ws.sub(" ", t).strip()
    return t


def main() -> int:
    if not VM_PATH.exists():
        print(f"[ERR] missing: {VM_PATH}")
        return 2
    if not SENT_PATH.exists():
        print(f"[ERR] missing: {SENT_PATH}")
        return 2

    vm = load_json(VM_PATH)
    sent = load_json(SENT_PATH)

    cards = ((vm.get("sections") or [{}])[0].get("cards")) or []
    sent_items = sent.get("items") or []

    vm_urls = [c.get("url") for c in cards if isinstance(c, dict) and c.get("url")]
    sent_urls = [it.get("url") for it in sent_items if isinstance(it, dict) and it.get("url")]

    vm_titles = [c.get("title") for c in cards if isinstance(c, dict) and c.get("title")]
    sent_titles = [it.get("title") for it in sent_items if isinstance(it, dict) and it.get("title")]

    print(f"[vm]   cards={len(cards)} urls={len(vm_urls)} titles={len(vm_titles)} date={vm.get('date')}")
    print(f"[sent] items={len(sent_items)} urls={len(sent_urls)} titles={len(sent_titles)} date={sent.get('date') or sent.get('base_date')}")

    vm_set = set(vm_urls)
    sent_set = set(sent_urls)
    exact_overlap = len(vm_set & sent_set)
    print(f"URL exact overlap = {exact_overlap}")

    vm_norm = set(norm_url(u) for u in vm_urls if u)
    sent_norm = set(norm_url(u) for u in sent_urls if u)
    norm_overlap = len(vm_norm & sent_norm)
    print(f"URL normalized overlap = {norm_overlap}")

    print("\n--- sample vm urls (raw -> norm) ---")
    for u in vm_urls[:8]:
        print(f"{u}\n  -> {norm_url(u)}")

    print("\n--- sample sent urls (raw -> norm) ---")
    for u in sent_urls[:8]:
        print(f"{u}\n  -> {norm_url(u)}")

    # title overlap check (fallback behavior)
    vm_tset = set(norm_title(t) for t in vm_titles if t)
    sent_tset = set(norm_title(t) for t in sent_titles if t)
    title_overlap = len(vm_tset & sent_tset)
    print(f"\nTitle normalized overlap = {title_overlap}")

    if exact_overlap == 0 and norm_overlap == 0:
        print("\n[HINT] Join will be all-missing because URLs do not match at all.")
        print("       Next fix: join by normalized URL OR stronger title fallback.")
    elif exact_overlap == 0 and norm_overlap > 0:
        print("\n[HINT] URLs match only after normalization.")
        print("       Next fix: sentiment.html join should use normalized URL.")
    elif exact_overlap > 0:
        print("\n[HINT] Some URLs match exactly, but you still see missing.")
        print("       Next fix: inspect sentiment.html join key logic (maybe uses different key).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
