# scripts/run_scenarios.py
# Usage:
#   python scripts/run_scenarios.py --diff data/world_politics/analysis/diff_2025-12-28.json
#   python scripts/run_scenarios.py --latest

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "configs" / "scenarios"
DEFAULT_ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def find_latest_diff(analysis_dir: Path) -> Path:
    # diff_YYYY-MM-DD.json を最新日付で選ぶ（なければ更新日時で fallback）
    diffs = list(analysis_dir.glob("diff_*.json"))
    if not diffs:
        raise FileNotFoundError(f"No diff_*.json found in: {analysis_dir}")

    def key(p: Path):
        stem = p.stem  # diff_YYYY-MM-DD
        parts = stem.split("_", 1)
        if len(parts) == 2:
            date_str = parts[1]
            return (date_str, p.stat().st_mtime)
        return ("", p.stat().st_mtime)

    diffs.sort(key=key, reverse=True)
    return diffs[0]


def load_scenarios(scenario_dir: Path) -> list[dict]:
    scenarios: list[dict] = []
    for p in sorted(scenario_dir.glob("sc_*.json")):
        try:
            scenarios.append(load_json(p))
        except Exception as e:
            raise RuntimeError(f"Failed to load scenario: {p} ({e})")
    return scenarios


def get_candidates(diff_doc: dict) -> list[dict]:
    ext = diff_doc.get("extensions") or {}
    return ext.get("signal_candidates") or []


def ensure_min_candidates(diff_doc: dict) -> None:
    """
    extensions.signal_candidates を補完する（diffファイルは変更しない）。
    既存の candidate を尊重しつつ、最低2種類（novelty / persistence）を揃える。
    """
    ext = diff_doc.setdefault("extensions", {})
    candidates = ext.setdefault("signal_candidates", [])

    existing_ids = {c.get("id") for c in candidates if isinstance(c, dict)}

    ev = diff_doc.get("event_level") or {}
    added = ev.get("added") or []
    removed = ev.get("removed") or []
    added_n = len(added)
    removed_n = len(removed)

    meta = diff_doc.get("meta") or {}
    date = meta.get("date")
    baseline = meta.get("baseline_date")

    def clamp01(x: float) -> float:
        return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

    novelty_sev = clamp01(added_n / 20.0)
    novelty_conf = 0.55 if added_n >= 5 else 0.35

    persist_sev = clamp01(removed_n / 20.0)
    persist_conf = 0.55 if removed_n >= 5 else 0.35

    if "sig_novelty_up" not in existing_ids:
        candidates.append(
            {
                "id": "sig_novelty_up",
                "label": "Novelty up / more new items",
                "kind": "volume",
                "severity": novelty_sev,
                "confidence": novelty_conf,
                "evidence": {
                    "refs": ["event_level.added"],
                    "metrics": {"added_count": added_n, "date": date, "baseline_date": baseline},
                },
                "explain": f"新規（added）が{added_n}件。新しい話題が増えている兆候。",
            }
        )

    if "sig_persistence_down" not in existing_ids:
        candidates.append(
            {
                "id": "sig_persistence_down",
                "label": "Persistence down / more removed items",
                "kind": "volume",
                "severity": persist_sev,
                "confidence": persist_conf,
                "evidence": {
                    "refs": ["event_level.removed"],
                    "metrics": {"removed_count": removed_n, "date": date, "baseline_date": baseline},
                },
                "explain": f"削除（removed）が{removed_n}件。継続して残る記事が減っている兆候。",
            }
        )


def match_scenario(candidate: dict, scenario: dict) -> bool:
    m = scenario.get("match") or {}

    sev = float(candidate.get("severity", 0.0))
    conf = float(candidate.get("confidence", 0.0))
    min_sev = float(m.get("min_severity", 0.0))
    min_conf = float(m.get("min_confidence", 0.0))

    return (sev >= min_sev) and (conf >= min_conf)


