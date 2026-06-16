# ADR-057 Phase C3 — Docker 멀티스테이지 빌드 (Python builder + slim runner)
# 효과: 최종 이미지 ~1.2GB → ~400MB, 빌드 캐시 효율 ↑, Fly.io 512MB VM 적합성 ↑

# ──────────────────────────── Stage 1: builder ────────────────────────────
# 의존성 빌드 전용 (pip wheel 캐시 + 컴파일 부산물 격리)
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# 시스템 build 의존성 (PyMuPDF·numpy 등 wheel 미제공 시 필요할 수 있음)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# wheel 다운로드 + 설치 (다음 stage에서 site-packages 복사용)
RUN pip install --user --no-warn-script-location -r requirements.txt


# ──────────────────────────── Stage 2: runner ────────────────────────────
# 최종 운영 이미지 — builder 의 site-packages만 복사 (gcc 등 빌드 도구 제외)
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

# ADR-264 — 한글 폰트 설치 (시각화 오버레이 라벨 깨짐 해결).
# NanumGothic: ADR-259 palm visualization 손금 영역 라벨용.
# fc-cache 불필요 (PIL ImageFont는 절대 경로 직접 로드 — fontconfig 미사용).
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# builder의 user-level site-packages 복사 (gcc·apt cache 제외)
COPY --from=builder /root/.local /root/.local

# 소스 코드 (변경 빈도 가장 높음 → 마지막 layer)
COPY engine ./engine
COPY web ./web
COPY front ./front
# 정적 데이터 (한자 9,932자·사주·손금 JSON 등) — assets/ 로 분리.
# data/ 는 Fly.io 볼륨(saju_data → /app/data) 마운트에 가려지므로,
# 코드가 읽는 정적 데이터는 볼륨 밖 assets/ 에 둔다. data/ 볼륨은 app.db·백업 전용.
COPY assets ./assets
# ADR-114: Skyfield + JPL DE440s ephemeris (1849-2150년 32MB, star 도메인 빅3·하우스·트랜짓)
COPY de440s.bsp ./de440s.bsp
# ADR-246 — CFM 가중치 (11MB). models/ 별도 경로. unet_line_extractor 가 models/ 우선 탐색.
COPY models ./models

# ADR-245 — CFM 가중치 사전 학습 + repo 포함 + 빌드 시 COPY (학습 X)
# 이전 (ADR-224): 빌드 시 11k Hands 다운로드 + 5 epoch 학습 + self-training
#   = 45분~ CI 빌드. GPU(local) 학습 후 CI에서 반복하는 낭비 구조.
# 변경: data/palm/unet_weights.pt (11MB, CFM 5 epoch loss 0.0338) 를 repo 포함,
#   data/ COPY 시 자동 포함. PyTorch만 추가 설치.
ARG ENABLE_PALM_UNET=1
COPY requirements-ml.txt ./requirements-ml.txt
RUN if [ "$ENABLE_PALM_UNET" = "1" ]; then \
        pip install --user --no-warn-script-location -r requirements-ml.txt ; \
    fi

# 빌드 컨텍스트에 __pycache__ 잔존 시 정리 (런타임 무용)
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
