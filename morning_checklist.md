■ GenesisPrediction
朝の健康チェック判定表（運用メモ）
■ ① 最初にこれだけ見る
NG = ?

NG = 0 → ✅ 運用継続

NG ≥1 → ↓へ

■ ② NG数で判断
NG数	判定	行動
1	🟢 軽微	様子見
2〜3	🟡 注意	原因確認
4以上	🔴 危険	調査開始
■ ③ core含まれるか
core（最重要）

daily_summary_latest.json

prediction_latest.json

global_status_latest.json

health_latest.json

判定

coreなし → 部分障害（継続OK）

coreあり → ☠️ 即対応

■ ④ Morning Ritual 完走確認
[OK] Morning Ritual completed

出てる → OK

出てない → ☠️ 即調査

■ ⑤ 最終4行チェック（超重要）
[OK] main
[OK] prediction
[OK] fx decision
[OK] health

全OK → 正常

1つでもNG → 該当層確認

■ ⑥ global_status 確認
AS_OF
RISK
SENTIMENT
FX
ARTICLES
HEALTH
判定

全部埋まってる → 統合OK

空あり → integration問題

■ ⑦ health意味
OK   <= 24h
WARN <= 48h
NG   > 48h
判断

WARN → 問題なし（鮮度低下）

NG → 要確認

■ ⑧ NG原因の切り分け
状態	原因
ファイルなし	生成失敗
古い	更新停止 / API
表示だけ変	integration不具合
guard停止	正常停止
FXだけ古い	API制限
■ ⑨ 層別チェック
層	見る場所
news	run_daily_with_publish
prediction	trend / signal / scenario / prediction
fx	fx_rates / inputs / overlay / decision
integration	refresh_latest_artifacts
■ ⑩ 最終判断テンプレ
NG=0 → 運用継続
NG=1 → 様子見
NG=2-3 → 部分障害
NG>=4 → 調査
core含む → 即対応
未完走 → 即対応