# 会社PC用 検証コマンド・チートシート
GenesisPrediction_v2  
目的：Open-WebUI の回答を「事実で即検証」する

---

## 原則
- AIの回答は **必ずローカルで検証**する
- 架空パスは `Test-Path` で即否定
- 生成元は文字列検索で特定する

---

## 1. ファイルの存在確認（最重要）
Open-WebUI が出したパスは必ずこれで確認する。

```powershell
Test-Path .\scripts\fx_remittance_overlay.py
Test-Path .\scripts\publish_fx_overlay_to_analysis.py
Test-Path .\src\visualization\generate_overlay.py
