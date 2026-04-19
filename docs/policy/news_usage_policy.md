# News Usage Policy
GenesisPrediction v2

Status: Active  
Purpose: ニュース記事・見出し・要約・出典の扱いを固定し、著作権・信頼性・公開運用の事故を防ぐ  
Location: docs/policy/  
Last Updated: 2026-04-19

---

# 0. Purpose

この文書は、GenesisPrediction v2 における

```text
ニュースコンテンツの利用方針
````

を定義する。

目的

* ニュース記事の無断転載事故を防ぐ
* 公開時の著作権リスクを下げる
* 見出し・要約・リンク・分析の責務を分離する
* AI と人間の運用判断を固定する
* 「ニュースサイトの複製」ではなく「分析システム」であることを守る

GenesisPrediction は

```text
ニュース本文を配るシステム
```

ではない。

GenesisPrediction は

```text
観測
↓
要約
↓
構造化
↓
判断支援
```

のためのシステムである。

---

# 1. Core Principle

最重要原則はこれである。

```text
ニュース本文を再配布しない
```

GenesisPrediction が扱うべきものは

* 事実の観測
* 要点の要約
* 構造化されたシグナル
* 影響分析
* 出典リンク

であり、

```text
記事本文そのもの
```

ではない。

---

# 2. Allowed Use

GenesisPrediction で許可する利用は以下とする。

## 2.1 Headline

短い見出しの参照は許可する。

例

```text
記事タイトル
短い見出し
短いアンカー表現
```

ただし、必要最小限に留めること。

---

## 2.2 Summary

記事内容を

```text
自分の言葉で要約する
```

ことを許可する。

要約は以下を満たすこと。

* 原文のコピペではない
* 原文の長文翻訳ではない
* 必要な事実の圧縮である
* GenesisPrediction の観測・分析に必要な範囲である

---

## 2.3 Link

出典リンクの掲載を許可する。

原則

```text
見出しだけで終わらせない
必ず source / url を持てる構造を優先する
```

理由

* 出典確認可能性の担保
* 信頼性の確保
* ユーザーが原文へ遷移できるようにするため

---

## 2.4 Multi-Source Integration

複数記事を横断して

* 共通論点を抽出する
* シグナルを抽出する
* リスクを整理する
* observation / trend / signal / scenario / prediction へ流し込む

ことを許可する。

これは転載ではなく

```text
分析
```

である。

---

## 2.5 Analytical Transformation

以下の変換を許可する。

* sentiment
* theme tag
* signal tag
* risk driver
* impact tag
* summary
* explanation
* historical context

重要原則

```text
原文の再配布ではなく
分析結果へ変換する
```

---

# 3. Forbidden Use

以下を禁止する。

## 3.1 Full Text Reproduction

ニュース本文の全文掲載を禁止する。

禁止例

```text
記事全文をそのまま表示する
記事本文を段落単位でコピーする
記事本文を複数段落そのまま掲載する
```

---

## 3.2 Long-Form Copy-Paste

長文転載を禁止する。

禁止例

```text
本文の大部分を引用する
記事の要旨を原文に近いまま並べる
リード文＋本文をそのまま並べる
```

---

## 3.3 Full Translation of Original Article

原文記事を丸ごと翻訳して掲載することを禁止する。

重要

```text
翻訳しても転載は転載である
```

禁止例

```text
英語記事を日本語に全文翻訳して表示する
原文を段落ごとに翻訳して載せる
```

---

## 3.4 Source Replacement

GenesisPrediction が原記事の代替として読める状態を作ることを禁止する。

禁止例

```text
リンク先へ行かなくても全文が読める状態
見出し・本文・翻訳文が揃いすぎて元記事不要になる状態
```

---

## 3.5 Misleading Attribution

出典不明のまま記事内容を断定表示することを禁止する。

禁止例

```text
source無し
url無し
どの媒体か分からないまま本文要約だけ載せる
```

---

# 4. Safe Display Rule

安全な表示は以下を基本形とする。

## 4.1 Recommended Structure

```text
Headline
↓
Short summary in our own words
↓
Source / URL
↓
Analytical implication
```

---

## 4.2 Example Structure

```text
Observed event
- Headline
- Source link

Summary
- 自分の言葉で短く要約

