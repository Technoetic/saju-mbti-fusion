FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine ./engine
COPY web ./web
COPY front ./front
# 작명 모듈이 data/korean_hanja_unihan.json (Unihan 한자 풀 8525자) 사용
COPY data ./data

CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
