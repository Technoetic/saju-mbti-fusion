FROM python:3.12.13-slim-trixie

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine ./engine
COPY web ./web
COPY front ./front
COPY step_archive ./step_archive

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
