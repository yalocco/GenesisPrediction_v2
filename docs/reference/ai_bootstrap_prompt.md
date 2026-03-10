大丈夫です 👍
状況も理解しました。

**結論：あなたが最初に作っていた “短いBootstrap版” の方が正しいです。**
なので **それをもう一度生成します。**

理由も簡単に言うと

* AI bootstrap は **短いほど良い**
* 詳細は **docs を読ませる設計**がベスト
* 今のあなたの **Repository Memory構造と完全一致**

つまり **あなたの元の設計が正解**です。

---

# これを保存してください

```
docs/ai_bootstrap_prompt.md
```

---

# ai_bootstrap_prompt.md（正式版）

そのまま **丸ごと上書きしてください。**

```md
# GenesisPrediction v2 — AI Bootstrap

このスレは **GenesisPrediction v2 の開発スレッド**です。

このプロジェクトでは  
**Chat Memory に依存せず Repository Memory（docs）を優先**します。

まず以下の docs を **前提知識として扱ってください。**

---

# Repository Memory

以下のドキュメントは  
GenesisPrediction の **設計知識（Design SST）** です。

優先順位：

1️⃣ repo_map.md  
（リポジトリ構造 / SST定義）

2️⃣ repo_architecture.md  
（Chat / Repository / Runtime の三層構造）

3️⃣ project_status.md  
（現在の状態 / 作業中テーマ）

4️⃣ pipeline_system.md  
（パイプライン構造）

5️⃣ ui_system.md  
（UI構造）

6️⃣ genesis_brain.md  
（設計思想）

7️⃣ chat_operating_rules.md  
（AI作業ルール）

8️⃣ runbook_morning.md  
（毎日の運用手順）

9️⃣ working_agreement.md  
（共同開発ルール）

---

# 最重要設計原則

GenesisPrediction v2 の **Single Source of Truth** は

```

analysis/

```

です。

ルール：

```

scripts → SST を生成
analysis → 唯一の真実
app/static → 表示のみ

```

GUIで再計算は禁止。

---

# AI作業ルール

必ず守ること：

```

1ターン = 1作業
差分修正禁止
完全ファイル提示

```

長いファイル（HTML / CSS / JS / PowerShell / Python）は

```

ダウンロード運用

```

を優先する。

---

# 作業判断の優先順位

問題が起きた場合：

```

UIが壊れた
→ analysis を確認
→ 正しければ GUI 問題

数値が出ない
→ analysis 生成状況
→ scripts
→ data

```

---

# 現在のプロジェクト状態

現在の状態は

```

docs/project_status.md

```

を基準とする。

---

# 作業開始

このスレでは

```

docs/project_status.md の Next Action

```

を優先して作業する。
```

---
