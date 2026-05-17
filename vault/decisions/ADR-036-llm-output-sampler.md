---
type: adr
status: accepted
date: 2026-05-18
authors: [Technoetic, Claude]
domain: [safety, face]
related:
  - vault/decisions/ADR-005-supplement-2-phase17-opus-vision-objective.md
  - vault/decisions/ADR-005-supplement-3-phase18-two-stage-pipeline.md
---

# ADR-036: LLM 운영 출력 샘플러 — 운명 매핑 어휘 모니터링

## 배경 (Context)

ADR-005 Supplement 2~7에서 반복적으로 명시된 "운영 모니터링 의무":

- Supplement 2 (Phase 17): "운명 매핑 어휘 출력 모니터링 의무"
- Supplement 3 (Phase 18): "Stage 2 Gemini 사전학습 매핑 우회 표현 모니터링"
- Supplement 6 (Phase 21): "모니터링 의무"
- Supplement 7 (Phase 22): "모니터링 의무"

1% 샘플링으로 운영 환경 LLM 출력을 저장하고, 운명 어휘 패턴(초년/중년/말년 복록,
직장운, 재물복 등) 발생 여부를 자동 탐지해야 한다.

## 검토한 옵션 (Options)

### A. 비동기 fire-and-forget (asyncio.create_task)
- 장점: 서버 레이턴시 0 추가
- 단점: 이벤트 루프 오염, 테스트 어려움

### B. 동기 I/O + 예외 silent (채택)
- 장점: 단순, 테스트 가능, 사용자 영향 0
- 단점: I/O 시간 미미하게 추가 (JSONL append, 서버 로컬 디스크)

### C. 외부 로깅 서비스 (Datadog, CloudWatch)
- 장점: 시각화, 대시보드
- 단점: 비용, PII 전송 위험 (ADR-006 위반 가능성)

## 채택 (Decision)

옵션 B — 동기 I/O + 예외 silent.

`engine/safety/llm_output_sampler.py`:
- `sample_llm_output(domain, text, sampling_rate=0.01)` 공개 API
- `random.random() < sampling_rate`이면 JSONL 한 줄 저장
- 저장 경로: `step_archive/llm_output_samples/<YYYY-MM-DD>.jsonl`
- 텍스트 앞 120자만 저장 (PII 최소화)
- 운명 어휘 5패턴 감지 → `fate_counter.json` 누적
- 모든 예외 silent (운영 영향 0 보장)

`web/server.py` `post_face_reading`:
```python
try:
    from engine.safety.llm_output_sampler import sample_llm_output
    sample_llm_output("face_reading", result.get("text", ""))
except Exception:
    pass  # silent
```

## 결과 (Consequences)

- 긍정적 영향:
  - ADR-005 Supplement 2~7 운영 모니터링 의무 이행
  - 운명 어휘 발생률 추적 → 프롬프트 개선 근거 데이터 확보
  - 사용자 영향 0 (백그라운드, silent)
- 부정적 영향·비용:
  - `step_archive/llm_output_samples/` 디렉토리 디스크 사용 (월 ~수 MB 예상)
  - 1% 샘플만 수집 → 대표성 제한
- 후속 작업:
  - fate_counter.json 주기적 리뷰 (월 1회)
  - palm_reading, name_reading 등 다른 도메인 확장 가능

## 면책·한계 (Caveats)

- LLM 사전학습 운명 매핑 완전 차단은 코드로 불가 (ADR-005 A류 한계)
- 본 모듈은 사후 탐지·측정이지 사전 차단 아님
- 샘플링 1%이므로 모든 위반 표현 잡지 못함

## 참조 (References)

- 코드: `engine/safety/llm_output_sampler.py`
- 테스트: `engine/safety/test_llm_output_sampler.py`
- 연동: `web/server.py:post_face_reading`
- 커밋: 9e5804d
- 관련 ADR: ADR-005 Supplement 2~7
