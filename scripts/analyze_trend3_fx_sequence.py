# scripts/analyze_trend3_fx_sequence.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
BT_DIR = REPO_ROOT / "analysis" / "prediction_backtests"

# correctness候補（よくある命名揺れ）
CORRECT_COL_CANDIDATES = [
    "correct",
    "is_correct",
    "ok",
    "hit",
    "win",
    "right",
    "success",
    "matched",
    "good",
]

# 0/1へ変換する際に「勝ち」を意味しがちな文字列
TRUE_STR = {"1", "true", "t", "yes", "y", "ok", "hit", "win", "right", "success"}
FALSE_STR = {"0", "false", "f", "no", "n", "ng", "miss", "lose", "loss", "wrong", "fail"}


def pick_latest(pattern: str) -> Path:
    files = sorted(BT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No CSV found under {BT_DIR} with pattern={pattern!r}")
    return files[0]


def _normalize_colname(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")


def _parse_to_01(x) -> Optional[int]:
    # NaN
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass

    # bool
    if isinstance(x, bool):
        return 1 if x else 0

    # numeric
    try:
        fx = float(x)
        if fx == 1.0:
            return 1
        if fx == 0.0:
            return 0
    except Exception:
        pass

    # string
    s = str(x).strip().lower()
    if s in TRUE_STR:
        return 1
    if s in FALSE_STR:
        return 0

    return None


def detect_correct_column(df: pd.DataFrame) -> Optional[str]:
    colmap = {c: _normalize_colname(c) for c in df.columns}
    inv = {}
    for orig, norm in colmap.items():
        inv.setdefault(norm, []).append(orig)

    # 1) 直接候補
    for cand in CORRECT_COL_CANDIDATES:
        if cand in inv:
            # 同名が複数あっても最初を採用
            return inv[cand][0]

    # 2) "correctness" のような部分一致
    for norm, origs in inv.items():
        if "correct" in norm or "correctness" in norm:
            return origs[0]
        if norm.endswith("_ok") or norm.startswith("ok_"):
            return origs[0]

    return None


@dataclass
class Streak:
    max_win: int
    max_loss: int
    win_range: Tuple[int, int]
    loss_range: Tuple[int, int]


def compute_streak(seq: List[int]) -> Streak:
    if not seq:
        return Streak(0, 0, (0, -1), (0, -1))

    max_w = 0
    max_l = 0
    w_range = (0, -1)
    l_range = (0, -1)

    cur = seq[0]
    length = 1
    start = 0

    for i in range(1, len(seq)):
        if seq[i] == cur:
            length += 1
        else:
            if cur == 1 and length > max_w:
                max_w = length
                w_range = (start, i - 1)
            if cur == 0 and length > max_l:
                max_l = length
                l_range = (start, i - 1)

            cur = seq[i]
            length = 1
            start = i

    # last run
    if cur == 1 and length > max_w:
        max_w = length
        w_range = (start, len(seq) - 1)
    if cur == 0 and length > max_l:
        max_l = length
        l_range = (start, len(seq) - 1)

    return Streak(max_w, max_l, w_range, l_range)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="trend3_fx_v2B_invert_*.csv")
    ap.add_argument("--show-columns", action="store_true", help="print CSV columns and exit")
    args = ap.parse_args()

    csv_path = pick_latest(args.pattern)
    df = pd.read_csv(csv_path)

    if args.show_columns:
        print("[COLUMNS]")
        print("csv:", csv_path)
        for c in df.columns:
            print(" -", c)
        return 0

    # date列は揺れるが、まずは最もありがちなものを探す
    date_col = None
    for cand in ["date", "day", "dt"]:
        for c in df.columns:
            if _normalize_colname(c) == cand:
                date_col = c
                break
        if date_col:
            break

    if date_col is None:
        # dateが無いなら index を疑似date扱い
        df["__date__"] = [str(i) for i in range(len(df))]
        date_col = "__date__"

    correct_col = detect_correct_column(df)

    if correct_col is None:
        print("[ERROR] Could not find a correctness column.")
        print("csv:", csv_path)
        print("available columns:")
        for c in df.columns:
            print(" -", c)
        print("")
        print("Tip: If your CSV uses another name (e.g. 'is_correct' / 'ok' / 'hit'),")
        print("this script should normally detect it. If not, tell me the column list above.")
        raise RuntimeError("correct column not found")

    # correct列を0/1へ（NaN除外）
    parsed: List[int] = []
    parsed_dates: List[str] = []

    for _, row in df.iterrows():
        v = _parse_to_01(row[correct_col])
        if v is None:
            continue
        parsed.append(int(v))
        parsed_dates.append(str(row[date_col]))

    if not parsed:
        raise RuntimeError(f"No usable trades after parsing {correct_col!r} into 0/1 (all NaN/unknown?)")

    streak = compute_streak(parsed)

    hit_rate = sum(parsed) / len(parsed)
    wl = "".join("W" if x == 1 else "L" for x in parsed)

    print("[SEQUENCE ANALYSIS]")
    print("csv:", csv_path)
    print("date_col:", date_col)
    print("correct_col:", correct_col)
    print("trades:", len(parsed))
    print("hit_rate:", hit_rate)
    print("W/L:", wl)
    print("")
    if streak.max_win > 0:
        print(
            "max_consecutive_wins:",
            streak.max_win,
            f"{parsed_dates[streak.win_range[0]]}..{parsed_dates[streak.win_range[1]]}",
        )
    else:
        print("max_consecutive_wins: 0")
    if streak.max_loss > 0:
        print(
            "max_consecutive_losses:",
            streak.max_loss,
            f"{parsed_dates[streak.loss_range[0]]}..{parsed_dates[streak.loss_range[1]]}",
        )
    else:
        print("max_consecutive_losses: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
