# F-1 GUI Panel Spec
（Observation → Hypotheses → Judgment / Read-only Dashboard）

## 0. 目的
F-1 は「判断を自動化するGUI」ではなく、
**人間が考えるために、情報を同一画面に整列するGUI**である。

- 観測（fact）
- 仮説（model output）
- 判断（human notes / next watch）

を「1画面で」往復できるようにする。

---

## 1. 基本原則（絶対）
1) GUIは “読む窓” であり “決める機械” ではない  
2) 数値（confidence）は強調しすぎない（補助情報）  
3) アナログは示唆として扱う（Notesが主）  
4) 当日速報は扱わない（前日確定主義）  
5) 1日=1ブロック、日付で完全に切る  
6) 欠損時は安全にフォールバックし、誤誘導しない

---

## 2. 画面の構成（1画面・3レーン）
上から下ではなく、**横3レーン**（同一高さで見比べる）を基本とする。

### Lane A: Observation（観測）
- 3行メモ（human）
- anchors_detail（added/removed/changed）
- top_domains / top_tokens（あれば）
- churn（あれば）
- 重要：これは「事実層」。断言や予測は置かない。

### Lane B: Hypotheses（仮説）
- change_reason_hypotheses（最大3）
  - hypothesis（短文）
  - rationale（短文）
  - anchors（サンプル）
  - confidence（各仮説の局所confidence）
- confidence_of_hypotheses（全体）
  - 表示は「小さく」
  - 可能なら `base + delta` も併記
    - base / analog_delta / reason（ツールチップ）

### Lane C: Judgment（判断）
- “What to watch next”（人が書く欄、または observation.md のテンプレ部）
- 「明日確認する指標 1〜3」
- 「結論」ではなく「次の観測のための問い」

---

## 3. Historical Analogs の扱い（Lane B と C の間）
Historical Analogs は “補助レイヤ” として配置し、誇張しない。

- Top 3 analogs
  - title
  - score
  - matched_tags
  - summary（短）
  - notes（details折りたたみ）
- 併記：historical_analog_tags（タグ一覧）

表示の注意：
- アナログは予測根拠ではない
- 「なぜ今日これが出た？」を考える材料
- Notes を説明責任の主にする

---

## 4. ナビゲーションとフォールバック
### 日付選択
- Date picker（YYYY-MM-DD）
- 「前日へ」「翌日へ」ボタン
- “latest” ボタン（最後に確定している日付へ）

### フォールバックの明示
- 指定日の daily_summary が無い場合：
  - latest にフォールバック
  - 画面上部に赤ではなく“淡い警告”で
    - 「fallback to latest (YYYY-MM-DD)」を明示

---

## 5. データ取得（API設計・追加/変更）
### 現状の想定
- GET /api/daily_summary?date=YYYY-MM-DD（※無ければ追加）
  - 無ければ latest を返す（fallback明示フラグも返す）
- GET /api/historical_analogs?date=YYYY-MM-DD（既存）
- GET /api/observation?date=YYYY-MM-DD（※可能なら追加）
  - docs/observation.md から当日ブロックを抽出して返す
  - ない場合は空（errorにしない）

### 返却フィールド（GUIが必要とする最小）
- date（実際に表示している日付）
- fallback: true/false + fallback_date
- confidence_of_hypotheses
- confidence_analog_base / delta / reason（あれば）
- change_reason_hypotheses（配列）
- historical_analogs（配列）
- observation:
  - memo3_lines（3行）
  - what_to_watch（テンプレ/人の追記）

---

## 6. 最小実装スコープ（F-1 MVP）
MVP は “読める” だけでよい。編集は後回し。

MVPでやる：
- 日付選択 + fallback 表示
- 3レーン表示（Observation / Hypotheses / Judgment）
- analogs表示（details）
- observation.md の当日ブロックを読み取り表示（read-only）

MVPでやらない：
- observation.md への書き込み（編集UI）
- 自動要約や自動判断
- 強い色やランキングUI

---

## 7. UXメモ（視覚の注意）
- 大きい文字で表示するのは “仮説文” ではなく “観測メモ”
- confidenceは小さく、補助的に
- Notes/Reason は折りたたみで常に見える位置に置く
- 「結論」欄は作らない（判断は人間の文章）

---

## 8. 実装開始のトリガ条件（やるタイミング）
次の条件が揃ったら、F-1を実装してよい：

- observation.md の構造が 2週間以上安定している
- 日次運用が迷いなく回せている
- GUIで “比較” したい日が増えてきた
