# Decision Log (GenesisPrediction v2)

Status: Active  
Purpose: Architecture decision record  
Last Updated: 2026-03-30

---

# 0. Purpose

このドキュメントは、GenesisPrediction v2 の重要な設計判断と運用判断を記録する。

目的

- 将来の自分が理由を思い出せるようにする
- AI が設計意図を理解できるようにする
- 同じ議論と事故を繰り返さないようにする
- 実装ルールだけでなく運用ルールも固定する

---

# 1. Core Principles

## Decision: analysis is Single Source of Truth

GenesisPrediction v2 の真実は `analysis/` を基準とする。

責務分離

```text
scripts = 生成
data    = 素材 / 中間成果 / 配布素材
analysis = 最終成果
UI      = 表示
```

固定ルール

```text
analysis = Single Source of Truth
UI must not decide truth
UI must not synthesize truth
```

意図

- 再現性の確保
- デバッグ容易性
- 表示と生成の責務分離

---

## Decision: UI is read-only and display-only

対象

```text
app/static/*.html
app/static/common/*.js
```

ルール

```text
UI は analysis / data を読むだけ
UI は計算しない
UI は判定しない
UI は日付決定しない
UI は翻訳しない
UI は fallback 生成しない
UI は意味を作らない
```

意図

- UI の純化
- 不整合の防止
- 将来の保守容易化

補足

```text
UI = display only
calculation / decision / translation = scripts / analysis only
```

---

## Decision: Full file delivery only

ルール

```text
差分提案禁止
完全ファイルのみ
```

理由

- コピペ事故防止
- 不完全生成防止
- セクション欠落防止

---

## Decision: Prevent incomplete file generation (Full File Integrity Rule)

長文ファイル生成時に以下を禁止する。

```text
短縮生成
省略生成
推測生成
行数大幅減少
セクション欠落
script / style 欠落
```

ルール

```text
既存ファイル未確認の生成禁止
行数減少を正当理由なく許可しない
長文ファイルはダウンロード形式優先
元ファイルに対して行数が不自然に減っていないか自己確認すること
```

特に UI では厳格適用する。

---

## Decision: Existing file must be verified before generation

既存ファイルがある場合は、必ずその内容を確認してから生成する。

ルール

```text
既存ファイルを確認せずに生成しない
既存構造に合わせて修正する
中身不明のまま推測生成しない
```

意図

- 構造整合性維持
- 上書き事故防止
- 再現性向上

---

# 2. Architecture Decisions

## Decision: Pipeline structure is fixed

GenesisPrediction v2 の基本構造は以下で固定する。

```text
Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction
```

補助層

```text
Explanation
Vector Memory
FX Decision
History Snapshot
```

---

## Decision: WorldDate = LOCAL DATE

ニュース raw データはローカル日付で保存されるため、WorldDate は LOCAL DATE を採用する。

```text
data/world_politics/YYYY-MM-DD.json
```

旧仕様の `UTC yesterday` はズレを生むため不採用。

---

## Decision: Vector Memory = reference-only memory

対象

```text
Qdrant
scripts/build_vector_memory.py
scripts/vector_recall.py
scripts/scenario_engine.py
scripts/prediction_engine.py
```

結論

```text
Vector Memory = reference-only memory
analysis = Single Source of Truth
Vector DB must never overwrite analysis
UI must not query vector memory directly
```

意図

- 記憶の補助利用
- black-box 化防止
- 真実の多重化防止

---

## Decision: Memory is promoted, not raw

会話・試行錯誤をそのまま記憶にしない。

対象

```text
decision
rule
insight
```

非対象

```text
仮説
試行錯誤
雑談
一時ログ
```

---

## Decision: Decision Log is primary memory source

Vector Memory の第一優先は `decision_log.md` とする。

---

## Decision: build_vector_memory.py is single entrypoint

Vector Memory 構築は `build_vector_memory.py` に統一する。  
似た役割の build script を増やさない。

---

## Decision: Reference Memory is compacted for UI

reference_memory は UI 用に短文化して渡す。

ルール

