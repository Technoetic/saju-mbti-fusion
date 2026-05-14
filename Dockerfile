FROM python:3.12.13-slim-trixie

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine ./engine
COPY web ./web
COPY front ./front

# 런타임 캐시 디렉터리 (face_reading 24h 캐시, 사주 일주 캐시 등)
RUN mkdir -p step_archive/face_reading_cache

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
