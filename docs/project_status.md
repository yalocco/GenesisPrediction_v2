# Project Status (GenesisPrediction v2)
Status: Active
Last Updated: 2026-03-06

## 0. 目的
この1枚で「現在地」を復元できるようにする。
スレ変更・PC変更（会社/自宅）でも、AIと人間が同じ前提から再開できる。

---

## 1. Current UI
Pages:
- Home: app/static/index.html
- Overlay: app/static/overlay.html
- Sentiment: app/static/sentiment.html
- Digest: app/static/digest.html

UI Baseline:
- sentiment.html baseline（背景 / topbar / container / glass cards）

---

## 2. Current Pipeline
Daily (Morning Ritual):
1) git pull（clean確認）
2) scripts/run_daily_with_publish.ps1
3) FX lane
   - scripts/run_daily_fx_rates.ps1
   - scripts/run_daily_fx_inputs.ps1
   - scripts/run_daily_fx_overlay.ps1
4) scripts/build_data_health.py（health更新）
5) GUI確認（4ページ）

SST:
- analysis/ 配下のみが真実（Single Source of Truth）

---

## 3. Git / Freeze Points
Branch:
- main

Known stable tags (freeze):
- (fill) gui-ui-stable-v2.0 など
- (fill) digest-ui-ok-20260305 など

---

## 4. Known Issues (if any)
- (fill) 例：KPIがALL_ZEROになる、join mismatch、特定のPNG missing など

---

## 5. Next Action (one)
- (fill) 次にやる1作業だけを書く（例：Sentiment分類の表示を positive/negative/neutral/mixed に反映）

---

## 6. Rules (short)
- 1ターン = 1作業
- 差分提案禁止（完全ファイルのみ）
- GUIファイルはダウンロード運用（貼り付け禁止）