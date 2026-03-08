# GenesisPrediction v2 — Project Status

Status: Active
Last Updated: 2026-03-06
Version: 1.1

---

# Repository Memory

GenesisPrediction v2 は  
**Repository Memory（docs）を中心に開発する。**

AIは以下を前提知識として扱う。

```

docs/ai_bootstrap_prompt.md

docs/repo_map.md
docs/repo_architecture.md
docs/project_status.md

docs/pipeline_system.md
docs/ui_system.md

docs/genesis_brain.md
docs/chat_operating_rules.md

```

---

# Current System

## UI

現在のUIページ

```

Home
Overlay
Sentiment
Digest

```

Digest UI は **安定版完成**

---

## Pipeline

現在のパイプライン構造

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

Morning Ritual は **安定動作**

---

# Runtime Architecture

GenesisPrediction v2 の Runtime 構造

```

scripts → analysis を生成
analysis → Runtime SST
UI → analysis を読む

```

analysis/ は **Single Source of Truth**

---

# Known Stable Tags

現在の安定タグ

```

deploy-ready-v1
digest-ui-ok-20260305
fx-multi-overlay-v1
gui-mvp
gui-ui-stable-v1
gui-ui-stable-v1.1
gui-ui-stable-v2.0
gui-ui-stable-v2.1
overlay-stable-v1
research-morning-ritual-stable-v2
research-morning-ritual-stable-v3
research-morning-ritual-v1
research-prediction-persistence-v1
research-reports-stable-v1
research-trend3-fx-v1
research-trend3-fx-v2B-stable
sentiment-stable-v1
sentiment-thumb-step1
ui-stable-2026-02-28
ui-stable-pre-theme
ui-stable-sentiment-v1

```

---

# Current Issue

Sentiment分類が正常に反映されていない。

Digest KPI

```

positive 0
negative 0
neutral 0
mixed 0
unknown 多数

```

原因

```

Sentiment join mismatch

```

---

# Next Task（最重要）

Sentiment分類を有効化する。

目標

```

positive
negative
neutral
mixed

```

が Digest KPI に表示されること。

unknown を減らす。

---

# Next Phase

Sentiment Trend 改良

予定

```

3軸グラフ

```

---

# Future Phase

Prediction Engine

```

signals
scenarios
predictions

```

---

# Development Rules

AI作業ルール

```

1ターン = 1作業
差分修正禁止
完全ファイル提示

```

---

# Change Log

## 2026-03-06

Morning Ritual の **WorldDate 仕様変更**

旧仕様

```

WorldDate = UTC yesterday

```

新仕様

```

WorldDate = LOCAL DATE

```

理由

ニュース raw データ

```

data/world_politics/YYYY-MM-DD.json

```

が **ローカル日付基準で生成されるため**

UTC yesterday を使用すると

```

missing raw news

```

エラーが発生することがあった。

現在の正式仕様

```

scripts/run_morning_ritual.ps1

```

を **引数無しで実行する場合**

```

WorldDate = (Get-Date -Format "yyyy-MM-dd")

```

が使用される。

この変更により

- 会社PC
- 自宅PC

両環境で **Morning Ritual が安定完走**するようになった。

---

# Knowledge Architecture

GenesisPrediction v2 は

```

Chat Memory
↓
Repository Memory
↓
Project Knowledge

```

構造で開発する。

---

END OF DOCUMENT
```
