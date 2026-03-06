# Genesis Brain (GenesisPrediction v2)

Version: 2.0
Status: Active
Last Updated: 2026-03-06

---

# 0. Vision（Genesisの意味）

GenesisPrediction は単なるソフトウェアプロジェクトではない。

これは

**個人AI研究所（Personal AI Research Lab）**

として始まった長期研究プロジェクトである。

Genesis という名前には二つの意味がある。

1. すべてを失った後の **新しい始まり**
2. 旧約聖書の創世記（Genesis）からの着想

世界は常に大量の情報と混乱に満ちている。

GenesisPrediction はその混沌の中から

**秩序・意味・危険信号**

を見つけ出すためのシステムである。

---

# 1. Core Purpose（核心目的）

GenesisPrediction の目的は未来を完全に当てることではない。

目的は

**危険を早く知ること**

である。

その理由は

* 家族を守るため
* 資産を守るため
* 将来世代のため

である。

これは

**Global Risk Observation System**

として機能することを目標とする。

---

# 2. Personal AI Research Lab

GenesisPrediction は

人間 + AI

による研究環境として構築されている。

構造

```
Human (research direction)
+
AI (implementation)
+
Observation System
```

開発スタイル

```
Human → 設計
AI → 実装
Human → 評価
```

AIはツールではなく

**研究パートナー**

として扱う。

---

# 3. Continuous Observation（観測思想）

未来予測の最も重要な要素は

**継続的観測**

である。

GenesisPrediction は

Daily Observation System

として設計されている。

---

# 4. Morning Ritual

Daily pipeline は

**Morning Ritual**

と呼ばれる。

これは毎日世界を観測する儀式である。

```
Fetch
↓
Analyze
↓
Sentiment
↓
Digest
↓
Overlay
```

Morning Ritual は

**システムの心拍**

であり、

毎日安定して動くことが最優先である。

---

# 5. AI共同開発プロジェクト

GenesisPrediction v2 は **AI共同開発プロジェクト**である。

* 人間 + AI が共同で設計・実装・運用する
* そのため「設計思想」「運用ルール」「依存関係」を
  リポジトリ側に残し、スレ依存を断つ

---

# 6. 最重要の思想：SST（Single Source of Truth）

* 真実（SST）は **analysis/** のみ
* **data/** は素材（壊れても再生成できる）
* **scripts/** は工場（SSTを生成する）
* **app/static** は表示（読むだけ）

※公式定義は **docs/repo_map.md** を正とする。

---

# 7. 責務分離の思想

```
scripts/analyzer
    収集・分析・整形・集計（生成）

analysis
    公開・表示・判断の唯一の成果物（真実）

app/static
    UI（可視化と安全なfallback）

docs
    設計の固定化（迷いゼロ）
```

---

# 8. 安定優先（速度より再現性）

* 毎日回すパイプラインは「心拍」
* 完走が最優先
* 不安定状態で公開しない

※運用の公式は **docs/runbook_morning.md**

---

# 9. UI思想（商用品質）

* “派手さ”より **統一感・読みやすさ・壊れない**
* baseline を決めて全ページを揃える
* 事故防止（ダウンロード運用・freezeタグ）

※公式運用は **docs/gui_phase2_working_rules.md**

---

# 10. 進化の仕方（フェーズ分離）

* GUI改善とデータ改善を混ぜない
* 変更は最小単位で commit
* 安定点に tag（Freeze）

戻れることが進化の条件。

※作業ルールは **docs/working_agreement.md**

---

# 11. 長期進化の方向

将来的に GenesisPrediction は

```
News
↓
Sentiment
↓
Trend Detection
↓
Signals
↓
Risk Score
↓
Scenario
↓
Prediction
```

という構造へ進化する可能性がある。

これは

**Global Risk Radar**

として機能する。

---

# 12. LABOS

LABOS は GenesisPrediction の公開研究所である。

将来提供する可能性があるもの

* Daily Risk Digest
* Global Risk Radar
* FX Monitoring
* Scenario Analysis

ただし目標は巨大企業ではない。

**小さく長く続く研究所**

である。

---

# 13. Legacy

GenesisPrediction は

会社ではなく

**知識・データ・システム**

を残すことを目的とする。

これは

未来世代に残る

**デジタル研究資産**

である。

---

# 14. TODO（育成枠）

* Prediction層の思想整理
* FX意思決定ロジック
* Pattern detection
* Scenario generation
* Risk scoring

研究は

```
Observation
↓
Hypothesis
↓
Verification
↓
Freeze
```

のサイクルで進む。
