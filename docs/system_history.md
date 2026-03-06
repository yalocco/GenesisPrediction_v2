はい、**入れた方が良いです。結論から言うと「入れるべき」です。**
理由は、あなたの GenesisPrediction の設計思想と完全に一致するからです。

あなたのプロジェクトは

```
Chat Memory
↓
Repository Memory
↓
Project Knowledge
```

という構造になっています。 

今回作った

* `runbook_morning.md`
* `project_status.md`
* `system_history.md`（これから作る）

は **すべて Repository Memory** に入れるべきドキュメントです。

つまり答えは

**YES：情報源に入れる**

です。

---

# どこに入れるか（重要）

すでに `project_status.md` に書かれている **AI bootstrap knowledge** に合わせると、次の配置が最適です。 

```
docs/

runbook_morning.md        ← 朝の儀式
project_status.md         ← 現在状態
system_history.md         ← 変更履歴（NEW）

repo_map.md
pipeline_system.md
ui_system.md
genesis_brain.md
chat_operating_rules.md
```

---

# 役割

### ① runbook_morning.md

**運用手順**

```
どうやって回すか
```

---

### ② project_status.md

**現在の状態**

```
今どこまで来ているか
```

---

### ③ system_history.md

**設計変更の履歴**

```
なぜそうなったか
```

これが **未来のデバッグで一番効きます。**

---

# system_history.md（完全版）

これを
`docs/system_history.md`
として保存してください。

```markdown
# GenesisPrediction v2 — System History

Status: Active
Purpose: Architecture change log

---

# Philosophy

GenesisPrediction は

再現可能な研究システム

である。

そのため

**設計変更は必ず履歴として残す。**

---

# 2026-03

## Morning Ritual WorldDate 修正

変更内容

```

WorldDate
UTC yesterday
↓
LOCAL DATE

```

変更理由

ニュース raw データは

```

data/world_politics/YYYY-MM-DD.json

```

として **ローカル日付基準で保存される。**

旧仕様

```

WorldDate = UTC yesterday

```

では

```

missing raw news

```

エラーが発生することがあった。

新仕様

```

run_morning_ritual.ps1

```

引数無し実行時

```

WorldDate = LOCAL DATE

```

---

## 結果

Morning Ritual が

- 会社PC
- 自宅PC

両環境で安定完走。

---

# 2026-02

## Digest UI 完成

UI構成

```

Home
Overlay
Sentiment
Digest

```

Digest UI

```

Summary
KPI
Top highlights
Risk sort
Show-all default
Thumbnail

```

安定版完成。

---

## FX Multi Overlay

通貨ペア

```

JPY/THB
JPY/USD

```

Overlay構造

```

analysis/
fx_overlay_latest.png

```

---

# Future History

将来の変更は必ずここに追加する。

例

```

Prediction Engine v1
Trend3 evolution
Scenario engine

```

---

END OF DOCUMENT
```
