
import argparse
import json
import re
from pathlib import Path

# v4 = quality patcher
# - does NOT retranslate everything
# - fixes common corruption patterns in existing description_i18n
# - can optionally retranslate only suspicious rows
# - never stops on one bad row

BAD_PATTERNS = [
    "サラWEEN", "Thiel", "マン Without Fear", "デッドプール：リブーン・アゲイン",
    "オバマ政権下", "スポーカー州知事", "ILLinois", "澳大利亚", "камео",
]

PROPER_NOUN_REPLACEMENTS_JA = {
    "サラWEEN": "サルウィン",
    "ピーター・ Thiel": "ピーター・ティール",
    "Thiel氏": "ティール氏",
    "マン Without Fear": "恐れを知らぬ男",
    "デッドプール：リブーン・アゲイン": "Daredevil: Born Again",
    "ILLinois": "イリノイ",
    "ऑबामा": "オバマ",
    "オバマ政権下": "大統領執務室だけでなく",
    "スポーカー州知事": "ユタ州知事スペンサー・コックス",
    "澳大利亚广播公司": "オーストラリア放送協会",
    "ジェフリー下院共和党代表": "下院少数党院内総務ハキーム・ジェフリーズ",
    "カシュミール活動家": "カシミールの活動家",
    "ジャムフルカシュミール": "ジャンムー・カシミール",
    "マシンの最後の戦い": "最後の戦い",
}

PROPER_NOUN_REPLACEMENTS_TH = {
    "Salween": "Salween",
    "ไทล์": "Peter Thiel",
    "แมน Without Fear": "Man Without Fear",
    "เดดพูล: บอร์น อะเกน": "Daredevil: Born Again",
    "อิมรอนखาน": "อิมราน ข่าน",
    "จิม คาร์เทอร์": "จิม เคอร์ติส",
    "ผู้ว่าราชการรัฐสเปน": "ผู้ว่าการรัฐยูทาห์ สเปนเซอร์ ค็อกซ์",
}

SUSPICIOUS_RE = re.compile(
    r"(サラWEEN|ピーター・\s+Thiel|マン Without Fear|デッドプール|ILLinois|澳大利亚|камео|อิมรอนखาน|ผู้ว่าราชการรัฐสเปน)",
    re.IGNORECASE
)

ASCII_LONG_RE = re.compile(r"[A-Za-z]{6,}")
WS_RE = re.compile(r"\s+")

def normalize_text(s: str) -> str:
    return WS_RE.sub(" ", (s or "")).strip()

def patch_lang(text: str, replacements: dict[str, str]) -> str:
    out = normalize_text(text)
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out

def is_suspicious(en: str, ja: str, th: str) -> bool:
    joined = f"{ja} || {th}"
    if SUSPICIOUS_RE.search(joined):
        return True
    # still too much English leakage in JA/TH
    if len(ASCII_LONG_RE.findall(ja)) >= 3:
        return True
    if len(ASCII_LONG_RE.findall(th)) >= 5:
        return True
    # copied English
    if normalize_text(ja) == normalize_text(en) or normalize_text(th) == normalize_text(en):
        return True
    return False

def soft_rewrite_from_en(en: str) -> tuple[str, str]:
    """
    Very light fallback, not full translation.
    Only used when the row is obviously broken and we want a safer short summary
    than leaving corrupted text.
    """
    en = normalize_text(en)
    if not en:
        return "", ""

    # keep short and safe
    short = en.split(".")[0].strip()
    if len(short) < 20:
        short = en[:140].strip()

    ja = f"この記事は次の内容を扱っています: {short}"
    th = f"บทความนี้กล่าวถึงเรื่องต่อไปนี้: {short}"
    return ja, th

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--safe-fallback", action="store_true",
                        help="Replace still-broken rows with safe EN-based summary wrappers")
    args = parser.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)

    data = json.loads(infile.read_text(encoding="utf-8"))

    patched = 0
    suspicious = 0
    safe_replaced = 0

    for item in data.get("items", []):
        block = item.get("description_i18n") or {}
        en = normalize_text(block.get("en", item.get("description", "")))
        ja = normalize_text(block.get("ja", ""))
        th = normalize_text(block.get("th", ""))

        new_ja = patch_lang(ja, PROPER_NOUN_REPLACEMENTS_JA)
        new_th = patch_lang(th, PROPER_NOUN_REPLACEMENTS_TH)

        changed = (new_ja != ja) or (new_th != th)
        if changed:
            patched += 1

        if is_suspicious(en, new_ja, new_th):
            suspicious += 1
            if args.safe_fallback:
                fb_ja, fb_th = soft_rewrite_from_en(en)
                new_ja, new_th = fb_ja, fb_th
                safe_replaced += 1

        item["description_i18n"] = {
            "en": en,
            "ja": new_ja,
            "th": new_th,
        }
        item["description_i18n_status_v4"] = (
            "safe_fallback" if args.safe_fallback and is_suspicious(en, new_ja, new_th) else
            "patched" if changed else
            "checked"
        )

    outfile.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {outfile}")
    print(f"[OK] patched rows: {patched}")
    print(f"[OK] suspicious rows: {suspicious}")
    print(f"[OK] safe fallback rows: {safe_replaced}")

if __name__ == "__main__":
    main()
