# Decision Log (GenesisPrediction v2)

Status: Active  
Purpose: Architecture decision record  
Last Updated: 2026-04-09

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

Status: adopted

---

## 2026-04-04
### Explanation Is a Mirror of Prediction

Decision: Explanation must mirror prediction, not reinterpret it

対象

```text
analysis/prediction/prediction_latest.json
analysis/explanation/prediction_explanation_latest.json
scripts/build_prediction_explanation.py
```

ルール

```text
explanation は prediction の mirror とする
explanation は新しい意味を生成してはならない
summary は prediction_statement を優先して mirror する
drivers は key_drivers を mirror する
watchpoints は monitoring_priorities を mirror する
```

補足

```text
Prediction = truth
Explanation = structured mirror
UI = read-only consumer
```

理由

```text
prediction と explanation の意味ズレを防ぐ
explanation layer を analysis-side の説明層として固定する
UI 側の再解釈圧力を防ぐ
```

Status: adopted

---

## 2026-04-04
### Watchpoints Must Not Be Mixed Across Layers

Decision: Prediction watchpoints must take priority over scenario/signal watchpoints

対象

```text
scripts/build_prediction_explanation.py
prediction.monitoring_priorities
scenario.watchpoints
signal.watchpoints
```

ルール

```text
prediction.monitoring_priorities が存在する場合
explanation.watchpoints はそれのみを使用する
scenario / signal 由来の watchpoint を混ぜない
prediction 側に watchpoints が無い場合のみ fallback を許可する
```

理由

```text
watchpoint 件数不一致の防止
explanation による勝手な拡張の防止
prediction = truth の原則維持
```

Status: adopted

---
## Decision: Digest summary i18n must be generated in analysis

Digest summary は自由文であるため、analysis 側で `summary_i18n` を生成し、UI はそれを表示するのみとする。

---

Status: adopted

---

## 2026-04-04
### Runtime UI Text Must Not Compete With Static i18n

Decision: Static labels and runtime text must not double-define the same field

対象

```text
app/static/*.html
heroText
section titles
static UI labels
```

禁止事項

```text
静的文言を共通 i18n で設定した後に
別の runtime ロジックで同じDOMへ英語直書き上書きすること
```

ルール

```text
同一DOMノードの文言責務は一系統に限定する
固定ラベルは共通 i18n 辞書で統一する
動的本文は analysis の *_i18n だけを使う
静的文言と動的文言の二重定義を禁止する
```

理由

```text
初期表示では日本語、再描画後は英語になる競合を防ぐ
local / deploy で見え方がずれる事故を防ぐ
UI を read-only に保つ
```

Status: adopted

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

## Decision: Deploy must be full replacement, not overlay

deploy 処理は既存ファイルの上に重ねる overlay ではなく、  
完全置換（full replacement）でなければならない。

禁止事項

```text
既存ディレクトリを残したまま展開する
data / analysis を部分上書きする
古い snapshot が混在する状態を許容する
```

必須ルール

```text
deploy 前に対象ディレクトリを削除する
data / analysis / static を完全に置き換える
deploy は「コピー」ではなく「状態の再現」とする
```

理由

```text
overlay deploy は古い data を残し、
UI上は正常に見えるが実際には不整合となる

これは silent failure の一種であり、
検知が困難で再発率が非常に高い
```

補足

```text
local（analysis/data）と deploy の差異が出た場合、
deploy 側の上書き不完全を最優先で疑う
```

Status: adopted

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

Status: adopted

---

## 2026-04-04
### Automation Must Expose Phase Status and Unified Exit Code

Decision: Unattended automation must expose per-phase status and final exit code

対象

```text
scripts/run_morning_ritual_with_checks.ps1
```

ルール

```text
各フェーズは OK / FAIL / SKIP を明示する
対象フェーズ:
- ritual
- post
- deploy
- verify

最終結果は 0 / 1 の exit code に統一する
0 = success
1 = failure
```

補足

```text
ログだけ読まないと状況が分からない状態を禁止する
Final Status を最後に必ず出力する
```

理由

```text
Windows Task Scheduler / cron 連携を容易にする
無人運用時の障害切り分けを高速化する
deploy 失敗や verify 未実行を見落とさないため
```

Status: adopted

---

## 2026-04-04
### Automatic Vector Memory Rebuild Is Accepted as Self-Healing in Pipeline

Decision: WARN -> rebuild -> re-check -> OK is正常運用として扱う

ルール

```text
vector memory freshness が WARN の場合
自動 rebuild を許可する
re-check で fresh を確認する
re-check が通らない場合は FAIL とする
```

理由

```text
reference memory は補助層であり、
stale を検知して自動回復できることは運用品質向上につながるため
```

Status: adopted

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

## Decision: UI must not silently mask missing data

UI は必要な data / analysis が欠損している場合、  
黙って正常表示を続けてはならない。

禁止事項

```text
空表示のまま正常に見せる
placeholder で誤魔化す
古い値の流用で正常に見せる
fallback による疑似正常化
```

必須ルール

```text
欠損状態は明示する
loading / missing / unavailable を区別して表示する
正常状態と誤認させない
UI で補完して正常化しない
```

理由

```text
Silent failure は最も危険な不整合である
「表示されているが正しくない」状態を防ぐため
```

---

## Decision: Release requires analysis completeness

公開対象の analysis / data は  
UI が必要とする完全性を満たしている必要がある。

