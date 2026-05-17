---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: palm
applied_to: []
neo4j_synced: false
factuality: mixed
related:
  - decisions/ADR-005-claude-opus-vision.md
  - decisions/ADR-006-legaltech-rejected.md
  - decisions/ADR-010-name-sibling-factuality.md
original_file: ../../지능형 손금 분석 모바일 애플리케이션 개발을 위한 종합 도메인 지식 및 기술 아키텍처 보고서.md
adr_017_first_application: "2026-05-17 (분석/판정 분리 절차 첫 적용)"
permanently_rejected:
  - "§4.1 2D:4D Digit Ratio = 성격 예측 — ADR-006 의료·생물학적 인과 + Manning 2002 출처 라이브 검증 실패"
  - "§4.2 한의학 손톱 병리 사용자 출력 — ADR-006 영구 거부 (1차 확정)"
  - "§5.1 베다 점성술(Jyotish) D10 통합 — 본 시스템 스코프 외 (한국 동양학)"
  - "§6.2 U-Net + CFM 딥러닝 세그멘테이션 — 학습 데이터 0장 + 온디바이스 아키텍처 부재 + 결정론 정책 위반"
  - "§2.2 생명선 끊어짐 = 환경 급변·스트레스 인과 — palm_reading.py 페르소나 이미 차단"
  - "환원주의 인과 ('Digit Ratio = 호르몬 = 성격')"
deferred_pending_research:
  - "§2.1 좌우 손 교차 분석 (선천=비우세수 / 후천=우세수) — MediaPipe Hand 21 키포인트 결정론 매핑 + 학술 출처 필요"
  - "§2.2-2.3 4대 주요 선 + 보조선 결정론 점수표 — 보고서 임계값 미명시 (호 넓이·곡률 모호 표현만), face_scoring.py 패턴 재사용 가능하나 손금 선 정량화 학술 출처 필요"
user_decision_required:
  - "§8 경쟁사 벤치마킹 + 에이전틱 AI UX — GDPR/PIPA 개인화 데이터 정책 ADR 선행 필요"
already_protected:
  - "palm_reading.py 옥선 할미 페르소나: 단정 예언 금지 + 의료·법률·투자 자문 거절 + 외모 평가 금지 + 겁주기 금지 (1차 처리에서 확인)"
  - "engine/divination/face_scoring.py 532줄: MediaPipe 478 키포인트 결정론 엔진 (LLM 없이 12궁 점수) — 손금 영역 적용 시 참조 패턴"

# 손금 분석 앱 도메인·아키텍처 — 사실성 검토

## 보고서 요약

베다 수수상학(Samudrika Shastra) + 서양 수수상학 + 한의학 손톱 병리학 결합. 좌우 손 교차 분석, 4대 주요 선(생명·두뇌·감정·운명) 위상수학적 해석, 손가락 비율(Digit Ratio), 딥러닝 선 분할, 온디바이스 엣지 AI.

## 본 프로젝트 현 상태

✅ **이미 손금 도메인 존재**: [engine/divination/palm_reading.py](../../engine/divination/palm_reading.py)
- 옥선 할미(玉仙) 페르소나
- Gemini Vision 호출 (멀티모달)
- 24h 캐시
- safety 통합 (crisis·legal_notice)

## 🟢 팩트

| 주장 | 검증 |
|---|---|
| 4대 주요 선 (생명·두뇌·감정·운명) | ✅ 수수상학 표준 |
| 좌우 손 차이 (비우세수=선천, 우세수=후천) | ✅ 수수상학 표준 |
| Digit Ratio (2D:4D) — 태아기 호르몬 지표 | ✅ 실제 학술 연구 존재 (단, 해석은 논란) |
| 딥러닝 선 분할 (Segmentation) 기술 | ✅ 실존 기법 |
| 온디바이스 엣지 AI | ✅ 일반 패러다임 |
| 손톱 병리학 (한의학) | 🟡 한의학 진단의 일부 — 의료 자문 영역 (ADR-006 충돌) |

## 🟡 구조

- 좌우 손 위상 차이 (Delta) 분석은 합리적
- 4 주요 선 + 구(Mounts) + 기호 다층 분석
- 도메인 지식 → 알고리즘 매핑

## 🔴 도그마 / 위험

| 항목 | 판정 |
|---|---|
| "선의 길이는 수명을 결정하지 않으며, 활력 측정 미터기" | 🟡 책임 회피 표현 — 그러나 여전히 인과 주장 |
| "생명선 끊어짐 = 물리적 환경 급변·스트레스" | 🔴 인과 예언 |
| "두뇌선 분기 = 작가의 포크" | 🟡 전통 관습 라벨 |
| "감정선 모양으로 연애 생활 결론" | 🔴 사적 영역 인과 주장 |
| **한의학 손톱 병리** → 사용자에게 출력 | 🔴 **의료 자문** (ADR-006 정면 충돌) |
| "재정적 잠재력" 분석 | 🔴 금융 자문 영역 가능 |

