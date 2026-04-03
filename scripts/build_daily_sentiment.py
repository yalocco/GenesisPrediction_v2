
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

THEME_LABELS: Dict[str, Dict[str, str]] = {
    "middle_east": {"en": "middle_east", "ja": "中東", "th": "ตะวันออกกลาง"},
    "ukraine_russia": {"en": "ukraine_russia", "ja": "ウクライナ・ロシア", "th": "ยูเครน-รัสเซีย"},
    "china_taiwan": {"en": "china_taiwan", "ja": "中国・台湾", "th": "จีน-ไต้หวัน"},
    "us_policy": {"en": "us_policy", "ja": "米国政策", "th": "นโยบายสหรัฐฯ"},
    "europe_policy": {"en": "europe_policy", "ja": "欧州政策", "th": "นโยบายยุโรป"},
    "energy": {"en": "energy", "ja": "エネルギー", "th": "พลังงาน"},
    "inflation_rates": {"en": "inflation_rates", "ja": "インフレ・金利", "th": "เงินเฟ้อ-ดอกเบี้ย"},
    "trade_supply_chain": {"en": "trade_supply_chain", "ja": "貿易・供給網", "th": "การค้า-ห่วงโซ่อุปทาน"},
    "market_financials": {"en": "market_financials", "ja": "市場・金融", "th": "ตลาด-การเงิน"},
    "food_agriculture": {"en": "food_agriculture", "ja": "食料・農業", "th": "อาหาร-เกษตร"},
    "technology_ai": {"en": "technology_ai", "ja": "技術・AI", "th": "เทคโนโลยี-AI"},
    "social_politics": {"en": "social_politics", "ja": "社会・政治文化", "th": "สังคม-การเมืองวัฒนธรรม"},
    "religion_values": {"en": "religion_values", "ja": "宗教・価値観", "th": "ศาสนา-คุณค่า"},
    "sports_entertainment": {"en": "sports_entertainment", "ja": "スポーツ・娯楽", "th": "กีฬา-บันเทิง"},
    "human_rights": {"en": "human_rights", "ja": "人権", "th": "สิทธิมนุษยชน"},
    "space_science": {"en": "space_science", "ja": "宇宙・科学", "th": "อวกาศ-วิทยาศาสตร์"},
    "general": {"en": "general", "ja": "一般", "th": "ทั่วไป"},
}

SIGNAL_LABELS: Dict[str, Dict[str, str]] = {
    "geopolitics": {"en": "geopolitics", "ja": "地政学", "th": "ภูมิรัฐศาสตร์"},
    "policy_shift": {"en": "policy_shift", "ja": "政策変化", "th": "การเปลี่ยนนโยบาย"},
    "monetary_policy": {"en": "monetary_policy", "ja": "金融政策", "th": "นโยบายการเงิน"},
    "market_stress": {"en": "market_stress", "ja": "市場ストレス", "th": "ความตึงเครียดตลาด"},
    "energy_shock": {"en": "energy_shock", "ja": "エネルギーショック", "th": "ช็อกพลังงาน"},
    "trade_disruption": {"en": "trade_disruption", "ja": "貿易混乱", "th": "การหยุดชะงักทางการค้า"},
    "food_price_pressure": {"en": "food_price_pressure", "ja": "食料価格圧力", "th": "แรงกดดันราคาอาหาร"},
    "social_instability": {"en": "social_instability", "ja": "社会不安定", "th": "ความไม่มั่นคงทางสังคม"},
    "technology_competition": {"en": "technology_competition", "ja": "技術競争", "th": "การแข่งขันเทคโนโลยี"},
    "human_rights_pressure": {"en": "human_rights_pressure", "ja": "人権圧力", "th": "แรงกดดันด้านสิทธิมนุษยชน"},
    "cultural_signal": {"en": "cultural_signal", "ja": "文化シグナル", "th": "สัญญาณทางวัฒนธรรม"},
    "general": {"en": "general", "ja": "一般", "th": "ทั่วไป"},
}

