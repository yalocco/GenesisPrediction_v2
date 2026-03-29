
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_WORLD_DIR = ROOT / "data" / "world_politics"
ANALYSIS_DIR = DATA_WORLD_DIR / "analysis"

OUT_LATEST = ANALYSIS_DIR / "sentiment_latest.json"
CACHE_PATH = ROOT / "data" / "translation_cache_sentiment.json"

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")
WS_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
READ_MORE_RE = re.compile(r"\bRead More:?\b.*$", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
ASCII_WORD_RE = re.compile(r"\b[A-Za-z]{3,}\b")

POSITIVE_WORDS = {
    "advance", "advances", "agreement", "agreements", "aid", "ally", "boost",
    "breakthrough", "calm", "ceasefire", "cooperate", "cooperation", "deal",
    "deescalation", "ease", "gain", "gains", "good", "growth", "improve",
    "improved", "launch", "launched", "opens", "optimism", "peace", "progress",
    "recovery", "relief", "rescue", "rise", "rises", "safe", "settlement",
    "stability", "stable", "strong", "success", "surge", "truce", "victory", "wins",
}
NEGATIVE_WORDS = {
    "attack", "attacks", "bomb", "bombing", "chaos", "collapse", "collapsed",
    "conflict", "crackdown", "crash", "crisis", "death", "deaths", "decline",
    "defeat", "drop", "drops", "escalate", "escalation", "fail", "fails", "fall",
    "falls", "famine", "fear", "fraud", "hostage", "inflation", "kill", "killed",
    "loss", "losses", "missile", "panic", "protest", "recession", "sanction",
    "scandal", "shortage", "slump", "strike", "strikes", "tension", "threat",
    "threats", "violence", "war", "worse", "worst",
}
RISK_WORDS = {
    "alert", "armed", "boycott", "danger", "dispute", "hostile", "instability",
    "military", "nuclear", "probe", "retaliation", "rocket", "shelling", "shock",
    "uncertain", "uncertainty", "warning", "warnings",
}
WEAK_NEGATIVE_WORDS = {"down", "fall", "falls", "drop", "drops", "slump", "crash", "weaken", "weaker"}
WEAK_POSITIVE_WORDS = {"up", "rise", "rises", "gain", "gains", "record", "strong", "stronger"}

SOURCE_I18N_MAP: Dict[str, Dict[str, str]] = {
    "ABC News (AU)": {"ja": "ABC News (AU)", "th": "ABC News (AU)"},
    "BBC News": {"ja": "BBC News", "th": "BBC News"},
    "CBS News": {"ja": "CBS News", "th": "CBS News"},
    "CNA": {"ja": "CNA", "th": "CNA"},
    "CNBC": {"ja": "CNBC", "th": "CNBC"},
    "CounterPunch": {"ja": "CounterPunch", "th": "CounterPunch"},
    "Crikey": {"ja": "Crikey", "th": "Crikey"},
    "Crypto Briefing": {"ja": "Crypto Briefing", "th": "Crypto Briefing"},
    "Deseret News": {"ja": "Deseret News", "th": "Deseret News"},
    "Financial Post": {"ja": "Financial Post", "th": "Financial Post"},
    "Fox News": {"ja": "フォックスニュース", "th": "ข่าว Fox"},
    "Globalresearch.ca": {"ja": "Globalresearch.ca", "th": "Globalresearch.ca"},
    "Ibtimes.com.au": {"ja": "Ibtimes.com.au", "th": "Ibtimes.com.au"},
    "Jezebel": {"ja": "Jezebel", "th": "Jezebel"},
    "KPBS": {"ja": "KPBS", "th": "KPBS"},
    "Landezine.com": {"ja": "Landezine.com", "th": "Landezine.com"},
    "New York Magazine": {"ja": "ニューヨーク・マガジン", "th": "นิตยสารนิวยอร์ก"},
    "NBC News": {"ja": "NBCニュース", "th": "NBC News"},
    "Patheos": {"ja": "Patheos", "th": "Patheos"},
    "Shannews.org": {"ja": "Shannews.org", "th": "Shannews.org"},
    "The American Conservative": {"ja": "The American Conservative", "th": "The American Conservative"},
    "The American Prospect": {"ja": "The American Prospect", "th": "The American Prospect"},
    "The Atlantic": {"ja": "The Atlantic", "th": "The Atlantic"},
    "The Conversation Africa": {"ja": "The Conversation Africa", "th": "The Conversation Africa"},
    "The Indian Express": {"ja": "The Indian Express", "th": "The Indian Express"},
    "The Irish Times": {"ja": "The Irish Times", "th": "The Irish Times"},
    "The New Republic": {"ja": "The New Republic", "th": "The New Republic"},
    "The Punch": {"ja": "The Punch", "th": "The Punch"},
    "The Times of India": {"ja": "The Times of India", "th": "The Times of India"},
    "Uxdesign.cc": {"ja": "Uxdesign.cc", "th": "Uxdesign.cc"},
    "Variety": {"ja": "Variety", "th": "Variety"},
    "War on the Rocks": {"ja": "War on the Rocks", "th": "War on the Rocks"},
}

SENTIMENT_LABELS: Dict[str, Dict[str, str]] = {
    "positive": {"en": "positive", "ja": "ポジティブ", "th": "เชิงบวก"},
    "negative": {"en": "negative", "ja": "ネガティブ", "th": "เชิงลบ"},
    "neutral": {"en": "neutral", "ja": "中立", "th": "เป็นกลาง"},
    "mixed": {"en": "mixed", "ja": "混合", "th": "ผสม"},
    "unknown": {"en": "unknown", "ja": "不明", "th": "ไม่ทราบ"},
}

METHOD_LABELS: Dict[str, Dict[str, str]] = {
    "lex": {"en": "lex", "ja": "辞書判定", "th": "พจนานุกรม"},
    "fallback": {"en": "fallback", "ja": "fallback", "th": "fallback"},
    "agg": {"en": "aggregate", "ja": "集計", "th": "สรุปรวม"},
}

PROPER_NOUNS = [
    "AIPAC", "Adult Braces", "Antichrist", "Apple TV+", "Australian Broadcasting Corporation",
    "Barcelona", "Bruce Springsteen", "CNBC", "COAC", "CSCAE", "CounterPunch", "Crikey",
    "Daredevil: Born Again", "David Berger", "Delhi", "Dillon Danis", "Disney+", "Fox News",
    "Friends", "HBO Max", "Hakeem Jeffries", "ICE", "Ibn Khaldun", "Illinois", "Imran Khan",
    "International Union of Architects", "Invincible", "Iran", "Jezebel", "Jennifer Aniston",
    "Jim Curtis", "Kasim", "Kat Abughazaleh", "Kingpin", "Landezine.com", "Labubu", "Marvel",
    "Meryl Fury", "Michael Horowitz", "Mormon Wives", "Muqaddimah", "NBC News", "NYU",
    "Nikita Bier", "Pakistan", "Paolo Benanti", "Patheos", "Peter Thiel", "Poland",
    "Prime Video", "Rachel Green", "Rebecca Karl", "Salween", "Salween River",
    "Sai De Moine", "Shan State", "Sir Ganga Ram Hospital", "Sonia Gandhi", "Sulaiman",
    "TSA", "Taiwo Awoniyi", "Tehran", "The Atlantic", "The Irish Times", "The New Republic",
    "The Punch", "The Times of India", "Thunderbolts", "Trump", "UIA", "UNHRC",
]
ENGLISH_LEAK_ALLOWLIST = {x.lower() for x in PROPER_NOUNS} | {
    "disney+", "prime", "video", "marvel", "cnbc", "aipac", "uia", "csae", "coac",
    "nbc", "news", "ice", "tsa", "raf", "mcu"
}
BAD_OUTPUT_FRAGMENTS = {
    "vůdơ", "partly", "premiere", "cameo", "fear of the dark", "deadpool",
    "man without fear", "the post ", "appeared first on "
}

@dataclass
class TranslationConfig:
    ollama_url: str
    model: str
    timeout: int = 60


@dataclass
class Score:
    risk: float
    positive: float
    uncertainty: float
    net: float
    method: str


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


def _normalize_text(value: Any) -> str:
    text = _as_str(value).replace("\u00a0", " ")
    text = HTML_TAG_RE.sub("", text)
    return WS_RE.sub(" ", text).strip()


def _clean_for_translation(value: str, limit: int = 280) -> str:
    text = _normalize_text(value)
    text = URL_RE.sub("", text)
    text = READ_MORE_RE.sub("", text)
    text = WS_RE.sub(" ", text).strip(" -–—")
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in [". ", "! ", "? ", "; "]:
        idx = cut.rfind(sep)
        if idx >= 120:
            return cut[: idx + 1].strip()
    idx = cut.rfind(" ")
    if idx >= 120:
        return cut[:idx].strip()
    return cut.strip()


def _pick(obj: Any, keys: Iterable[str], default: Any = None) -> Any:
    if not isinstance(obj, dict):
        return default
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return default


def _extract_items(doc: Any) -> List[Dict[str, Any]]:
    if isinstance(doc, dict):
        for key in ("items", "articles", "rows", "data", "news"):
            value = doc.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    return []


def _source_name(item: Dict[str, Any]) -> str:
    src = item.get("source")
    if isinstance(src, dict):
        return _normalize_text(src.get("name") or src.get("id") or "")
    return _normalize_text(_pick(item, ["source", "publisher", "site", "domain"], "") or "")


def _image_url(item: Dict[str, Any]) -> str:
    return _normalize_text(_pick(item, ["urlToImage", "image", "thumbnail", "thumb", "og_image"], "") or "")


def _published_at(item: Dict[str, Any]) -> str:
    return _normalize_text(_pick(item, ["publishedAt", "published_at", "pubDate", "date", "datetime"], "") or "")


def _source_i18n_block(source: str) -> Dict[str, str]:
    src = _normalize_text(source)
    if not src:
        return {"en": "", "ja": "", "th": ""}
    mapped = SOURCE_I18N_MAP.get(src)
    if mapped:
        return {"en": src, "ja": mapped["ja"], "th": mapped["th"]}
    return {"en": src, "ja": src, "th": src}

def _label_i18n_block(value: str, mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    key = _normalize_text(value).lower()
    mapped = mapping.get(key)
    if mapped:
        return {"en": mapped["en"], "ja": mapped["ja"], "th": mapped["th"]}
    raw = _normalize_text(value)
    return {"en": raw, "ja": raw, "th": raw}


def _label_counts_i18n_block(counts: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for key in ["positive", "negative", "neutral", "mixed", "unknown"]:
        out[key] = {
            "label_i18n": _label_i18n_block(key, SENTIMENT_LABELS),
            "count": int(counts.get(key, 0)),
        }
    return out


def _tokenize(*parts: str) -> List[str]:
    text = " ".join(p for p in parts if p)
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def score_text(title: str, desc: str) -> Score:
    toks = _tokenize(title, desc)
    if not toks:
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")
    pos = sum(1 for t in toks if t in POSITIVE_WORDS)
    neg = sum(1 for t in toks if t in NEGATIVE_WORDS)
    rsk = sum(1 for t in toks if t in RISK_WORDS)
    if (pos + neg + rsk) == 0:
        pos += sum(1 for t in toks if t in WEAK_POSITIVE_WORDS)
        neg += sum(1 for t in toks if t in WEAK_NEGATIVE_WORDS)
    hits = pos + neg + rsk
    if hits == 0:
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")
    raw = (pos - neg) - 0.5 * rsk
    denom = max(6.0, float(hits) * 2.0)
    net = max(-1.0, min(1.0, raw / denom))
    positive = max(0.0, net)
    risk = max(0.0, -net)
    uncertainty = 0.12 + 0.18 * (1.0 - min(1.0, abs(net) * 2.0))
    return Score(risk=risk, positive=positive, uncertainty=uncertainty, net=net, method="lex")


def classify_sentiment(score: Score) -> str:
    if score.uncertainty >= 0.24 and abs(score.net) <= 0.10:
        return "mixed"
    if score.net >= 0.12:
        return "positive"
    if score.net <= -0.12:
        return "negative"
    return "neutral"


def _label_counts(items: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    for item in items:
        lab = _normalize_text(item.get("sentiment") or item.get("sentiment_label") or "unknown").lower()
        out[lab if lab in out else "unknown"] += 1
    return out


def _load_cache() -> Dict[str, Dict[str, str]]:
    if not CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        return {}
    return {}


def _save_cache(cache: Dict[str, Dict[str, str]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _restore_proper_nouns(text: str) -> str:
    out = text
    for noun in PROPER_NOUNS:
        out = re.sub(re.escape(noun), noun, out, flags=re.IGNORECASE)
    return out


def _sanitize_translation(text: str) -> str:
    return _restore_proper_nouns(_normalize_text(text))


def _english_leak_score(src_en: str, translated: str) -> int:
    src = _normalize_text(src_en).lower()
    dst = _normalize_text(translated)
    count = 0
    for word in ASCII_WORD_RE.findall(dst):
        wl = word.lower()
        if wl in ENGLISH_LEAK_ALLOWLIST:
            continue
        if wl in src and len(word) > 6:
            count += 1
        elif wl not in src:
            count += 1
    return count


def _looks_corrupted_translation(src_en: str, translated: str) -> bool:
    src = _normalize_text(src_en)
    dst = _normalize_text(translated)
    if not src or not dst:
        return False
    if len(dst) > max(len(src) * 2.2, len(src) + 180):
        return True
    lowered_src = src.lower()
    foreign_hits = 0
    for noun in PROPER_NOUNS:
        if noun.lower() in dst.lower() and noun.lower() not in lowered_src:
            foreign_hits += 1
            if foreign_hits >= 4:
                return True
    leak = _english_leak_score(src, dst)
    if leak >= 3:
        return True
    bad_lower = dst.lower()
    if any(fragment in bad_lower for fragment in BAD_OUTPUT_FRAGMENTS):
        return True
    return False


def _parse_llm_json(raw: str) -> Dict[str, str] | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            data = json.loads(raw[start:end + 1])
        except Exception:
            return None
    if not isinstance(data, dict):
        return None
    ja = _sanitize_translation(data.get("ja", ""))
    th = _sanitize_translation(data.get("th", ""))
    if not ja or not th:
        return None
    return {"ja": ja, "th": th}


def _call_ollama_json(text: str, cfg: TranslationConfig, session: requests.Session, strict: bool = False) -> Dict[str, str] | None:
    protected = ", ".join(PROPER_NOUNS)
    extra = ""
    if strict:
        extra = """
- Do not leave English words except protected proper nouns and well-known brands.
- Do not transliterate to unrelated titles or characters.
- Avoid mixed-language output.
"""
    prompt = f"""Translate the following English news text into Japanese and Thai.

Rules:
- Preserve proper nouns exactly when they appear: {protected}
- Do not add names, places, organizations, brands, or titles that are not in the source text.
- Translate only this single item. Do not mix with any other article.
- Return STRICT JSON only.
- Keep output concise and natural.
- If the source is truncated, translate only the visible text.
{extra}

Text:
{text}

Output JSON:
{{"ja":"...", "th":"..."}}
"""
    try:
        response = session.post(
            f"{cfg.ollama_url.rstrip('/')}/api/generate",
            json={"model": cfg.model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=cfg.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return _parse_llm_json(_as_str(payload.get("response", "")))
    except Exception:
        return None


def _translated_block_valid(src: str, block: Dict[str, str]) -> bool:
    if not block:
        return False
    ja = _normalize_text(block.get("ja", ""))
    th = _normalize_text(block.get("th", ""))
    if not ja or not th:
        return False
    if ja == src or th == src:
        return False
    if _looks_corrupted_translation(src, ja) or _looks_corrupted_translation(src, th):
        return False
    return True


def _translate_item_text(kind: str, value: str, cfg: TranslationConfig, session: requests.Session, cache: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    src = _clean_for_translation(value, limit=220 if kind == "title" else 280)
    if not src:
        return {"en": "", "ja": "", "th": ""}

    cache_key = f"{kind}::{src}"
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        cached_block = {"en": src, "ja": _normalize_text(cached.get("ja", src)), "th": _normalize_text(cached.get("th", src))}
        if _translated_block_valid(src, cached_block):
            return cached_block

    first = _call_ollama_json(src, cfg, session, strict=False)
    if first:
        first_block = {"en": src, "ja": first["ja"], "th": first["th"]}
        if _translated_block_valid(src, first_block):
            cache[cache_key] = {"ja": first_block["ja"], "th": first_block["th"]}
            return first_block

    retry_src = _clean_for_translation(src, limit=200 if kind == "description" else 180)
    second = _call_ollama_json(retry_src, cfg, session, strict=True)
    if second:
        second_block = {"en": src, "ja": second["ja"], "th": second["th"]}
        if _translated_block_valid(src, second_block):
            cache[cache_key] = {"ja": second_block["ja"], "th": second_block["th"]}
            return second_block

    out = {"en": src, "ja": src, "th": src}
    cache[cache_key] = {"ja": out["ja"], "th": out["th"]}
    return out


def _resolve_input(date: str) -> Path:
    raw_daily = DATA_WORLD_DIR / f"{date}.json"
    analysis_daily = ANALYSIS_DIR / f"daily_news_{date}.json"
    latest_daily = ANALYSIS_DIR / "daily_news_latest.json"
    if raw_daily.exists():
        return raw_daily
    if analysis_daily.exists():
        return analysis_daily
    if latest_daily.exists():
        return latest_daily
    raise SystemExit(f"[ERR] missing daily news input: {raw_daily} / {analysis_daily} / {latest_daily}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name")
    parser.add_argument("--ollama-url", default="http://localhost:11435", help="Ollama API base URL")
    parser.add_argument("--timeout", type=int, default=60, help="Per request timeout seconds")
    args = parser.parse_args()

    src_path = _resolve_input(args.date.strip())
    cfg = TranslationConfig(ollama_url=args.ollama_url, model=args.model, timeout=args.timeout)

    doc = json.loads(src_path.read_text(encoding="utf-8"))
    items = _extract_items(doc)
    cache = _load_cache()

    out_items: List[Dict[str, Any]] = []
    rule_hit = 0
    fallback = 0

    with requests.Session() as session:
        for item in items:
            url = _normalize_text(_pick(item, ["url", "link", "href"], "") or "")
            title = _normalize_text(_pick(item, ["title", "headline", "name"], "") or "")
            source = _source_name(item)
            description = _clean_for_translation(_pick(item, ["description", "summary", "content", "snippet"], "") or "")
            published_at = _published_at(item)
            image = _image_url(item)

            score = score_text(title, description)
            label = classify_sentiment(score)

            if score.method == "lex":
                rule_hit += 1
            else:
                fallback += 1

            sentiment_i18n = _label_i18n_block(label, SENTIMENT_LABELS)
            method_i18n = _label_i18n_block(score.method, METHOD_LABELS)
            translated_title = _translate_item_text("title", title, cfg, session, cache)
            translated_description = _translate_item_text("description", description, cfg, session, cache)

            out_items.append({
                "url": url,
                "title": title,
                "title_i18n": translated_title,
                "source": source,
                "source_i18n": _source_i18n_block(source),
                "description": description,
                "description_i18n": translated_description,
                "summary": description,
                "summary_i18n": translated_description,
                "publishedAt": published_at,
                "image": image,
                "risk": round(score.risk, 6),
                "positive": round(score.positive, 6),
                "uncertainty": round(score.uncertainty, 6),
                "net": round(score.net, 6),
                "score": round(score.net, 6),
                "sentiment": label,
                "sentiment_i18n": sentiment_i18n,
                "sentiment_label": label,
                "sentiment_label_i18n": sentiment_i18n,
                "method": score.method,
                "method_i18n": method_i18n,
            })

    n = len(out_items)
    avg_risk = sum(x["risk"] for x in out_items) / n if n else 0.0
    avg_pos = sum(x["positive"] for x in out_items) / n if n else 0.0
    avg_unc = sum(x["uncertainty"] for x in out_items) / n if n else 0.0
    avg_net = sum(x["net"] for x in out_items) / n if n else 0.0

    label_counts = _label_counts(out_items)
    today_score = Score(risk=avg_risk, positive=avg_pos, uncertainty=avg_unc, net=avg_net, method="agg")
    today_label = classify_sentiment(today_score) if n else "neutral"

    today_label_i18n = _label_i18n_block(today_label, SENTIMENT_LABELS)
    payload = {
        "date": args.date.strip(),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "lang_default": "en",
        "languages": ["en", "ja", "th"],
        "items": out_items,
        "today": {
            "articles": n,
            "risk": round(avg_risk, 6),
            "positive": round(avg_pos, 6),
            "uncertainty": round(avg_unc, 6),
            "net": round(avg_net, 6),
            "score": round(avg_net, 6),
            "sentiment": today_label,
            "sentiment_i18n": today_label_i18n,
            "sentiment_label": today_label,
            "sentiment_label_i18n": today_label_i18n,
            "label_counts": label_counts,
            "label_counts_i18n": _label_counts_i18n_block(label_counts),
        },
        "summary": {
            "rule_hit": int(rule_hit),
            "fallback": int(fallback),
            "positive": int(label_counts["positive"]),
            "negative": int(label_counts["negative"]),
            "neutral": int(label_counts["neutral"]),
            "mixed": int(label_counts["mixed"]),
            "unknown": int(label_counts["unknown"]),
            "label_counts_i18n": _label_counts_i18n_block(label_counts),
        },
        "base": args.date.strip(),
        "base_date": args.date.strip(),
    }

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_dated = ANALYSIS_DIR / f"sentiment_{args.date.strip()}.json"
    OUT_LATEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_dated.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _save_cache(cache)

    print("[OK] built sentiment")
    print(f"  news : {src_path}")
    print(f"  out  : {OUT_LATEST}")
    print(f"  dated: {out_dated}")
    print(f"  items={n} rule_hit={rule_hit} fallback={fallback}")
    print(
        "  labels="
        f"positive:{label_counts['positive']} "
        f"negative:{label_counts['negative']} "
        f"neutral:{label_counts['neutral']} "
        f"mixed:{label_counts['mixed']} "
        f"unknown:{label_counts['unknown']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
