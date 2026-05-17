---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: palm
applied_to:
  - "§1 Size Korea 한국인 인체측정학 (남성 0.770 비율)"
  - "§2 MediaPipe Hand 21 키포인트 + 4대 선 ROI 매핑"
  - "§4 5개 라인 임계값 YAML (4대 선 + 금성대)"
  - "§5 좌우 손 비대칭성 알고리즘 (equal weighting W_i=0.25)"
  - "§6 ADR-010 차단 토큰 15건 + 면책 자동 포함"
  - "§7 회귀 30쌍 palm_001~030 (4대 선 라벨 100% 정확도)"
permanently_rejected:
  - "§3 U-Net CFM 딥러닝 세그멘테이션 — 학습 데이터 0 + 결정론 패턴 충돌"
deferred_pending_data:
  - "§2.2 Bézier curve fitting 알고리즘 구체 구현 (보고서 추상 명세만)"
  - "§5.1 W_i 가중치 학술 수치 (보고서 미명시, equal weighting 임시 적용)"
  - "§3 손금 세그멘테이션 마스크 (학습 데이터 + 모델 배포 결정)"
already_implemented:
  - "ADR-005 palm_reading.py LLM Vision (351줄)"
  - "ADR-006 의료·법률 자문 거절 페르소나"
  - "ADR-010 사실성 분리 disclaimer 패턴"
  - "ADR-020 L2 photo_quality Laplacian (palm 임계값 150)"
related_adr: [ADR-001, ADR-002, ADR-004, ADR-005, ADR-006, ADR-010, ADR-020, ADR-030]
adr_017_first_application: "2026-05-17 (squeeze-report 11회째)"
original_file: ../../../손금 4대 선 및 보조선 결정론 점수 엔진 구축 명세서.md
adopted_option: "C — 5개 라인 결정론 점수 + 비대칭성 equal weighting + U-Net REJECT + Bézier DEFER"
---

# 손금 4대 선 + 보조선 결정론 점수 엔진 구축 — palm_scoring.py 본문화 (ADR-030)

## 보고서 요약

652줄, 51KB. palm-reading-app C1·C2 DEFER 영역 직격. MediaPipe Hand 21
키포인트 기반 4대 선 + 금성대 결정론 점수 엔진 명세 + Size Korea 임계값
+ ADR-010 차단 토큰 + 회귀 30쌍 완전 기술.

학술 출처: Size Korea + KCI NODE00559265 + PubMed PMC7195958·PMC9256497.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| Size Korea 7/8차 인체측정 (남성 0.770 비율) | ✅ 보고서 §1.1 명시 |
| KCI NODE00559265 한국인 손금 11.5% Simian | ✅ KCI 출처 |
| MediaPipe Hand Landmarker 21 키포인트 | ✅ ai.google.dev 공식 |
| PubMed PMC7195958·PMC9256497 | ✅ 학술 출처 |
| §4 5개 라인 임계값 본문 명시 | ✅ 라인 113-213 완전 기술 |
| §7 회귀 30쌍 palm_001~030 | ✅ 라인 292-557 본문 명시 |

## 🟡 구조 (시스템 설계 명제)

- 4대 선 기하학적 ROI (MediaPipe 키포인트 폴리곤)
- 정규화 메트릭 (예: lifeline_arc / distance(kp5, kp0))
- 3분위 라벨 (low / medium / high) + label_ko
- 좌우 손 비대칭성 AI = Σ(Δ_i × W_i)
- 학파 명시 래핑 (Samudrika Shastra)

## 🔴 빈 약속 / 영구 거부

| 영역 | 사유 |
|---|---|
| **§3 U-Net CFM 세그멘테이션** | 학습 데이터 0, 온디바이스 미결정, 결정론 충돌 → REJECT |
| §2.2 Bézier curve fitting 알고리즘 | 추상 명세, 구체 알고리즘 미정 → DEFER |
| §5.1 W_i 가중치 | "발달적 변동성 계수에 역비례" 명시했으나 구체 수치 0 → equal weighting 임시 |
| §7 keypoints_subset (3/21) | 보고서 회귀 데이터에 kp0·5·17만 명시. expected_scores 정상 추출 |