RISK_DRIVER_LABELS: Dict[str, Dict[str, str]] = {
    "military_escalation": {"en": "military_escalation", "ja": "軍事的エスカレーション", "th": "การยกระดับทางทหาร"},
    "policy_uncertainty": {"en": "policy_uncertainty", "ja": "政策不確実性", "th": "ความไม่แน่นอนของนโยบาย"},
    "market_fragility": {"en": "market_fragility", "ja": "市場の脆弱性", "th": "ความเปราะบางของตลาด"},
    "energy_supply_risk": {"en": "energy_supply_risk", "ja": "エネルギー供給リスク", "th": "ความเสี่ยงด้านพลังงาน"},
    "social_unrest": {"en": "social_unrest", "ja": "社会不安", "th": "ความไม่สงบทางสังคม"},
    "general": {"en": "general", "ja": "一般", "th": "ทั่วไป"},
}

IMPACT_LABELS: Dict[str, Dict[str, str]] = {
    "inflation_up": {"en": "inflation_up", "ja": "インフレ上昇", "th": "เงินเฟ้อเพิ่มขึ้น"},
    "risk_off": {"en": "risk_off", "ja": "リスクオフ", "th": "หลีกเลี่ยงความเสี่ยง"},
    "supply_disruption": {"en": "supply_disruption", "ja": "供給混乱", "th": "การหยุดชะงักของอุปทาน"},
    "growth_down": {"en": "growth_down", "ja": "成長鈍化", "th": "การเติบโตชะลอลง"},
    "policy_repricing": {"en": "policy_repricing", "ja": "政策再評価", "th": "การประเมินนโยบายใหม่"},
    "energy_cost_up": {"en": "energy_cost_up", "ja": "エネルギーコスト上昇", "th": "ต้นทุนพลังงานสูงขึ้น"},
    "market_volatility": {"en": "market_volatility", "ja": "市場変動性", "th": "ความผันผวนของตลาด"},
    "general": {"en": "general", "ja": "一般", "th": "ทั่วไป"},
}

THEME_RULES: List[tuple[str, List[str]]] = [
    ("middle_east", ["iran", "israel", "gaza", "hormuz", "tehran", "hezbollah", "lebanon", "middle east"]),
    ("ukraine_russia", ["ukraine", "russia", "moscow", "kyiv", "putin"]),
    ("china_taiwan", ["china", "taiwan", "beijing", "south china sea", "pla"]),
    ("us_policy", ["trump", "congress", "white house", "senate", "house", "u.s.", "us ", "american policy"]),
    ("europe_policy", ["eu", "european union", "lords", "parliament", "religious freedom"]),
    ("energy", ["oil", "gas", "energy", "fuel", "lng", "barrel"]),
    ("inflation_rates", ["inflation", "interest rate", "rates", "yield", "fed", "ecb", "boj"]),
    ("trade_supply_chain", ["tariff", "sanction", "shipping", "supply chain", "export", "import", "trade"]),
    ("market_financials", ["market", "stocks", "equity", "bond", "liquidity", "bank", "credit", "financial"]),
    ("food_agriculture", ["fertilizer", "grain", "food", "harvest", "crop", "agriculture"]),
    ("technology_ai", ["ai", "artificial intelligence", "streaming", "apple", "netflix", "hbo", "tech"]),
    ("social_politics", ["cpac", "campaign", "activism", "misinformation", "election", "political campaigns"]),
    ("religion_values", ["jesus", "christian", "church", "religious", "faith"]),
    ("sports_entertainment", ["eurovision", "festival", "tour", "film festival", "webby", "sports", "band", "disney"]),
    ("human_rights", ["human rights", "transgender", "service members", "rights campaign"]),
    ("space_science", ["lunar", "space", "democracies", "science"]),
]

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


def _list_i18n_block(values: List[str], mapping: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    cleaned = [_normalize_text(v).lower() for v in values if _normalize_text(v)]
    en: List[str] = []
    ja: List[str] = []
    th: List[str] = []
    for key in cleaned:
        mapped = mapping.get(key)
        if mapped:
            en.append(mapped["en"])
            ja.append(mapped["ja"])
            th.append(mapped["th"])
        else:
            en.append(key)
            ja.append(key)
            th.append(key)
    return {"en": en, "ja": ja, "th": th}


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


def _extract_theme_tags(title: str, desc: str, source: str = "") -> List[str]:
    text = " ".join(x for x in [title, desc, source] if x).lower()
    tags: List[str] = []
    for theme, keywords in THEME_RULES:
        if any(keyword in text for keyword in keywords):
            tags.append(theme)
    if not tags:
        tags.append("general")
    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)
    return deduped[:6]


