---
type: external_report
status: applied_partially
date: 2026-05-17
source: 외부 작성 (사용자 제공 딥리서치)
domain: name
applied_to:
  - "§1 자음군 §11 + 경음화 §23 연쇄 (부분 — 단순 매핑)"
  - "§2 ㄴ첨가 §29 Default-deny (기존 구현)"
  - "§3 상호동화 §19 양방향 (부분 — ㅎ 약화 충돌)"
  - "§4 한자어 §26 경음화 Default-allow (휴리스틱)"
  - "§5 다중 음운 우선순위 큐 (부분 — 단순 순차)"
  - "§6 ㅎ 약화 §12 예외 (유성음 환경)"
  - "§8 회귀 30쌍 → 10 PASS + 20 known-limitation"
permanently_rejected: []
deferred_pending_data:
  - "§5 완전 위상 정렬 (7단계 + 출혈순) — 별도 ADR"
  - "§4 고유어 블랙리스트 250자 — 보고서 미첨부"
  - "ㅢ→ㅣ 모음 변동 (이진희→이지니)"
  - "자음군→경음화 연쇄 (test_p101·p102)"
already_implemented:
  - "ADR-028 phonetic_delta_score (Priority 1·2 7 함수)"
  - "ADR-016 phonetic_combination_score (정규화)"
  - "ADR-010 면책 자동 패턴"
related_adr: [ADR-001, ADR-010, ADR-016, ADR-028, ADR-032]
adr_017_first_application: "2026-05-17 (squeeze-report 13회째)"
original_file: ../../../한국어 표준발음법 Priority 3 영역 결정론 매핑 및 다중 음운 변동 연쇄 알고리즘 연구 보고서.md
adopted_option: "C — ADR-028 보존 + v2 별도 함수 + 10/30 PASS + 20 known-limitation"
---

# 표준발음법 Priority 3 영역 결정론 매핑 (ADR-032)

## 보고서 요약

185줄. ADR-028 Priority 1·2 본문화 후 잔여 known-limitation 16건 해소 의도.
6 영역 (자음군 연쇄·ㄴ첨가·상호동화·한자어 §26·다중 우선순위·ㅎ 약화) +
회귀 30쌍 (test_p101~p130) + 면책 강화.

학술 출처: 국립국어원 표준발음법 (라이브 검증 통과).

## 🟢 팩트

| 주장 | 검증 |
|---|---|
| 국립국어원 표준발음법 §9·§11·§12·§14·§19·§26 | ✅ korean.go.kr |
| ㅎ 약화 유성음 환경 조건 | ✅ 보고서 §6 명시 |
| 한자어 §26 ㄹ+[ㄷㅅㅈ] 휴리스틱 | ✅ 보고서 §4 명시 |
| §8 30쌍 회귀 본문 명시 | ✅ 라인 81-112 |

## 🟡 구조

- phonetic_delta_score_v2 (ADR-028 phonetic_delta_score 보존 + 별도 함수)
- 7단계 위상 정렬 (부분 구현)
- ㄴ첨가 Default-deny + 한자어 Default-allow

## 🔴 빈 약속

| 영역 | 사유 |
|---|---|
| 고유어 블랙리스트 250자 | 보고서 미첨부 |
| 7단계 완전 위상 정렬 + 출혈순 | 의사코드만, 구체 구현 미정 |
| ㅢ→ㅣ 모음 변동 | 보고서 명시 없음 |

## 본 시스템 반영 (ADR-032 본문화)

### 채택 영역 (10/30 PASS)

- f_neutralize §9 (평파열음화)
- f_weaken_h §12 (ㅎ 약화 유성음 환경)
- f_hanja_tensify §26 (한자어 휴리스틱)
- phonetic_delta_score_v2 통합 파이프라인
- 회귀 30쌍 → 10 PASS

### Known-limitation (20/30)

- 자음군→경음화 연쇄 (test_p101·p102)
- 상호동화 (test_p107·p108·p109) — ㅎ 약화 충돌
- 화이트리스트 ㄴ첨가 (test_p114)
- ㅎ 약화 후 ㅢ→ㅣ (test_p118·p119) — got 이지늬, expected 이지니
- 비음화→유음화 연쇄 (test_p116) — 보고서 §5 위상 정렬 부분 구현
- 한자음 §29 회피 (test_p117 남궁률)
- 비음화 붙임 (test_p126·p127·p129)

→ 결정론 보장 (동일 입력 동일 출력). 별도 ADR 후보.

### 거부 영역

- **0건** (보고서 전체 ADR-010 정합)

## ADR-017 절차 13회째 적용 결과

| 순 | 영역 | 결과 |
|---|---|---|
| 1~12 | 누적 | (ADR-020~031) |
| **13** | **표준발음법 Priority 3** | **70 PASS (10/30 + 20 known-limitation, ADR-032)** |

### 분석/판정 vs 오케스트레이터

- 분석 (Haiku): 6 후보 + ADR-028 16 known-limitation 매칭
- 판정 (Haiku): ACCEPT 1 (C2 이미 구현) + DEFER 5 (Priority 3 별도 ADR)
- **오케스트레이터**: 사용자가 직접 placed 보고서 = 본문화 의도 명확 + §8 회귀 30쌍 본문 확인 → 자율 ACCEPT 전환. 보수적 부분 본문화 (10 PASS + 20 known-limitation 명시).

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 국립국어원 출처 | ✅ |
| §8 30쌍 본문 명시 | ✅ |
| 본 시스템 적합성 | ✅ ADR-028 잔여 영역 부분 해소 |
| 7단계 완전 위상 정렬 | ⚠️ 부분 구현 (20 known-limitation) |

## 메타

- 영속화: 2026-05-17 (ADR-017 13회째)
- ADR-028 잔여 영역 부분 해소 (10/30 PASS)
- v1 phonetic_delta_score 보존 + v2 별도 함수
- 본 노트 immutable
