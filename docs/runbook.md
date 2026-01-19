# GenesisPrediction v2 Runbook
（Frozen Operational Guide）

## 0. 位置づけ
GenesisPrediction v2 は、
**未来を決めるシステムではなく、人間が考えるための道具**である。

本 Runbook は、
- 日次運用を安定させる
- 思考を歪めない
- 後から読み返しても意味が分かる

ことを目的に、**2026-01 時点の正解構成を凍結**したものである。

---

## 1. 全体思想（最重要）
- 数値は「結論」ではない
- アナログは「示唆」であり「証拠」ではない
- 判断は常に **人間が行う**
- システムは「観測 → 仮説 → 判断」を支援するだけ

---

## 2. 日次フロー（正式・固定）

### 2.1 データ生成（前日確定主義）
1. fetcher  
   - **前日分のみを確定データとして取得**
   - 当日速報は扱わない（ノイズ防止）

2. analyzer  
   - daily_summary_YYYY-MM-DD.json を生成
   - anchors / regime / historical analogs を確定

---

### 2.2 信頼度の微調整（D-1）
3. apply_confidence_analog_delta.py（D-1b）
   - historical_analogs に基づき confidence を ±0.05 微調整
   - **冪等（何度回してもドリフトしない）**
   - 理由は以下を必ず保存：
     - confidence_analog_delta
     - confidence_analog_reason
     - confidence_analog_base

---

### 2.3 観測ログ化（D-2 / D-3）
4. update_observation_md.py（D-2）
   - historical_analogs / notes を observation.md に自動転記
   - 日付単位で **idempotent upsert**

5. update_observation_memo_link.py（D-3）
   - 人間が書く「3行メモ」と historical analogs を対応付け
   - 「なぜこのアナログが出たか」を言語化するための足場

---

### 2.4 思考補助ヒント（E-2）
6. enrich_observation_memo_template.py（E-2）
   - tag / domain / token の **半自動候補**を提示
   - 数値評価は禁止
   - あくまで「考えるための材料」

---

## 3. GUI の位置づけ
- GUI は **生成装置ではない**
- daily_summary / observation を「読むための窓」
- 正解を示さない
- 判断を代行しない

※ GUI に表示されない日は「データが未確定」なだけで異常ではない

---

## 4. 設計上のルール（厳守）

### 4.1 データ管理
- data/ : Git 管理外
- resources/ : Git 管理対象
- docs/ : 思考ログ・設計意図として保存

### 4.2 STOP の扱い
- STOP は **最後の手段**
- 誤殺を避けるため、原則使用しない
- 使う場合は理由を docs に残す

---

## 5. 非目標（やらないこと）
以下は **v2 では意図的に行わない**：

- 自動判断
- スコア最適化
- 当日速報モード
- 未来断定
- 数値による意思決定の強制

---

## 6. 今後の拡張候補（未実装）
- F-1：GUI「観測 → 仮説 → 判断」1画面パネル
- E-3：候補の“強さ”を色/記号で示す非数値ヒント
- provisional mode（速報用・別ブランチ）

※ いずれも **本 Runbook を破らない範囲でのみ実施**

---

## 7. 状態宣言
GenesisPrediction v2 は、
**壊さずに深めるフェーズ**に入った。

急がず、1タスクずつ進める。
