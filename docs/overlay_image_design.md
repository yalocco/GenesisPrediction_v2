# overlay_image_design.md
（overlay 画像読み込み・表示設計 / 運用前提）

## 目的

overlay.html における「画像の読み込み・表示設計・運用前提」を仕様として確定する。

本ドキュメントは **設計・契約（contract）** を定義するものであり、
この時点では **HTML/CSS の即時修正やGUI調整は行わない**。

### スコープ

- overlay における画像の
  - primary 選定（latest / dated）
  - 存在しない場合の挙動（fallback）
  - キャッシュ対策（?t=）
  - 表示が壊れない最小要件
  - 生成側・表示側の運用契約

### 非スコープ

- index / sentiment の変更
- overlay.html のレイアウト/デザイン調整（CSS修正）
- 画像生成ロジック自体の改善（Analyzer の中身）

---

## 前提（SST / Read-only）

- `data/world_politics/analysis/` は **Analyzer の成果物（SST）**。
- overlay.html は **SST を読むだけ**（書き換えない）。
- 画像の存在/更新/命名は **生成側の責務**、表示側は **安全に読み取る責務**。

---

## 画像の種別と役割

overlay で扱う画像は、原則として次の2系統に分ける。

### 1) latest（固定URL / primary）

- 役割：日次の「最新」を常に表示する
- 特徴：パスが固定で上書き更新される
- 例：
  - `data/world_politics/analysis/jpy_thb_remittance_overlay.png`

> overlay の基本表示は **latest を primary** とする。

### 2) dated（日付付き / optional）

- 役割：特定日を再現・比較・検証する
- 特徴：日付付きファイルで過去分を保持できる
- 例：
  - `data/world_politics/analysis/fx_overlay_YYYY-MM-DD.png`

> overlay は通常 latest を表示し、必要時のみ dated を指定して表示する。

---

## 表示の優先順位（primary / fallback）

画像読み込みは「壊れない」ことを最優先にする。
画像が存在しない日があっても **overlay 表示は正常系**とする。

### 優先順位（候補リスト）

1. `dated`（URL クエリ `?date=YYYY-MM-DD` が指定された場合のみ）
2. `latest`
3. `placeholder`（常に存在する静的ダミー画像）
4. 最終 fallback：画像枠は維持し、メッセージ表示（例：No image / not generated yet）

### placeholder の要件

- placeholder はリポジトリに同梱し **必ず存在**させる
- 推奨パス（例）：
  - `app/static/img/no_overlay.png`

---

## URL パラメータ仕様

### `?date=YYYY-MM-DD`

- 指定された場合：dated を最優先で試行する
- 例：
  - `/overlay.html?date=2026-02-10`
- dated が存在しない場合：fallback 規則に従い latest → placeholder へ降格する

---

## キャッシュ対策（Cache Busting）

latest は固定パスのため、ブラウザキャッシュで古い画像が表示される可能性がある。
これを回避するため、画像URLに `?t=` を付与する。

### 推奨（最も整合が取れる方式）

- ViewModel / JSON 側で `overlay_updated_at` を提供し、
  overlay.html はそれを `?t=` に使用する。

例（値の形式はどちらでも可）：

- ISO:
  - `overlay_updated_at: "2026-02-10T06:12:34+09:00"`
- epoch:
  - `overlay_updated_at_epoch: 1739145154`

画像 URL 例：
- `.../jpy_thb_remittance_overlay.png?t=<overlay_updated_at_epoch>`

### 非推奨

- `Date.now()` を毎回付ける（キャッシュ破壊しすぎて無駄が大きい）
- 日付だけ `?t=YYYY-MM-DD`（同日再生成の追随が弱い）

---

## 表示が壊れないための最小要件（UI安定性）

overlay は、画像が 404 / 未生成でも **レイアウトが崩れない**ことを要件とする。

- 画像枠（表示領域）は常に確保する
  - width/height もしくは aspect-ratio を後段で導入する想定
- 画像読み込み失敗時（onerror 等）は **次の候補へ自動切替**
- 最終候補（placeholder）も無い場合は
  - 画像枠は維持し、短い運用メッセージを表示する

推奨メッセージ例：
- `overlay image not generated yet (run_daily.ps1 not executed)`

※ 文言は Runbook（朝の儀式）と整合させること。

---

## 生成側（Analyzer / publish）との運用契約

表示が安定するために、生成側は次の契約を満たす。

### latest の契約

- 固定パスに毎日（または再実行時）上書き保存する
- 推奨：
  - `data/world_politics/analysis/jpy_thb_remittance_overlay.png`

### dated の契約

- 日付付きで保存する（過去保持）
- 推奨：
  - `data/world_politics/analysis/fx_overlay_YYYY-MM-DD.png`

### 任意（推奨）：状態ファイル

生成できない日があることを正常系として扱うため、
次のような軽量状態ファイルがあると運用が強くなる。

- 例：
  - `data/world_politics/analysis/overlay_status.json`
- 含めたい情報（例）：
  - `generated: true/false`
  - `reason: "missing fx csv" / "fetch failed" ...`
  - `updated_at`

※ 本ファイルは “あると強い” 推奨であり、必須ではない。

---

## 実装フェーズへの引き継ぎ（この設計の使い方）

本設計の反映は別フェーズで行う。

実装側（overlay.html / server / ViewModel）の作業は、以下を満たすこと：

- `?date=` があれば dated を先頭に候補リストを構築
- `?t=` は `overlay_updated_at` を使用
- fallback を必ず実装（404で止めない）
- placeholder を同梱し、最終 fallback を保証

---

## 変更履歴

- v1: overlay 画像読み込み・表示設計 / 運用契約を定義
