cd D:\AI\Projects\GenesisPrediction_v2
docker compose build
docker compose build analyzer
docker compose build fetcher
docker compose run --rm fetcher
docker compose run --rm analyzer

docker compose build --no-cache
docker compose build analyzer
docker compose build fetcher
docker compose run --rm fetcher
docker compose run --rm analyzer

docker compose down --remove-orphans

git pull
git pull origin main
docker compose build
docker compose run fetcher
docker compose run analyzer

✅ docker compose build --no-cache
用途：キャッシュを一切使わずに「全部作り直す」
使う場面：
Dockerfile / requirements.txt / ベースイメージ周りが変わった
「反映されてない気がする」系のトラブル時の最終手段
注意：遅い（毎回やる必要は基本ない）

✅ docker compose build analyzer
用途：analyzer サービスだけビルド
使う場面：
docker/analyzer/*（analyze.py / diff.py / requirements.txt / Dockerfile 等）を変えた
あるいは pull でそれらが更新された
補足：キャッシュは使う（速い）

✅ docker compose build fetcher
用途：fetcher サービスだけビルド
使う場面：
docker/fetcher/* や fetcher の Dockerfile・依存が変わった

✅ docker compose run --rm fetcher
用途：fetcher を 1回実行して終了（バッチ実行）
--rm：終わったらコンテナを自動削除（孤児が増えない）
あなたの用途（毎日 fetch/analyze してファイル生成）にはこの形式が合ってる

✅ docker compose run --rm analyzer
用途：analyzer を 1回実行して終了
これで summary.json や diff_YYYY-MM-DD.json が出る

✅ 反映される条件
docker compose build (analyzer/fetcher) をしたあとに
docker compose run ... で実行した場合
❌ 反映されない典型
.py を編集したのに build せず run した
→ 前のイメージのまま動くことがある（ここでハマりがち）

B. コンテナ自体は変更を保持する？
docker compose run は基本 使い捨てコンテナなので…
--rm あり：終了したら消える → 保持しない
--rm なし：終了してもコンテナが残る → ただ残骸（orphan になりやすい）

変更したファイル                       やること
docker/fetcher/fetcher.py	         docker compose build fetcher
docker/fetcher/requirements.txt	     docker compose build fetcher

docker/analyzer/analyze.py	         docker compose build analyzer
docker/analyzer/diff.py	             docker compose build analyzer
docker/analyzer/requirements.txt     docker compose build analyzer

volumes / command / depends_on       docker compose build
README.md / docs/*                   何もしなくてOK


----git pull した直後にやること（最重要）----
git pull
git status
その後：
Dockerfile が変わった	              docker compose build --no-cache（安全）
analyzer のコードが変わった	           docker compose build analyzer
fetcher のコードが変わった	           docker compose build fetcher
両方	                              docker compose build

その後
docker compose run --rm fetcher
docker compose run --rm analyzer
.\.venv\Scripts\python.exe scripts\build_daily_summary_index.py
.\.venv\Scripts\python.exe scripts\plot_*.py
------------------------------------------
実行（run）の正しい使い方
docker compose run --rm fetcher
docker compose run --rm analyzer

Found orphan containers
docker compose down --remove-orphans

#failed to prepare extraction snapshot ... parent snapshot ... does not exist
docker builder prune -af
docker system prune -af

毎日必ず回す
python .\scripts\run_daily_pipeline.py --with-scenarios

Docker がどれだけ食ってるか確認
docker system df
ビルダーキャッシュだけ掃除（安全寄り）
docker builder prune -a -f
