---
type: adr
adr_number: 13
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [infra, safety]
related:
  - ADR-005-claude-opus-vision
  - ADR-010-name-sibling-factuality
  - reports/llm-token-caching.md
related_file: ../../engine/safety/prompt_cache_telemetry.py
---

# ADR-013: Anthropic Prompt Cache 적중률 측정 — L2 telemetry

## 배경

[[../reports/llm-token-caching]] (LLM 캐싱 전략 보고서) 4차 검토 결과,
본 프로젝트는 5개 LLM 호출 모듈(face_reading / palm_reading / name_reading /
llm_sync / llm_async)에서 `cache_control: ephemeral`을 system 프롬프트에
일관 적용 중이나 **적중률 측정 부재**.

본 프로젝트 SLO 시스템의 `cache_hit_rate`는 **L4 응답 파일 캐시** 적중률
(`step_archive/face_reading_cache/`). **L2 Anthropic prompt cache** 적중률
(`usage.cache_read_input_tokens`)은 측정되지 않아 다음이 불가능:

- "Prompt caching이 실제 작동하는가?" 확인 불가
- 캐시 적중률 저하 시 SLO 알림 불가
- 비용 추적 (적중 토큰 0.1x 단가) 불가

보고서 §3.2: vendor가 반환하는 `cacheReadInputTokens`로 캐싱 효과 투명
모니터링 권장.

## 검토한 옵션

### A. 미구현 유지
- 장점: 추가 코드 없음
- 단점: cache_control 적용했으나 실제 작동 여부 미확인

### B. 각 호출 모듈에 직접 측정 코드 삽입
- 장점: 단순
- 단점: 5개 모듈 + 응답 객체 처리 중복

### C. 별도 telemetry 모듈 (채택)
- 장점: 단일 모듈에 추출·요약 로직 격리. 호출자는 1줄로 emit
- 단점: 모듈 1개 추가 (의존성 0)

## 채택

**C 채택**. `engine/safety/prompt_cache_telemetry.py` 신규.

### API

```python
from engine.safety.prompt_cache_telemetry import extract_usage, summarize

msg = client.messages.create(...)
usage = extract_usage(msg.usage)
metrics = summarize(usage)
# → {"prompt_cache_hit": bool, "prompt_cache_savings_ratio": float, ...}
```

### 호환성

- Anthropic SDK `Usage` Pydantic 모델 + dict 양쪽 지원
- 필드 부재 시 0 기본값 (이전 SDK 버전 호환)
- None / 비정수 값 안전 처리 (DIV0 방지)
- Bizrouter (OpenAI 호환) 응답은 별도 형식 — 본 모듈 미지원 (명시)

### 통합 정책

본 ADR은 **모듈 신설만**. 5개 LLM 호출 모듈에 emit 코드 삽입은 별도 PR
(SLO 시스템과 결합 시점에 함께 진행). 본 ADR 채택만으로 향후 측정 도입 시
일관 패턴 사용 가능.

## 결과

- `engine/safety/prompt_cache_telemetry.py` 신규 (110줄)
- `engine/safety/test_prompt_cache_telemetry.py` 신규 (12 PASS)
- L2 prompt cache 적중률 측정 인프라 준비

## 면책

- 본 ADR은 측정 인프라만 — 5개 호출 모듈 통합은 향후 PR
- Bizrouter (Gemini 등) 응답은 OpenAI 형식이라 본 모듈 미지원. 별도 처리 필요 시 새 ADR
- 본 모듈은 telemetry만 — 캐시 작동 보장 X. Anthropic 정책 변경에 따라 적중률 변동 가능

## 향후

- 5개 호출 모듈에 emit 통합 (별도 PR)
- SLO 시스템 (kpi_dashboard·quick_check)에 prompt_cache_savings_ratio 추가
- 본 ADR 적중률 데이터 누적 후 시맨틱 캐싱 ROI 재평가 (현 시점 보고서 검토에서 보류)
