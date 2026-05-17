---
type: done
status: applied
date: 2026-05-17
domain: [infra, safety]
related:
  - decisions/ADR-013-prompt-cache-telemetry.md
  - reports/llm-token-caching.md
commit: TBD
---

# Anthropic Prompt Cache 적중률 측정 인프라 (L2)

## 무엇

[[../reports/llm-token-caching]] 4차 검토에서 발견한 적용 후보 1건.
본 프로젝트 5개 LLM 호출 모듈이 `cache_control: ephemeral` 일관 적용했으나
적중률 미측정 → L2 telemetry 모듈 신설.

## 변경

### 신규 모듈
- [engine/safety/prompt_cache_telemetry.py](../../engine/safety/prompt_cache_telemetry.py)
  - `PromptCacheUsage` 데이터 모델 (input/cache_creation/cache_read/output_tokens + cache_hit·savings_ratio property)
  - `extract_usage(usage)` — Anthropic SDK 모델 또는 dict에서 안전 추출
  - `summarize(usage)` — SLO·로그용 평탄화 dict

### 신규 테스트
- [engine/safety/test_prompt_cache_telemetry.py](../../engine/safety/test_prompt_cache_telemetry.py) — 12 PASS
  · 기본 동작 5 (cache_hit / cache_miss / total / savings / DIV0)
  · extract_usage 5 (dict / Pydantic 객체 / 필드 부재 / None / 비정수)
  · summarize 2 (적중 / 미스)

### vault
- ADR-013 신규
- INDEX 갱신
- reports/llm-token-caching.md `applied_to` 갱신

## 통합 정책

본 PR은 **측정 모듈 신설만**. face_reading 등 5개 LLM 호출 모듈에 emit
코드 삽입은 별도 PR (SLO 시스템 결합 시).

## 검증

```
python -m pytest engine/safety/test_prompt_cache_telemetry.py --no-skip-all
12 passed in 0.93s
```

## 결과

- 본 프로젝트 SLO `cache_hit_rate`는 L4 (응답 파일) — 본 모듈은 L2 (Anthropic prompt cache) 분리
- 향후 5개 호출 모듈 + SLO 결합 시 일관 패턴 사용 가능
- ADR-010 사실성 분리 적용: "적중률 단정 없이 측정값 그대로 반환"

## 면책

- Bizrouter (OpenAI 호환) 응답은 본 모듈 미지원 (Anthropic SDK 형식만)
- 측정 인프라일 뿐 캐시 작동 보장 X — Anthropic 정책 변경 영향 받음
