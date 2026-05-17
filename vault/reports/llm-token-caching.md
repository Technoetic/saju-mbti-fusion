---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: infra
applied_to:
  - L2 적중률 측정 → ADR-013 + engine/safety/prompt_cache_telemetry.py (2026-05-17)
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-010-name-sibling-factuality.md
  - decisions/ADR-005-claude-opus-vision.md
original_file: ../../LLM 토큰 절약을 위한 캐싱 전략.md
---

# LLM 토큰 캐싱 전략 — 사실성 검토

## 보고서 요약

다계층 캐싱: ① KV 캐싱(모델 내부) → ② 프롬프트 캐싱(인프라) → ③ 시맨틱 캐싱(애플리케이션) → ④ 응답 캐싱.
벤더별 메커니즘 비교 (OpenAI / Anthropic / Google / Bedrock).

## 🟢 팩트 (검증 가능)

| 주장 | 검증 |
|---|---|
| KV 캐싱은 트랜스포머 표준 기법 ($O(N^2d)$ → $O(N \cdot d)$) | ✅ 기술 사실 |
| OpenAI 프롬프트 캐싱 자동 (1024 토큰 이상, 256 토큰 접두사 해싱) | ✅ 공식 문서 일치 |
| Anthropic `cache_control` 명시 분기점 | ✅ 본 프로젝트 face_reading.py에서 이미 사용 |
| Anthropic 5분 TTL 기록 1.25배, 읽기 0.1배 | ✅ 공식 가격 정책 일치 |
| 시맨틱 캐싱 — 코사인 유사도 / ANN 인덱싱 | ✅ 표준 기법 |
| 벡터 임베딩으로 의미 유사 쿼리 매칭 | ✅ 표준 |

## 🟡 구조 (시스템 설계 명제)

- 다계층 캐싱 (L1 KV → L2 프롬프트 → L3 시맨틱 → L4 응답)
- 정적/동적 콘텐츠 분리 배치 (정적 → 상단, 동적 → 하단)
- 캐시 예열(Pre-warming) 패턴

## 🔴 도그마 / 부정확 / 검증 불가

| 항목 | 판정 |
|---|---|
| "최대 80~90% 절감" 단정 | 환경 의존적, 일률 적용 불가 |
| **OpenAI 모델명 "gpt-5.5", "gpt-5.4"** | ❌ 2026-05 현재 존재 미확인 — 보고서 작성 시점 기준 가상 또는 미공개 모델일 가능성. 본 프로젝트 사용 모델 아님 |
| **Anthropic 모델명 "Opus 4.7 / 4.6 / 4.5"** | ✅ Opus 4.7은 본 환경 (1M 컨텍스트). 다른 버전 가격은 별도 확인 필요 |
| 가격표 구체 수치 (gpt-5.5 $12.50 등) | 출처는 OpenAI/Anthropic이라 명시되지만 직접 검증 필요 — 벤더 가격 정책은 변동성 큼 |
| "AWS Marketplace CCU 100 = $1" | 검증 보류 — 본 프로젝트 AWS 미사용 |
| "Bash 245 토큰, 텍스트 에디터 700 토큰" 시스템 오버헤드 | 본 프로젝트는 Claude API 직접 호출이라 무관 |
| "Computational Déjà Vu" 같은 광고성 신조어 | 수사 — 무시 |

## 본 프로젝트 현 상태 매핑

| 보고서 권장 | 본 프로젝트 현 상태 |
|---|---|
| KV 캐싱 (모델 내부) | 자동 — 본 프로젝트 관여 X |
| 프롬프트 캐싱 (Anthropic cache_control) | ✅ [engine/divination/face_reading.py:218](../../engine/divination/face_reading.py) `"cache_control": {"type": "ephemeral"}` |
| 정적 시스템 프롬프트 분리 | ✅ face_reading.py 이미 적용 |
| 로컬 파일 캐시 (응답 캐싱) | ✅ `step_archive/face_reading_cache/` |
| `lru_cache` (Python 인메모리) | ✅ face_reading.py:144, 156 |
| 시맨틱 캐싱 (벡터 유사도) | ❌ 미적용 |
| 캐시 예열 패턴 | ❌ 미적용 (현재 트래픽 낮아 불필요) |

**평가**: 본 프로젝트는 **인프라 캐싱 (L2) + 응답 캐싱 (L4)** 이미 적용. 시맨틱 캐싱 (L3)는 미적용이나 본 프로젝트 특성상 ROI 낮음 — 다음 절 참조.

## 본 시스템 반영

### ✅ 이미 적용 완료

본 프로젝트는 face_reading.py에서:
1. **Anthropic `cache_control: ephemeral`** — 시스템 프롬프트 + 페르소나 캐시
2. **로컬 파일 캐시** — `step_archive/face_reading_cache/` (Railway volume)
3. **lru_cache** — 페르소나/규칙 로더 인메모리

### 🟡 추가 검토 가치

1. **응답 캐시 키 정밀화** — 현재 metrics 기반. 의미 유사 입력은 다른 키 → 미스. 다만 관상은 메트릭이 사용자 사진 기반이라 *진짜로* 다른 입력이라 시맨틱 캐싱 부적합.
2. **사주 LLM 작문 응답 캐싱** — 현재 face만 캐시. 사주·작명 LLM 작문도 캐시 가치 있음. 단 사용자별 결과가 거의 유니크해 적중률 낮을 가능성.

### ❌ 본 프로젝트 미적용 권장

- **시맨틱 캐싱 (벡터 임베딩 + ANN)** — 추가 인프라(Redis/벡터 DB) 필요. 본 프로젝트 트래픽 규모 미달. SaaS 운영 시작 후 트래픽 데이터로 ROI 재평가.
- **OpenAI 캐싱 정책** — 본 프로젝트는 Anthropic만 사용 (ADR-005). OpenAI 도입 결정 없음.
- **Google Gemini 캐싱** — 본 프로젝트 미사용. 적용 무관.
- **AWS Bedrock** — 본 프로젝트는 Railway 직접 배포. Bedrock 미사용.

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| KV 캐싱 이론 설명 | ✅ 정확 |
| 벤더별 메커니즘 | ✅ 대체로 정확 (Anthropic은 본 프로젝트 사용 중이라 직접 검증됨) |
| 가격표 | 🟡 변동성 큼, 직접 확인 필요 |
| 미래 모델명 (gpt-5.5) | 🔴 미공개 또는 추측 |
| 광고성 수사 ("Computational Déjà Vu") | 🔴 무시 |
| 본 프로젝트 적합성 | 🟡 일부 (이미 핵심 적용, 추가 도입 ROI 낮음) |

## 다음 액션

- [ ] (선택) 사주·작명 LLM 작문 응답 캐싱 — 트래픽 데이터 수집 후 결정
- [ ] (보류) 시맨틱 캐싱 — SaaS 운영 시작 후 트래픽 패턴 분석 후 ROI 평가
- [ ] (정보) 본 노트를 미래 캐싱 의사결정의 reference로 보관

## 출처

- 본 보고서 원본: `사주/LLM 토큰 절약을 위한 캐싱 전략.md`
- 본 프로젝트 검증: engine/divination/face_reading.py (이미 prompt caching 사용)

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리)
- ADR-010 사례 4호
- 본 노트 immutable