## 본 프로젝트 현 palm_reading.py와 매핑

[engine/divination/palm_reading.py](../../engine/divination/palm_reading.py)의 옥선 할미 시스템 프롬프트는 본 보고서가 권장하는 인과적 표현을 **이미 회피**:
- "단정적 예언 금지 — '~될 것이다' 같은 단언 X. 대신 '~한 결이 보이는구먼'"
- "의료·법률·투자 자문 거절"
- "외모 평가·미추 비교 금지"
- "절대 겁주지 말 것"

→ 본 보고서가 채택을 권하는 인과 표현은 **palm_reading.py 페르소나 규칙으로 이미 차단됨**.

## 본 시스템 반영

### ✅ 채택 가능 (이미 부분 적용)

1. **4 주요 선 정량 분석** — 현재 LLM Vision 호출로 처리. 결정론 점수표(face_scoring.py 패턴) 도입 가능
2. **좌우 손 비교** — 현재 미구현 (palm_reading.py는 단일 손). 추가 검토 가치 있음
3. **딥러닝 선 분할** — 정확도 향상 시 도입 검토 (비용·복잡도 평가 필요)

### 🟡 위험 영역 (사용자 출력 면책 강화)

1. **한의학 손톱 병리** — 도입 거부 (ADR-006 충돌)
2. **금융·연애·건강 인과 예언** — palm_reading.py 페르소나가 이미 차단. 추가 강화는 output_safety_gate에서

### ❌ 본 프로젝트 미적용 결정

- 사용자에게 "당신의 손금은 [질병 가능성]" 같은 의료성 출력 금지
- "Digit Ratio = 호르몬 노출 = 성격" 같은 환원주의적 인과 출력 금지

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 수수상학 전통 지식 | ✅ 대체로 정확 |
| 딥러닝·엣지 AI 기술 | ✅ 정확 |
| Digit Ratio 학술 | 🟡 학술 존재하나 해석 논란 |
| 한의학 손톱 병리 사용자 출력 | 🔴 의료 자문 위험 |
| 본 프로젝트 적합성 | 🟡 부분 적용 가능, 위험 영역 차단 필요 |

## 다음 액션

- [ ] (선택) palm_reading.py에 결정론 점수표 추가 — face_scoring.py 패턴 (Phase 2 시점)
- [ ] (확정) 손톱 병리·의료 인과 출력 금지 정책 유지
- [ ] (보류) 좌우 손 비교 — 사용자 UX 평가 후 결정

## 출처

- 본 보고서 원본: `사주/지능형 손금 분석 모바일 애플리케이션 개발을 위한 종합 도메인 지식 및 기술 아키텍처 보고서.md`

## 2026-05-17 ADR-017 절차 첫 적용 결과

본 보고서는 1차 처리(2026-05-17)가 ADR-017 분석/판정 분리 패턴 도입 전이라
**ADR-017 절차 첫 적용 재호출** 수행. 분석/판정 에이전트 (Haiku) 2회 dispatch.

### 분석 결과
- 후보 7건 (C1~C7) + 거부 3건 (R1·R2·R3) + 사용자 결정 3건 (U1·U2·U3)

### 판정 결과
- **ACCEPT 0건**
- **REJECT 6건**: C3 Digit Ratio·C4 손톱·C5 점성술·C6 U-Net·R1·R2·R3
- **DEFER 2건**: C1 좌우 손·C2 4선 점수표 (별도 딥리서치 + 학술 임계값 필요)
- **USER_DECISION 2건**: C7 에이전틱 UX·U1~U3

### 오케스트레이터 핵심 발견

| 항목 | 사실 |
|---|---|
| face_scoring.py | 532줄, MediaPipe Face Landmarker 478 키포인트 → 12궁 0.0~1.0 점수, LLM 없이 결정론 산출 |
| palm_reading.py | 351줄, **Gemini Vision LLM 단독**, 결정론 점수표 0개 |
| 결손 영역 | palm_scoring.py (face_scoring.py 패턴 차용) — 단, 보고서 본문에 손금 선 정량 임계값 명시 부재 → 즉시 본문화 불가 |

### 결론

본 호출도 코드 변경 0. 비용 (Haiku 2회 ≈ $0.02)으로:
- ADR-017 절차 정합화
- frontmatter `permanently_rejected` 6건 + `deferred_pending_research` 2건 + `already_protected` 2건 영속화
- C1·C2 DEFER 영역은 별도 딥리서치 프롬프트(palm_scoring) 신설 가치 발견

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리)
- ADR-017 첫 적용: 2026-05-17 (코드 변경 0, 절차 정합화 + 영구 거부 영속화)
- ADR-010 사례 9호
- 본 노트 immutable
