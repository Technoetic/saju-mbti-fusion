---
type: adr
adr_number: 21
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [dream]
related:
  - ADR-006-legaltech-rejected
  - ADR-010-name-sibling-factuality
  - ADR-014-saju-mbti-prediction-exception
  - ADR-017-squeeze-report-command
related_module: ../../engine/agents/dreamnet_multimodal.py
related_report: ../reports/b6-dreamnet-v4-research
related_reference: ../references/korean-dream-norms-hvdc
related_prompt: ../templates/PROMPT_dreamnet-multimodal-v4
---

# ADR-021: B6 DreamNet v4 — 멀티모달 꿈 통합 결정론 엔진

## 배경

`engine/agents/__init__.py`에 명시된 `B6 DreamNet (v4) — TODO` 영역.
[PROMPT_dreamnet-multimodal-v4.md](../templates/PROMPT_dreamnet-multimodal-v4.md)
딥리서치 의뢰 → 보고서 수령 → /squeeze-report 절차 적용 결과:

- 분석 에이전트 (Haiku): 후보 5건 (C1·C2·C3·C4·C5)
- 판정 에이전트 (Haiku): ACCEPT 5건 (모두 통합)
- 오케스트레이터 (Opus): 본문화

본 보고서는 ADR-017 절차 두 번째 본문화 사례 + 명시 TODO 영역 첫 해소.

## 결정

`engine/agents/dreamnet_multimodal.py` 보강:
- `integrate_multimodal_dream()` 함수 신규 (보고서 §4 명세)
- `MultimodalIntegration` dataclass (결과 컨테이너)
- `DEFAULT_DISCLAIMERS` 강제 면책 배열 (ADR-006/010/014 정합)
- `_compute_korean_baseline_delta()` 한국 KCI 규준 편차

`engine/divination/dream_lex/dreambank.py` 보강:
- `NORMS_KOREAN` dict 추가 (김성재 2004 + 김린 2007 KCI)

### 멀티모달 입력

- text: 꿈 보고 텍스트 (기본)
- hvdc_parsed_data: A1·A2 Hall-Van de Castle 파싱 결과 (옵션)
- voice_audio_features: 음성 메타 (emotion_tone·speech_rate, 옵션)
- sleep_stages: 수면 단계 (REM 비율 등, 옵션)
- user_baseline: 사용자 개인 베이스라인 (post_traffic, 옵션)

입력된 모달리티만 통합 — 누락된 모달리티는 None 유지.

### ADR-006/010/014 정합 강제

`DEFAULT_DISCLAIMERS` 3건:
1. "본 결과는 자기 보고 분석이며 임상 진단이 아닙니다."
2. "Hall-Van de Castle(1966) 시스템 + 한국 KCI 학술 규준 비교 통계입니다."
3. "꿈 패턴 해석은 다중 요인 영향이며 미래 사건 예언 아닙니다."

회귀 테스트로 자동 검증:
- disclaimers 비어있지 않음
- '임상'·'진단' 단어 포함
- 'Hall-Van de Castle'·'HVDC' 학파 명시
- 인과 표현 금지어 0건 (확실히·반드시 발생·당신은 우울증·예언합니다·운명입니다)

### 한국 KCI 규준 (NORMS_KOREAN)

| 지표 | 규준값 | 출처 |
|---|---|---|
| aggression_pct | 45.0 | 김성재 외(2004) 20대 남녀 |
| negative_emotion_pct | 40.0 | 김성재 외(2004) |
| unfamiliar_character_pct | 55.0 | 김성재 외(2004) |
| misfortune_pct | 35.0 | 김린 외(2007) 청소년 |

출처: 수면정신생리 (대한수면의학회) KCI 등재.
[vault/references/korean-dream-norms-hvdc.md](../references/korean-dream-norms-hvdc.md) 영속화.

### 회귀 테스트 17 PASS

`engine/agents/test_dreamnet_multimodal.py`:

