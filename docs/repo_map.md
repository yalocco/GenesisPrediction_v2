# GenesisPrediction v2
# Repo Map & SST Definition（構造地図＋真実の定義）
Version: 1.0
Status: Active
Last Updated: 2026-02-19

---

## 0. 目的

本ドキュメントは、GenesisPrediction v2 のリポジトリ構造と
Single Source of Truth（SST）の定義を固定化するための地図である。

目的：

- 新しいスレッド / 新しい相棒（ChatGPT / Open-WebUI）でも迷わない
- GUI・分析・データの責務分離を維持する
- 「どこを直すべきか」を一発で判断できるようにする

---

## 1. 重要原則（SST）

### 1.1 SST（Single Source of Truth）の定義

GenesisPrediction v2 における **真実（SST）は `analysis/` 配下のみ** とする。

- GUIは `analysis/` のみを参照する
- `data/` は原材料であり真実ではない
- `scripts/` は生成装置であり真実ではない
- 手動編集で `analysis/` を改変することは禁止（再現性を壊すため）

**結論：**
- `analysis/` = 公開・表示・判断の唯一の情報源
- `data/` = 収集した生データ（素材）
- `scripts/` = SSTを生成する工場

---

## 2. リポジトリ構造（全体地図）

推奨の理解：

- 生成（scripts / docker）
- 素材（data）
- 真実（analysis）
- 表示（app/static）
- 設計（docs）

代表的な構造：

GenesisPrediction_v2/
│
├─ scripts/ # 生成スクリプト（SSTを作る）
│
├─ data/ # 生データ（Git管理しない）
│ ├─ world_politics/ # 日次ニュース等の素材
│ └─ fx/ # 為替素材CSVなど（素材）
│
├─ analysis/ # SST（唯一の真実）
│ ├─ world_politics/ # 表示・判断用に整形された成果物
│ └─ fx/ # overlay PNG / dashboard / viewmodel 等
│
├─ app/
│ └─ static/ # GUI（読み取り専用）
│ ├─ index.html
│ ├─ overlay.html
│ ├─ sentiment.html
│ ├─ digest.html
│ ├─ app.css
│ └─ .js
│
├─ docs/ # 設計思想・運用ルール・Runbook
│ ├─ working_agreement.md
│ ├─ repo_map.md
│ └─ runbook_.md
│
├─ docker-compose.yml # fetcher/analyzer等の実行基盤
├─ run_daily.ps1 # 朝の儀式入口（完走が最優先）
└─ README.md # 入口説明（短く）


---

## 3. ディレクトリ責務（何を置くべきか）

### 3.1 scripts/
- 役割：SST（analysis）を生成する
- 置くもの：Python / PowerShell / 補助ツール
- 禁止：SSTの手動修正のためのスクリプト化（原則NG）

### 3.2 data/（Git除外）
- 役割：収集・キャッシュ・中間生成物の置き場
- 置くもの：API取得結果、素材CSV、原文JSON等
- 原則：破損しても再生成できる（SSTではない）

### 3.3 analysis/（SST）
- 役割：GUI表示・運用判断の唯一の真実
- 置くもの：ViewModel JSON、集計JSON、overlay PNG、dashboard CSV等
- 原則：必ず scripts / pipeline から生成される
- 禁止：手動での直接編集

### 3.4 app/static/
- 役割：表示（読み取り専用）
- 置くもの：HTML/CSS/JS（見た目と表示ロジック最小）
- 原則：analysis を読むだけ
- 禁止：計算・推論・集計の実装（それは scripts/analyzer の仕事）

### 3.5 docs/
- 役割：思想・運用・再現性の固定化
- 置くもの：Working Agreement / Repo Map / Runbook / 設計メモ
- 原則：迷いをゼロにするために書く

---

## 4. 「どこを直す？」判断チャート（最短導線）

- GUIが崩れた  
  → `app/static/` を疑う（ただしデータ欠落かも）

- 数値が変・欠ける  
  → `analysis/` を確認（ViewModelや集計が生成されているか）

- analysisが古い / 生成されない  
  → `scripts/` と run_daily のログを確認

- 生データが取れてない  
  → `data/` の生成元（fetcher / API）を確認

---

## 5. 安定運用のための原則

- mainは常に安定（Working Agreement参照）
- フェーズは混ぜない（GUI調整とデータ改善は別）
- 変更は最小単位でコミット
- 安定点はタグで残す（例：gui-ui-stable-v1.x）

---

END OF DOCUMENT