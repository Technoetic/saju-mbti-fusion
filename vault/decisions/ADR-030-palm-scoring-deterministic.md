---
type: adr
status: accepted
date: 2026-05-17
domain: [palm]
related: [ADR-001, ADR-002, ADR-004, ADR-005, ADR-006, ADR-010, ADR-020]
related_report: reports/palm-scoring-deterministic-engine
---

# ADR-030 — 손금 4대 선 + 보조선 결정론 점수 엔진 (palm_scoring.py)

## 상태

Accepted (2026-05-17).

## 맥락

palm_reading.py (351줄, LLM Vision)는 비결정론. 이전 보고서 palm-reading-app에서
C1·C2 (결정론 점수 엔진) DEFER로 보류.

외부 보고서 "손금 4대 선 및 보조선 결정론 점수 엔진 구축 명세서"(2026-05-17, 652줄)가:

- §1 Size Korea 7/8차 인체측정학 (남성 손길이 0.770 비율)
- §2 MediaPipe Hand 21 키포인트 + 4대 선 기하학적 ROI
- §4 임계값 YAML 명시 (4대 선 + 금성대 = 5 라인)
- §5 좌우 손 비대칭성 지수 알고리즘
- §6 ADR-010 차단 토큰 + 면책 자동 포함
- §7 회귀 30쌍 완전 기술 (palm_001~palm_030)

학술/공식 출처: Size Korea + KCI NODE00559265 + PubMed PMC7195958·PMC9256497.

## 결정

**보고서 §4 명시 5개 라인 본문화** + face_scoring.py (ADR-004) 패턴 차용.
딥러닝 세그멘테이션 (U-Net §3)은 학습 데이터 0 + 결정론 충돌로 REJECT.
좌우 손 비대칭성 (§5)은 W_i 가중치 학술 미명시로 equal weighting 적용
(별도 학술 자료 의뢰 시 ADR supplement).

### 본문화 영역

| 영역 | 내용 |
|---|---|
| `data/palm_scoring_rules.json` | 5 라인 임계값 + 15 차단 토큰 + 면책 |
| `data/palm_scoring_regression.json` | 보고서 §7 회귀 30쌍 (palm_001~030) |
| `engine/divination/palm_scoring.py` | 결정론 점수 엔진 (LineScore + PalmScoringReport) |
| `engine/divination/test_palm_scoring.py` | 회귀 21건 (120/120 라벨 정확도) |

### 5 라인 임계값 (보고서 §4)

| 라인 | 메트릭 | baseline_mean ± std | low | high |
|---|---|---|---|---|
| 생명선 (lifeline) | arc_length_normalized | 0.81 ± 0.08 | <0.73 | >0.89 |
| 두뇌선 (headline) | horizontal_extent | 0.65 ± 0.12 | <0.53 | >0.77 |
| 감정선 (heartline) | curvature_prominence | 0.58 ± 0.15 | <0.43 | >0.73 |
| 운명선 (fateline) | vertical_linearity | 0.45 ± 0.20 | <0.25 | >0.65 |
| 금성대 (girdle_of_venus) | arc_prominence | 0.20 ± 0.10 | <0.10 | >0.30 |

### Public API

```python
score_palm(keypoints, hand_side="unknown") -> PalmScoringReport
asymmetry_index(left_report, right_report) -> dict  # W_i = 0.25 equal weighting
filter_forbidden_tokens(text) -> tuple[bool, list[str]]
disclaimer_palm_ko() -> str
total_lines() -> int  # 5
is_loaded() -> bool
```

### 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론 + LLM 분리) | OK | MediaPipe 기하 + lru_cache, LLM 무관 |
| ADR-002 (학파 회피) | OK | Samudrika Shastra 학파 명시 + 한국 전통 손금 |
| ADR-004 (face_keypoint_scoring) | OK | PalaceScore → LineScore 동일 패턴 |
| ADR-005 (claude-opus-vision) | N/A | 본 모듈 LLM 무관 (palm_reading.py 별도) |
| ADR-006 (자문 거절) | OK | 의료·법률 단정형 토큰 자동 차단 |
| ADR-010 (사실성 분리) | OK | 면책 자동 포함 + 차단 토큰 regex 검증 |
| ADR-020 (L2 photo_quality) | OK | palm Laplacian variance 임계값 150 (별도) |

## REJECT 영역

- **C3 U-Net CFM 세그멘테이션**: 학습 데이터 0 + 온디바이스/클라우드 미결정 + 본 시스템 결정론 패턴 충돌. arXiv:2102.12127은 일반 이미지 세그논문.

## DEFER 영역

- **C1 W_i 가중치 학술 출처**: 보고서 §5.1 "발달적 변동성 계수에 역비례" 명시했으나 구체 수치 미제시. equal weighting (W_i=0.25) 적용 + 별도 딥리서치 의뢰 가능

## 학술/공식 출처

- **Size Korea 7/8차** 인체측정 — 남성 손길이 183.3mm, 비율 0.770
- **KCI NODE00559265** 한국인 손금 형태 조사 (정상 86.3%, Simian 11.5%)
- **PubMed PMC7195958** Dermatoglyphics and Palmar Crease
- **PubMed PMC9256497** Palmar crease asymmetry
- **MediaPipe Hand Landmarker** 공식 21 키포인트 (ai.google.dev)

## 면책 (ADR-010 준수 강제)

손금 전용 면책 (보고서 §6.2):

> 본 손금 분석 지표는 MediaPipe Vision AI와 Size Korea 한국인 인체측정학
> 통계를 기반으로 손바닥 주름의 형태적 비율을 0.0~1.0 점수로 변환한
> 정량적 데이터입니다. 이는 전통적 학파 이론을 참조하여 흥미 목적으로
> 재구성되었을 뿐, 어떠한 의학적 진단이나 미래에 대한 절대적 예언을
> 포함하지 않습니다. 촬영 시 조명, 각도, 손의 굴곡에 따라 비전 인식
> 오차가 발생할 수 있습니다.

### 차단 토큰 (15건, ADR-010 의무)

- **의료**: 수명·단명·사망·치매·유전병·다운증후군
- **사적 위험**: 이혼·파산·사고·과부·절연·횡사
- **성격 결함**: 호르몬 이상·지능 저하·어리석음

`filter_forbidden_tokens()` 자동 검증 + palm_reading.py LLM 응답 후처리 가능.

## 한계 (영구 기록)

- 본 ADR 기하 메트릭은 입력 keypoints에 raw scores (lifeline_arc 등)
  명시 시 직접 사용. MediaPipe Hand 21 키포인트 실시간 곡선 적분 (Bézier)
  알고리즘은 보고서 §2.2 추상 명세만, 후속 구현 영역
- 좌우 손 비대칭성 W_i는 equal weighting (보고서 §5.1 학술 미명시)
- U-Net 세그멘테이션 마스크 미사용 (REJECT)
- 회귀 30쌍은 4대 선 라벨 정확도 100% (보고서 §7 본문 명시 영역)
- 금성대 등 보조선 회귀는 §7 미명시 (4대 선만)
- 본 ADR은 **immutable**

## 관련

- 외부 보고서: [[../reports/palm-scoring-deterministic-engine]]
- 본 작업 영속화: [[../done/palm-scoring-deterministic]]
- 회귀: `engine/divination/test_palm_scoring.py` (21/21 PASS, 120/120 라벨 정확도)
- 데이터: `data/palm_scoring_rules.json` + `data/palm_scoring_regression.json`
- 이전 DEFER 영역: [[../reports/palm-reading-app]] C1·C2 해소
