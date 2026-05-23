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

WORKDIR /app

# builder의 user-level site-packages 복사 (gcc·apt cache 제외)
COPY --from=builder /root/.local /root/.local

# 소스 코드 (변경 빈도 가장 높음 → 마지막 layer)
COPY engine ./engine
COPY web ./web
COPY front ./front
# 작명 모듈이 data/hanja/korean_hanja_unihan.json (9,932자) 사용 — ADR-041 도메인 분리
COPY data ./data
# ADR-114: Skyfield + JPL DE440s ephemeris (1849-2150년 32MB, star 도메인 빅3·하우스·트랜짓)
COPY de440s.bsp ./de440s.bsp

# ADR-224 — Fly.io 가중치 호스팅 옵션 빌드
# 빌드 인자: --build-arg ENABLE_PALM_UNET=1 시 PyTorch 설치 + 학습 + 가중치 빌드 시 영속.
# 비활성 시 코어 이미지 영향 0 (Gabor fallback 작동).
# 사용:
#   fly deploy --build-arg ENABLE_PALM_UNET=1
# 효과: 외부 호스팅(S3·Hugging Face) 결단 우회 — 이미지 자체에 가중치 포함.
ARG ENABLE_PALM_UNET=0
ARG ENABLE_REAL_PALM_DATA=0
COPY requirements-ml.txt ./requirements-ml.txt
RUN if [ "$ENABLE_PALM_UNET" = "1" ]; then \
        pip install --user --no-warn-script-location -r requirements-ml.txt && \
        if [ "$ENABLE_REAL_PALM_DATA" = "1" ]; then \
            pip install --user --quiet gdown && \
            python -m engine.divination.palm.download_11k_hands \
                --output-dir data/palm/11k_dataset/ && \
            cp data/palm/11k_dataset/palmar_only/*.jpg data/palm/training/ 2>/dev/null || true ; \
        else \
            python -m engine.divination.palm.generate_training_data \
                --output-dir data/palm/training/ --n-images 500 --img-size 256 ; \
        fi && \
        python -m engine.divination.palm.train_unet \
            --data-dir data/palm/training/ \
            --output data/palm/unet_weights.pt \
            --epochs 10 --batch-size 8 --img-size 256 --model cfm && \
        python -c "from engine.divination.palm.self_training import run_self_training; \
            print(run_self_training( \
                initial_weights_path='data/palm/unet_weights.pt', \
                data_dir='data/palm/training/', \
                output_path='data/palm/unet_weights.pt', \
                n_iterations=3, epochs_per_iter=5, batch_size=8, img_size=256, \
                use_augmentation=True))" && \
        rm -rf data/palm/training/ data/palm/11k_dataset/ ; \
    fi

# 빌드 컨텍스트에 __pycache__ 잔존 시 정리 (런타임 무용)
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