必須条件

```text
必要な *_latest.json が存在する
必要な *_i18n フィールドが存在する
UI が読むキーが揃っている
latest / view_model / explanation の整合が取れている
```

未達時のルール

```text
deploy しない
UI 修正で誤魔化さない
analysis 側で不足を補う
会社PCで再生成しない
```

理由

```text
UI は表示層であり
不完全な analysis を補完してはならないため
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

## Decision: Incomplete Input Guard (No Guessing Rule)

必要な情報が揃っていない場合、AIは生成を行ってはならない。

■禁止事項

- 推測による補完
- 仮データ生成
- fallback による誤魔化し
- 「とりあえず動く」実装
- 不完全な状態でのUI修正

■必須行動

1. 不足している情報を明示する
2. ユーザーに提出を求める
3. 情報が揃うまで生成を停止する

■優先順位

正確性 > 生成スピード  
整合性 > 見た目の完成度  
停止 > 推測生成

■理由

不完全な状態での生成は一見正しく見えるが、  
後に重大な不整合を生む。

GenesisPredictionは  
「それっぽい正解」ではなく  
「完全に整合した正解」のみを許容する。  
情報不足状態での出力は「無効」とみなす。

---

## Decision: LangChain is not adopted for Vector Memory (v1)

GenesisPrediction v2 における Vector Memory 実装では、  
LangChain などの外部オーケストレーションフレームワークは採用しない。

### 結論

```text
Vector Memory は
Qdrant + scripts / engines による
シンプル構成で実装する
```

### 理由

- 既存の責務分離（analysis / scripts / UI）がすでに完成している
- Vector Memory は reference-only であり、判断主体ではない
- LangChain を導入すると責務が曖昧になる可能性がある
- ブラックボックス化を防ぐため
- 再現性・デバッグ性を維持するため
- Partial obedience（便利だから入れる）を防ぐため

### 方針

```text
build_vector_memory.py を単一入口とする
vector_recall は scripts 側で実装する
Scenario Engine に最初に統合する
Prediction Engine では補助的に使用する
```

### 許可される将来拡張

```text
LangChain は将来的に以下用途に限定して検討可能
```

- query 構築補助
- metadata filter 整理
- rerank 補助

```text
ただし判断ロジックには関与させない
```

### 非交渉ルール

```text
LangChain は
- Prediction を生成しない
- Scenario を決定しない
- Explanation を生成しない
- UI と接続しない

