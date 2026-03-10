# FX送金判断｜推奨行動自動化 引き継ぎ

## 追加ファイル
- fx_remittance_recommend.py

## 役割
WARN時の仕送り判断をルールベースで自動化し、
人間判断によるブレ・判断疲れを防ぐ。

## 使用想定
- fx_remittance_today.py から呼び出し
- fx_remittance_log.py の recommended_action 列生成

## 出力例
- send_normal
- half_next_week
- split_3
- wait_or_small
- wait

## 設計思想
- 当てない
- ノイズが高い日は行動を抑制
- 実務判断を軽くする