def _extract_signal_tags(title: str, desc: str, theme_tags: List[str]) -> List[str]:
    text = " ".join(x for x in [title, desc] if x).lower()
    tags: List[str] = []

    if any(t in theme_tags for t in ["middle_east", "ukraine_russia", "china_taiwan"]):
        tags.append("geopolitics")
    if any(t in theme_tags for t in ["us_policy", "europe_policy", "social_politics"]):
        tags.append("policy_shift")
    if "fed" in text or "ecb" in text or "boj" in text or "interest rate" in text or "rates" in text:
        tags.append("monetary_policy")
    if any(t in theme_tags for t in ["market_financials", "inflation_rates"]) or any(k in text for k in ["bank", "credit", "bond", "equity", "liquidity", "market"]):
        tags.append("market_stress")
    if "oil" in text or "gas" in text or "lng" in text or "fuel" in text or "energy" in text:
        tags.append("energy_shock")
    if any(k in text for k in ["tariff", "sanction", "shipping", "supply chain", "export", "import", "trade"]):
        tags.append("trade_disruption")
    if any(k in text for k in ["fertilizer", "grain", "food", "crop", "harvest", "agriculture"]):
        tags.append("food_price_pressure")
    if any(k in text for k in ["protest", "activism", "misinformation", "civil conflict", "shutdown"]):
        tags.append("social_instability")
    if any(t in theme_tags for t in ["technology_ai"]) or any(k in text for k in ["ai", "technology", "streaming", "apple", "netflix", "hbo"]):
        tags.append("technology_competition")
    if any(t in theme_tags for t in ["human_rights"]) or any(k in text for k in ["human rights", "transgender", "rights campaign"]):
        tags.append("human_rights_pressure")
    if any(t in theme_tags for t in ["sports_entertainment", "religion_values"]) or any(k in text for k in ["festival", "tour", "film", "music", "faith", "jesus"]):
        tags.append("cultural_signal")

    if not tags:
        tags.append("general")

    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)
    return deduped[:6]


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

def _extract_risk_drivers(title: str, desc: str, signal_tags: List[str]) -> List[str]:
    text = " ".join(x for x in [title, desc] if x).lower()
    tags: List[str] = []
    if any(k in text for k in ["attack", "strike", "missile", "war", "military", "retaliation"]):
        tags.append("military_escalation")
    if any(k in text for k in ["policy", "uncertain", "uncertainty", "election", "tariff", "warning"]):
        tags.append("policy_uncertainty")
    if "market_stress" in signal_tags or any(k in text for k in ["bank", "liquidity", "crisis", "credit", "bond"]):
        tags.append("market_fragility")
    if "energy_shock" in signal_tags or any(k in text for k in ["oil", "gas", "energy", "supply", "hormuz"]):
        tags.append("energy_supply_risk")
    if "social_instability" in signal_tags or any(k in text for k in ["protest", "riot", "unrest", "crackdown"]):
        tags.append("social_unrest")
    if not tags:
        tags.append("general")
    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)
    return deduped[:6]

def _extract_impact_tags(title: str, desc: str, theme_tags: List[str], signal_tags: List[str], risk_drivers: List[str]) -> List[str]:
    text = " ".join(x for x in [title, desc] if x).lower()
    tags: List[str] = []
    if any(k in text for k in ["inflation", "price", "prices", "cost", "fertilizer", "food"]) or "food_price_pressure" in signal_tags:
        tags.append("inflation_up")
    if any(d in risk_drivers for d in ["military_escalation", "market_fragility"]) or any(k in text for k in ["panic", "shock", "uncertainty", "volatility"]):
        tags.append("risk_off")
    if "trade_disruption" in signal_tags or any(k in text for k in ["shipping", "supply chain", "shortage", "export", "import"]):
        tags.append("supply_disruption")
    if any(k in text for k in ["recession", "decline", "slump", "growth", "slowdown", "collapse"]):
        tags.append("growth_down")
    if any(d in risk_drivers for d in ["policy_uncertainty"]) or any(k in text for k in ["policy", "tariff", "sanction", "election", "fed", "ecb", "boj"]):
        tags.append("policy_repricing")
    if "energy_shock" in signal_tags or "energy_supply_risk" in risk_drivers or any(k in text for k in ["oil", "gas", "energy", "fuel"]):
        tags.append("energy_cost_up")
    if "market_stress" in signal_tags or any(k in text for k in ["market", "equity", "bond", "bank", "credit", "liquidity"]):
        tags.append("market_volatility")
    if not tags:
        tags.append("general")
    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)
    return deduped[:6]

