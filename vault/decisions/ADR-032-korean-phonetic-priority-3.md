---
type: adr
status: accepted
date: 2026-05-17
domain: [name]
related: [ADR-001, ADR-010, ADR-016, ADR-028]
related_report: reports/korean-phonetic-priority-3
---

# ADR-032 — 표준발음법 Priority 3 영역 결정론 매핑 (phonetic_delta_score_v2)

## 상태

Accepted (2026-05-17).

## 맥락

ADR-028 (Priority 1·2) 본문화 완료, 회귀 14/30 PASS. Priority 3 known-limitation 16건:
- 자음군 §11 + 경음화 §23 연쇄
- ㄴ첨가 §29~§30 단어 경계
- 상호동화 §19
- 한자어 §26 경음화 특례
- 평음화 §9 + 비음화 연쇄
- ㅎ 약화 §12 예외
- 격음화 변형 + 비음화 붙임 + 겹받침 연음 예외 + 비음화+유음화 연쇄

외부 보고서 "한국어 표준발음법 Priority 3 영역 결정론 매핑 및 다중 음운
변동 연쇄 알고리즘 연구 보고서" (2026-05-17, 185줄) §1~§8 본문화.

학술 출처: 국립국어원 표준발음법 §9·§11·§12·§13·§14·§18·§19·§20·§23·§26·§29.

## 결정

**ADR-028 phonetic_delta_score 보존 + ADR-032 phonetic_delta_score_v2 별도 함수 신설**.
ADR-016 부분 채택 + ADR-028 옵션 b 패턴 정합.

### 본문화 영역

| 영역 | 내용 |
|---|---|
| `data/korean_phonetic_priority_3_regression.json` | 보고서 §8 30쌍 (test_p101~p130) |
| `engine/divination/name_aesthetic.py` | 신규 함수 4개 + phonetic_delta_score_v2 |
| `engine/divination/test_name_aesthetic.py` | 회귀 11건 신규 (70/70 PASS) |

### 신규 함수 (보고서 §1~§6)

| 함수 | 표준발음법 조항 | 역할 |
|---|---|---|
| `f_neutralize(coda)` | §9 평파열음화 | 종성 7자음 중화 (ㅊ→ㄷ 등) |
| `f_weaken_h(prev_coda, current_initial, next_jung)` | §12 ㅎ 약화 예외 | 유성음 환경 ㅎ 탈락 + 연음 |
| `f_hanja_tensify(coda, initial)` | §26 한자어 경음화 | ㄹ+[ㄷㅅㅈ] 휴리스틱 (Default-allow) |
| `phonetic_delta_score_v2(name)` | 통합 (§1~§6) | Priority 1·2·3 통합 파이프라인 |

### 파이프라인 (보고서 §5 7단계 위상 정렬)

1. f_weaken_h (ㅎ 약화 유성음 환경)
2. f_aspirate (격음화 §12)
3. f_neutralize (평파열음화 §9 — 후속 비음화 트리거)
4. §19 상호동화 (코다 폐쇄음 + 초성 ㄹ → 비음 + ㄴ)
5. §14 형식형태소 자음군 연음 우선 (단순화 배제)
6. §18 비음화 (평음화 결과 적용)
7. §20 유음화
8. §26 한자어 경음화 (Default-allow)
9. §23 일반 경음화
10. §13 연음 (Default-deny ㄴ첨가)

### 회귀 30쌍 결과

**10/30 PASS**:
- test_p103·p104·p105·p106: 보수적 연음 (ㄴ첨가 배제)
- test_p110·p111·p112: 한자어 §26 휴리스틱
- test_p113: 평음화+비음화 연쇄 (최빛나→최빈나)
- test_p121·p122: 형식형태소 자음군 연음 (박넓음→방널븜)
- test_p128·p130: 비음화 + 상호동화

**20/30 known-limitation**:
- test_p101·p102: 자음군→경음화 연쇄 (단순화 후 재경음화 미구현)
- test_p107·p108·p109: 상호동화 잘못 적용 (ㅎ 약화 충돌)
- test_p114: 화이트리스트 ㄴ첨가 미구현
- test_p115·p118·p119·p120: ㅎ 약화·ㅢ→ㅣ 모음 변동 미정
- test_p116·p117·p123·p124·p125·p126·p127·p129: 다중 연쇄 정밀화 필요

모든 미통과 영역도 **결정론 보장** (동일 입력 동일 출력).

### 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론) | OK | lru_cache + 정규식 + 결정론 자모 분리 |
| ADR-002 (학파 회피) | N/A | 음운론 |
| ADR-006 (자문 거절) | OK | 의료·법률 인과 0 |
| ADR-010 (사실성 분리) | OK | 면책 자동 + 한자어 단정 회피 (Default-allow 보수적) |
| ADR-016 (어감 부분 채택) | OK | phonetic_delta_score 보존, v2 별도 함수 |
| ADR-028 (Priority 1·2) | OK | 보존 + v2 보강 |

## 학파/공식 출처

- 국립국어원 표준발음법 (보고서 라인 122-125 라이브 검증 통과)
- 보고서 §6 보수적 정책: ㄴ첨가 §29 Default-deny, 한자어 §26 Default-allow

## 면책 (ADR-010 준수)

phonetic_delta_score_v2 rationale 자동 포함:
- "Priority 3 통합 적용 시" 명시
- DISCLAIMER_KO 자동 첨부
- 차단 토큰 자동 검증 (운명·길흉 0건)

## 한계 (영구 기록)

- 10/30 PASS. 20/30 known-limitation 결정론 보장만
- f_weaken_h가 ㅎ 약화 후 ㅢ→ㅣ 모음 변동 미처리 (이진희 → 이지늬, expected 이지니)
- 자음군→경음화 연쇄 미구현 (test_p101·p102)
- 보고서 §8 7단계 위상 정렬 부분 구현 (완전 위상 정렬은 별도 ADR)
- v1 phonetic_delta_score는 보존 (ADR-028 회귀 14/30 PASS 유지)
- 본 ADR은 **immutable**

## 관련

- 외부 보고서: [[../reports/korean-phonetic-priority-3]]
- 본 작업 영속화: [[../done/korean-phonetic-priority-3]]
- 회귀: `engine/divination/test_name_aesthetic.py` (70/70 PASS)
- 데이터: `data/korean_phonetic_priority_3_regression.json` (30 entries)
- 직전 ADR: ADR-028 (Priority 1·2)
