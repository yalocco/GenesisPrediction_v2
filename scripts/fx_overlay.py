import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 1) データ取得（Stooq: USDJPY）
# =========================
url = "https://stooq.com/q/d/l/?s=usdjpy&i=d"
df = pd.read_csv(url)
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").set_index("Date")

# =========================
# 2) 期間を直近2年に制限
# =========================
df = df[df.index >= (df.index.max() - pd.DateOffset(years=2))]

# =========================
# 3) 実値
# =========================
px = df["Close"].astype(float)

# =========================
# 4) 予測線（例：20日移動平均）
# =========================
pred = px.rolling(20).mean()

# 予測帯（参考）
vol = px.pct_change().rolling(20).std()
band = pred * vol
upper = pred + band
lower = pred - band

# =========================
# 5) 一致／不一致判定
# =========================

# 方向一致（上か下か）
actual_dir = np.sign(px.diff())
pred_dir = np.sign(pred.diff())
direction_match = actual_dir == pred_dir

# 誤差一致（±0.5円以内）
tol = 0.5
error_match = (px - pred).abs() <= tol

# =========================
# 6) 描画
# =========================
plt.figure(figsize=(12, 6))
plt.plot(px, label="Actual USDJPY")
plt.plot(pred, label="Forecast (MA20)")
plt.fill_between(pred.index, lower, upper, alpha=0.2, label="Forecast band")

# 外れ日（方向 or 誤差どちらか外れ）
miss = ~(direction_match & error_match)
plt.scatter(px.index[miss], px[miss], s=12, label="Miss")

plt.title("USDJPY: Actual vs Forecast (2Y) + Miss highlights")
plt.legend()
plt.grid(True)
plt.show()

# =========================
# 7) 指標出力
# =========================
print(f"Direction match rate: {direction_match.mean():.2%}")
print(f"Error match rate (±{tol} JPY): {error_match.mean():.2%}")

# =========================
# 8) 外れ日の保存
# =========================

# 保存用DataFrame
miss_df = pd.DataFrame({
    "date": px.index[miss],
    "price": px[miss],
    "forecast": pred[miss],
    "error": (px - pred)[miss],
    "direction_match": direction_match[miss],
    "error_match": error_match[miss],
})

# 保存先
import os
out_dir = "data/fx"
os.makedirs(out_dir, exist_ok=True)

csv_path = f"{out_dir}/usd_jpy_miss_days.csv"
json_path = f"{out_dir}/usd_jpy_miss_days.json"

miss_df.to_csv(csv_path, index=False)
miss_df.to_json(json_path, orient="records", date_format="iso")

print(f"[OK] Miss days saved:")
print(f" - {csv_path}")
print(f" - {json_path}")

