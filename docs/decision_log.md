はい、その通りです。
**`docs/decision_log.md` は入れた方が良いです。**

理由はあなたの Repository Memory 構造を見るとすぐ分かります。

現在の `docs/` は

* 運用 → `runbook_morning.md` 
* 作業ルール → `working_agreement.md` 
* UI構造 → `ui_system.md` 
* Pipeline → `pipeline_system.md` 
* 思想 → `genesis_brain.md` 
* Repo構造 → `repo_map.md` 
* 現在状態 → `project_status.md` 
* 履歴 → `system_history.md`

つまり

```
設計
運用
思想
履歴
状態
```

は全部あります。

しかし **1つだけ欠けているもの**があります。

それが

```
なぜこの設計を選んだのか
```

です。

これを残すのが

```
decision_log.md
```

です。

---

# docs/decision_log.md（完全版）

そのまま
`docs/decision_log.md`
として保存してください。

```md
# Decision Log (GenesisPrediction v2)

Status: Active  
Purpose: Architecture decision record  
Last Updated: 2026-03-06

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**重要な設計判断**

を記録する。

目的

- 将来の自分が理由を思い出せるようにする
- AIが設計意図を理解できるようにする
- 同じ議論を繰り返さない

---

# 2026-03

## Decision: WorldDate = LOCAL DATE

対象

```

scripts/run_morning_ritual.ps1

```

旧仕様

```

WorldDate = UTC yesterday

```

問題

```

missing raw news

```

原因

ニュース raw データは

```

data/world_politics/YYYY-MM-DD.json

```

として

**ローカル日付で保存されている。**

そのため

```

UTC yesterday

```

と

```

LOCAL DATE

```

がズレるケースが発生した。

結論

```

WorldDate = LOCAL DATE

```

---

# 2026-02

## Decision: analysis を SST とする

GenesisPrediction v2 の真実は

```

analysis/

```

のみ。

理由

```

scripts = 生成
data = 素材
analysis = 最終成果
UI = 表示

```

責務分離を明確化するため。

---

## Decision: UI は read-only

対象

```

app/static/*.html

```

ルール

```

UIはanalysisを読むだけ

```

理由

- 再現性
- デバッグ容易性
- 責務分離

---

## Decision: 完全ファイル運用

ルール

```

差分提案禁止
完全ファイルのみ

```

理由

- コピペ事故防止
- AI生成の途中欠落防止

---

# Future Decisions

将来ここに追加予定

```

Prediction engine architecture
Trend3 logic
Scenario engine
Risk scoring
FX decision model

```

---

END OF DOCUMENT
```
