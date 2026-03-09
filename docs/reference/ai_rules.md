# AI Rules

GenesisPrediction v2

Status: Active
Purpose: AIが守るべき絶対ルール
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 において
AIが **必ず守るべきルール** を定義する。

目的

* AIの誤動作を防ぐ
* 設計原則を固定する
* 長期プロジェクトを安定させる
* 人間とAIの役割を明確にする

---

# 1. Single Source of Truth

GenesisPrediction v2 の最重要原則

```
analysis = 唯一の真実
```

つまり

```
scripts → analysis を生成
UI → analysis を読む
UI → 再計算しない
```

AIは

```
analysis を最優先で確認する
```

---

# 2. No UI Logic Rule

AIは

```
UI に分析ロジックを入れてはいけない
```

UIの役割

```
表示のみ
```

分析ロジックは

```
scripts
analysis
prediction
```

に置く。

---

# 3. Verify Before Assuming

AIは

```
推測してはいけない
```

必ず

```
analysis
data
json
```

を確認してから判断する。

---

# 4. Respect System Layers

GenesisPrediction の層構造

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

AIは

```
層を破ってはいけない
```

例

```
UI → scripts を直接呼ばない
```

---

# 5. One Task Per Turn

AI作業ルール

```
1ターン = 1作業
```

理由

```
デバッグしやすい
履歴が明確
事故防止
```

---

# 6. Full File Rule

GenesisPrediction の作業ルール

```
差分修正禁止
```

AIは

```
完全ファイル
```

で提示する。

---

# 7. Large File Safety

大きなファイル

```
200行以上
```

の場合

```
ダウンロード方式
```

で提示する。

理由

```
GUI事故防止
コピー事故防止
```

---

# 8. GUI Safety Rule

以下ディレクトリは慎重に扱う

```
app/static
```

理由

```
GUIは人間ミスが起きやすい
```

AIは

```
完全ファイル提示
```

を守る。

---

# 9. Morning Ritual Stability

GenesisPrediction は

```
Morning Ritual
```

を中心に動く。

AIは

```
朝の儀式を壊す変更
```

をしてはいけない。

---

# 10. Repository Memory Respect

AIは

```
Repository Memory
```

を最優先で参照する。

入口

```
docs/ai_quick_context.md
```

次

```
docs/repository_memory_index.md
```

---

# 11. Human Authority

GenesisPrediction は

```
Human + AI
```

の共同研究である。

最終決定

```
Human
```

AIは

```
提案
分析
設計補助
```

を行う。

---

# 12. Long-Term Stability

GenesisPrediction は

```
10年以上続く研究
```

である。

AIは

```
短期最適化
```

ではなく

```
長期安定
```

を優先する。

---

# 13. Final Principle

GenesisPrediction の目的

```
世界を理解する
危機を早く知る
家族を守る
```

AIは

```
この目的に反する提案
```

をしてはいけない。

---

END OF DOCUMENT
