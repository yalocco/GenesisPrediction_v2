# LABOS Deploy Runbook
GenesisPrediction v2

Purpose
-------

LABOS（labos.soma-samui.com）への deploy 手順と、
過去に発生したトラブルおよび対処方法を記録する。

この Runbook は以下の目的で作成される。

- 新しい AI / 新しい PC でも deploy を再現できる
- トラブル発生時に迅速に復旧できる
- GenesisPrediction Deploy Architecture を明文化する


------------------------------------------------------------
Architecture
------------------------------------------------------------

GenesisPrediction Deploy Flow

analysis (SST)
    ↓
payload build
    ↓
tar archive
    ↓
scp upload
    ↓
remote extract
    ↓
publish to webroot


Entry Point

scripts/run_deploy_labos.ps1


このスクリプトは以下を順に実行する。

1. build payload
2. deploy
3. publish
4. verify


------------------------------------------------------------
Deploy Command
------------------------------------------------------------

Deploy は以下のコマンドのみで実行可能。

```

powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1

```

このコマンドは以下を内部で実行する。

```

scripts/build_labos_deploy_payload.ps1
scripts/deploy_labos.ps1

```


------------------------------------------------------------
Payload Structure
------------------------------------------------------------

deploy payload

```

dist/labos_payload

```
static/
    index.html
    overlay.html
    digest.html
    sentiment.html
    common/

data/
    world_politics/
        analysis/

analysis/
    fx/

data/fx/
```

```

LABOS は **Static SST 構造**として公開される。

analysis が single source of truth である。


------------------------------------------------------------
LABOS Public URLs
------------------------------------------------------------

Example

```

[https://labos.soma-samui.com/static/index.html](https://labos.soma-samui.com/static/index.html)
[https://labos.soma-samui.com/static/overlay.html](https://labos.soma-samui.com/static/overlay.html)
[https://labos.soma-samui.com/data/world_politics/analysis/fx/fx_overlay_latest_usdthb.png](https://labos.soma-samui.com/data/world_politics/analysis/fx/fx_overlay_latest_usdthb.png)

```


------------------------------------------------------------
Important Deploy Rules
------------------------------------------------------------

GenesisPrediction deploy は以下のルールに従う。

1. analysis は read-only (SST)
2. UI は表示のみ
3. 計算は scripts 側で行う
4. deploy は payload から行う
5. server 側で計算を行わない


------------------------------------------------------------
Troubleshooting
------------------------------------------------------------


CRLF Error
----------

Error

```

bash: line 8: $'\r': command not found

```

Cause

Windows PowerShell から生成された script に
CRLF が含まれていた。

Linux shell は CRLF を認識しない。

Solution

deploy script を LF で保存する。

PowerShell 側では

```

Set-Content -NoNewline

```

などを使用する。



PowerShell Variable Parsing Error
---------------------------------

Error

```

$user@$host:$port

```

PowerShell が ":" を変数の一部と解釈してしまう。

Solution

```

"${user}@${host}:${port}"

```



Remote Command Failure
----------------------

旧方式

```

ssh user@host "command1 && command2"

```

これは quoting 問題を引き起こしやすい。

新方式

```

scp remote_script.sh
ssh user@host bash remote_script.sh

```

deploy では **remote script 方式を使用する。**



Tar Extract Failure
-------------------

Error

```

tar: release.tar.gz: Cannot open

```

原因

CRLF によりファイル名に `\r` が混入した。

対策

remote script を LF 固定にする。



Git Artifact Accident
---------------------

commit message の一部が
ファイルとして生成される事故が発生した。

例

```

entiment_timeseries health requirement…

```

対処

```

Remove-Item "entiment_timeseries*" -Force

```



------------------------------------------------------------
Best Practice
------------------------------------------------------------

deploy は常に以下の順序で実行する。

1. analysis を生成
2. payload build
3. deploy
4. verify


deploy は **必ず run_deploy_labos.ps1 を使用する。**


------------------------------------------------------------
Future Improvements
------------------------------------------------------------

将来的に以下を追加予定。

- deploy verification script
- release rollback
- deploy log archiving
- deploy version tagging


------------------------------------------------------------
History
------------------------------------------------------------

LABOS Deploy System Stabilized

2026-03

Key improvements

- remote script deploy
- CRLF safe execution
- one-command deploy
- payload architecture fixed


GenesisPrediction LABOS Deploy System は
この時点で安定状態に到達した。
```
