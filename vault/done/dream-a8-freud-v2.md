---
type: done
status: applied
date: 2026-05-17
domain: [dream]
adr: ADR-023-freud-v2-adoption
related_report: reports/freud-v2-research
related_reference: references/freud-korean-isbn
related_prompt: templates/PROMPT_freud-classical-v2
---

# A8 Freud v2 고전 정신분석 4기제 + 보편 상징 본문화

## 작업 요약

`engine/agents/__init__.py` 명시 TODO `A8 freud (v2) — TODO` 해소.
PROMPT_freud-classical-v2.md 의뢰 → 보고서 수령 → /squeeze-report
ADR-017 절차 적용 → ACCEPT 5건 → ADR-023 본문화.

ADR-017 절차 **네 번째 본문화 사례** (ADR-020 L2 + ADR-021 B6 + ADR-022
face_shape 다음).

## 변경 사항

### 신규 파일
- [engine/agents/freud_v2.py](../../engine/agents/freud_v2.py) — 결정론 4기제 + 보편 상징
- [engine/agents/test_freud_v2.py](../../engine/agents/test_freud_v2.py) — 회귀 26 PASS
- [vault/decisions/ADR-023-freud-v2-adoption.md](../decisions/ADR-023-freud-v2-adoption.md)
- [vault/references/freud-korean-isbn.md](../references/freud-korean-isbn.md)
- [vault/reports/freud-v2-research.md](../reports/freud-v2-research.md)

### 갱신
- vault/decisions/INDEX.md — ADR-023 추가
- vault/done/INDEX.md — 꿈해석 도메인 A8 행 추가

## 회귀 26 PASS

- 4기제 정합 (3건)
- 보편 상징 정합 (4건, ISBN 13자리 + 가능성 다중 제시 포맷)
- DEFAULT_DISCLAIMERS (3건)
- analyze 통합 (3건)
- 보고서 §6 회귀 5건 (freud_001~005)
- Forbidden patterns (4건)
- Frozen dataclass (3건)
- 통합 (1건)

## 4기제 매핑

| 기제 | 영문 | ISBN |
|---|---|---|
| 응축 | Verdichtung | 9788932920528 |
| 전치 | Verschiebung | 9788932920528 |
| 상징화 | Symbolisierung | 9788932920498 |
| 이차가공 | sekundäre Bearbeitung | 9788932920528 |

## 보편 상징 6건 (한국어 표준판 ISBN)

집·부모·왕족·물·여행·벌거벗음 + 출처 3종 (열린책들 2 + 서울대출판부 1).

## ADR-006/010/014 자동 회귀

`DEFAULT_DISCLAIMERS` 3건:
1. Freud 정신분석 학파 학설 (ADR-010)
2. 가능성 다중 해석 (ADR-006)
3. 다른 학파 (Jung·Hobson·Solms) 다른 해석 (ADR-002 학파 분리)

`FORBIDDEN_OUTPUT_PATTERNS` 8건:
- 의료 단정 ("당신은 [질병명]")
- 미래 예언 (확실히·반드시·운명)
- 성환원 단정 (지팡이=남근·동굴=자궁)

`has_forbidden_output()` 함수로 LLM 페르소나 출력 사후 검증 가능.

## engine/agents/ TODO 진척

| 항목 | 상태 |
|---|---|
| **A8 Freud v2** | ✅ **완료 (본 ADR-023)** |
| B6 DreamNet v4 | ✅ 완료 (ADR-021) |
| A13 social_unconscious v3 | ⏸️ PROMPT 영속화, post_traffic 영역 |

## 후속 작업 (별도 ADR)

- v1·v2 통합 호출 (orchestrator.py interpret_dream_v2)
- 회귀 25쌍 추가 (freud_006~030)
- ISBN Aladin 라이브 검증
- 추가 보편 상징 12개 이상

## 메타

- ADR-017 네 번째 본문화 사례
- 분석 에이전트 오추정 0건 (보강된 프롬프트 작동 입증)
- engine/agents/ 명시 TODO 2건 해소 (B6 + A8)
- 본 노트 immutable
