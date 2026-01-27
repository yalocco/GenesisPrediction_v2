# docker/analyzer/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# 依存を先に入れる（キャッシュが効く）
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# アプリ本体をコピー
COPY analyze.py /app/analyze.py
COPY anchors.py /app/anchors.py
COPY diff.py /app/diff.py
COPY history_analog.py /app/history_analog.py

# 念のため探索パスを固定（WORKDIRが変わっても壊れない）
ENV PYTHONPATH=/app

CMD ["python", "analyze.py"]