def build_prediction(diff_doc: dict, candidate: dict, scenario: dict) -> dict:
    meta = diff_doc.get("meta") or {}

    # シナリオIDは scenario_id 優先（無ければ id）
    sid = scenario.get("scenario_id") or scenario.get("id") or "unknown"

    pred = scenario.get("prediction") or {}
    title = pred.get("title") or scenario.get("label") or sid

    ev = candidate.get("evidence") or {}
    metrics = (ev.get("metrics") or {}) if isinstance(ev, dict) else {}
    refs = (ev.get("refs") or []) if isinstance(ev, dict) else []
    ref_count = len(refs) if isinstance(refs, list) else 0

    # 主要スコア要素
    sev = float(candidate.get("severity") or 0.0)
    conf = float(candidate.get("confidence") or 0.0)

    # metrics から拾えそうな代表値（無ければNone）
    removed_count = metrics.get("removed_count")
    delta_events = metrics.get("delta_events")
    today_cnt = metrics.get("today_count") or metrics.get("today")
    base_cnt = metrics.get("baseline_count") or metrics.get("baseline")

    # --- Explain (A: 短い・機械的) ---
    # claim（1行）
    if "novelty" in str(sid):
        claim = f"{title}: 新規/変化の兆候が強まっています。"
    elif "persistence" in str(sid):
        claim = f"{title}: 継続性（残り続ける話題）が弱まっています。"
    elif ("rotation" in str(sid)) or ("churn" in str(sid)):
        claim = f"{title}: 話題の入れ替わりが激しくなっています。"
    else:
        claim = f"{title}: シナリオ条件に合致しました。"

    # rationale（根拠・箇条書き）
    rationale = [
        f"severity={sev:.2f}, confidence={conf:.2f}",
    ]
    if removed_count is not None:
        rationale.append(f"metrics.removed_count={removed_count}")
    if delta_events is not None:
        rationale.append(f"metrics.delta_events={delta_events}")
    if (today_cnt is not None) or (base_cnt is not None):
        rationale.append(f"metrics.count today={today_cnt}, baseline={base_cnt}")
    if ref_count:
        rationale.append(f"refs={ref_count}")

    # uncertainty（短い不確実性メモ）
    if conf < 0.35:
        uncertainty = "confidenceが低め。短期ノイズの可能性。"
    elif conf < 0.60:
        uncertainty = "confidenceは中程度。翌日も継続するか要確認。"
    else:
        uncertainty = "confidenceは十分。ただし単日変動の偏りには注意。"

    # watch（次に観測すべきポイント）
    if "novelty" in str(sid):
        watch = [
            "翌日も同方向（novelty_up）が継続するか",
            "refsの内訳（地域/主体/テーマ）に偏りがないか",
        ]
    elif "persistence" in str(sid):
        watch = [
            "baseline側に残るテーマと比較して弱まりが続くか",
            "removed_countが連日増えるか（反転するか）",
        ]
    elif ("rotation" in str(sid)) or ("churn" in str(sid)):
        watch = [
            "回転が一過性か（翌日も高churnか）",
            "特定テーマに偏った入替か（広く分散か）",
        ]
    else:
        watch = [
            "翌日の同シナリオ再発",
            "refs/metricsの増減",
        ]

    return {
        "id": f"{sid}::{candidate.get('id')}::{meta.get('date')}",
        "scenario_id": sid,
        "label": title,
        "kind": "prediction",

        # Explain（prediction直下）
        "claim": claim,
        "rationale": rationale,
        "uncertainty": uncertainty,
        "watch": watch,

        "trigger": {
            "signal_id": candidate.get("id"),
            "severity": candidate.get("severity"),
            "confidence": candidate.get("confidence"),
            "evidence": candidate.get("evidence") or {},
            "explain": candidate.get("explain") or "",
        },
        "notes": scenario.get("notes") or [],
        "source": {
            "dataset": meta.get("dataset"),
            "date": meta.get("date"),
            "baseline_date": meta.get("baseline_date"),
        },
    }


