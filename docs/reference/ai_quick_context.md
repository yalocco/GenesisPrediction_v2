# AI Quick Context

GenesisPrediction v2

Status: Active
Purpose: AIがプロジェクトを20秒で理解するための最短コンテキスト
Last Updated: 2026-03-07

---

# 1. What This Project Is

GenesisPrediction v2 は

```
世界観測AI
```

を構築する研究プロジェクトである。

目的

```
世界の変化を観測
↓
パターン理解
↓
未来リスク予測
↓
判断支援
```

用途

```
家族の安全
資産防衛
世界理解
```

---

# 2. System Structure

システム構造

```
data
↓
scripts
↓
analysis
↓
prediction
↓
UI
```

役割

```
data        = 素材
scripts     = データ生成
analysis    = 真実 (Single Source of Truth)
prediction  = 未来推定
UI          = 表示
```

---

# 3. Critical Rule

GenesisPrediction の最重要ルール

```
analysis = 唯一の真実
```

つまり

```
scripts → analysis を生成
UI → analysis を読む
UI → 再計算しない
```

---

# 4. Runtime

日次処理

```
Morning Ritual
```

流れ

```
git pull
↓
run_daily_with_publish
↓
FX lane
↓
build_data_health
↓
latest artifacts refresh
```

---

# 5. Key Data

主要データ

```
analysis/world_politics
analysis/digest
analysis/fx
analysis/prediction
analysis/health
```

---

# 6. Key UI

主要UI

```
index.html
sentiment.html
digest.html
overlay.html
```

---

# 7. AI Collaboration

GenesisPrediction は

```
Human + AI
```

共同研究プロジェクトである。

Human

```
目的
判断
倫理
```

AI

```
観測
分析
設計補助
```

---

# 8. System Evolution

GenesisPrediction は

```
観測AI
↓
時系列AI
↓
予測AI
↓
判断AI
```

へ進化する。

---

# 9. Repository Memory Entry

AIはまず以下を読む。

```
docs/repository_memory_index.md
```

---

END OF DOCUMENT
