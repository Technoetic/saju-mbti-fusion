# 月下夢 (saju-mbti-fusion)

사주·MBTI·꿈·관상·임상 스크리닝을 통합한 인격 융합 대시보드. FastAPI 단일 백엔드 + 정적 SPA(`front/index.html`) 구성.

## 구조

```
engine/         결정론적 도메인 엔진 (사주/임상/안전/저장)
  saju/         사주 명리 (pillars, luck_cycle, ten_gods, myeong …)
  clinical/     임상 스크리닝 (PSQI, ISI, CES-D, BDI-K, STAI-K, IRT)
  divination/   점복 (꿈, 화패, 관상 face_reading)
  agents/       LLM 오케스트레이션 / 페르소나 / Jung 분류 등
  safety/       위기 감지, 법적 고지
  storage/      SQLite 영속 계층 (Railway 볼륨 /data/app.db)
web/            FastAPI 진입점 (`web.server:app`)
front/          정적 SPA + 캐릭터 영상 (운학 도사, 만월 아씨, 몽이 도령, 화선 낭자)
step_archive/   런타임 캐시 (관상 풀이 24h)
```

## 로컬 실행

```bash
pip install -r requirements.txt
export BIZROUTER_API_KEY=sk-br-v1-...
export BIZROUTER_BASE_URL=https://api.bizrouter.ai/v1
export DREAM_APP_DB_PATH=./local_app.db
uvicorn web.server:app --reload --port 8080
```

## Railway 배포

```bash
railway up
```

이 레포는 Dockerfile 빌더(`/Dockerfile`)로 빌드된다. 환경변수는 Railway 대시보드에서 주입.

## 핵심 환경변수

| 변수 | 용도 |
|---|---|
| `BIZROUTER_API_KEY` | Gemini 멀티모달 (관상/이미지) |
| `BIZROUTER_MODEL` | 기본 텍스트 모델 (`google/gemini-2.5-flash-lite`) |
| `BIZROUTER_IMAGE_MODEL` | 이미지 생성 모델 (`google/gemini-2.5-flash-image`) |
| `MINIMAX_API_KEY` | 음악 생성 |
| `ANTHROPIC_API_KEY` | Claude fallback (선택) |
| `DREAM_APP_DB_PATH` | SQLite 경로 (Railway: `/data/app.db`) |

## 관상 풀이 (`/api/face/reading`)

- 페르소나: 雲鶴道士 (운학 도사)
- 입력: 얼굴 이미지 base64 + 나이/성별/화두
- LLM: Gemini Vision (Bizrouter) → Claude Opus fallback
- 캐시: 이미지+보조정보 해시 기준 24h
- 위기 감지: 화두에 위기 신호 감지 시 1393/1577-0199 안내 후 풀이 미생성
