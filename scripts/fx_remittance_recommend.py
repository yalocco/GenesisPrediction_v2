"""
fx_remittance_recommend.py

WARN時を中心に、JPY→THB仕送り判断の「推奨行動」と理由を自動生成する。
人間の裁量を減らし、実務判断を安定させるための補助ロジック。
"""

import pandas as pd


def recommend_action(today_row: dict, recent_df: pd.DataFrame):
    decision = today_row.get("decision")
    combined = float(today_row.get("combined_noise_prob", 0))
    usdjpy = float(today_row.get("usd_jpy_noise_prob", 0))
    usdthb = float(today_row.get("usd_thb_noise_prob", 0))

    if decision == "ON":
        return "send_normal", "ノイズ低水準のため通常送金可"

    if decision == "OFF":
        return "wait", "ノイズ高水準のため見送り推奨"

    # WARN logic
    avg7 = recent_df.tail(7)["combined_noise_prob"].mean()
    warn_streak = (recent_df.tail(3)["decision"] == "WARN").sum()

    if combined >= 0.58:
        return "wait_or_small", "OFFに近いWARN（高ノイズ）"

    if usdthb > usdjpy and usdthb >= 0.55:
        return "split_3", "USDTHB側ノイズ優勢のため小分け推奨"

    if avg7 >= 0.50 or warn_streak >= 2:
        return "half_next_week", "直近ノイズ高めのため分割推奨"

    return "split_or_small", "軽度WARNのため分割または少額推奨"
