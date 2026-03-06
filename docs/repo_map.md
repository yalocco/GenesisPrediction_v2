# Repository Map (GenesisPrediction v2)

Version: 2.0
Status: Active
Last Updated: 2026-03-06

---

# 0. 目的

このドキュメントは
GenesisPrediction v2 の **リポジトリ構造と責務** を定義する。

AIと人間が

```
どの問題を
どのディレクトリで
修正すべきか
```

を迷わないようにする。

---

# 1. GenesisPrediction ディレクトリ構造

```
GenesisPrediction_v2/

docs/        ← Repository Memory
scripts/     ← データ生成
data/        ← 素材
analysis/    ← Single Source of Truth
app/static/  ← UI
```

---

# 2. Single Source of Truth

GenesisPrediction v2 の
**唯一の真実（SST）** は

```
analysis/
```

である。

ルール

```
scripts → analysis を生成
analysis → UIが読む
UI → 再計算しない
```

---

# 3. 各ディレクトリの責務

## docs/

役割

```
Repository Memory
```

内容

```
設計
ルール
プロジェクト思想
現在状態
```

主なファイル

```
repo_map.md
repo_architecture.md
ui_system.md
pipeline_system.md
project_status.md
genesis_brain.md
chat_operating_rules.md
working_agreement.md
runbook_morning.md
gui_phase2_working_rules.md
```

---

## scripts/

役割

```
SST生成装置
```

主な処理

```
fetch
analyze
aggregate
publish
health
```

例

```
run_daily_with_publish.ps1
run_daily_fx_rates.ps1
run_daily_fx_overlay.ps1
build_data_health.py
```

---

## data/

役割

```
素材
```

特徴

```
Git管理対象外
再生成可能
```

---

## analysis/

役割

```
Single Source of Truth
```

内容

```
daily_news
sentiment
digest
overlay
health
```

このディレクトリのデータが
**GenesisPrediction の最終出力**である。

---

## app/static/

役割

```
表示UI
```

ページ

```
index.html
overlay.html
sentiment.html
digest.html
```

重要ルール

```
UIはanalysisのみ読む
UIは再計算しない
```

---

# 4. パイプライン構造

GenesisPrediction の基本フロー

```
Morning Ritual
↓
Analyzer
↓
Sentiment
↓
Digest
↓
Overlay
↓
Health
```

詳細

```
docs/pipeline_system.md
```

---

# 5. 問題発生時の判断ルール

## UI表示がおかしい

```
1 analysis を確認
2 analysis が正しい → GUI問題
3 analysis が壊れている → scripts問題
```

---

## 数値が出ない

```
1 analysis を確認
2 scripts 実行状況
3 data
```

---

## パイプラインが止まる

```
scripts/
```

を確認。

---

# 6. AI作業ルール

GenesisPrediction v2 の AI作業規約

```
1ターン = 1作業
差分修正禁止
完全ファイル提示
```

詳細

```
docs/chat_operating_rules.md
```

---

# 7. 現在地

現在の状態は

```
docs/project_status.md
```

を参照。

---

# 8. 結論

GenesisPrediction v2 は

```
scripts
↓
analysis
↓
UI
```

の責務分離構造で動く
**AI共同開発プロジェクト**である。

---

END OF DOCUMENT
