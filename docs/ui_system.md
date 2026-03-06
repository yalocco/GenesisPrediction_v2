# UI System (GenesisPrediction v2)
Version: 1.0
Status: Draft -> Active
Last Updated: 2026-03-05

## 0. 目的
UI（app/static）は「表示装置」であり、設計・依存関係を固定化する。
スレが変わっても、AIがUIの構造を即復元できる状態を作る。

## 1. UIの大原則
- UIは **SST（analysis/）だけを読む**（計算・生成・推論をUIへ持ち込まない）
- UI側の役割は「整形」「可視化」「安全なfallback」のみ
- 大規模刷新より「統一感」「再現性」「事故防止」を優先する

補足:
- SST定義（analysis/が真実）は docs/repo_map.md を参照
- GUI運用（ダウンロード徹底・freeze・baseline）は docs/gui_phase2_working_rules.md を参照

## 2. ページ一覧（現行）
- Home: app/static/index.html
- Overlay: app/static/overlay.html
- Sentiment: app/static/sentiment.html
- Digest: app/static/digest.html

## 3. 参照データ（SST側）の基本方針
- 原則: `analysis/**/**_latest.*` を優先参照
- dated（YYYY-MM-DD）は、必要な場合のみ参照（UIは “最新” を見せるのが基本）
- 参照が欠けた時は、UIが落ちないように fallback する（空表示・エラーカード・代替テキスト）

## 4. 各ページの責務と依存（概要）

### 4.1 Home (index.html)
責務:
- 全体の入口
- 今日の状況を「軽く」見せる（リンク導線 + 主要KPI）
想定依存（例）:
- analysis/.../daily_summary_latest.json（as_of / 主要KPI）
- analysis/.../health_latest.json（OK/WARN/NG）

### 4.2 Overlay (overlay.html)
責務:
- FX overlay（画像/CSV）を見せる
- remittance意思決定に必要な“表示”をする（判断ロジックはUIに入れない）
想定依存（例）:
- analysis/fx/fx_overlay_latest.png
- analysis/fx/*dashboard*.csv
- analysis/fx/*view_model*_latest.json（存在する場合）

### 4.3 Sentiment (sentiment.html)
責務:
- 日次ニュース由来の sentiment を見せる（トレンド/カテゴリ/KPI）
- UI baseline（背景/トップバー/カード/幅）の基準ページ
想定依存（例）:
- analysis/world_politics/sentiment_latest.json
- analysis/world_politics/daily_news_latest.json（必要なら補助参照）
- analysis/world_politics/view_model_latest.json（存在する場合）

### 4.4 Digest (digest.html)
責務:
- “まとめ”ページ（サムネ/ハイライト/リスク順など）
想定依存（例）:
- analysis/digest/view_model_latest.json
- analysis/digest/daily_summary_latest.json（存在する場合）

## 5. UI共通要素（統一仕様）
- topbar（ブランド + nav pills）
- container 幅（max-width）
- ガラスカード（glass / stroke / shadow）
- as_of（今日の日付表示は、source JSON が古い可能性を疑う。UIで捏造しない）
- raw JSON 生表示は通常隠す（detailsへ隔離 / Open JSON導線）

※詳細は docs/gui_phase2_working_rules.md の baseline 設計に従う。

## 6. 事故防止の運用（UI編集時）
- 長大ファイル（特に app/static/*.html）は **ダウンロード運用**
- 差分提案は禁止、必ず完全ファイルで受け渡す
- 1ターン=1作業（複数ページ同時編集を避ける）

この方針は docs/working_agreement.md を正とする。

## 7. TODO（今後、追記して育てる）
- 実際の参照パス（analysis配下）を確定したら、ページ別に “確定依存一覧” を表にする
- fallback仕様（missing時の表示）を各ページで統一テンプレ化する
- CSS（app/static/app.css）の責務（共通 vs ページ内style）を明文化する