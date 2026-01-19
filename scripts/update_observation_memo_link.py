from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime


OBS_MD = Path("docs/observation.md")


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


def _extract_obs_block(md_text: str, date_str: str) -> tuple[str, str, str] | None:
    """
    Returns (pre, block, post) if date block exists, else None
    """
    start = f"<!-- OBS:{date_str} -->"
    end = f"<!-- /OBS:{date_str} -->"
    if start not in md_text or end not in md_text:
        return None
    pre, rest = md_text.split(start, 1)
    block, post = rest.split(end, 1)
    block = start + block + end
    return pre, block, post


def _upsert_memo_section(block: str, memo_lines: list[str]) -> str:
    """
    Insert or replace the "3-line memo" section inside a single OBS block.
    Uses internal markers to be idempotent.
    """
    mstart = "<!-- MEMO3_START -->"
    mend = "<!-- MEMO3_END -->"

    # sanitize memo: keep at most 3 lines, strip bullets/whitespace
    clean = []
    for ln in memo_lines[:3]:
        ln = ln.strip()
        if ln.startswith(("-", "•", "*")):
            ln = ln.lstrip("-•* ").strip()
        clean.append(ln)
    while len(clean) < 3:
        clean.append("(blank)")

    memo_md = []
    memo_md.append("### 3-line memo × analog mapping")
    memo_md.append("")
    memo_md.append("**Today’s 3-line memo (human)**")
    memo_md.append("")
    memo_md.append(f"- 1) {clean[0]}")
    memo_md.append(f"- 2) {clean[1]}")
    memo_md.append(f"- 3) {clean[2]}")
    memo_md.append("")
    memo_md.append("**Why these analogs today (template)**")
    memo_md.append("")
    memo_md.append("- Anchor overlap:")
    memo_md.append("  - (Which tags / domains / themes in today’s news match the analog tags?)")
    memo_md.append("- Regime/context:")
    memo_md.append("  - (Which macro regime signals are consistent with the analog summaries?)")
    memo_md.append("- What to watch next:")
    memo_md.append("  - (1–3 concrete indicators to monitor tomorrow)")
    memo_md.append("")
    memo_md.append("> Notes: This section is intentionally conservative. Replace placeholders after your review.")
    memo_md.append("")

    payload = mstart + "\n" + "\n".join(memo_md) + "\n" + mend

    if mstart in block and mend in block:
        # replace existing memo section
        pre = block.split(mstart, 1)[0]
        post = block.split(mend, 1)[1]
        pre = pre.rstrip() + "\n\n"
        post = post.lstrip()
        return pre + payload + "\n" + post
    else:
        # insert before end marker
        end_marker = "<!-- /OBS:"
        idx = block.rfind(end_marker)
        if idx == -1:
            # fallback: append
            return block.rstrip() + "\n\n" + payload + "\n"
        head = block[:idx].rstrip() + "\n\n"
        tail = block[idx:].lstrip()
        return head + payload + "\n" + tail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD (required)")
    parser.add_argument("--memo", default="", help="Memo text with 1-3 lines separated by \\n")
    args = parser.parse_args()

    date_str = _normalize_date(args.date)
    if not date_str:
        print("[ERR] invalid --date")
        return

    if not OBS_MD.exists():
        print(f"[ERR] {OBS_MD} not found. Run D-2 first.")
        return

    memo_raw = args.memo.replace("\\n", "\n")
    memo_lines = [ln for ln in memo_raw.splitlines() if ln.strip()]

    if not memo_lines:
        print("[ERR] --memo is empty. Provide 1-3 lines. Example: --memo \"a\\nb\\nc\"")
        return

    md = OBS_MD.read_text(encoding="utf-8")
    parts = _extract_obs_block(md, date_str)
    if not parts:
        print(f"[ERR] OBS block for {date_str} not found in {OBS_MD}. Run D-2 for that date.")
        return

    pre, block, post = parts
    new_block = _upsert_memo_section(block, memo_lines)
    new_md = pre + new_block + post
    OBS_MD.write_text(new_md, encoding="utf-8")

    print(f"[OK] upserted 3-line memo mapping into {OBS_MD} for {date_str}")


if __name__ == "__main__":
    main()
