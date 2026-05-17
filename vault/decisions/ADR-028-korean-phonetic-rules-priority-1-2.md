---
type: adr
status: accepted
date: 2026-05-17
domain: [name]
related: [ADR-001, ADR-010, ADR-016]
related_report: reports/korean-phonetic-rules-architecture
---

# ADR-028 — 한국어 표준발음법 §10~§30 음운 변동 (Priority 1·2)

## 상태

Accepted (2026-05-17).

## 맥락

ADR-016 (어감 부분 채택)에서 보고서 §1 본문 명시 4규칙(격음+평음 충돌,
ㄴ받침+ㅇ/ㅎ 연음, ㄹㄹ 유음화, 비음 동화)만 부분 채택. 표준발음법
§10~§30 매핑은 미구현 상태.

외부 보고서 "한국어 표준발음법 전산 매핑 및 작명 어감 평가 아키텍처
고도화 연구 보고서"(2026-05-17, 439줄)가 다음 명시:

- §1 매핑 표 (7×5): 7대 음운 변동 × {조항·유니코드 조건·함수·빈도}
- §3 YAML 40 사례 (각 음운 변동별 5~7개 예시)
- §4 JSON 30쌍 회귀 데이터셋 (test_p001~test_p030)
- §5 3단계 로드맵 (Priority 1·2·3)
- §6 ADR-010 준수 면책 가이드라인 (white-list/black-list)

학술 출처: 국립국어원 표준발음법(공식 어문 규범) + 조성문(2025) +
신지영(2010·2014) — 본 시스템 이미 KCI/ISBN 검증 완료 (ADR-016).

## 결정

**Priority 1·2 영역(보고서 §5 라인 343-345)만 본 ADR 본문화**.
Priority 3 (자음군 §11, ㄴ첨가 §29~§30, 상호동화 §19)는 별도 ADR 후보.

### 본문화 영역 (Priority 1·2)

| 음운 변동 | 표준발음법 조항 | 함수 | 우선도 |
|---|---|---|---|
| 비음화 | §18~§19 | `f_nasalize(coda, initial)` | Priority 1 (Critical) |
| 유음화 | §20 | `f_lateralize(coda, initial)` | Priority 1 (Critical) |
| 격음화 | §12 | `f_aspirate(coda, initial)` | Priority 2 (High) |
| 경음화 | §23 (§26 한자어 일부) | `f_tensify(coda, initial)` | Priority 2 (High) |
| 연음 | §13~§16 (§14 겹받침 포함) | `f_link(coda, initial)` | 기본 |
| 자음군 단순화 | §10~§11 | `f_simplify_cluster(coda)` | 기본 (§11+§23 연쇄는 후속) |
| ㄴ첨가 | §29~§30 | `f_insert_n(coda, initial, jung_next)` | Priority 3 (Medium) — 결정론 단정 회피 |

### 합성 함수 (옵션 b — 별도 함수 신설)

판정 에이전트 권장 옵션 b 채택:

```python
phonetic_delta_score(name_korean: str) -> dict
# 반환: {input_name, expected_phonetic, applied_rules, score_delta, rationale}
# score_delta: [-5, 0] 절대값 (보고서 §3·§4 명세)
```

기존 `phonetic_combination_score()` 정규화 [-1.0, 1.0] 스케일은 그대로
보존. 두 함수 독립 호출 가능 (스키마 명확성 + ADR-016 회귀 영향 0).

### 데이터

- `data/korean_phonetic_rules.json` (신규)
  - 보고서 §4 JSON 30쌍 회귀 검증 데이터셋 본문화
  - 각 entry: id, input_name, expected_phonetic, rule_applied, expected_score_delta

### 회귀 (보고서 §4 30쌍)

- **Priority 1·2 통과 14쌍**: 비음화·유음화·기본 경음화·격음화·연음
  - test_p001 (박나리→방나리), test_p003·p005 (비음화)
  - test_p006~p009 (유음화)
  - test_p011·p013·p014·p015 (경음화, p014 송학동→송학똥 -5 극단)
  - test_p018·p019 (격음화)
  - test_p030 (송닭이→송달기 §14 겹받침 연음)
- **Priority 3 known-limitation 16쌍**: 자음군 §11+경음화 연쇄, ㄴ첨가 §29, 상호동화 §19, 한자어 §26 특례
  - 별도 ADR 후보

### 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론 + LLM 분리) | OK | 결정론 자모 분리 + 조건 제어 + lru_cache |
| ADR-002 (사주 학파 회피) | N/A | 음운론, 학파 없음 |
| ADR-006 (자문 거절) | OK | 의료·법률 인과 0 |
| ADR-010 (사실성 분리) | OK | 국립국어원 공식 규범 + 면책 자동 포함 + 인과 단어 차단 |
| ADR-014 (사주→MBTI) | N/A | |
| ADR-015 (옵션 B 병행) | N/A | |
| ADR-016 (어감 부분 채택) | OK | 기존 함수 보존, 신규 함수 별도 |

## 학파 출처

- **국립국어원 표준발음법** — 공식 어문 규범 (대한민국 문화체육관광부 고시)
- **조성문 (2025)** — KCI 「한국인 이름의 음운적 특성에 대한 연구」 
  (국제언어문학, DBpia NODE12552211, ADR-016 영속화 완료)
- **신지영 (2010)** — 『한국어 발음 교육의 이론과 실제』 (한글파크,
  ISBN 9788955186840, ADR-016 영속화 완료)
- **신지영 (2014)** — 『말소리의 이해』 (한국문화사,
  ADR-016 영속화 완료)

## 면책 (ADR-010 준수 강제)

사용자 출력에 `phonetic_delta_score()` 사용 시:

1. **결과 표시**: "박나리"는 표준발음법 §18 비음화 적용 시 [방나리]로
   발음됩니다 (음운 변동 -2 가점)
2. **면책 자동 포함**: `DISCLAIMER_KO` 자동 append
3. **차단 인과 단어**: 운명·사주·흉함·재물운·개명·치명적·팔자
   (회귀 테스트 자동 검증)
4. **white-list만 노출**: 학술적 음운론 설명 + 면책 보일러플레이트
5. **black-list 차단**: "운명에 흉" / "당장 개명 필요" / "재물운 막힘"

## 한계 (영구 기록)

- 본 ADR 14/30 PASS (Priority 1·2). 16건은 known-limitation:
  - 자음군 단순화 §11 + 경음화 연쇄 (test_p028·p029)
  - ㄴ첨가 §29~§30 단어 경계 식별 (test_p021·p022·p023·p025) — 합성어
    경계는 결정론 단정 회피, 보고서도 라인 347 "수의적 발생" 인정
  - 상호동화 §19 (test_p004 송학림 → 송항님)
  - 한자어 경음화 §26 특례 (test_p012 박철수 → 박철쑤) — 한자어/고유어
    구분 LLM 단정 회피
- 인명 단어 경계는 합성어인지 단일 어소인지 결정론 단정 불가 → 보고서가
  명시한 "보수적 최악 시나리오"는 본 ADR 범위 외
- 본 ADR은 **immutable**. Priority 3 본문화 시 새 ADR.

## 관련

- 외부 보고서: [[../reports/korean-phonetic-rules-architecture]]
- 본 작업 영속화: [[../done/korean-phonetic-rules-priority-1-2]]
- 회귀: `engine/divination/test_name_aesthetic.py` (59/59 PASS, ADR-028 신규 25)
- 데이터: `data/korean_phonetic_rules.json` (30 entries)
- 보고서 §6 면책 white-list/black-list: 프론트엔드 단 강제 정책 (별도 작업)
