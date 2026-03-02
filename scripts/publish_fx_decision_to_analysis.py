#!/usr/bin/env python3
# scripts/publish_fx_decision_to_analysis.py
"""
GenesisPrediction v2 - Publish FX "decision" JSON(s) into analysis/fx/

目的（GUI安定化フェーズ3 / Overlay判断UI）
- Overlay UI が参照できる「ON/WARN/OFF」のテキスト情報を JSON として analysis/ に置く
- GUI側で計算しない（SSTは生成側）
- 入力が無い/列が無い場合も壊さない（"--" を出す）
- 既存の生成物（CSVダッシュボード等）から「最もそれっぽい列」を自動検出して採用

出力（例）
analysis/fx/fx_decision_latest_jpythb.json
analysis/fx/fx_decision_2026-02-27_jpythb.json

JSON スキーマ（最小）
{
  "pair": "jpythb",
  "state": "WARN",        // ON | WARN | OFF | --
  "reason": "....",       // 可能なら
  "as_of": "2026-02-27",  // 可能なら
  "source": "data/fx/....csv"
}

使い方
  python scripts/publish_fx_decision_to_analysis.py
  python scripts/publish_fx_decision_to_analysis.py --pair usdjpy
  python scripts/publish_fx_decision_to_analysis.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Helpers
# -----------------------------

def repo_root() -> Path:
    # scripts/ の1つ上をROOTとする
    return Path(__file__).resolve().parents[1]

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def upper_clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).upper()

def guess_pair_from_name(name: str) -> Optional[str]:
    # usdjpy / usdthb / jpythb などを推測
    m = re.search(r"(jpythb|usdjpy|usdthb)", name.lower())
    return m.group(1) if m else None

def pick_first_existing(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists() and p.is_file():
            return p
    return None

def normalize_state(x: Optional[str]) -> str:
    if not x:
        return "--"
    s = upper_clean(x)
    # よくある揺れの吸収
    if s in {"ON", "BUY", "GO", "SEND", "YES", "OK"}:
        return "ON"
    if s in {"WARN", "WARNING", "HOLD", "CAUTION"}:
        return "WARN"
    if s in {"OFF", "STOP", "NO", "SKIP", "DONT", "DON'T"}:
        return "OFF"
    # すでに ON/WARN/OFF っぽい
    if "WARN" in s:
        return "WARN"
    if "OFF" in s or "STOP" in s:
        return "OFF"
    if "ON" in s or "OK" in s:
        return "ON"
    return "--"


@dataclass
class Decision:
    pair: str
    state: str
    reason: str
    as_of: str
    source: str


def choose_columns(headers: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    汎用CSVから state/reason/as_of の列を推測して返す。
    """
    # 大文字化して比較
    H = {h: upper_clean(h) for h in headers}

    # state候補（優先順）
    state_keys = [
        "STATE", "STATUS", "DECISION", "ACTION", "SIGNAL", "MODE", "REMittance_action".upper(), "REMITTANCE_ACTION",
        "REMIT", "SEND_ACTION", "FX_ACTION"
    ]

    # reason候補
    reason_keys = [
        "REASON", "WHY", "NOTE", "MESSAGE", "COMMENT", "SUMMARY", "DETAIL", "DESC", "DESCRIPTION"
    ]

    # as_of候補
    asof_keys = [
        "AS_OF", "ASOF", "DATE", "DAY", "TODAY", "UPDATED_AT", "GENERATED_AT", "TIMESTAMP"
    ]

    def find_key(candidates: List[str]) -> Optional[str]:
        for want in candidates:
            for raw, up in H.items():
                if up == want:
                    return raw
        # 部分一致も許容（例: decision_state, action_today など）
        for want in candidates:
            for raw, up in H.items():
                if want in up:
                    return raw
        return None

    return find_key(state_keys), find_key(reason_keys), find_key(asof_keys)


def pick_latest_row(rows: List[Dict[str, str]], asof_col: Optional[str]) -> Dict[str, str]:
    """
    最終行を基本とするが、asof_col があれば、日付っぽい値で最大を選ぶ。
    """
    if not rows:
        return {}

    if not asof_col or asof_col not in rows[0]:
        return rows[-1]

    def parse_dt(v: str) -> Tuple[int, int, int]:
        s = v.strip()
        m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
        if not m:
            return (0, 0, 0)
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return (y, mo, d)

    best = rows[-1]
    best_dt = parse_dt(best.get(asof_col, ""))
    for r in rows:
        dt = parse_dt(r.get(asof_col, ""))
        if dt > best_dt:
            best = r
            best_dt = dt
    return best


