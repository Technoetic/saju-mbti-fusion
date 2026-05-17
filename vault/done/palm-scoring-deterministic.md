---
type: done
status: applied
date: 2026-05-17
domain: [palm]
adr: ADR-030-palm-scoring-deterministic
related_report: reports/palm-scoring-deterministic-engine
---

# 손금 4대 선 + 보조선 결정론 점수 엔진 본문화 (ADR-030)

## 작업 요약

외부 보고서 "손금 4대 선 및 보조선 결정론 점수 엔진 구축 명세서" (652줄)
§2·§4·§5·§6·§7 본문화. palm-reading-app 보고서 C1·C2 DEFER 영역 직격 해소.
face_scoring.py (ADR-004) 패턴 차용으로 LineScore + PalmScoringReport 구조.

ADR-017 절차 **열한 번째 본문화 사례**.

## 변경 사항

### 데이터 (신규 2건)

- [data/palm_scoring_rules.json](../../data/palm_scoring_rules.json) — 5 lines 임계값 + 15 차단 토큰 + 면책
- [data/palm_scoring_regression.json](../../data/palm_scoring_regression.json) — 보고서 §7 회귀 30쌍

### 코드 (신규)

- [engine/divination/palm_scoring.py](../../engine/divination/palm_scoring.py) — 신규 모듈
  - `score_palm(keypoints, hand_side)` 핵심 함수
  - `asymmetry_index(left, right)` 비대칭성 (equal weighting)
  - `filter_forbidden_tokens(text)` ADR-010 차단 토큰 검증
  - `disclaimer_palm_ko()` 손금 전용 면책
  - `total_lines()` / `is_loaded()` 메타
  - `LineScore`·`PalmScoringReport` 불변 dataclass

### 회귀 테스트

- [engine/divination/test_palm_scoring.py](../../engine/divination/test_palm_scoring.py) — **21/21 PASS**
  - 5 라인 임계값 (low/medium/high 경계)
  - 보고서 §7 30쌍 × 4선 = **120/120 라벨 정확도 100%**
  - ADR-010 차단 토큰 15건 (의료·위험·성격 결함)
  - 면책 자동 포함 + 학파 명시 + 결정론
  - 비대칭성 지수 + face_scoring 패턴 호환

### 신규 ADR

- [vault/decisions/ADR-030-palm-scoring-deterministic.md](../decisions/ADR-030-palm-scoring-deterministic.md)

### 신규 보고서

- [vault/reports/palm-scoring-deterministic-engine.md](../reports/palm-scoring-deterministic-engine.md)

## 5 라인 임계값 본문화 (보고서 §4)

| 라인 | 메트릭 | 한국인 baseline | low | high |
|---|---|---|---|---|
| 생명선 | arc_length_normalized | 0.81 ± 0.08 | <0.73 | >0.89 |
| 두뇌선 | horizontal_extent | 0.65 ± 0.12 | <0.53 | >0.77 |
| 감정선 | curvature_prominence | 0.58 ± 0.15 | <0.43 | >0.73 |
| 운명선 | vertical_linearity | 0.45 ± 0.20 | <0.25 | >0.65 |
| 금성대 | arc_prominence | 0.20 ± 0.10 | <0.10 | >0.30 |

## 보고서 §7 회귀 30쌍 결과

**120/120 라벨 정확도 100%** (30 케이스 × 4 라인)

샘플:
| ID | hand | 입력 scores | 본 시스템 결과 |
|---|---|---|---|
| palm_001 | right | life 0.85 / head 0.65 / heart 0.50 / fate 0.20 | medium·medium·medium·low ✓ |
| palm_002 | left | 0.35 / 0.88 / 0.42 / 0.77 | low·high·low·high ✓ |
| palm_005 | left | 0.95 / 0.90 / 0.85 / 0.88 | high·high·high·high ✓ |
| palm_004 | right | 0.22 / 0.22 / 0.30 / 0.15 | low·low·low·low ✓ |
| palm_030 | right | 모든 0.80 균일 | medium·high·high·high ✓ |

## REJECT 영역

- **C3 U-Net CFM 세그멘테이션** (보고서 §3):
  - 학습 데이터 0
  - 온디바이스 vs Railway 클라우드 미결정
  - 본 시스템 결정론 엔진 패턴 (face_scoring·hwapae_korean) 충돌
  - 손금 분야 ≠ arXiv:2102.12127 일반 이미지 세그논문

## DEFER 영역

- **C1 W_i 가중치**: 학술 미명시 → equal weighting (W_i=0.25)
- **§2.2 Bézier curve fitting**: 추상 명세 → keypoints에 raw scores 직접 입력으로 회피
- **§3 마스크 데이터**: U-Net REJECT로 자동 DEFER

## ADR-010 사실성 분리

- ✅ 학술 출처 (Size Korea + KCI + PubMed)
- ✅ 면책 자동 포함 (rationale에 학파 명시 + "운명·수명·재물 인과관계 X")
- ✅ 차단 토큰 15건 regex (수명·단명·이혼·파산·치매 등)
- ✅ 학파 명시 (Samudrika Shastra + 한국 전통 손금)
- ✅ 결정론 (lru_cache + JSON)

## ADR-002 학파 회피 패턴

비대칭성 rationale (보고서 §5.2 정합):

> "양손 주름 형태적 비대칭 지수 산출 결과 0.18. 인도 Samudrika Shastra
> 학설 및 한국 전통 손금 관습에서는 비우세수를 선천적 성향, 우세수를
> 후천적 변화 지표로 분석합니다. 본 지표는 양손 근육 사용량 및 환경
> 부하에 따른 형태적 차이 정량화입니다."

## 라이브 검증 예시

```python
>>> from engine.divination.palm_scoring import score_palm, filter_forbidden_tokens
>>> r = score_palm({"lifeline_arc": 0.85, "headline_horizontal": 0.65,
...                 "heartline_curve": 0.50, "fateline_vertical": 0.20},
...                 hand_side="right")
>>> r.lines["lifeline"].label
'medium'
>>> r.lines["fateline"].label
'low'
>>> safe, tokens = filter_forbidden_tokens("이 선은 단명을 의미합니다")
>>> safe
False
>>> tokens
['단명']
```

## 향후 작업

- W_i 가중치 학술 자료 의뢰 (별도 ADR supplement)
- Bézier curve fitting 알고리즘 구현 (MediaPipe 21 키포인트 → 실시간 곡선)
- U-Net 세그멘테이션 (학습 데이터 확보 시 별도 ADR)
- palm_reading.py LLM 응답 후처리에 filter_forbidden_tokens 통합

## 메타

- ADR-017 열한 번째 본문화
- palm-reading-app C1·C2 DEFER 영역 해소
- face_scoring.py 패턴 차용 (ADR-004) 성공
- 보고서 §7 회귀 120/120 라벨 정확도 100%
- 본 노트 immutable
