FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine ./engine
COPY web ./web
COPY front ./front
# 작명 모듈이 data/korean_hanja_unihan.json (Unihan 한자 풀 8525자) 사용
COPY data ./data

# 운영 컨테이너에서 회귀 테스트 제외 (Railway nixpacks가 .dockerignore의
# **/test_*.py 패턴을 무시하는 경우 대비한 명시 삭제)
# Diagnostic: Before deletion
RUN echo "=== BEFORE DELETE ===" && find /app/engine -name "test_*.py" -type f | wc -l

RUN find /app -name "test_*.py" -delete \
 && find /app -name "conftest.py" -delete \
 && find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Diagnostic: After deletion
RUN echo "=== AFTER DELETE ===" && find /app/engine -name "test_*.py" -type f | wc -l || echo "0 (success)"

CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
