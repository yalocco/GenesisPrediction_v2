# Daily Routine v1  
GenesisPrediction v2 / Runbook

## 目的

本ドキュメントは、GenesisPrediction v2 における  
**日次運用（Daily Routine）を再現可能に固定するための正本**である。

- 「今日は何をすればよいか」を迷わず実行できること
- 日が空いても、環境が変わっても同じ結果に戻れること
- チャットや記憶に依存しない運用を可能にすること

本 Runbook は、憲法・仕様に従属し、これらに反してはならない。

---

## 参照関係（優先順位）

本ルーティーンは、以下の正本を前提とする。

1. 憲法  
   - `docs/constitution/file_generation_rules_v1.md`
2. 各仕様  
   - `docs/specs/fx_operation_spec_v1.md`
   - `docs/specs/sentiment_spec_v1.md`
3. 本 Runbook（daily_routine_v1.md）

---

## 基本原則（運用）

- 日次処理は **再実行可能**であること
- 成果物は **ファイルとして生成**されること
- 差分や手動編集は行わない
- 欠損・未生成は「異常」ではなく **観測結果の一部**として扱う

---

## 日次ルーティーン（標準）

### Step 0. 環境準備（最初のみ／変更時）

- Python venv が有効であること
- 必要な依存関係がインストール済みであること
- 作業ディレクトリが GenesisPrediction v2 のルートであること

---

### Step 1. データ取得（Fetch）

**目的**  
外部ソースから、その日の生データを取得する。

**実行内容（例）**
- ニュース API / RSS / 外部 CSV など
- 対象日は原則「当日」または明示指定日

**成果物（例）**
- `data/raw/`
- `data/news/YYYY-MM-DD.json`

> 取得失敗・空データの場合も処理は継続する。

---

### Step 2. 分析・計算（Analyze）

**目的**  
取得した生データから、判断に必要な数値・構造を生成する。

**責務**
- Analyzer は計算・分類・スコア算出のみを行う
- 表示用構造を考慮しない

**成果物（例）**
- `data/analysis/`
- `data/sentiment/YYYY-MM-DD.csv`
- `data/fx/YYYY-MM-DD.csv`

---

### Step 3. Digest / ViewModel 生成

**目的**  
Analyzer の成果物を、表示契約（ViewModel）に変換する。

**ルール**
- 正本は **JSON ファイル**
- 1日 = 1 ViewModel

**成果物（例）**
- `data/digest/view/YYYY-MM-DD.json`

> 欠損セクションは `status: "na"` として保持する。

---

### Step 4. 可視化（PNG / 補助生成物）

**目的**  
判断補助としての可視化を生成する。

**成果物（例）**
- `data/digest/images/YYYY-MM-DD/*.png`

> PNG / CSV は正本。  
> HTML / Markdown は閲覧用途に限定する。

---

### Step 5. GUI 表示（任意）

**目的**  
その日の状態を人間が確認する。

**ルール**
- GUI は正本ファイルを **読むだけ**
- 再計算・補完・推測は禁止

---

## 異常系の扱い（重要）

- ファイルが存在しない  
- データが空  
- 404 が返る  

これらは **運用エラーではない**。

GUI や確認者は：
- 「未生成」「観測なし」として扱う
- 無理に埋めない
- 過去データで補完しない

---

## 日次運用の完了条件

以下が満たされていれば、その日の運用は完了とする。

- 正本 ViewModel JSON が存在する  
  または  
- 意図的に未生成であることが確認できる

---

## 補足

- 日次ルーティーンは **人間のためのもの**であり、
  自動化・cron 化は将来の拡張として扱う
- 自動化する場合も、本 Runbook の順序と責務を崩してはならない

---

## バージョニング

- 本ドキュメントは v1 とする
- 変更は新バージョンとしてのみ行う
- 暗黙変更は禁止する

---

（GenesisPrediction v2 / Daily Routine v1）
