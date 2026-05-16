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

명세서(`관상 분석 명세서.md`) §3~§7 구현. Flutter→웹 SPA로 의도적 대체했고
나머지 §4~§7 모든 항목 라이브 반영.

**백엔드**
- 페르소나: 雲鶴道士 (운학 도사) — 12궁/오관/오형 어휘집 + 사극풍 어조 규칙
- 입력: `image_base64`, `age`, `gender`, `question`, `metrics`(클라이언트 산출)
- LLM: Gemini Vision (Bizrouter, `google/gemini-2.5-flash-lite`) → Claude Opus fallback
- 캐시: 이미지+보조정보+메트릭 SHA256 해시 키, 24h TTL
- 위기 감지: 화두에 자해·자살 신호 시 LLM 호출 우회 → 1393/1577-0199 안내

**클라이언트 (front/index.html)** — 명세서 §5/§6/§7
- **MediaPipe Face Landmarker** (`@mediapipe/tasks-vision`, ESM CDN lazy load)
  - 478 랜드마크 + 52 blendshape + GPU delegate
- **헤드 포즈 정규화** (§6.2): 양 눈꼬리 기울기 → 코끝 기준 아핀 회전
- **12 메트릭** (§5/§6.3):
  - 핵심 7개: 3정 비율, 콧방울 너비, 입꼬리 lift, 미간 폭, 얼굴형 5체질, 좌우 비대칭, **처첩궁/자녀궁 폭**
  - 보조 5개: z 분산(라이브니스), face_center_offset, head_tilt_deg, brightness, blendshapes(jaw/smile/brow/blink)
  - 모든 핵심 메트릭이 사극풍 라벨 동봉 (도탑/고르/아담, 명궁 좁다/고르다/트였다, …)
- **5중 가드** (§7):
  - 조도 0.18 미만 / 0.88 초과 (실시간 가이드)
  - 무표정 (jaw_open 0.30 / mouth_smile 0.40 초과)
  - 평면 사진 (z_variance < 0.0001)
  - 광각 왜곡 (face_center_offset > 0.18)
  - 얼굴 미감지
- **§6.1 가이드 UI**:
  - 카메라 화면에 사극풍 금색 타원 + 중앙 십자
  - 1초마다 실시간 색 변화 (녹/금/주황)
  - 캡처 후 품질 배지
- **§6.4 시각화**:
  - 6축 방사형 차트 (상정·중정·하정·콧방울·입꼬리·미간)
  - 사진 위 안면 윤곽 오버레이 (사극풍 금색 라인)
  - 6종 수치 카드

**자산 (face 탭 첫 진입 시 lazy 다운로드)**
- vision_bundle.mjs ~134 KB
- face_landmarker.task ~3.7 MB
- 이후 브라우저 캐시. face 탭을 안 열면 0 byte 추가.

**회귀 테스트**: `engine/divination/test_face_reading.py` 25개
- LLM 호출 없는 순수 로직 (해시·임계값·캐시·페르소나 어휘집)
- CI에서 fail-fast 게이트로 보호

## CI/CD

`.github/workflows/deploy.yml`:
1. Lint & Import Check — Python 3.12.13 + 의존성 + import 스모크 + pytest engine/
2. Deploy — Railway CLI 설치 + `railway up --detach`
3. Wait for new deployment SUCCESS — GraphQL `service(id:)` 폴링 (false positive/negative 방지)

GitHub Secret 필요: `RAILWAY_API_TOKEN` (계정 토큰)
