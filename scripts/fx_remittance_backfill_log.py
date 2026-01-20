import pandas as pd
from pathlib import Path

IN_CSV = Path("data/fx/jpy_thb_remittance_dashboard.csv")
OUT_LOG = Path("data/fx/jpy_thb_remittance_decision_log.csv")

KEEP_COLS = [
    "date",
    "combined_decision",
    "combined_noise_prob",
    "usd_jpy_decision",
    "usd_thb_decision",
    "usd_jpy_noise_prob",
    "usd_thb_noise_prob",
    "remit_note",
]

RENAME = {
    "combined_decision": "decision",
}

def main():
    if not IN_CSV.exists():
        print("[ERR] input not found:", IN_CSV)
        return

    df = pd.read_csv(IN_CSV)
    if df.empty:
        print("[ERR] input empty:", IN_CSV)
        return

    # date normalize
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

    # keep only existing columns
    cols = [c for c in KEEP_COLS if c in df.columns]
    missing = [c for c in KEEP_COLS if c not in df.columns]
    if missing:
        print("[WARN] missing columns (will be blank):", missing)

    out = df[cols].copy()
    out = out.rename(columns=RENAME)

    # ensure all output columns exist
    for c in ["decision", "combined_noise_prob", "usd_jpy_decision", "usd_thb_decision",
              "usd_jpy_noise_prob", "usd_thb_noise_prob", "remit_note"]:
        if c not in out.columns:
            out[c] = ""

    # sort
    out["_dt"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.sort_values("_dt").drop(columns=["_dt"])

    # merge with existing log (upsert by date)
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    if OUT_LOG.exists():
        old = pd.read_csv(OUT_LOG)
        if not old.empty and "date" in old.columns:
            old["date"] = pd.to_datetime(old["date"]).dt.date.astype(str)
        else:
            old = pd.DataFrame(columns=out.columns)
    else:
        old = pd.DataFrame(columns=out.columns)

    # upsert: keep latest from out, drop same date from old
    old = old[~old["date"].isin(out["date"])]
    merged = pd.concat([old, out], ignore_index=True)

    merged["_dt"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.sort_values("_dt").drop(columns=["_dt"])

    merged.to_csv(OUT_LOG, index=False)
    print("[OK] backfilled decision log")
    print(f" - {OUT_LOG}")
    print(f"[INFO] rows={len(merged)} (added/updated={len(out)})")

if __name__ == "__main__":
    main()