1. integrate basic
2. text modality
3. multi modality
4. disclaimers required (강제 + Hall-Van de Castle 명시)
5. no causal words (인과 표현 0건)
6. korean baseline delta + (양수 편차)
7. korean baseline delta - (음수 편차)
8. integration_score range (-10~+10)
9. dreamnet_001 falling (보고서 §8 절벽 추락)
10. dreamnet_002 unfamiliar (보고서 §8 낯선 남성)
11. dreamnet_003 teeth (보고서 §8 이빨)
12. dreamnet_004 flying (보고서 §8 비행)
13. dreamnet_005 pursuit (보고서 §8 추적)
14. to_dict (dataclass 변환)
15. empty text
16. DEFAULT_DISCLAIMERS count (3 이상)
17. empty delta (HVDC 없을 때)

## 검토한 옵션

### A. 보고서 명세 그대로 본문화 (채택)

- 장점:
  - PROMPT_dreamnet-multimodal-v4.md 의뢰 결과 정합
  - KCI 학술 출처 라이브 검증 통과
  - ADR-006/010/014 정합 자동 회귀
  - B6 명시 TODO 해소
- 단점:
  - 5개 모달리티 중 text만 즉시 사용 (voice·sleep·user_baseline는 미래 확장)
  - 보고서 회귀 20쌍 중 5쌍만 채택 (나머지 15쌍은 후속 작업)

### B. 보고서 §7 동적 스케일링 즉시 채택

- 장점: 완전성
- 단점: 운영 데이터 10만 건+ 누적 필요 (post_traffic) — DEFER

### C. 음성 UI + GDPR/PIPA 동의 즉시 구현

- 장점: 완결
- 단점: 법무 부서 검토 의존 → DEFER

## 채택

**A 채택**. 코드 영속화 단계만. 운영·법무 영역은 별도 ADR 대기.

## 결과

### 신규 / 변경 파일
- `engine/agents/dreamnet_multimodal.py` (95줄 → 247줄 보강)
- `engine/agents/test_dreamnet_multimodal.py` (회귀 17 PASS)
- `engine/divination/dream_lex/dreambank.py` (NORMS_KOREAN dict 추가)
- `vault/references/korean-dream-norms-hvdc.md` (KCI 학술 출처)
- `vault/decisions/ADR-021-dreamnet-b6-v4.md` (본 ADR)

### vault 영속화
- `vault/decisions/INDEX.md` (ADR-021 추가)
- `vault/done/dream-b6-dreamnet-v4.md` (done 기록)
- `vault/done/INDEX.md` (꿈해석 도메인 행 추가)
- `vault/reports/b6-dreamnet-v4-research.md` 신규 (사실성 분리)

### engine/agents/__init__.py TODO 갱신

본 ADR 본문화로 B6 TODO 해소. A8 Freud v2 + A13 social_unconscious v3
2건 TODO 잔존 (각각 PROMPT 영속화 완료).

## 한계

- 음성·수면 모달리티는 SDK 안정화 + 법무 검토 후 활성 (현재 인터페이스만)
- 한국 KCI 규준은 정적 값 (운영 데이터 10만 건+ 누적 시 동적 스케일링 별도 ADR)
- 회귀 20쌍 중 5쌍만 즉시 채택 (나머지는 후속 보강 가능)
- orchestrator.py::interpret_dream_v2 통합 호출은 선택 (별도 작업)

## 면책

- 본 모듈은 **결정론 멀티모달 통합**이며 LLM 생성 0
- 사용자 출력 disclaimers 강제 (ADR-006/010/014)
- 의료 단정·미래 예언 절대 금지
- Hall-Van de Castle 학설 명시 의무

## 향후

- 회귀 15쌍 추가 (dreamnet_006~020)
- orchestrator.py interpret_dream_v2 통합 호출
- 음성·수면 모달리티 활성 (SDK + 법무 검토 후)
- 동적 한국 규준 (10만 건+ 운영 데이터 후)
- A8 Freud v2 + A13 social_unconscious v3 후속 본문화

## 메타

- ADR-017 절차 두 번째 본문화 사례 (ADR-020 L2 photo_quality 다음)
- engine/agents/ 명시 TODO 3건 중 1건 해소 (B6)
- PROMPT_dreamnet-multimodal-v4.md → 보고서 수령 → ADR-021 본문화 = 완전 파이프라인
