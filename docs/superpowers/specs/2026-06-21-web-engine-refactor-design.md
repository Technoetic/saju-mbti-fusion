# web/engine 구조 리팩터링 설계

**날짜**: 2026-06-21
**상태**: 설계 (승인 대기)
**원칙**: 작업량·리스크를 감수하더라도 **결과가 가장 좋은 구조** + 회귀 1738개 0 실패 유지

---

## 1. 배경·목표

현재 저장소는 동작·CI·보안 모두 안정 상태이나, 두 구조적 부채가 있다:

- `web/server.py` **4,540줄** — `PersonalityAPIServer` 단일 클래스에 Pydantic 모델 47개 + 핸들러 69개 + 미들웨어가 모두 집중.
- `engine/saju/` **21개 평면 모듈**, `engine/divination/` 루트에 `dream.py`·`saju_webtoon.py` 방치.

**이미 잘 된 부분(유지)**: server는 이미 클래스+async(82개), engine 결정론은 CPU-bound라 동기가 정답 → **async 신규 도입 없음**. 리팩터링은 *파일·모듈 경계 정리*에 집중한다.

목표: 도메인별로 응집된 모듈 경계 + 한 파일이 한 책임 + 회귀·CI 그린 유지.

---

## 2. 범위 (4 페이즈, 안전한 순서)

### Phase 1 — `web/schemas/` 분리 (리스크: 낮음)
- 요청/응답 `BaseModel` 47개를 도메인별 파일로 분리:
  `web/schemas/{saju,dream,palm,face,name,star,hwapae,clinical,auth,common}.py`
- `server.py`는 `from web.schemas.saju import SajuRequest, ...` 로 import.
- import 경로는 **새 경로로 전부 교체** (re-export shim 미사용 — 잔재 없는 깨끗한 상태).

### Phase 2 — `web/routers/` 분리 (리스크: 중, 효과: 최대)
- 핸들러 69개를 도메인별 `APIRouter`로 분리:
  `web/routers/{saju,dream,palm,face,name,star,hwapae,clinical,auth,user,ops,diary,iching,tarot,dormio,lucid,incubation,misc}.py`
- 공유 상태(결정론 엔진 인스턴스, 세션, sanitize 유틸)는 **모듈 단위 의존성 또는 router factory**로 주입.
- `PersonalityAPIServer`는 **조립자**로 축소: 미들웨어 등록 + `startup` 이벤트 + `app.include_router(...)`. 4,540줄 → 수백 줄.
- 라우트 경로·메서드·응답 스키마는 **동일하게 보존** (외부 계약 불변).

### Phase 3a — divination 방치 파일 이동 (리스크: 낮음)
- `engine/divination/dream.py` → `engine/divination/dream/orchestrator.py` (또는 `dream_lex/`와의 관계 확인 후 결정)
- `engine/divination/saju_webtoon.py` → `engine/divination/saju_mbti/webtoon.py`
- import 30곳 새 경로로 교체.

### Phase 3b — `engine/saju/` 그룹화 (리스크: 높음, 강행 결정됨)
21개 모듈을 책임별 하위 패키지로 그룹화. 33개 파일의 `from engine.saju.<m>` import를 새 경로로 전수 교체.

| 하위 패키지 | 포함 모듈 |
|---|---|
| `core/` | pillars, calendar, geo_lut, wuxing, luck_cycle |
| `shensha/` | shensha, twelve_sinsal, twelve_stages |
| `tengods/` | ten_gods, balance_meter |
| `compat/` | compat, mbti_compat_v2, mbti_functions |
| `hanja/` | hanja_data, alias |
| `media/` | music_gen, image_gen |
| `interpret/` | explain, myeong |
| 루트 유지 | cli, kasi_verifier |

각 하위 패키지에 `__init__.py` 추가. `engine/saju/__init__.py`는 주요 심볼을 re-export해 `from engine.saju import X` 상위 import는 보존.

---

## 3. 데이터 흐름 (불변)

리팩터링 후에도 ADR-010 결정론 분리는 그대로:
```
요청 → web/routers/<domain> (검증: web/schemas) → engine/<domain> 결정론(동기)
     → 시스템 프롬프트 주입 → engine/llm_async (async I/O) → safety sanitize → 응답
```
변경되는 것은 **파일 위치와 import 경로뿐**, 런타임 동작·API 계약·결정론 로직은 불변.

---

## 4. 안전 전략

- **페이즈별 독립 커밋**: Phase 1 → 2 → 3a → 3b 순서, 각 페이즈 후 검증 게이트.
- **검증 게이트(매 페이즈)**:
  1. `pytest tests/regression/ -q` → **1738 passed / 0 failed** 의무
  2. `pytest tests/smoke/ -q`
  3. `python -c "import web.server"` (앱 import 성공)
  4. 서버 기동 + 헬스체크 (Phase 2 후 전 엔드포인트 라우팅 확인)
- **깨지면 해당 페이즈만 롤백** (`git reset`), 원인 수정 후 재시도.
- **import 누락 0**: 각 이동마다 `grep -rn "옛경로"` 전수 확인 → 0건 될 때까지.
- **CI 확인**: 각 push 후 `CI/CD — Test & Deploy` + WebKit success 확인.

## 5. 비목표 (YAGNI)
- engine 결정론의 async 전환 ❌ (CPU-bound, 해로움)
- 새 기능·API 추가 ❌
- 라우트 경로/응답 스키마 변경 ❌
- `web/services/` 등 추가 계층 신설 ❌ (현 시점 불필요)

## 6. 리스크·완화
| 리스크 | 완화 |
|---|---|
| import 누락 → 회귀 대량 실패 | grep 전수 + 페이즈별 회귀 게이트 |
| 공유 상태 주입 누락(Phase 2) | router factory에 엔진 인스턴스 명시 주입, startup 순서 보존 |
| engine/saju 그룹화 대규모 변경(Phase 3b) | __init__ re-export로 상위 import 보존 + 33파일 grep 추적 |
| circular import | 그룹화 시 패키지 간 의존 방향 단방향 유지(core ← 나머지) |
