# AI Memory Architecture
GenesisPrediction v2

Status: Active
Purpose: AIの記憶層構造を定義する
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
GenesisPrediction v2 における AI の記憶構造

を定義する。

目的

AIが何をどの層の記憶として扱うべきかを固定する

新しいAI / 新しいスレ / 新しいPC でも理解を再現可能にする

Chat Memory と Repository Memory と Observation Memory の責務を分離する

将来の Prediction System へ自然に接続できる構造を作る

1. Memory Layers Overview

GenesisPrediction の AI記憶は、以下の層で構成される。

Human Memory
↓
Chat Memory
↓
Repository Memory
↓
Observation Memory
↓
Prediction Memory

ただし、GenesisPrediction v2 で現在正式に運用している主要層は以下である。

Chat Memory
Repository Memory
Observation / Analysis Memory
2. Chat Memory
Definition

Chat Memory は

現在の会話スレッドの文脈

である。

例

このスレの目的

直前の修正内容

現在の相談テーマ

今回の1ターン1作業

Role

役割

短期記憶

である。

AIは Chat Memory によって

今なにをしているか

直前に何を決めたか

次に何をすべきか

を理解する。

Limitation

Chat Memory は

消える
重くなる
スレが変わると引き継がれない

そのため Chat Memory は

長期の真実

として扱ってはいけない。

3. Repository Memory
Definition

Repository Memory は

docs/

に保存された、固定化されたプロジェクト知識である。

例

docs/repo_map.md
docs/pipeline_system.md
docs/ui_system.md
docs/runbook_morning.md
docs/working_agreement.md
docs/ai_bootstrap.md
docs/repository_memory_index.md
Role

役割

長期知識
設計知識
運用知識
プロジェクト知識

である。

AIは Repository Memory によって

システム構造

運用手順

開発ルール

設計思想

現在状態

を復元する。

Rule

新しいAIはまず

docs/ai_bootstrap.md

から起動し、Repository Memory をロードする。

4. Observation / Analysis Memory
Definition

Observation Memory は

analysis/
および
history/

に保存される、世界観測の記憶である。

現在の正式SSTは

analysis/

である。

将来の時系列保存先は

data/world_politics/history/

などを想定する。

Role

役割

観測記憶
状態記憶
時系列記憶

である。

例

sentiment_latest.json

daily_summary_latest.json

health_latest.json

dated snapshots

trend data

observation history

Rule

Observation Memory は

世界の状態

を保持する。

これは Repository Memory のような設計知識ではなく、

観測対象そのもの

である。

5. Prediction Memory
Definition

Prediction Memory は

analysis/prediction/

または将来の prediction layer に保存される、

未来推定の記憶

である。

Role

役割

予測結果
シナリオ
リスク推定
将来見通し

を保持すること。

例

risk_score_latest.json
scenario_latest.json
prediction_latest.json
Status

現在は

設計段階

であり、本格運用はこれからである。

6. Truth Priority

AIが情報の優先順位で迷った場合は、以下に従う。

6.1 System Truth

システム構造・設計・運用・ルールについては

Repository Memory を正とする

対象

構造

ルール

運用

思想

履歴

現在状態

6.2 Runtime Truth

現在のデータ・数値・状態・表示元については

analysis/ を正とする

対象

latest JSON

health

digest

sentiment

overlay

prediction outputs

6.3 Conversation Truth

このスレでの直近タスクや今回の意図は

Chat Memory を使う

対象

今回の作業目的

直前の確認事項

次の1手

7. Critical Principle

GenesisPrediction の最重要原則

analysis = Single Source of Truth

ただしこれは

Runtime Data Truth

の意味である。

一方で

設計の真実

は

docs/

にある。

つまり AI は次のように理解する。

docs/     = 設計知識 / 運用知識 / ルール
analysis/ = 実行時の世界状態 / 現在の真実
chat      = 今回の作業文脈
8. Memory Usage Rule

AIは以下の順で記憶を使う。

Step 1

今回の作業目的を Chat Memory で理解する

Step 2

構造・ルール・運用を Repository Memory で復元する

Step 3

実際のデータ状態を analysis / history で確認する

Step 4

必要なら prediction outputs を読む

Step 5

推測ではなく、確認した情報だけで提案する

9. New Thread Behavior

新しいスレでは、Chat Memory が弱いことを前提とする。

そのため AI は

docs/ai_bootstrap.md

を入口として Repository Memory をロードしなければならない。

新スレ開始時の安全運用

AI bootstrap
docs/ai_bootstrap.md を読み込んでください
10. Relation to Observation Memory Layer

Observation Memory Layer は

analysis/latest
↓
history/YYYY-MM-DD snapshots

という形で構築する。

これは AI Memory Architecture における

Observation / Analysis Memory

の拡張である。

将来ここから

trend detection

pattern similarity

risk evolution

early warning

へ進む。

11. Relation to Repository Memory

Repository Memory と Observation Memory は混同してはいけない。

Repository Memory
プロジェクトを理解するための知識

例

repo_map

runbook

working_agreement

system_history

Observation Memory
世界を理解するための観測記憶

例

sentiment history

health history

daily summary history

12. Design Rule

AIは以下を守る。

Chat Memory を長期知識として信じすぎない
Repository Memory を設計知識として使う
analysis を実行時真実として使う
history を時系列観測として使う
prediction を未来推定として使う
13. Final Structure

GenesisPrediction の AI記憶構造

Human
↓
Chat Memory
↓
Repository Memory
↓
Observation Memory
↓
Prediction Memory
↓
Decision Support

これは最終的に

世界観測AI
↓
時系列AI
↓
予測AI
↓
判断AI

へ進化するための土台である。

END OF DOCUMENT