Vector Memory は常に reference-only とする
```

Status: adopted

---

## 2026-04-02
### Sentiment Semantic Enrichment (B-1〜B-4)

Decision: Sentiment output is semantic, not score-only

`build_daily_sentiment.py` の出力は、  
単なる sentiment score の集合ではなく、  
Prediction 層へ渡すための semantic analysis として扱う。

必須出力

```text
theme_tags
signal_tags
risk_drivers
impact_tags
```

ルール

```text
sentiment = 数値 + 意味タグ
Prediction / Scenario はこの意味タグを参照してよい
UI はこれらを再解釈しない
UI はタグから意味を生成しない
```

意図

```text
score-only analysis からの脱却
Scenario / Prediction の説明力向上
analysis 層で意味圧縮を完了させるため
```

Status: adopted

---

## 2026-04-02
### World View Structured Summary Enforcement

Decision: World view summary must be structured-first

`build_world_view_model_latest.py` における summary は、  
自由文をそのまま採用するのではなく、  
structured summary から生成する。

ルール

```text
summary_structured = 正
summary = summary_structured から生成
壊れた upstream summary は構造に流し込まない
upstream_summary は malformed な場合 blank とする
```

補足

```text
event_count / risk_level / signal_density / top_headlines など
整合確認可能な structured fields を先に確定する
その後に summary を生成する
```

意図

```text
件数矛盾の防止
free text 汚染の防止
explanation の構造維持
```

Status: adopted

---

## 2026-04-02
### Prediction Must Use Semantic Analysis Fields

Decision: Prediction enhancement must consume sentiment semantic fields

Prediction 改善では、  
sentiment の score のみを使うのではなく、  
semantic fields を入力として扱う。

対象

```text
theme_tags
signal_tags
risk_drivers
impact_tags
```

ルール

```text
Prediction narrative は score-only で作らない
Prediction は signal / risk / impact を明示的に参照する
Prediction は Scenario の再説明ではなく
semantic analysis を圧縮した最終表現とする
```

意図

```text
テンプレ化された予測文の防止
drivers / watchpoints / invalidation の質向上
prediction の説明可能性向上
```

Status: adopted

---

---

## 2026-04-04
### Deploy Hardening (Full Replacement, Target-Only, Permission-Aware)

Decision: Deploy must be target-isolated and permission-aware

ルール

```text
- labos.soma-samui.com 以外のディレクトリを操作しない
- public_html 直下を削除しない
- 他サイト領域に影響を与えない
```

理由

```text
レンタルサーバーでは複数サイトが共存しているため、
誤削除は即サービス停止につながる
```

---

### Deploy Payload Self-Deletion Guard

Decision: Deploy must avoid self-deletion of payload

ルール

```text
cleanup 処理で deploy payload（tar）を除外する
find 使用時は必ず除外条件を入れる
例: find ... ! -name 'deploy_payload.tar.gz'
```

理由

```text
payload が削除されると展開不能となり、
空ディレクトリが生成される（silent failure）
```

---

### Deploy Permission Constraints (Conoha)

Decision: Deploy must be permission-aware

ルール

```text
- ディレクトリ自体の削除ではなく中身のみ削除する
- 許可されたパスにのみ scp / ssh を行う
- public_html 親階層への書き込み/削除を前提にしない
```

理由

```text
レンタルサーバーでは root 権限が無く、
rm -rf や配置先に制限があるため
```

---

## 2026-04-04
### Full File Integrity Reinforcement (Line Count & Copy Safety)

Decision: Line count integrity must be enforced

ルール

```text
- 元ファイルより大幅に行数が減る場合は生成禁止
- 行数減少は必ず理由を説明する
- 行数が半分以下になる場合は不完全とみなす
- 生成後に行数を自己確認する
```

理由

```text
長文ファイルでは一部欠落が検知しにくく、
重大な機能欠損や不整合を引き起こすため
```

---

Decision: Web copy-paste editing is prohibited for long files

ルール

```text
- 長文コードはWebからのコピペ編集を禁止する
- 必ずダウンロードファイルで編集する
- 保存可能形式での受け渡しを優先する
```

理由

```text
コードブロック崩壊、インデント破壊、
不可視文字混入により PowerShell / bash が誤動作するため
```

---


---

## 2026-04-04
### Deploy Verification Must Follow Deploy

Decision: Deploy must be verified immediately after deployment

ルール

```text
deploy 成功表示だけで完了とみなさない
deploy 後に公開先 JSON をローカル成果物と比較する
verification が失敗した場合は deploy 完了扱いにしない
```

最小確認対象

```text
analysis/prediction/prediction_latest.json
analysis/explanation/prediction_explanation_latest.json
```

比較先

```text
https://labos.soma-samui.com/data/prediction/prediction_latest.json
https://labos.soma-samui.com/data/explanation/prediction_explanation_latest.json
```

理由

```text
deploy は成功表示でも snapshot mismatch が起こり得る
silent failure を排除するには deploy 後検証が必須である
```

---

## 2026-04-04
### Morning Ritual End-to-End Chain Is Valid

Decision: Morning Ritual → Post Checks → Deploy → Verify の直列実行を正式運用として許可する

正式フロー

```text
run_morning_ritual.ps1
↓
run_post_ritual_checks.ps1
↓
run_deploy_labos.ps1
↓
verify_deploy.py
```

ルール

```text
analysis 完成前に deploy しない
post checks 未通過で deploy しない
verify 未実行の deploy は最終完了とみなさない
```

意図

```text
朝の儀式から公開確認までを一つの運用線として固定し、
手動判断の抜け漏れを防ぐため
```




---

## 2026-04-04
### Prediction Enhancement Phase 2 Completion (Recall Alignment & Text Quality)

Decision: Vector Memory remains reference-only in Prediction

ルール

```text
Prediction は Vector Memory を補助情報として参照する
Prediction の truth は Scenario / analysis に依存する
Vector Memory は prediction を上書きしない
UI は Vector Memory を直接参照しない
```

理由

```text
判断主体の一貫性維持
black-box 化の防止
SSOT 原則の維持
```

Status: adopted

---

Decision: Prediction recall support must stay internally consistent

ルール

```text
reference_memory.summary にヒットが存在する場合
Prediction 側の recall_support_level はそれと矛盾してはならない

compact item（arrays）が空でも
summary に基づく fallback により整合を保つ
```

理由

```text
summary と support_level の不整合防止
UI 表示の信頼性確保
Prediction の説明一貫性維持
```

Status: adopted

---

Decision: Prediction text must be short, strong, and public-facing

ルール

```text
prediction_statement / summary は最終要約とする
冗長な semantic 列挙を含めない
internal metadata（例: similar_cases=1）を本文に露出しすぎない

構造は以下に限定する
1. 結論
2. ドライバー / watchpoint
3. 歴史的文脈（必要な場合のみ）
```

理由

```text
Prediction を explanation と分離するため
可読性と公開品質の向上
情報過多によるノイズ防止
```

Status: adopted


---

## 2026-04-04
### Dirty Repo Guard Enforcement (Run Requires Clean Working Tree)

Decision: All run scripts must execute on a clean working tree

対象

```text
scripts/run_daily_with_publish.ps1
scripts/run_morning_ritual.ps1
scripts/run_morning_ritual_with_checks.ps1
```

ルール

```text
run系スクリプト実行前は working tree を clean にする

許可される方法
- git commit による clean 化

禁止
- dirty 状態での実行
- push による回避（無効）
- 同じ状態での再実行ループ
```

補足

```text
dirty guard は remote 状態ではなく
local working tree を基準とする

したがって
push は無関係
commit のみが解決手段である
```

理由

```text
未確定変更での分析生成を防ぐため
再現性を保証するため
deploy 不整合の防止
```

Status: adopted

---

## 2026-04-04
### Pre-Run Commit Rule (Operational Requirement)

Decision: Commit before run is mandatory

ルール

```text
run 前は必ず commit を行う

標準手順
git add -A
git commit -m "auto commit before run"
```

意図

```text
dirty guard 回避の標準化
運用の単純化
実行失敗ループの防止
```

Status: adopted

---

## 2026-04-04
### PowerShell Switch Parameter Rule (No Boolean Value Passing)

Decision: SwitchParameter must not receive explicit boolean values

対象

```text
PowerShell scripts
-AutoRebuildVectorMemory
```

ルール

```text
switch パラメータは値を渡さない