## 본 시스템 반영 (ADR-030 본문화)

### 채택 영역

- **5 라인 임계값** (생명·두뇌·감정·운명·금성대)
- **palm_scoring.py 신규 모듈**:
  - `score_palm(keypoints, hand_side)` → PalmScoringReport
  - `asymmetry_index(left, right)` → 비대칭성 (equal weighting)
  - `filter_forbidden_tokens(text)` → ADR-010 차단 토큰 검증
  - `disclaimer_palm_ko()` → 손금 전용 면책
- **회귀 21건** (test_palm_scoring.py):
  - 보고서 §7 30쌍 × 4선 = **120/120 라벨 정확도 100%**
  - 5 라인 임계값 검증 (low/medium/high 경계)
  - 15 차단 토큰 검증 (의료·위험·성격 결함)
  - 면책 자동 포함 + 학파 명시 + 결정론
- **데이터**: korean_baseline + Size Korea 0.770/0.745 비율

### 거부 영역

- **§3 U-Net 세그멘테이션 (REJECT)**: 학습 데이터 0 + 결정론 충돌 + Railway 배포 비용
  → 본 시스템 결정론 엔진 패턴 (face_scoring·hwapae_korean·name_uniqueness)과 정합 X

### DEFER 영역

- **§2.2 Bézier curve fitting**: 직선 거리 정규화 대체 (Phase 1)
- **§5.1 W_i 학술 수치**: equal weighting (별도 딥리서치 후 ADR supplement)

## ADR-017 절차 11회째 적용 결과

| 순 | 영역 | 결과 |
|---|---|---|
| 1 | L2 photo_quality | 9 PASS (ADR-020) |
| 2 | B6 DreamNet v4 | 17 PASS (ADR-021) |
| 3 | face_shape 5형 | 18 PASS (ADR-022) |
| 4 | A8 Freud v2 | 26 PASS (ADR-023) |
| 5 | MBTI compat v2 | 29 PASS (ADR-024) |
| 6 | 한국 화투 48매 | 30 PASS (ADR-025) |
| 7 | 9389자 scourt API | 자동 통과 (ADR-026) |
| 8 | KCI 자원오행 94자 | 28 PASS (ADR-027) |
| 9 | 표준발음법 Priority 1·2 | 59 PASS (ADR-028) |
| 10 | 한국 성씨·인명 빈도 | 21 PASS (ADR-029) |
| **11** | **손금 결정론 5 라인** | **21 PASS (ADR-030, 120/120 라벨 정확도)** |

### 분석/판정 vs 오케스트레이터 보충 결과

- 분석 에이전트 (Haiku): 후보 8건 + 사용자 결정 3건 (U1·U2·U3) + 빈 약속 5건
- 판정 에이전트 (Haiku): ACCEPT 6 (C2·C4·C5·C6·C7·C8) + REJECT 1 (C3 U-Net) + DEFER 1 (C1 비대칭성)
- **오케스트레이터**: 보고서 §4 5개 라인 임계값 + §7 30쌍 JSON 직접 추출 + 본 시스템 face_scoring 패턴 차용 결정. 비대칭성도 equal weighting으로 ACCEPT 전환 (사용자 자율 정신).

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Size Korea 출처 | ✅ 공식 |
| KCI 학술 출처 | ✅ 검증 |
| MediaPipe 21 키포인트 | ✅ 공식 |
| 보고서 §7 회귀 30쌍 | ✅ 본문 완전 명시 |
| §4 임계값 5 라인 | ✅ 본문 명시 |
| U-Net 학습 데이터 | ❌ 보고서 0건 (REJECT) |
| Bézier curve 알고리즘 | ❌ 추상 명세 (DEFER) |
| W_i 가중치 학술 수치 | ❌ 미명시 (equal weighting) |
| 본 프로젝트 적합성 | ✅ palm-reading-app DEFER 영역 직격 해소 |

## 메타

- 영속화: 2026-05-17 (ADR-017 11회째)
- palm-reading-app C1·C2 DEFER → ADR-030으로 해소
- face_scoring.py (ADR-004) 패턴 차용 성공
- 본 노트 immutable
