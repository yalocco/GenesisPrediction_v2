# Open-WebUI 質問テンプレ集
GenesisPrediction_v2（会社PC / gemma3:4b）用  
目的：推測（幻覚）を封じ、RAG検索＋根拠抽出だけをさせる

---

## 共通ルール（全テンプレ共通）
- 推測は禁止
- ナレッジベース（GenesisPrediction_v2）を必ず検索する
- 実在しないファイルパスは書かない
- 根拠コードの引用に `...` を含めてはいけない
- 根拠が出せない場合は「特定不可」と答える

---

## テンプレA：生成元特定（候補限定・最重要）
小モデルで最も安定する基本形。

> 次のファイルだけを根拠に検索して答えて：  
> - `scripts/fx_remittance_overlay.py`  
> - `scripts/publish_fx_overlay_to_analysis.py`  
>
> `jpy_thb_remittance_overlay.png` について  
> 1) 最初の生成（保存）箇所  
> 2) analysis/ へのコピー箇所  
> を、該当行を**省略なし**で引用して示して。  
> 上記以外のファイルパスを出してはいけない。推測禁止。

---

## テンプレB：存在確認（YES / NO 型）
幻覚チェック用。

> 次の文字列が repo 内に存在するかだけ確認して：  
> - `jpy_thb_remittance_overlay.png`  
> - `OUT_PNG`  
>
> ヒットした **実在ファイルパス一覧のみ**を出して。  
> 見つからなければ「見つからない」と答える。推測禁止。

---

## テンプレC：責務確認（docs 優先）
設計確認用。

> `scripts/xxx.py` の役割・責務を  
> docs（spec / runbook / README）および docstring から特定して。  
> 明示的な記述が無い場合は「見つからない」と答える。推測禁止。

---

## テンプレD：I/O 抽出（入力・出力）
データフロー確認用。

> `scripts/xxx.py` について  
> - 入力（CSV / JSON / ENV など）  
> - 出力（CSV / PNG / JSON など）  
> をコードから特定し、該当行を省略なしで引用して示して。推測禁止。
