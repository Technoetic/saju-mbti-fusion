---
type: external_report
status: applied
date: 2026-05-17
source: deepresearch
domain: dream
factuality: kci_verified
applied_to:
  - "§4 integrate_multimodal_dream 함수 → engine/agents/dreamnet_multimodal.py (C1 ACCEPT)"
  - "§4 한국 KCI 규준 (aggression 45·negative 40·unfamiliar 55·misfortune 35) → dreambank.py NORMS_KOREAN (C2 ACCEPT)"
  - "§2.1 KCI 학술 출처 (김성재 2004 + 김린 2007) → vault/references/korean-dream-norms-hvdc.md (C3 ACCEPT)"
  - "§8 회귀 20쌍 중 핵심 5쌍 (dreamnet_001~005) → test_dreamnet_multimodal.py (C4 ACCEPT 부분)"
  - "§6 disclaimers 강제 (ADR-006/010/014 정합) → DEFAULT_DISCLAIMERS 3건 (C5 ACCEPT)"
related:
  - decisions/ADR-021-dreamnet-b6-v4
  - decisions/ADR-006-legaltech-rejected
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-014-saju-mbti-prediction-exception
  - references/korean-dream-norms-hvdc
  - templates/PROMPT_dreamnet-multimodal-v4
original_file: ../../멀티모달 꿈 네트워크 B6 v4 연구.md
adr_017_first_application: "2026-05-17 (분석/판정 분리 절차 첫 적용 + ADR-017 두 번째 본문화 사례)"
permanently_rejected:
  - "§2.2 DreamLLM-3D 음성 3D 시각화 — 본 시스템 scope 외 (UI 프론트엔드)"
  - "§7.2 음성 데이터 수집 UI — 법무 부서 검토 + GDPR/PIPA 동의 별도 ADR 필요"
deferred_pending_traffic:
  - "§7.1 한국 규준 동적 스케일링 (10만 건+ 운영 데이터 누적 후 별도 ADR)"
  - "§8 회귀 15쌍 추가 (dreamnet_006~020) — 후속 보강"
deferred_pending_decision:
  - "orchestrator.py::interpret_dream_v2 통합 호출 — 사용자 결정 후 별도 작업"
already_implemented:
  - "BiosignalReport + boost_text_analysis_with_biosignals (B6 v4 인터페이스 정의)"
  - "Hall-Van de Castle 미국 규준 NORMS dict (dreambank.py)"
  - "A1 text_cleaner + A2 hvdc_llm + dreambank + hallvandecastle 학파 모듈 풍부"
---

# B6 DreamNet v4 연구 보고서 — 사실성 분리 + ADR-021 본문화

## 보고서 요약

PROMPT_dreamnet-multimodal-v4.md 의뢰 결과 수령. 58KB 대형 보고서.
B6 DreamNet 멀티모달 꿈 통합 결정론 엔진 명세 + 한국 KCI 학술 규준 +
회귀 데이터셋 20쌍 + ADR-006/010/014 정합 면책 패턴.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| Hall-Van de Castle (1966) 시스템 | ✅ 학술 표준 |
| 김성재 외(2004) "Hall/Van de Castle System을 이용한 20대 한국 남녀의 꿈 내용 분석" | ✅ 수면정신생리 KCI 등재 |
| 김린 외(2007) "Hall/Van de Castle System에 의한 한국 초기 청소년의 최근 꿈 분석" | ✅ 수면정신생리 KCI 등재 |
| 한국 규준값 (aggression 0.45 등) | ✅ 보고서 라인 159-169 명시 |
| 회귀 20쌍 JSON 실 데이터 | ✅ 라인 271 이후 dreamnet_001~020 명시 (빈 약속 아님) |

## 🟡 구조 (시스템 설계 명제)

- integrate_multimodal_dream 결정론 통합 함수 (보고서 §4)
- 멀티모달 입력 5종 (text·HVDC·voice·sleep·user_baseline)
- 한국 baseline delta 계산 (KCI 규준 vs HVDC 파싱 비교)
- DEFAULT_DISCLAIMERS 강제 (ADR-006/010/014)
- post_traffic 동적 스케일링 (10만 건+ 후)

## 🔴 도그마 (영구 거부)

- §2.2 DreamLLM-3D 음성 3D 시각화 — 본 시스템 scope 외
- §7.2 음성 데이터 UI 즉시 활성 — 법무 검토 + GDPR/PIPA 동의 ADR 선행 필요

본 영역은 본 ADR-021 범위 외이며 별도 ADR 작성 시 재검토.

## 본 시스템 반영 (ADR-017 분석/판정 분리 절차 적용)

### 분석 에이전트 (Haiku)
후보 5건 추출 (C1·C2·C3·C4·C5) + 거부 2건 (R1·R2) + 사용자 결정 2건 (U1·U2)

### 판정 에이전트 (Haiku)
**ACCEPT 5건 (모두 통합)** — ADR-002·006·010·014 정합 통과

### 오케스트레이터 직접 검증
- dreamnet_multimodal.py 95줄 인터페이스 정의만 확인 (라인 5-7 주석 명시)
- dreambank.py NORMS 미국 규준만, 한국 0건 확인
- vault/references/ 한국 꿈 규준 0건 확인
- 보고서 §8 dreamnet_001~020 JSON 실 데이터 직접 확인 (분석 에이전트 정확)

### 본문화 (ADR-021)

| 영역 | 파일 | 결과 |
|---|---|---|
| C1 함수 | dreamnet_multimodal.py | integrate_multimodal_dream 신규 + MultimodalIntegration dataclass |
| C2 한국 baseline | dreambank.py | NORMS_KOREAN dict 추가 (4 지표) |
| C3 학술 출처 | references/korean-dream-norms-hvdc.md | KCI 2건 영속화 |
| C4 회귀 | test_dreamnet_multimodal.py | 17 tests PASS (dreamnet_001~005 핵심 5건 포함) |
| C5 disclaimers | DEFAULT_DISCLAIMERS | 3건 강제 + 자동 회귀 검증 |

## 회귀 17 PASS

(ADR-021 명세 참조)

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Hall-Van de Castle 학술 표준 | ✅ |
| 한국 KCI 학술 출처 (수면정신생리) | ✅ 라이브 검증 가능 |
| 회귀 20쌍 JSON 실 데이터 | ✅ 빈 약속 아님 |
| DEFAULT_DISCLAIMERS 강제 | ✅ 회귀 자동 검증 |
| 결정론 보장 | ✅ LLM 호출 0건 |
| 본 프로젝트 적합성 | ✅ 매우 높음 (B6 명시 TODO 해소) |

**총평**: 본 보고서는 PROMPT_dreamnet-multimodal-v4.md 의뢰 결과로 정합도
높음. ADR-017 절차 두 번째 본문화 사례 (ADR-020 L2 다음). 분석 에이전트
오추정 0건 (실 코드 직접 확인 의무 작동 입증).

## 향후

- 회귀 15쌍 추가 (dreamnet_006~020)
- orchestrator.py interpret_dream_v2 통합 호출
- 음성·수면 모달리티 활성 (법무 검토 + SDK 안정화 후)
- 동적 한국 규준 (운영 데이터 10만 건+ 후 별도 ADR)

## 메타

- 영속화: 2026-05-17 (ADR-017 절차 적용 + ADR-021 본문화)
- ADR-017 두 번째 본문화 성공 사례
- 분석 에이전트 오추정 0건 (보강된 프롬프트 작동 입증)
- B6 명시 TODO 1건 해소 (A8·A13 잔존)
- 본 노트 immutable