正:
-AutoRebuildVectorMemory

誤:
-AutoRebuildVectorMemory False
-AutoRebuildVectorMemory:$false
```

補足

```text
付ける = True
付けない = False

False を渡すと positional 引数として解釈され、
想定外のパラメータエラーを引き起こす
```

理由

```text
PowerShell の仕様に起因する事故防止
引数解釈バグの防止
```

Status: adopted

## 2026-04-04
### Scenario Engine Must Produce Causal Branches, Not Templates

Decision: Scenario output must be causal, branch-readable, and monitoring-linked

対象

```text
scripts/scenario_engine.py
analysis/prediction/scenario_latest.json
```

ルール

```text
scenario narrative はテンプレ説明文にしない
best / base / worst は因果の流れで記述する

最低構造
1. current flow
2. active pressure / signal
3. core drivers
4. propagation
5. branch watchpoint condition
6. historical background
```

補足

```text
watchpoints は単なる一覧ではなく branch trigger として扱う
watchpoint_roles は以下に整理する
- stabilization
- persistence
- escalation
```

理由

```text
Scenario を Prediction の土台として使うため
best / base / worst の説得力を高めるため
watchpoints を判断材料に昇格させるため
```

Status: adopted

---

## 2026-04-04
### Scenario Drivers Must Be Cause-Oriented

Decision: Scenario key_drivers must be cause-oriented and separated from outcomes

対象

```text
scripts/scenario_engine.py
scenario.key_drivers
scenario.structured_drivers
scenario.expected_outcomes
```

ルール

```text
key_drivers には原因寄りの driver のみを置く
state / intensity / meta tag / outcome を混ぜない

structured_drivers は以下で整理する
- core_drivers
- pressure_modifiers
- trend_context
- downstream_risks
```

補足

```text
downstream_risks は expected_outcomes 側へ寄せる
trend_context は narrative 材料とする
```

理由

```text
driver と outcome の混線防止
Prediction 側へ渡す因果材料の純化
説明可能性の向上
```

Status: adopted

---

## 2026-04-04
### Prediction Must Be Decision-Grade, Not Scenario Restatement

Decision: Prediction is the decision-grade conclusion layer

対象

```text
scripts/prediction_engine.py
analysis/prediction/prediction_latest.json
```

ルール

```text
Prediction は Scenario の再説明にしない
Prediction は判断に使える最終結論とする

prediction_statement は以下を優先する
1. dominant scenario
2. risk / direction
3. main propagation
4. escalation or branch condition
5. historical support（必要時）
```

補足

```text
primary_narrative は短く一本化する
長い scenario narrative の貼り付けを禁止する
```

理由

```text
Prediction と Explanation の責務分離
公開品質と判断性の向上
説明過多によるノイズ防止
```

Status: adopted

---

## 2026-04-04
### Prediction Drivers Must Be Limited and Cause-Oriented

Decision: Prediction key_drivers must be short and cause-oriented

対象

```text
scripts/prediction_engine.py
prediction.key_drivers
prediction.drivers
```

ルール

```text
prediction key_drivers は 4〜6 件程度に制限する
原因寄り driver を優先する
state / meta / trend label / monitoring item を混ぜない
```

禁止事項

```text
overall_direction_* の混入
risk_level_* の混入
pressure_easing の混入
watchpoint の混入
internal metadata の混入
```

理由

```text
意思決定時の視認性向上
driver の意味純度維持
Scenario との責務分離
```

Status: adopted

---

## 2026-04-04
### Prediction Monitoring Priorities Must Follow Branch Logic

Decision: Prediction monitoring_priorities must be ordered by branch logic

対象

```text
scripts/prediction_engine.py
prediction.monitoring_priorities
prediction.watchpoints
```

ルール

```text
monitoring_priorities は branch trigger を優先する
並び順は以下を基本とする
1. escalation
2. persistence
3. stabilization
```

補足

```text
単なる watchpoint 全列挙は禁止
分岐判定に効く項目を優先する
```

理由

```text
監視の優先順位を明確にするため
Prediction を判断支援として使いやすくするため
```

Status: adopted

---

## 2026-04-04
### Explanation Must Be Mirror-Only Across Structured Fields

Decision: Explanation must mirror prediction fields directly and must not reconstruct them from lower layers

対象

```text
scripts/build_prediction_explanation.py
analysis/explanation/prediction_explanation_latest.json
```

ルール

```text
drivers       = prediction.key_drivers / prediction.drivers を mirror
monitor       = prediction.monitoring_priorities / prediction.watchpoints を mirror
implications  = prediction.expected_outcomes / prediction.implications を mirror
risks         = prediction.risk_flags を mirror
invalidation  = prediction.invalidation_conditions を mirror
```

禁止事項

```text
scenario / signal / historical から explanation 用の再構成をしない
prediction に存在しない structured field を explanation 側で新規生成しない
```

理由

```text
Explanation が第二の truth layer になることを防ぐため
Prediction = truth / Explanation = mirror を厳密化するため
```

Status: adopted

---

## 2026-04-04
### Explanation May Clarify Reading, But Must Not Create New Truth

Decision: Explanation may structure reading guidance, but must not create new factual content

対象

```text
headline
summary
interpretation
decision_line
narrative_flow
must_not_mean
ui_terms
```

ルール

```text
Explanation は prediction の読み方整理に限定する
許可されるのは以下
- human-readable structuring
- mirror-based wording
- misread prevention
- UI term explanation
```

禁止事項

```text
新しい原因の追加
新しい watchpoint の追加
新しい implication の追加
Prediction にないリスク判断の追加
```

理由

```text
説明層の責務固定
UI 側の再解釈圧力抑制
analysis artifact 間の整合維持
```

Status: adopted

---


## 2026-04-04
### Scenario Driver Canonicalization Must Exclude Scenario Labels

Decision: scenario driver canonicalization must drop scenario-name labels before structured classification

対象

```text
scripts/scenario_engine.py
canonicalize_driver_token()
scenario.key_drivers
scenario.structured_drivers.core_drivers
```

ルール

```text
scenario label は driver に含めない
除外対象には以下を含む
- base_case / best_case / worst_case
- 基本シナリオ / 最良シナリオ / 最悪シナリオ
- กรณีฐาน / กรณีดีที่สุด / กรณีเลวร้ายที่สุด
```

補足

```text
シナリオ名は branch label であり cause ではない
driver canonicalization の入口で除去する
後段の structured_drivers / key_drivers / scenario narratives に流さない
```

理由

```text
scenario label が core_drivers に混入すると
Prediction へ非因果ラベルが伝播するため
driver purity を維持し
Scenario = cause-oriented branches を完成形として固定するため
```

Status: adopted

---

## 2026-04-04
### Prediction Enhancement (Cause-Oriented Scenario + Decision-Grade Prediction) Is Completed

Decision: Prediction Enhancement phase is complete when scenario drivers are purified and prediction remains decision-grade

対象

```text
analysis/prediction/scenario_latest.json
analysis/prediction/prediction_latest.json
scripts/scenario_engine.py
scripts/prediction_engine.py
```

完成条件

```text
scenario.key_drivers は cause-oriented driver のみ
scenario.structured_drivers.core_drivers は cause-oriented driver のみ
prediction.key_drivers は scenario core + semantic risk drivers を統合した短い因果列
prediction は explanation ではなく decision-grade conclusion を維持する
```

確認済み状態

```text
scenario.key_drivers
- banking stress
- currency instability
- social unrest

