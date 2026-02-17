# scripts/diagnose_sentiment_join_keys.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, List, Set, Tuple


RE_HAS_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://")


def pick(d: Any, keys: List[str]) -> Any:
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d:
            return d[k]
    return None


def decode_html_entities(s: str) -> str:
    return (
        s.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )


def normalize_source_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        t = v.strip()
        return re.sub(r"\s+", " ", t) if t else ""
    if isinstance(v, dict):
        cand = pick(v, ["name", "domain", "id", "title", "site", "publisher"])
        if isinstance(cand, str) and cand.strip():
            return cand.strip()
    return ""


def normalize_url_strong(u: Any) -> str:
    if not u:
        return ""
    raw = str(u).strip()
    if not raw:
        return ""
    raw = decode_html_entities(raw)

    if raw.startswith("//"):
        raw = "https:" + raw

    has_scheme = bool(RE_HAS_SCHEME.match(raw))
    if not has_scheme:
        raw = "https://" + raw.lstrip("/")

    raw = re.sub(r"#.*$", "", raw)
    raw = re.sub(r"\?.*$", "", raw)

    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+\-.]*://)([^/]+)(/.*)?$", raw)
    if not m:
        s = raw.strip().lower()
        return s[:-1] if s.endswith("/") else s

    scheme = m.group(1).lower()
    host = m.group(2).strip().lower()
    path = m.group(3) or ""

    if host.startswith("www."):
        host = host[4:]

    s = scheme + host + path
    s = s[:-1] if s.endswith("/") else s
    return s


def pick_url_any(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""

    direct = pick(
        obj,
        [
            "url",
            "link",
            "href",
            "norm_url",
            "article_url",
            "articleUrl",
            "canonical_url",
            "canonicalUrl",
            "final_url",
            "finalUrl",
            "resolved_url",
            "resolvedUrl",
            "source_url",
            "sourceUrl",
            "original_url",
            "originalUrl",
            "url_key",
            "urlKey",
            "join_key",
            "joinKey",
            "key",
            "id",
        ],
    )
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    for base in ["article", "meta", "raw", "item", "news", "data"]:
        b = obj.get(base)
        if isinstance(b, dict):
            v = pick_url_any(b)
            if v:
                return v
    return ""


def pick_title_any(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    direct = pick(obj, ["title", "headline", "name", "subject"])
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    for base in ["article", "meta", "raw", "item", "news", "data"]:
        b = obj.get(base)
        if isinstance(b, dict):
            v = pick_title_any(b)
            if v:
                return v
    return ""


def pick_source_any(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    direct = pick(obj, ["source", "publisher", "site", "domain"])
    s1 = normalize_source_text(direct)
    if s1:
        return s1
    for base in ["article", "meta", "raw", "item", "news", "data"]:
        b = obj.get(base)
        if isinstance(b, dict):
            v = pick_source_any(b)
            if v:
                return v
    return ""


def build_keys(url: str, title: str, source: str) -> List[str]:
    keys: List[str] = []

    if url:
        u_strong = normalize_url_strong(url)
        if u_strong:
            keys.append("u:" + u_strong)
        keys.append("u2:" + url.strip())

    title = decode_html_entities(title).strip()
    if title:
        tt = title.lower()
        keys.append("t:" + tt)
        if source:
            keys.append("ts:" + tt + "||" + source.lower())

    seen: Set[str] = set()
    out: List[str] = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def head_fields(obj: Any, max_keys: int = 25) -> str:
    if not isinstance(obj, dict):
        return str(type(obj))
    ks = list(obj.keys())[:max_keys]
    return ", ".join(ks)


def main() -> None:
    root = Path(".")
    cat_path = root / "data" / "world_politics" / "analysis" / "daily_news_categorized_latest.json"
    sent_path = root / "data" / "world_politics" / "analysis" / "sentiment_latest.json"

    if not cat_path.exists():
        print(f"[ERR] not found: {cat_path}")
        return
    if not sent_path.exists():
        print(f"[ERR] not found: {sent_path}")
        return

    cat_doc = load_json(cat_path)
    sent_doc = load_json(sent_path)

    cat_items = pick(cat_doc, ["items", "articles", "rows", "data"])
    if not isinstance(cat_items, list):
        print("[ERR] categorized items not list. top keys:", head_fields(cat_doc))
        return

    sent_items = pick(sent_doc, ["items", "articles", "rows", "data"])
    if not isinstance(sent_items, list):
        print("[ERR] sentiment items not list. top keys:", head_fields(sent_doc))
        return

    print(f"[OK] categorized items={len(cat_items)} sentiment items={len(sent_items)}")
    if cat_items:
        print("[INFO] categorized[0] keys:", head_fields(cat_items[0]))
    if sent_items:
        print("[INFO] sentiment[0] keys:", head_fields(sent_items[0]))

    sent_keyset: Set[str] = set()
    sent_key_counts = 0
    sent_url_fields: List[str] = []
    sent_title_fields: List[str] = []
    sent_source_fields: List[str] = []

    for it in sent_items:
        url = pick_url_any(it)
        title = pick_title_any(it)
        source = pick_source_any(it)
        if url:
            sent_url_fields.append(url)
        if title:
            sent_title_fields.append(title)
        if source:
            sent_source_fields.append(source)

        keys = build_keys(url, title, source)
        sent_key_counts += len(keys)
        sent_keyset.update(keys)

    overlap = 0
    cat_has_url = 0
    cat_has_title = 0
    cat_has_source = 0

    examples_miss: List[Tuple[str, str, str]] = []
    examples_hit: List[Tuple[str, str, str, str]] = []

    for it in cat_items:
        url = pick_url_any(it)
        title = pick_title_any(it)
        source = pick_source_any(it)

        if url:
            cat_has_url += 1
        if title:
            cat_has_title += 1
        if source:
            cat_has_source += 1

        keys = build_keys(url, title, source)
        hit_key = next((k for k in keys if k in sent_keyset), "")
        if hit_key:
            overlap += 1
            if len(examples_hit) < 5:
                examples_hit.append((hit_key, url, title, source))
        else:
            if len(examples_miss) < 5:
                examples_miss.append((url, title, source))

    print()
    print("[STATS] categorized has_url/has_title/has_source =", cat_has_url, "/", cat_has_title, "/", cat_has_source)
    print("[STATS] sentiment keys =", len(sent_keyset), "(total built =", sent_key_counts, ")")
    print("[STATS] overlap (categorized rows that hit sentiment key) =", overlap, "/", len(cat_items))

    def show_sample(name: str, arr: List[str]) -> None:
        print(f"\n[SAMPLE] {name}:")
        for s in arr[:5]:
            print(" -", s)

    show_sample("sentiment url candidates", sent_url_fields)
    show_sample("sentiment title candidates", sent_title_fields)
    show_sample("sentiment source candidates", sent_source_fields)

    print("\n[HIT EXAMPLES]")
    if not examples_hit:
        print(" - (none)")
    else:
        for hk, url, title, source in examples_hit:
            print(" - hit_key:", hk)
            print("   url   :", url)
            print("   title :", title)
            print("   source:", source)

    print("\n[MISS EXAMPLES]")
    for url, title, source in examples_miss:
        print(" - url   :", url)
        print("   title :", title)
        print("   source:", source)

    print("\n[HINT]")
    print("If overlap=0, compare MISS url/title/source vs SAMPLE sentiment url/title/source.")
    print("Likely cause is different field names (url not in expected keys) or url formats.")


if __name__ == "__main__":
    main()
