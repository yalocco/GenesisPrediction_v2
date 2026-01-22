python scripts\run_scenarios.py --latest
python docker/analyzer/analyze.py
docker compose run analyzer
docker compose build --no-cache analyzer
docker compose run --rm analyzer


python .\scripts\build_daily_summary_index.py
python .\scripts\plot_daily_summary_conf.py

python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install matplotlib
