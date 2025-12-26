# Genesis Diff JSON v1

## 概要
Genesis Diff は、前日（baseline）との差分を  
**機械可読（diff）＋ 人間可読（interpretation）** の両立を目的とした JSON 形式。

- 出力先: `analysis/diff_YYYY-MM-DD.json`
- 比較対象:
  - today: 当日データ
  - baseline: 原則として前日データ

---

## トップレベル構造

```json
{
  "schema_version": 1,
  "diff": {},
  "summary": {},
  "quality": {},
  "extensions": {}
}
