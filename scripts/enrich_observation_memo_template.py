from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime


ANALYSIS_DIR = Path("data/world_politics/analysis")
OBS_MD = Path("docs/observation.md")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_date(s: str) -> str | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d")
    except Exception:
        return s


def _find_daily_summary(date_str: str) -> Path | None:
    p = ANALYSIS_DIR / f"daily_summary_{date_str}.json"
    if p.exists():
        return p
    # fallback: latest (safety)
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)


def _extract_obs_block(md_text: str, date_str: str) -> tuple[str, str, str] | None:
    start = f"<!-- OBS:{date_str} -->"
    end = f"<!-- /OBS:{date_str} -->"
    if start not in md_text or end not in md_text:
        return None
    pre, rest = md_text.split(start, 1)
    mid, post = rest.split(end, 1)
    block = start + mid + end
    return pre, block, post


def _uniq(seq):
    seen = set()
    out = []
    for x in seq:
        if x is None:
            continue
        s = str(x).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _gather_candidates(doc: dict) -> dict:
    analog_tags = _uniq(doc.get("historical_analog_tags") or [])

    # union of matched_tags from top 3 analogs
    matched = []
    for a in (doc.get("historical_analogs") or [])[:3]:
        matched.extend(a.get("matched_tags") or [])
    matched_tags = _uniq(matched)

    top_domains = _uniq((doc.get("top_domains") or [])[:8])
    top_tokens = _uniq((doc.get("top_tokens") or [])[:10])

    anchors = doc.get("anchors")
    anchors_list = []
    if isinstance(anchors, list):
        anchors_list = [str(x) for x in anchors[:10]]
    elif isinstance(anchors, dict):
        # 形式が違う場合は空でOK
        anchors_list = []
    anchors_list = _uniq(anchors_list)

    return {
        "analog_tags": analog_tags,
        "matched_tags": matched_tags,
        "top_domains": top_domains,
        "top_tokens": top_tokens,
        "anchors": anchors_list,
    }


def _render_candidates_md(c: dict) -> str:
    def fmt_list(xs):
        if not xs:
            return "(none)"
        return "`" + ", ".join(xs) + "`"

    lines = []
    lines.append("**Auto candidates (semi-auto)**")
    lines.append("")
    lines.append(f"- analog_tags: {fmt_list(c['analog_tags'])}")
    lines.append(f"- matched_tags(top3): {fmt_list(c['matched_tags'])}")
    lines.append(f"- top_domains: {fmt_list(c['top_domains'])}")
    lines.append(f"- top_tokens: {fmt_list(c['top_tokens'])}")
    if c["anchors"]:
        lines.append(f"- anchors(sample): {fmt_list(c['anchors'])}")
    lines.append("")
    lines.append("> Use these as hints only. Keep/Remove after your review.")
    lines.append("")
    return "\n".join(lines)


def _upsert_candidates_into_memo(block: str, candidates_md: str) -> str:
    """
    Inside MEMO3 section, replace the candidate sub-block.
    Idempotent markers:
      <!-- CAND_START --> ... <!-- CAND_END -->
    """
    mstart = "<!-- MEMO3_START -->"
    mend = "<!-- MEMO3_END -->"
    cstart = "<!-- CAND_START -->"
    cend = "<!-- CAND_END -->"

    if mstart not in block or mend not in block:
        return block  # nothing to do

    # locate MEMO3 payload region
    pre, rest = block.split(mstart, 1)
    memo_body, post = rest.split(mend, 1)

    # decide insertion point: after "**Why these analogs today (template)**"
    key = "**Why these analogs today (template)**"
    if key not in memo_body:
        # fallback: append to end of memo_body
        new_memo = memo_body.rstrip() + "\n\n" + cstart + "\n" + candidates_md + "\n" + cend + "\n"
        return pre + mstart + new_memo + "\n" + mend + post

    head, tail = memo_body.split(key, 1)
    # rebuild tail with candidates inserted just after key line
    after_key = key + "\n\n"

    # remove existing candidate block if present
    if cstart in tail and cend in tail:
        tpre = tail.split(cstart, 1)[0]
        tpost = tail.split(cend, 1)[1]
        tail = tpre.rstrip() + "\n\n" + tpost.lstrip()

    cand_block = cstart + "\n" + candidates_md + "\n" + cend + "\n\n"

    new_tail = after_key + cand_block + tail.lstrip()
    new_memo = head + new_tail
    return pre + mstart + new_memo + mend + post


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    date_str = _normalize_date(args.date)
    if not date_str:
        print("[ERR] invalid --date")
        return

    if not OBS_MD.exists():
        print(f"[ERR] {OBS_MD} not found. Run D-2/D-3 first.")
        return

    ds = _find_daily_summary(date_str)
    if not ds:
        print("[ERR] no daily_summary found")
        return

    doc = _read_json(ds)
    c = _gather_candidates(doc)
    candidates_md = _render_candidates_md(c)

    md = OBS_MD.read_text(encoding="utf-8")
    parts = _extract_obs_block(md, date_str)
    if not parts:
        print(f"[ERR] OBS block for {date_str} not found. Run D-2 for that date.")
        return

    pre, block, post = parts
    new_block = _upsert_candidates_into_memo(block, candidates_md)
    OBS_MD.write_text(pre + new_block + post, encoding="utf-8")

    print(f"[OK] inserted candidates into MEMO3 for {date_str} (source: {ds.name})")


if __name__ == "__main__":
    main()
