---
type: prompt_template
target: deepresearch
purpose: SaaS의 외부 LLM 의존성 리스크 평가 + 폐쇄형 대안 객관 정보
created: 2026-05-17
related_adr:
  - ADR-005-claude-opus-vision (Anthropic 채택)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-013-prompt-cache-telemetry (캐시 인프라)
---

# 딥리서치 프롬프트 — LLM 의존성 리스크 + 대안 평가

## 사용법

본 SaaS는 6개 페르소나가 모두 외부 LLM (Anthropic Claude + Bizrouter Gemini)
의존. 단일 벤더 장애·가격 변동·정책 변경 시 전 서비스 중단 위험.

본 프롬프트로 객관 리스크 평가 + 대안 옵션 정보 수집.

---

## 프롬프트 본문

```
한국 소형 SaaS의 외부 LLM 의존성 리스크 평가 + 대안 옵션 객관 정보를 다음
요구사항에 맞춰 조사·정리해주세요.

## 본 SaaS 컨텍스트

LLM 사용 패턴:
- engine/divination/face_reading.py — claude-opus-4.7 vision (관상)
- engine/divination/palm_reading.py — claude-opus-4.7 vision (손금)
- engine/divination/name_reading.py — claude-opus-4.7 (작명 풀이)
- engine/saju/explain.py — call_llm_sync (사주 해석)
- engine/divination/dream.py — call_llm_sync (해몽)
- engine/saju/image_gen.py — Gemini 또는 별도 이미지 생성

라우팅:
- Bizrouter (Anthropic 호환 게이트웨이) 우선
- 실패 시 Anthropic SDK 직접 호출 fallback
- 일부 모듈은 Bizrouter의 Gemini 모델 사용

리스크 영역:
- 벤더 단일 장애 (Anthropic 5xx 또는 Bizrouter 다운)
- 가격 변동 (월 1회 이상 변동 가능)
- 정책 변경 (페르소나 출력 차단·콘텐츠 정책)
- API 키 만료·rate limit 초과
- 모델 deprecated (claude-opus-4-7 → 다음 버전 마이그레이션)

## 요구사항

### 1. 리스크 매트릭스 (객관 평가)

각 리스크의 확률·영향·완화 방법:

| 리스크 | 확률 | 영향 | 현 상태 |
|---|---|---|---|
| Anthropic 5xx 장애 | 월 1-2회 (status.anthropic.com 통계) | 전 페르소나 중단 | Bizrouter 우회 가능 |
| Bizrouter 장애 | ? | ? | Anthropic 직접 호출 fallback |
| 가격 인상 | 분기별 | 운영 비용 ↑ | ? |
| 모델 deprecated | 6-12개월 | 마이그레이션 작업 | ADR-005 후속 |
| 콘텐츠 정책 변경 | 분기별 | 페르소나 차단 | ? |

조사:
- status.anthropic.com 과거 12개월 장애 빈도·지속 시간
- Anthropic 모델 라이프사이클 정책 (deprecation 통지 기간)
- 가격 변경 이력 (2024-2026)

### 2. 폐쇄형 대안 평가

다음 옵션의 비용·성능·라이선스·운영 복잡도:

#### A. 멀티 벤더 (OpenAI / Anthropic / Gemini 동시)
- 추가 비용
- 라우팅 로직 복잡도
- 페르소나 일관성 (다른 모델로 같은 어조 유지 가능?)

#### B. 로컬 LLM (FLUX.1·Llama 3.x·Mistral 등)
- VRAM 요구사항 (8GB·16GB·24GB·48GB)
- Railway 환경 GPU 비용
- 페르소나 (만월 아씨·운학 도사 사극풍) 품질 유지 가능?
- 데이터 유출 방지 효과 (사용자 사진·꿈 텍스트)

#### C. 한국 LLM (네이버 HyperCLOVA·KT 믿음·LG 엑사원)
- 한국어 어조 (사극풍 가능?)
- API 가격
- 운영 안정성
- 가입·결제 절차

#### D. 단일 벤더 유지 + 회복 로직 강화
- Circuit breaker 패턴
- Rate limit 감지·우회
- 캐시 의존도 ↑ (현 prompt caching 활용)
- 사용자 통보 (현 페르소나 어투 유지하는 우아한 장애 메시지)

### 3. 페르소나 일관성 평가

본 SaaS 6 페르소나:
- 만월 아씨 (사주, 사극풍 여성)
- 운학 도사 (관상, 사극풍 남성 노년)
- 옥선 할미 (손금, 사극풍 여성 노년)
- 묵향 선생 (작명, 사극풍 남성)
- 몽이 도령 (해몽, 사극풍 남성 청년)
- 화선 낭자 (타로, 사극풍 여성)

조사:
- 멀티 벤더 운영 시 동일 페르소나 출력 품질 차이 측정 방법
- 페르소나 system prompt를 다른 모델로 이식했을 때 어조 보존도
- 회귀 테스트로 페르소나 일관성 자동 검증 방법 (output_safety_gate.py 확장 가능?)

### 4. 비용 시뮬레이션

가정:
- 일 사용자 100명 (운영 초기)
- 사용자당 평균 3 페르소나 호출 (사주 + 관상 + 작명 등)
- 사용자당 평균 5000 입력 토큰 + 1500 출력 토큰

각 옵션 월 비용 산출:
- Anthropic Opus 4.7 단독 (현재)
- 멀티 벤더 (50/50)
- 로컬 LLM (GPU 인스턴스 월 임대)
- 한국 LLM (네이버·KT·LG)

### 5. 마이그레이션 계획 (현 시점 합리적이면)

ADR-005 (Anthropic 채택) 유지 시:
- prompt caching 의존도 ↑로 비용 절감 (현 ADR-013 telemetry로 측정 가능)
- circuit breaker 추가
- 사용자 통보 UI 강화

다른 옵션 채택 시:
- 단계별 마이그레이션 로드맵
- A/B 테스트 가능성

### 6. 절대 조건

- 단일 옵션 권장 금지 (사용자가 결정)
- 검증 불가 비용·성능 데이터 거부
- "○○가 최고" 같은 단정 금지
- 가짜 인용 거부 (Anthropic·OpenAI 공식 문서 또는 GitHub·블로그 URL 명시)

## 출력 형식

마크다운 보고서:
1. 리스크 매트릭스 (확률·영향·완화)
2. 폐쇄형 대안 4종 비교 (A·B·C·D)
3. 페르소나 일관성 평가 방법
4. 비용 시뮬레이션 (3-5가지 시나리오)
5. 마이그레이션 옵션별 로드맵
6. 출처 (Anthropic·OpenAI·Google·KISA·관련 블로그 URL)
7. 본 SaaS 적용 시 면책 — "사용자 결정 영역"

## 메타

본 조사 결과는 ADR-005 후속 결정 자료. 본 보고서 + 운영 트래픽 데이터 + 사용자
비즈니스 결정으로 통합 결정 가능. AI 단독 결정 불가 (🔵 사업 단계).
```

---

## 결과물 처리 절차

1. 결과 .md를 `사주/[보고서명].md`로 저장
2. `/squeeze-report` 명령어로 처리
3. ACCEPT 항목: 객관 정보 vault 영속화
4. DEFER 항목: 모델·벤더 선택은 사용자 결정

## 우선순위

🟡 **SaaS 운영 시작 후 1-3개월** — 트래픽 데이터 누적 + 첫 장애 경험 후 본 보고서가 가장 가치 있음. 운영 전 실행은 추측 작업 비중 ↑.

## 면책

본 조사 결과는 객관 정보 + 옵션 비교. 모델·벤더 선택은 사용자 + 비즈니스 결정. AI 단독 결정 불가.