Signal / Risk
- 何が兆候か
- 何が影響か
```

---

## 4.3 Maximum Intent Rule

重要なのは文字数そのものより

```text
原記事の代替になっていないか
```

である。

GenesisPrediction は常に

```text
要点だけを示し
原文は出典先で読む
```

という構造を守る。

---

# 5. Role Separation

ニュースの扱いにおいても責務分離を維持する。

## 5.1 Source Side

ニュース媒体・配信元の責務

```text
原文の提供
本文の所有
一次情報の公開
```

---

## 5.2 GenesisPrediction Side

GenesisPrediction の責務

```text
観測
要約
構造化
比較
分析
判断支援
```

GenesisPrediction は

```text
ニュース出版社ではない
```

---

## 5.3 UI Side

UI の責務

```text
analysis にある見出し・要約・出典を表示する
```

UI はニュース本文を生成しない。
UI は翻訳転載をしない。
UI は長文引用をしない。

---

# 6. AI Usage Rule

AI を使う場合もこの方針を崩してはならない。

## 6.1 Allowed AI Behavior

AI に許可する処理

* 記事の要点要約
* 複数記事の共通論点抽出
* トレンド圧縮
* signal 化
* explanation 化
* title / summary の短文化

---

## 6.2 Forbidden AI Behavior

AI に禁止する処理

* 記事本文の丸ごと整形
* 記事全文の翻訳再配布
* 長文引用の自動生成
* 元記事の代替になる再構成
* 出典なしの断定的本文生成

---

## 6.3 Principle

AI は

```text
ニュース本文を複製するためではなく
分析価値へ変換するために使う
```

---

# 7. Source Attribution Rule

出典は可能な限り明示する。

原則

```text
headline だけで終わらせない
source と url を保持する
```

最低限保持したいもの

```text
title
source
url
publishedAt
```

理由

* 追跡可能性
* 誤引用防止
* 出典確認
* 信頼性維持

---

# 8. Public Release Rule

公開サイトでの利用は、通常運用よりさらに慎重に行う。

## 8.1 Public UI

公開UIでは以下を優先する。

* 見出し
* 短い要約
* 構造化シグナル
* source link

本文長文化は禁止する。

---

## 8.2 OGP / SNS

SNS共有では、ニュース本文を出さない。

使ってよいのは

* プロダクトの説明
* 現在のリスク要約
* key drivers
* date
* prediction headline

であり、原記事本文ではない。

---

## 8.3 Explanation

Explanation は原記事本文の説明ではない。

Explanation は

```text
analysis に存在する判断結果の説明
```

である。

したがって、ニュース記事の本文を explanation に流し込んで長文化してはならない。

---

# 9. Terms of Service Reminder

ニュースソースごとの API / 配信 / 再利用規約は別途存在する可能性がある。

重要原則

```text
著作権ポリシー順守
+
配信元利用規約順守
```

特に将来的に以下を確認対象とする。

* News API 利用規約
* MediaStack 利用規約
* 個別媒体の再利用条件
* 商用利用可否
* キャッシュ / 再配布制限

この文書は一般運用ポリシーであり、個別契約や個別規約を上書きしない。

---

# 10. Decision Boundary

判断に迷った場合は以下で決める。

## Safe

```text
短い見出し
短い要約
自分の言葉での再記述
構造化分析
出典リンク
```

## Unsafe

```text
本文転載
長文転載
全文翻訳転載
原記事の代替表示
出典なし表示
```

---

# 11. Final Principle

GenesisPrediction のニュース利用方針を一言で言うとこれである。

```text
ニュースを貼るのではなく
ニュースを分析する
```

さらに公開運用ではこれを守る。

```text
本文を配らない
要点を示す
出典を残す
分析価値へ変換する
```

---

# 12. Recommended Operational Note

この文書は主に人間向け運用ポリシーである。

AI に恒常的に効かせたい場合は、
以下を decision_log に短く反映すること。

推奨圧縮例

```text
Decision: News content must never be reproduced in full; only summarized, linked, and transformed into analysis.
```

理由

* policy 文書単体は AI の常時参照対象にならない場合がある
* decision_log は AI の判断抑制に直接効く
* 人間用の詳細ルールと AI 用の短い判断ルールを分離できる

---

END OF DOCUMENT

```
```