def score_pred(p: dict) -> float:
    """
    Scenario-aware scoring
    - novelty: 勢い重視（severity を強める）
    - persistence: 信頼度重視（confidence を強める）
    - topic_churn: バランス型
    """
    trig = p.get("trigger") or {}
    ev = trig.get("evidence") or {}

    sev = trig.get("severity", ev.get("severity", 0.0))
    conf = trig.get("confidence", ev.get("confidence", 0.0))

    sev = float(sev or 0.0)
    conf = float(conf or 0.0)

    sid = str(p.get("scenario_id") or "")

    if "novelty" in sid:
        score = (sev ** 1.2) * conf
    elif "persistence" in sid:
        score = sev * (conf ** 1.2)
    elif "rotation" in sid or "churn" in sid:
        score = sev * conf
    else:
        score = sev * conf

    return round(score, 4)



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", type=str, default=None, help="Path to diff_YYYY-MM-DD.json")
    ap.add_argument("--latest", action="store_true", help="Use latest diff in analysis dir")
    ap.add_argument("--analysis-dir", type=str, default=str(DEFAULT_ANALYSIS_DIR), help="Analysis dir for --latest")
    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir)

    if args.latest:
        diff_path = find_latest_diff(analysis_dir)
    elif args.diff:
        diff_path = Path(args.diff)
        if not diff_path.is_absolute():
            diff_path = (ROOT / diff_path).resolve()
    else:
        raise SystemExit("Specify --diff <path> or --latest")

    if not diff_path.exists():
        raise FileNotFoundError(f"Diff file not found: {diff_path}")

    diff_doc = load_json(diff_path)

    # candidates 補完（diff自体は変更しない：メモリ上だけ）
    ensure_min_candidates(diff_doc)

    scenarios = load_scenarios(SCENARIO_DIR)
    candidates = get_candidates(diff_doc)

    predictions: list[dict] = []
    for cand in candidates:
        for sc in scenarios:
            if match_scenario(cand, sc):
                p = build_prediction(diff_doc, cand, sc)
                p["source"]["diff_file"] = str(diff_path)
                predictions.append(p)

    # --- rank / filter (scenario-aware) ---
    for p in predictions:
        p["score"] = round(score_pred(p), 4)

    MIN_SCORE = 0.10
    predictions = [p for p in predictions if float(p.get("score", 0.0)) >= MIN_SCORE]

    TOP_K_PER_SCENARIO = 1
    by_sc: dict[str, list[dict]] = {}
    for p in predictions:
        sid = str(p.get("scenario_id") or "unknown")
        by_sc.setdefault(sid, []).append(p)

    kept: list[dict] = []
    for sid, items in by_sc.items():
        items.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        kept.extend(items[:TOP_K_PER_SCENARIO])

    TOP_K_GLOBAL = 3
    kept.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    predictions = kept[:TOP_K_GLOBAL]
    # --- /rank ---

    # --- metrics (minimal) ---
    meta = diff_doc.get("meta") or {}
    inp = diff_doc.get("input") or {}
    today_cnt = (inp.get("today") or {}).get("events_count")
    base_cnt = (inp.get("baseline") or {}).get("events_count")
    delta_events = (diff_doc.get("summary") or {}).get("delta_events")

    scenario_hits: dict[str, int] = {}
    for p in predictions:
        sid = p.get("scenario_id") or "unknown"
        scenario_hits[str(sid)] = scenario_hits.get(str(sid), 0) + 1

    print("[METRIC] date:", meta.get("date"), "baseline:", meta.get("baseline_date"))
    print("[METRIC] diff_event_count:", {"today": today_cnt, "baseline": base_cnt, "delta": delta_events})
    print("[METRIC] signal_candidates_count_total:", len(candidates))
    print("[METRIC] scenario_match_count_by_scenario:", scenario_hits)
    print("[METRIC] predictions_count:", len(predictions))
    # --- /metrics ---

    # 出力: signals は候補（candidates）、predictions は scenario 由来の予兆（predictions）
    signals = candidates
    scenario_predictions = predictions

    # --- dedupe scenario predictions (scenario_id + trigger.signal_id + date) ---
    deduped: list[dict] = []
    seen: set[tuple] = set()
    for p in scenario_predictions:
        sid = p.get("scenario_id")
        trig = (p.get("trigger") or {}).get("signal_id")
        date = ((p.get("source") or {}).get("date")) or ((diff_doc.get("meta") or {}).get("date"))
        key = (sid, trig, date)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    scenario_predictions = deduped
    # --- /dedupe ---

    out = {
        "schema": {"name": "genesis.predictions", "version": "0.2.0"},
        "meta": {
            "dataset": (diff_doc.get("meta") or {}).get("dataset"),
            "date": (diff_doc.get("meta") or {}).get("date"),
            "baseline_date": (diff_doc.get("meta") or {}).get("baseline_date"),
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "generator": {"repo": "GenesisPrediction_v2", "component": "scenario_runner"},
        },
        "source": {"diff_file": str(diff_path), "scenario_dir": str(SCENARIO_DIR)},
        "signals": signals,
        "predictions": scenario_predictions,
    }

    date = (diff_doc.get("meta") or {}).get("date", "unknown")
    out_path = diff_path.parent / f"predictions_{date}.json"
    write_json(out_path, out)

    print("[OK] diff:", diff_path)
    print("[OK] scenarios:", SCENARIO_DIR)
    print("[OK] output:", out_path)
    print("[OK] signals:", len(signals))
    print("[OK] predictions:", len(scenario_predictions))


if __name__ == "__main__":
    main()