def find_dashboard_csvs(root: Path) -> List[Path]:
    """
    data/fx/ 配下にある “それっぽい” CSV を集める。
    """
    data_fx = root / "data" / "fx"
    if not data_fx.exists():
        return []
    # よくある命名を広く拾う（remittance/dashboard/decision 等）
    patterns = [
        "*remittance*dashboard*.csv",
        "*dashboard*.csv",
        "*decision*.csv",
        "*remittance*.csv",
    ]
    found: List[Path] = []
    for pat in patterns:
        found.extend(sorted(data_fx.glob(pat)))
    # 重複排除（順序保持）
    uniq: List[Path] = []
    seen = set()
    for p in found:
        if p.resolve() not in seen:
            uniq.append(p)
            seen.add(p.resolve())
    return uniq


def compute_decision_for_pair(pair: str, root: Path) -> Decision:
    """
    指定pairの decision を CSV群から推測して作る。
    入力が無ければ '--' を返す（壊さない）
    """
    csvs = find_dashboard_csvs(root)

    # pairを含むCSVを優先
    pair_csvs = [p for p in csvs if pair in p.name.lower()]
    candidates = pair_csvs + [p for p in csvs if p not in pair_csvs]

    src = pick_first_existing(candidates)
    if not src:
        return Decision(pair=pair, state="--", reason="--", as_of="--", source="(no csv found)")

    try:
        rows = read_csv_rows(src)
        if not rows:
            return Decision(pair=pair, state="--", reason="--", as_of="--", source=str(src))
        headers = list(rows[0].keys())
        state_col, reason_col, asof_col = choose_columns(headers)
        row = pick_latest_row(rows, asof_col)

        state = normalize_state(row.get(state_col, "") if state_col else "")
        reason = (row.get(reason_col, "").strip() if reason_col else "").strip() or "--"
        as_of = (row.get(asof_col, "").strip() if asof_col else "").strip() or "--"

        # as_of が無い場合は今日を埋めるのはやめる（SSTにない情報を創らない）
        return Decision(pair=pair, state=state, reason=reason, as_of=as_of, source=str(src))

    except Exception as e:
        return Decision(pair=pair, state="--", reason=f"ERROR reading csv: {e}", as_of="--", source=str(src))


def write_json(dec: Decision, out_dir: Path, dry_run: bool) -> List[Path]:
    """
    latest + date-stamped（as_of が YYYY-MM-DD なら）の2種を出す
    """
    ensure_dir(out_dir)
    payload = {
        "pair": dec.pair,
        "state": dec.state,
        "reason": dec.reason,
        "as_of": dec.as_of,
        "source": dec.source,
    }

    outs: List[Path] = []
    latest = out_dir / f"fx_decision_latest_{dec.pair}.json"
    outs.append(latest)

    asof = dec.as_of.strip()
    stamped = None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", asof):
        stamped = out_dir / f"fx_decision_{asof}_{dec.pair}.json"
        outs.append(stamped)

    if dry_run:
        return outs

    for p in outs:
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return outs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="", help="jpythb / usdjpy / usdthb (empty=all)")
    ap.add_argument("--dry-run", action="store_true", help="do not write files")
    args = ap.parse_args()

    root = repo_root()
    out_dir = root / "analysis" / "fx"

    pairs = ["jpythb", "usdjpy", "usdthb"]
    if args.pair.strip():
        p = args.pair.strip().lower()
        if p not in pairs:
            print(f"[WARN] unknown pair '{p}', allowed: {pairs}")
            pairs = [p]
        else:
            pairs = [p]

    wrote_any = False
    for pair in pairs:
        dec = compute_decision_for_pair(pair, root)
        outs = write_json(dec, out_dir, args.dry_run)
        wrote_any = True
        print(f"[OK] {pair}: state={dec.state} as_of={dec.as_of} -> " + ", ".join(str(p) for p in outs))

    if not wrote_any:
        print("[WARN] nothing to do")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
