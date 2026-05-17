---
type: done
status: applied
date: 2026-05-17
domain: [dream]
adr: ADR-021-dreamnet-b6-v4
related_report: reports/b6-dreamnet-v4-research
related_reference: references/korean-dream-norms-hvdc
related_prompt: templates/PROMPT_dreamnet-multimodal-v4
---

# B6 DreamNet v4 멀티모달 꿈 통합 — 본문화 완료

## 작업 요약

`engine/agents/__init__.py` 명시 TODO `B6 DreamNet (v4)` 해소.
PROMPT_dreamnet-multimodal-v4.md 의뢰 → 보고서 수령 → /squeeze-report
ADR-017 절차 적용 → ACCEPT 5건 → ADR-021 본문화.

ADR-017 절차 두 번째 본문화 사례 (ADR-020 L2 photo_quality 다음).

## 변경 사항

### 신규 / 변경 파일
- [engine/agents/dreamnet_multimodal.py](../../engine/agents/dreamnet_multimodal.py) — 95줄 → 247줄 보강
  - `integrate_multimodal_dream()` 함수 신규
  - `MultimodalIntegration` dataclass 신규
  - `DEFAULT_DISCLAIMERS` 강제 면책 배열 (3건)
  - `_compute_korean_baseline_delta()` 한국 KCI 규준 편차
- [engine/agents/test_dreamnet_multimodal.py](../../engine/agents/test_dreamnet_multimodal.py) — 회귀 17 PASS
- [engine/divination/dream_lex/dreambank.py](../../engine/divination/dream_lex/dreambank.py) — NORMS_KOREAN dict 추가
- [vault/references/korean-dream-norms-hvdc.md](../references/korean-dream-norms-hvdc.md) — KCI 학술 출처 영속화
- [vault/decisions/ADR-021-dreamnet-b6-v4.md](../decisions/ADR-021-dreamnet-b6-v4.md) — 결정 영속화
- [vault/reports/b6-dreamnet-v4-research.md](../reports/b6-dreamnet-v4-research.md) — 사실성 분리 결과

### 갱신
- vault/decisions/INDEX.md — ADR-021 추가
- vault/done/INDEX.md — 꿈해석 도메인 행 추가

## 회귀 테스트 (17 PASS)

1. integrate basic
2. text modality
3. multi modality (text + voice + sleep)
4. disclaimers required (강제 + 임상/진단/HVDC 명시)
5. no causal words (인과 표현 0건)
6. korean baseline delta + (양수 편차)
7. korean baseline delta - (음수 편차)
8. integration_score range (-10~+10)
9. dreamnet_001 falling (보고서 §8 절벽 추락)
10. dreamnet_002 unfamiliar (낯선 남성)
11. dreamnet_003 teeth (이빨 빠짐)
12. dreamnet_004 flying (비행·자유)
13. dreamnet_005 pursuit (추적)
14. to_dict (dataclass 변환)
15. empty text
16. DEFAULT_DISCLAIMERS count (3 이상)
17. empty delta (HVDC 없을 때)

## 한국 KCI 학술 출처

- 김성재 외 (2004) "Hall/Van de Castle System을 이용한 20대 한국 남녀의 꿈 내용 분석"
- 김린 외 (2007) "Hall/Van de Castle System에 의한 한국 초기 청소년의 최근 꿈 분석"
- 학술지: 수면정신생리 (대한수면의학회) KCI 등재

NORMS_KOREAN dict (aggression 45·negative 40·unfamiliar 55·misfortune 35).

## ADR-006/010/014 정합

`DEFAULT_DISCLAIMERS` 3건 자동 회귀 검증:
1. "본 결과는 자기 보고 분석이며 임상 진단이 아닙니다." (ADR-006)
2. "Hall-Van de Castle(1966) 시스템 + 한국 KCI 학술 규준 비교 통계입니다." (ADR-010)
3. "꿈 패턴 해석은 다중 요인 영향이며 미래 사건 예언 아닙니다." (ADR-014 정신)

인과·예언 표현 금지어 (확실히·반드시 발생·당신은 우울증·예언합니다·운명입니다) 자동 검증.

## 후속 작업 (별도 ADR)

- 회귀 15쌍 추가 (dreamnet_006~020)
- orchestrator.py interpret_dream_v2 통합 호출
- 음성·수면 모달리티 활성 (법무 검토 + SDK 안정화 후)
- 동적 한국 규준 (10만 건+ 운영 데이터 후, post_traffic ADR)
- A8 Freud v2 + A13 social_unconscious v3 후속 본문화

## 메타

- ADR-017 절차 두 번째 본문화 사례
- 분석 에이전트 오추정 0건 (보강된 프롬프트 작동 입증)
- engine/agents/ 명시 TODO 3건 중 1건 해소 (B6)
- 본 노트 immutable
