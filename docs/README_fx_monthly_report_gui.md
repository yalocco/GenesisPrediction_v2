# FX 月次レポート生成（手動GUI）

## 追加ファイル
- `scripts/fx_monthly_report_gui.ps1`

## 目的
- 会社PCでも安全に運用できるように、**自動実行ではなく手動ボタン**で月次レポートを生成する。
- 前月分（または月指定）をワンクリックで生成し、出力フォルダも開ける。

## 前提
- `.venv\Scripts\python.exe` が存在する
- `scripts\fx_remittance_monthly_report.py` が存在する（MD+CSV 出力版）
- 生成先: `data\fx\reports\`

## 実行方法
PowerShell で repo 直下から実行:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fx_monthly_report_gui.ps1
```

GUIのボタン:
- **前月レポートを生成**: 前月（YYYY-MM）を自動計算して生成
- **月指定で生成**: テキストボックスに `YYYY-MM` を入力して生成
- **出力フォルダを開く**: `data\fx\reports\` をエクスプローラで開く

## 出力
- `data\fx\reports\YYYY-MM.md`
- `data\fx\reports\YYYY-MM_summary.csv`
- `data\fx\reports\YYYY-MM_daily.csv`