prediction.key_drivers
- banking stress
- currency instability
- social unrest
- military escalation
- market fragility
- energy supply risk
```

補足

```text
Scenario = 原因の整理
Prediction = 最終判断
Explanation = mirror
```

理由

```text
Prediction Enhancement の本命目的
「Predictionの質を1段引き上げる」
を architecture ルールとして固定するため
以後はこの状態を baseline として扱うため
```

Status: adopted

---

---
## 2026-04-04
### Scenario Transmission Must Be Deterministic Per Branch

Decision: Scenario transmission outcome must be deterministic by branch

対象

```text
scripts/scenario_engine.py
scenario.transmission_chain
scenario.transmission_chain_i18n
```

ルール

```text
best_case  は stabilizes / moderates 系に固定する
base_case  は down / up 系の中間悪化に固定する
worst_case は sharp / default 系に固定する

同じ driver でも
scenario が違えば
到達 outcome を変える
```

補足

```text
transmission_chain は
driver -> propagation -> outcome
の因果鎖として扱う

best_case なのに equities_down のような
branch と逆方向の終点を許可しない
```

理由

```text
Scenario を説明テンプレではなく
判断入力分岐として成立させるため
Prediction へ渡す因果の質を固定するため
```

Status: adopted

---

## 2026-04-04
### Scenario Narrative Must Be Built From Structured Drivers, Not Raw Tags

Decision: Scenario narrative must use structured_drivers as source of truth

対象

```text
scripts/scenario_engine.py
scenario.narrative
scenario.narrative_i18n
```

ルール

```text
narrative は raw signal / raw trend tag から直接組み立てない
narrative は structured_drivers を正規化して使用する

使用優先
- core_drivers
- pressure_modifiers
- trend_context
```

禁止事項

```text
overall_direction_* の露出
risk_level_* の露出
raw watchpoint token の露出
signal_tags / trend_tags 直接依存の narrative 生成
```

理由

```text
構造は正しいのに文章だけが汚れる事故を防ぐため
Scenario narrative を SSOT 準拠の説明文として固定するため
```

Status: adopted

---

## 2026-04-04
### Scenario Narrative Outcomes Must Align With Branch Outcomes

Decision: Scenario narrative outcome text must follow branch-specific deterministic outcomes

対象

```text
scripts/scenario_engine.py
scenario.narrative
scenario.expected_outcomes
scenario.transmission_chain
```

ルール

```text
best_case narrative は
equities_stabilizes / credit_spreads_moderates / growth_stabilizes / currency_stabilizes
を基準にする

base_case narrative は
equities_down / credit_spreads_up / growth_down / currency_down
を基準にする

worst_case narrative は
equities_sharp_down / credit_spreads_sharp_up / growth_sharp_down / currency_sharp_down
を基準にする
```

禁止事項

```text
best_case narrative に equities_down を混ぜる
worst_case narrative に弱い base 表現を残す
narrative と transmission の不一致を許可する
```

理由

```text
Scenario 説明文と因果鎖を一致させ
branch の説得力を固定するため
```

Status: adopted

---

## 2026-04-04
### Internal Scenario / Transmission Tokens Must Be Snake Case

Decision: Internal causal tokens must be snake_case and display text must be resolved only through i18n maps

対象

```text
scripts/scenario_engine.py
transmission_chain
expected_outcomes
watchpoint_roles
TERM_LABELS / TRANSMISSION_TERM_LABELS / OUTCOME_LABELS
```

ルール

```text
内部トークンは snake_case に統一する
表示文は i18n 辞書でのみ解決する