```text
decision_log                -> title のみ
historical_pattern/analog   -> title のみ
snapshot / explanation      -> 必要なら summary を短文化
JSON / raw text / 全文       -> UIへ渡さない
最大 6 件まで
短文化は analysis 側で行う
UI 側で compact しない
```

---

# 3. UI / i18n Decisions

## Decision: Global i18n Architecture Unification

対象

```text
app/static/*.html
app/static/common/*.js
scripts/build_*_view_model.py
analysis/*_latest.json
```

結論

```text
i18n は analysis 層で完全生成する
UI は *_i18n を参照するのみ
```

固定ルール

```text
UI は pickI18n / pickI18nList のみ使用
英語フィールド直接参照禁止
UI で翻訳禁止
UI で fallback ロジック禁止
```

基準実装

```text
prediction.html
```

を唯一の正解として全ページを統一する。

最終状態

```text
analysis = 言語生成
UI       = 表示のみ
language = 共通管理
```

---

## Decision: Language state must be centrally managed

テーマと同様に言語状態も一箇所で集中管理する。

ルール

```text
各ページ個別で言語判定を持たない
localStorage を各ページで直接読まない
LANG は共通マネージャーのみ参照
静的文言も動的文言も共通 i18n helper 経由で解決
```

---

## Decision: UI must never generate or process language

固定ルール

```text
UI はあらゆる状況で言語を生成・加工してはならない
```

これには以下を含む。

```text
翻訳
補完
fallback 文生成
意味の圧縮
debug 表示を利用した擬似翻訳
```

---

## Decision: Digest summary i18n must be generated in analysis

Digest summary は自由文であるため、analysis 側で `summary_i18n` を生成し、UI はそれを表示するのみとする。

---

## Decision: Static UI labels may use central dictionary, but runtime text must come from analysis

ルール

```text
固定ラベル = 共通 i18n 辞書で可
動的本文   = analysis の *_i18n のみ
```

意図

- 画面共通ラベルの安定運用
- 動的テキスト責務の明確化

---

# 4. Deploy / Distribution Decisions

## Decision: Deploy target is snapshot, not source of truth

結論

```text
labos = 配信環境
Git + analysis/data = 正
```

labos は配信用 snapshot であり、設計上の正ではない。

ルール

```text
labos から設計を逆算しない
labos を authoritative source とみなさない
復旧時に labos から戻すのは最終手段
```

---

## Decision: Local and deploy must be compared, but deploy must not redefine architecture

deploy 側で見た目が安定していても、古い snapshot である可能性がある。  
ローカルとの比較確認は必要だが、設計判断は Git / analysis / data を基準に行う。

---

# 5. Operations Decisions

## Decision: Build environment and view environment must be separated

結論

生成環境と表示環境を分離する。

### Build Environment（自宅PC）

```text
LLMあり
Morning Ritual 実行可
analysis/data 生成
翻訳生成
vector memory 再構築
```

### View Environment（会社PC）

```text
UI確認
表示確認
deploy確認
analysis/data は外部同期
build禁止
Morning Ritual禁止
```

意図

- 環境差事故の防止
- i18n 欠落事故の防止
- 生成物の純度維持

---

## Decision: Company PC must not regenerate analysis/data

会社PCは確認専用とする。

理由

- 翻訳環境差による `_i18n` 欠落
- view_model の英語化
- overlay / digest / index の再崩壊

固定ルール

```text
会社PCでは Morning Ritual を実行しない
会社PCでは build script を実行しない
会社PCは analysis/data の消費者とする
```

---

## Decision: analysis/data USB sync is valid transport

analysis と data を USB で同期する運用は SSOT transport として有効とする。

前提

```text
自宅PC = 生成元
会社PC = 消費先
```

ルール

```text
analysis + data は丸ごと同期
差分判断を会社PCで行わない
会社PCで再生成しない
```

---

## Decision: Git restore is destructive and must be treated as rollback

`git restore` は未コミット変更を完全に破棄する rollback 操作として扱う。

ルール

```text
restore 前に必ず対象を確認する
完成直後に restore しない
restore は rollback 判断が確定した場合のみ使う
```

