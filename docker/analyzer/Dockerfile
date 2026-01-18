FROM python:3.13-slim

WORKDIR /app

COPY analyze.py .
COPY diff.py .
COPY history_analog.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "analyze.py"]
