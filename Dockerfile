FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy engine without test files using BuildKit syntax
COPY --exclude=**/test_*.py --exclude=**/conftest.py engine ./engine
COPY web ./web
COPY front ./front
# 작명 모듈이 data/korean_hanja_unihan.json (Unihan 한자 풀 8525자) 사용
COPY data ./data

# 운영 컨테이너에서 불필요한 캐시 정리
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