意図

- 完成ファイル消失事故の防止
- index / home_page.js 巻き戻し事故の防止

---

## Decision: Detached HEAD work must not be trusted as final state

detached HEAD 上の作業は最終成果として扱わない。

ルール

```text
detached HEAD を見つけたら main に戻す
残す必要がある変更だけ stash か commit する
不要変更は restore する
```

---

## Decision: Local cache failures are operational incidents, not architecture failures

`fastembed_cache` 破損などのキャッシュ異常は設計破綻ではなく運用事故として扱う。

対処手順

```text
1. fastembed_cache を削除
2. python scripts/build_vector_memory.py --recreate
3. powershell -ExecutionPolicy Bypass -File scripts/run_post_ritual_checks.ps1
```

---

## Decision: Automatic Vector Memory rebuild is valid self-healing behavior

Post Ritual Checks で vector memory が stale と判定された場合、自動 rebuild を許可する。

これは異常ではなく self-healing とみなす。

---

# 6. Debug / Fallback Decisions

## Decision: Temporary debug/meta English is acceptable if it is not user-facing meaning content

debug 表示・開発用メタ表示に限り、英語の短語は許容する。

対象例

```text
as_of
items
rendered
trend_points
debug
source path
```

ただし条件は以下。

```text
意味本文ではない
翻訳対象の主文ではない
UI設計判断を汚染しない
```

---

## Decision: Unintended foreign-language contamination must be treated as abnormal noise

日本語・英語・タイ語以外の言語が UI / 生成文に混入した場合は異常ノイズとみなす。

ルール

```text
韓国語など想定外言語は正式対象に含めない
混入を確認したらコード / data / runtime の順に切り分ける
コード上に無ければ runtime noise と判断する
```

---

# 7. Release Readiness Decisions

## Decision: Do not add attractive new features before pre-release checklist is complete

公開前は機能追加より検証を優先する。

順序

```text
1. 公開前チェック
2. 公開
3. フィードバック収集
4. 機能追加
```

---

## Decision: Pre-release focus is stability, not expansion

公開直前フェーズでは以下を優先する。

```text
UI整合
多言語整合
deploy整合
データ欠損耐性
説明可能性
```

新機能追加は公開後に行う。

---

# 8. Open WebUI / Shared Infra Decisions

## Decision: Open WebUI Integration with Qdrant

Open WebUI を Qdrant に接続し、Knowledge / File を vector search 可能にする。

確認結果

```text
open-webui_files
open-webui_knowledge
```

collection 作成と保存確認済み。

---

## Decision: Qdrant instance can be shared

Open WebUI と GenesisPrediction は同一 Qdrant instance を共有してよい。  
ただし collection は必ず分離する。

---

## Decision: Collection must be separated

```text
Open WebUI:
  open-webui_files
  open-webui_knowledge

GenesisPrediction:
  genesis_reference_memory
```

---

## Decision: Conversation is NOT auto-vectorized

Open WebUI 会話ログは自動で Qdrant に保存しない。  
会話全文は記憶対象としない。

---

# 9. Operational Reminders

## Build side reminder

```text
翻訳付き生成は自宅PCで行う
provider_available=False のまま公開用データを作らない
requests / ollama / model availability を確認する
```

## View side reminder

```text
会社PCは確認専用
analysis/data を同期して使う
UI問題と生成問題を混ぜない
```

## Recovery reminder

```text
まず Git 状態を clean にする
次に自宅PCを正として確認する
labos は最後の参考としてのみ使う
```

---

# 10. Future Decisions

将来ここに追加予定

```text
Prediction engine architecture freeze
Trend / Signal schema freeze
Scenario engine rule freeze
Risk scoring freeze
FX decision model freeze
Release policy
Public-facing explanation template
```

---

## 2026-03-27
### UI i18n Template Standardization

- Adopt prediction-based UI i18n template
- Integrate into global_language_architecture.md
- UI must not translate or fallback
- All dynamic text must use *_i18n

Status: adopted

---

END OF DOCUMENT
