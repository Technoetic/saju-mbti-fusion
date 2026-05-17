---
type: done
status: applied
date: 2026-05-17
domain: [saju, mbti]
adr: ADR-024-mbti-compat-v2-socionics
related_report: reports/mbti-gunghap-academic-validation
related_reference: references/jung-myers-keirsey-socionics
related_prompt: templates/PROMPT_gunghap-mbti-matrix-academic
---

# MBTI 16×16 호환 매트릭스 v2 본문화 — 결정론 4단계 알고리즘

## 작업 요약

`engine/saju/compat.py` 라인 8 명시 "MBTI 16×16 호환 매트릭스 (간이)"
학술 출처 부재 결손 해소.

PROMPT_gunghap-mbti-matrix-academic.md 의뢰 → 보고서 수령 → /squeeze-report
ADR-017 절차 적용 → ACCEPT 6건 + DEFER 1건 → ADR-024 본문화.

ADR-017 절차 **다섯 번째 본문화 사례** (ADR-020·021·022·023 다음).

## 변경 사항

### 신규 파일
- [engine/saju/mbti_compat_v2.py](../../engine/saju/mbti_compat_v2.py) — 4단계 결정론 알고리즘
- [engine/saju/test_mbti_compat_v2.py](../../engine/saju/test_mbti_compat_v2.py) — 회귀 29 PASS
- [vault/decisions/ADR-024-mbti-compat-v2-socionics.md](../decisions/ADR-024-mbti-compat-v2-socionics.md)
- [vault/references/jung-myers-keirsey-socionics.md](../references/jung-myers-keirsey-socionics.md)
- [vault/reports/mbti-gunghap-academic-validation.md](../reports/mbti-gunghap-academic-validation.md)

### 갱신
- vault/decisions/INDEX.md — ADR-024 추가
- vault/done/INDEX.md — 사주 도메인 MBTI compat v2 행 추가

## 4단계 알고리즘 (보고서 §5.1)

```
score = max(1, min(9, 5 + sn_bonus + socionics_bonus + keirsey_bonus))
```

| 단계 | 가중치 | 학술 근거 |
|---|---|---|
| 1 base | 5 | 중립 |
| 2 S/N 동기화 | +2/-1 | 윤호균·이선희 (2000) |
| 3 Socionics | dual+4·activation+3·mirror+2·identity+1·super_ego-2·conflict-4 | Aushra Augusta |
| 4 Keirsey | N공유+T/F역전+J/P역전 → +1 | Please Understand Me II |

## 회귀 29 PASS

- 입력 검증 3건 + 관계 분류 6건 + 4단계 알고리즘 3건
- 보고서 §5.1 예시 4건 (INTJ-ENFP·INTJ-ESFP·INTP-ESFP·INTJ-INTJ)
- 대칭 행렬 1건 + 256 매트릭스 2건
- DEFAULT_DISCLAIMERS 6건 (count·school·causal·MBTI limit·multi factor·in result)
- ADR-014 경계 1건 + 학파 명시 1건
- Frozen 1건 + to_dict 1건

## ADR-006/010/014 자동 회귀

`DEFAULT_DISCLAIMERS` 3건:
1. Jung·Socionics 학설 + 결혼·연애 자문 아님 (ADR-006)
2. MBTI 학계 재현성·구성 타당도 논쟁 (ADR-010)
3. 다중 요인 영향 + 맹신 금지 (ADR-014)

자동 검증:
- 인과·예언 표현 0건
- 학파 명시 (Jung·Socionics·Keirsey)
- MBTI 학계 한계 (자기보고·재현성·논쟁)
- 다중 요인 (환경·요인)

## ADR-014 경계 명확화

`compute_mbti_compat(a: str, b: str)` 시그니처:
- 사용자 명시 두 MBTI 유형만 입력
- 사주 파라미터 0 (saju·pillars 없음)
- 사주→MBTI 단정 예측과 구조적 분리

## compat.py 호환

- 라인 87-108 32 엔트리 `_MBTI_PAIR_SCORE` 유지 (호환성)
- v2 사용 원할 시: `from engine.saju.mbti_compat_v2 import compute_mbti_compat`

## 후속 작업 (별도 ADR)

- compat.py v1 + v2 통합 호출 (옵션)
- KCI 4건 표본 크기·p-value 추가
- §8 회귀 30쌍 사용자 보강 (선택)
- 운영 데이터 매트릭스 보정 (post_traffic)
- Aladin ISBN 라이브 검증 재시도

## 메타

- ADR-017 다섯 번째 본문화 사례
- 분석 에이전트 오추정 0건
- 본 노트 immutable