例
pressure_easing
mobility_restrictions
credit_spreads_sharp_up
unemployment_sharp_up
safe_haven_sharp_up
fiscal_subsidy_up
```

禁止事項

```text
snake_case と space-separated token の混在
内部トークンを表示用文字列として使う
UI で token を整形して救済する
```

理由

```text
因果鎖・outcome・i18n の整合を保つため
最後の token 混在バグを再発させないため
```

Status: adopted

---

## 2026-04-04
### Scenario Must Carry Invalidation Conditions

Decision: Each scenario branch must define invalidation conditions

対象

```text
scripts/scenario_engine.py
scenario.invalidation_i18n
```

ルール

```text
best / base / worst の各 branch は
その branch が崩れる条件を持つ

invalidation は explanation 用ではなく
判断破棄条件として扱う
```

補足

```text
best_case  = 再悪化で無効
base_case  = 安定化または同時悪化で無効
worst_case = ストレス緩和または信認回復で無効
```

理由

```text
Scenario を monitoring-linked branch として完成させるため
Prediction / Explanation の判断破棄条件を analysis 側で固定するため
```

Status: adopted

---

## 2026-04-04
### Scenario Engine Final Polish Completed

Decision: Scenario engine is considered production-ready when causal branches, deterministic transmission, aligned narratives, snake_case internal tokens, and invalidation are all present

対象

```text
analysis/prediction/scenario_latest.json
scripts/scenario_engine.py
```

完成条件

```text
1. key_drivers が cause-oriented
2. structured_drivers が cause / modifier / trend / downstream に分離
3. transmission_chain が branch deterministic
4. narrative が structured_drivers 準拠
5. narrative outcome と transmission が一致
6. internal token が snake_case に統一
7. invalidation_i18n を各 scenario が持つ
```

完成状態

```text
Scenario = cause-oriented branch engine
Prediction = decision-grade conclusion
Explanation = mirror
```

理由

```text
Prediction Enhancement フェーズの scenario 側ゴールを固定し
以後この状態を baseline として扱うため
```

Status: adopted


---

## 2026-04-05
### Markdown Editing Must Use Download-Based Full File Workflow

Decision: Long markdown files (especially decision_log.md) must not be edited via browser copy-paste

対象

```text
docs/*.md
特に decision_log.md
```

---

### 背景

ブラウザ経由のコピペ編集により以下の問題が発生した：

```text
コードブロック崩壊
インデント破壊
不可視文字混入
構造崩壊
PowerShell / bash 誤動作
```

---

### 新ルール

```text
.md ファイルはブラウザコピペ編集を禁止する
```

---

### 必須運用

```text
完全ファイルをダウンロード形式で受け取る
ローカルエディタで編集する
保存後に上書きする
```

---

### 禁止事項

```text
ブラウザ上での直接編集
部分コピペによる追記
差分貼り付け
コードブロックを含む断片編集
```

---

### 理由

```text
Markdown は構造依存が強く、
部分編集で容易に破壊されるため
```

---

### 既存ルールとの関係

```text
完全ファイルのみ
不完全生成禁止
長文ファイルはダウンロード形式優先
```

を強化するものである

---

### 本質

```text
Markdown はコードである

テキストではない
```

---

Status: adopted

---


## 2026-04-05
### Prediction Output Must Preserve Structure (No Partial Translation)

Decision:
Prediction output must never use partial word-level translation fallback.

Rule:
- Unknown phrases must remain unchanged (raw text)
- No word-by-word translation allowed
- All translation must be:
  - label registry based
  - phrase mapping based
  - or explicitly defined

Reason:
Partial translation creates corrupted mixed-language outputs
(e.g. "debtbubbleand銀行crisis")

Impact:
- Stabilizes i18n output
- Preserves semantic integrity
- Improves UI reliability

Status: adopted

---

## 2026-04-05
### Scenario Labels Must Not Use Generic Translation

Decision:
Scenario-related labels must always use SCENARIO_LABELS mapping.

Rule:
- base_case / best_case / worst_case must not go through labelize()
- Must use label_from_map(..., SCENARIO_LABELS)

Reason:
Scenario is structural truth, not free text

Impact:
- Prevents semantic drift
- Ensures consistency across prediction / explanation / UI

Status: adopted

---

## 2026-04-05
### Prediction Enhancement v4 Completed

Status: adopted

Summary:
- narrative compressed
- drivers structured
- monitoring converted to triggers
- invalidation clarified
- scenario → prediction alignment enforced
- vector memory restricted to reference-only
- i18n stabilized

Result:
Prediction Engine reached production-ready state

---

---

## 2026-04-05
### Prediction Layer i18n Must Be Fully Resolved in Analysis (Structure Fix)

Decision: Prediction layer i18n must be fully generated in analysis and must not rely on UI fallback

対象

```text
scripts/prediction_engine.py
analysis/prediction/prediction_latest.json
```

ルール

```text
すべての出力は *_i18n で完結させる
UI は翻訳・補完・fallback を一切行わない

translation = analysis
UI = selector only
```

必須条件

```text
reference_memory.summary_i18n を完全生成する
historical_pattern / historical_analog prefix を翻訳対象に含める
expected_outcomes を完全辞書化する

英語残り禁止
部分翻訳禁止
runtime補完禁止
```

禁止事項

```text
UIで翻訳する
UIでfallbackする
英語をそのまま表示する
単語単位の翻訳
```

理由

```text
i18n不完全状態はUI崩壊の原因となる
表示層での補完は責務違反である
analysis側で完全性を担保することで
再現性・安定性・整合性を確保するため
```

補足

```text
Step1: reference_memory i18n
Step2: historical prefix translation
Step3: expected_outcomes i18n

の3段階で構造固定を完了した
```

最終状態

```text
Prediction = fully localized structured output
Explanation = mirror
UI = read-only renderer
```

Status: adopted

---

---



## 2026-04-05
### Prediction Must Carry Structured Semantics (No Meaning Gap)

Decision: Prediction must carry fully structured semantic fields required for UI and explanation

対象

```text
scripts/prediction_engine.py
analysis/prediction/prediction_latest.json
scripts/build_prediction_explanation.py
```

ルール

```text
prediction は以下の structured field を持たなければならない

key_drivers_structured
  - driver
  - why
  - impact

monitoring_priorities_structured
  - item
  - trigger
  - meaning

implications_structured
  - outcome
  - path
  - confidence

invalidation_conditions_structured
  - condition
  - effect
```

補足

```text
explanation はこれらを mirror するのみ
explanation 側で構造補完を行わない
UI はこれらを表示するのみ
```

禁止事項

```text
explanation で意味を生成する
UI で意味を補完する
structured field を explanation 側で作る
```

理由

```text
意味の所在を prediction に一本化するため
Explanation を pure mirror として固定するため
UI を完全な表示層として維持するため
```

最終状態

```text
Prediction = structured truth
Explanation = mirror
UI = display only
```

Status: adopted

---

## 2026-04-05
### System Completion and Phase Transition to Operation

Decision: System is considered complete when end-to-end pipeline passes ritual + post + deploy + verify

対象

```text
scripts/run_morning_ritual_with_checks.ps1
```

ルール

```text
以下がすべて成功した場合、システムは完成とみなす

ritual OK
post OK
deploy OK
verify OK
exit code 0
```

補足

```text
この状態以降は開発フェーズではなく運用フェーズとする
新機能追加は禁止
UI調整のみ許可
```

理由

```text
完成基準を明確化し
無限開発ループを防ぐため
```

Status: adopted

---

---

## 2026-04-07
### Prediction History Must Be Synced to data Layer for UI

Decision: prediction history must be explicitly synced from analysis to data for UI consumption

対象

```text
analysis/prediction/history/*
data/prediction/history/*
scripts/run_daily_with_publish.ps1
```

ルール

```text
UI は data/prediction/history のみを参照する

analysis/prediction/history は
UI が直接参照してはならない

run_daily_with_publish.ps1 にて
history ディレクトリを毎回同期する

sync:
analysis/prediction/history → data/prediction/history
```

禁止事項

```text
UI が analysis/history を直接読む
手動コピーに依存する
history 未同期状態で deploy する
```

理由

```text
history が data 層に存在しない場合
UI は 404 を返し silent failure となる

analysis は SSOT だが
UI は distribution layer（data）を読むため
明示的な同期が必要である
```

補足

```text
prediction_latest / scenario_latest / reference_memory は
alias で同期されていたが

history は未同期だったため
今回の不整合が発生した
```

最終状態

```text
analysis = truth
data = distribution
UI = data only

history も distribution 対象に含める
```

Status: adopted


---

---

## 2026-04-07
### Local Server and Distribution Structure Must Be Strictly Distinguished

Decision: Local development server and distribution (dist) structure must not be confused

対象

scripts/run_server.ps1
dist/labos_deploy/*
python -m http.server
UI data loading paths

ルール

run_server.ps1 は開発用サーバーであり
配信構造（dist）とは一致しない

UIの最終確認は必ず dist を対象に行う

python -m http.server は
dist/labos_deploy をルートにして起動する

UIのfetchパスは dist 構造に一致している必要がある

禁止事項

開発サーバーで正常 → deployも正常とみなす
dist を通さずUI動作確認する
analysis / app を直接参照する

理由

開発サーバーと配信構造が一致しないため

ローカルでは正常でも
deployで404になる silent failure が発生する

補足

UI不具合のように見える問題の多くは
distribution mismatch に起因する

Status: adopted

---

## 2026-04-07
### UI 404 Debug Must Start From Distribution Layer

Decision: UI 404 errors must be debugged from distribution layer, not UI layer

ルール

UIで404が発生した場合の優先確認順

1. data 配信構造（dist）
2. history sync
3. ファイル存在確認
4. パス整合性
5. その後にUI

必須確認

dist/data/prediction/history/YYYY-MM-DD/prediction.json が存在するか
http.server で直接アクセス可能か
URLとファイルパスが一致しているか

禁止事項

即UI修正に入る
consoleエラーだけで判断する
仮fallbackで隠す

理由

UIエラーの多くは表示層ではなく
distribution層の不整合であるため

Status: adopted

---

## 2026-04-08
### GUI Final Audit Completed

Decision: GUI final audit is complete and UI is confirmed stable

ルール

```text
全ページで local / LABOS 一致確認済み
UI差分と distribution差分を分離して検証する
UIは表示のみ（display only）を厳守する
UIは修正対象ではなく、analysis / data を正とする
```

理由

```text
UI不具合と見える問題の多くは distribution / deploy に起因するため
設計原則（UI = display only）を最終監査で確認・固定するため
```

Status: adopted

---

### Pre-deploy Payload Freshness Check Is Mandatory

Decision: Deploy前に payload freshness を必ず確認する

ルール

```text
deploy前に dist/labos_deploy の snapshot を確認する

確認対象:
- data/world_politics/analysis/daily_summary_latest.json の date
- data/prediction/prediction_latest.json の as_of

local analysis/data と一致しない場合は deploy 禁止
```

理由

```text
古い dist payload を配信すると
UIは正常でも内容が不整合となるため

これは silent failure であり検知が困難であるため
deploy前チェックを必須運用として固定する
```

Status: adopted
---
---

## 2026-04-08
### EN as SSOT (Language Architecture Finalization)

Decision:
Prediction / Explanation の default language は英語（en）とする

Rule:
- lang_default = "en" を全analysis出力で固定する
- languages = ["en","ja","th"] を維持する
- ja / th は補助言語とする
- UI は selector のみで言語切替を行う
- UI は翻訳・fallback・補完を行わない

Reason:
- 国際標準化
- 一貫性確保
- UI責務の完全分離

Status: adopted

---
---

---

## 2026-04-08
### Explanation Pure Mirror Hardening

Decision:
Explanation は prediction の pure mirror とする

Rule:
- summary = prediction_statement
- drivers = key_drivers
- watchpoints = monitoring_priorities
- implications = expected_outcomes

禁止:
- lower layer（scenario / signal）から再構成
- explanation側で新規意味生成
- structured field の再生成

Reason:
- 第二のtruth層を排除
- SSOTの一貫性維持

Status: adopted
---
---

---

## 2026-04-08
### Structured Truth Consolidation

Decision:
structured semantic fields は prediction 層に集約する

Rule:
- structured_* は prediction のみ生成
- explanation は mirror のみ
- UI は表示のみ

Reason:
- 意味の所在を一本化
- デバッグ容易性向上

Status: adopted

---

---

---
## 2026-04-08
### Prediction Enhancement Phase1

Decision:
Prediction の因果性・判断性を強化

Enhancement:
- causal narrative 強化
- driver structure 拡張
- decision_actions 改善開始

Result:
- narrative が因果ベースへ進化
- decision_actions が部分的に具体化

Status: adopted


## 2026-04-08
### Decision Action Hardening (Branch-Linked Actions, Triggers, Outcomes)

Decision:
prediction.decision_actions must be scenario-aware, trigger-linked, and outcome-linked.

対象

```text
scripts/prediction_engine.py
analysis/prediction/prediction_latest.json
prediction.decision_actions
prediction.decision_action_links
```

ルール

```text
decision_actions は best / base / worst ごとに生成する
各 branch action は scenario branch の watchpoints / expected_outcomes と整合しなければならない
prediction 側で decision-grade な branch link を保持する
```

必須構造

```text
decision_actions
- base_case
- worst_case
- best_case

decision_action_links
- scenario_id
- watchpoints
- expected_outcomes
- primary_trigger
- stabilization_trigger
- persistence_trigger
- primary_negative_outcome
- primary_positive_outcome
- targets
```

branch rule

```text
base_case  = persistence-driven action
worst_case = deterioration-driven action
best_case  = stabilization-driven action
```

整合ルール

```text
action token と targets は一致させる
例:
cut::equities_sharp_down
⇔
targets.cut_target = equities_sharp_down

best_case.primary_trigger は stabilization 側 trigger を優先する
base / worst の primary_positive_outcome は空でよい
best の negative slot は negative outcome が無い場合は空とする
```

禁止事項

```text
scenario と逆向きの outcome を branch action に混ぜる
action token と targets を不一致のまま出力する
best_case に deterioration trigger を primary として置く
prediction 側で branch link を持たずに explanation / UI へ判断構造を委ねる
```

理由

```text
Prediction を decision-grade conclusion layer として完成させるため
Scenario の branch logic を行動判断へ橋渡しするため
watchpoints を単なる一覧ではなく action trigger として扱うため
Explanation / UI が新しい判断構造を作らずに済むようにするため
```

最終状態

```text
Scenario = cause-oriented branches
Prediction = decision-grade conclusion + branch-linked actions
Explanation = pure mirror
UI = display only
```

Status: adopted


---

## 2026-04-09
### Daily Summary Materialization Must Be Count-Based

Decision: daily_summary summary text must be materialized from structured count-based fields

対象

```text
scripts/run_daily_with_publish.ps1
data/world_politics/analysis/daily_summary_latest.json
analysis/daily_summary_latest.json
```

ルール

```text
daily_summary の summary は today.count と矛盾してはならない
count > 0 のとき "Observed 0 events." を出してはならない
summary materialization は free text 優先ではなく structured-first とする
summary は count-based に再生成する
```

理由

```text
today.count と summary の矛盾は
公開時の説明性と analysis completeness を壊すため
world summary は観測件数と整合した短文で固定する必要があるため
```

補足

```text
Observed {count} events. のような count-based summary を基準とする
Dominant anchors は count-based summary と矛盾しない範囲で付加してよい
UI はこの不整合を補正してはならない
```

Status: adopted


# END OF DOCUMENT
---
---