def _aggregate_tag_counts(items: List[Dict[str, Any]], field_name: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        for tag in item.get(field_name, []) if isinstance(item.get(field_name), list) else []:
            key = _normalize_text(tag).lower()
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

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
            theme_tags = _extract_theme_tags(title, description, source)
            signal_tags = _extract_signal_tags(title, description, theme_tags)
            risk_drivers = _extract_risk_drivers(title, description, signal_tags)
            impact_tags = _extract_impact_tags(title, description, theme_tags, signal_tags, risk_drivers)

            if score.method == "lex":
                rule_hit += 1
            else:
                fallback += 1

            sentiment_i18n = _label_i18n_block(label, SENTIMENT_LABELS)
            method_i18n = _label_i18n_block(score.method, METHOD_LABELS)
            theme_tags_i18n = _list_i18n_block(theme_tags, THEME_LABELS)
            signal_tags_i18n = _list_i18n_block(signal_tags, SIGNAL_LABELS)
            risk_drivers_i18n = _list_i18n_block(risk_drivers, RISK_DRIVER_LABELS)
            impact_tags_i18n = _list_i18n_block(impact_tags, IMPACT_LABELS)
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
                "theme_tags": theme_tags,
                "theme_tags_i18n": theme_tags_i18n,
                "signal_tags": signal_tags,
                "signal_tags_i18n": signal_tags_i18n,
                "risk_drivers": risk_drivers,
                "risk_drivers_i18n": risk_drivers_i18n,
                "impact_tags": impact_tags,
                "impact_tags_i18n": impact_tags_i18n,
            })

    n = len(out_items)
    avg_risk = sum(x["risk"] for x in out_items) / n if n else 0.0
    avg_pos = sum(x["positive"] for x in out_items) / n if n else 0.0
    avg_unc = sum(x["uncertainty"] for x in out_items) / n if n else 0.0
    avg_net = sum(x["net"] for x in out_items) / n if n else 0.0

    label_counts = _label_counts(out_items)
    theme_counts = _aggregate_tag_counts(out_items, "theme_tags")
    signal_counts = _aggregate_tag_counts(out_items, "signal_tags")
    risk_driver_counts = _aggregate_tag_counts(out_items, "risk_drivers")
    impact_counts = _aggregate_tag_counts(out_items, "impact_tags")
    top_theme_tags = list(theme_counts.keys())[:5]
    top_signal_tags = list(signal_counts.keys())[:5]
    top_risk_drivers = list(risk_driver_counts.keys())[:5]
    top_impact_tags = list(impact_counts.keys())[:5]
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
            "theme_counts": theme_counts,
            "top_theme_tags": top_theme_tags,
            "top_theme_tags_i18n": _list_i18n_block(top_theme_tags, THEME_LABELS),
            "signal_counts": signal_counts,
            "top_signal_tags": top_signal_tags,
            "top_signal_tags_i18n": _list_i18n_block(top_signal_tags, SIGNAL_LABELS),
            "risk_driver_counts": risk_driver_counts,
            "top_risk_drivers": top_risk_drivers,
            "top_risk_drivers_i18n": _list_i18n_block(top_risk_drivers, RISK_DRIVER_LABELS),
            "impact_counts": impact_counts,
            "top_impact_tags": top_impact_tags,
            "top_impact_tags_i18n": _list_i18n_block(top_impact_tags, IMPACT_LABELS),
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
            "theme_counts": theme_counts,
            "top_theme_tags": top_theme_tags,
            "top_theme_tags_i18n": _list_i18n_block(top_theme_tags, THEME_LABELS),
            "signal_counts": signal_counts,
            "top_signal_tags": top_signal_tags,
            "top_signal_tags_i18n": _list_i18n_block(top_signal_tags, SIGNAL_LABELS),
            "risk_driver_counts": risk_driver_counts,
            "top_risk_drivers": top_risk_drivers,
            "top_risk_drivers_i18n": _list_i18n_block(top_risk_drivers, RISK_DRIVER_LABELS),
            "impact_counts": impact_counts,
            "top_impact_tags": top_impact_tags,
            "top_impact_tags_i18n": _list_i18n_block(top_impact_tags, IMPACT_LABELS),
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
    print(f"  themes={top_theme_tags}")
    print(f"  signals={top_signal_tags}")
    print(f"  risk_drivers={top_risk_drivers}")
    print(f"  impacts={top_impact_tags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
