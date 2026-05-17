---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-032-korean-phonetic-priority-3
related_report: reports/korean-phonetic-priority-3
---

# 표준발음법 Priority 3 영역 결정론 매핑 본문화 (ADR-032)

## 작업 요약

외부 보고서 "한국어 표준발음법 Priority 3 영역 결정론 매핑 및 다중 음운
변동 연쇄 알고리즘 연구 보고서" (185줄) §1~§8 부분 본문화. ADR-028
Priority 1·2 잔여 known-limitation 16건 중 일부 해소.

ADR-017 절차 **열세 번째 본문화 사례**.

## 변경 사항

### 데이터 (신규)

- [data/korean_phonetic_priority_3_regression.json](../../data/korean_phonetic_priority_3_regression.json) — 보고서 §8 30쌍

### 코드 (확장)

- [engine/divination/name_aesthetic.py](../../engine/divination/name_aesthetic.py) — 신규 4 함수
  - `f_neutralize(coda)` — §9 평파열음화 (7자음 중화)
  - `f_weaken_h(prev_coda, current_initial, next_jung)` — §12 ㅎ 약화 유성음 환경
  - `f_hanja_tensify(coda, initial)` — §26 한자어 경음화 휴리스틱
  - `phonetic_delta_score_v2(name)` — Priority 1·2·3 통합 (ADR-028 v1 보존)

### 회귀 테스트

- [engine/divination/test_name_aesthetic.py](../../engine/divination/test_name_aesthetic.py) — **70/70 PASS** (59 기존 + 11 신규)
  - f_neutralize 7자음 매핑
  - f_weaken_h 유성음/무성음 환경 분기
  - f_hanja_tensify ㄹ+[ㄷㅅㅈ]
  - phonetic_delta_score_v2 스키마 + 결정론 + 면책
  - 보고서 §8 30쌍 → 10 PASS + 20 known-limitation
  - v1 v2 독립 호출

### 신규 ADR

- [vault/decisions/ADR-032-korean-phonetic-priority-3.md](../decisions/ADR-032-korean-phonetic-priority-3.md)

### 신규 보고서

- [vault/reports/korean-phonetic-priority-3.md](../reports/korean-phonetic-priority-3.md)

## 보고서 §8 30쌍 회귀 결과

### 10 PASS ✅

| ID | 입력 | 출력 | 적용 규칙 |
|---|---|---|---|
| test_p103 | 박영진 | 바경진 | 보수적 연음 (§13) |
| test_p104 | 김유리 | 기뮤리 | 보수적 연음 |
| test_p110 | 박철수 | 박철쑤 | 한자어 §26 휴리스틱 |
| test_p111 | 김말자 | 김말짜 | 한자어 §26 |
| test_p112 | 이일도 | 이일또 | 한자어 §26 |
| test_p113 | 최빛나 | 최빈나 | 평음화 §9 + 비음화 §18 |
| test_p121 | 박넓음 | 방널븜 | 형식형태소 §14 자음군 연음 |
| test_p122 | 김맑음 | 김말금 | 형식형태소 §14 |
| test_p128 | 오백로 | 오뱅노 | 비음화 + 상호동화 |
| test_p130 | 정십리 | 정심니 | 비음화 + 상호동화 |

### 20 known-limitation ⏸️

- test_p101·p102: 자음군→경음화 연쇄 (단순화 후 재경음화 미구현)
- test_p105·p106: 미세 연음 차이 (정연우→저여누, 송여름→소여름)
- test_p107·p108·p109: 상호동화 (ㅎ 약화 충돌)
- test_p114: 화이트리스트 ㄴ첨가 (꽃잎→꼰닙) 미구현
- test_p115: 평음화→격음화 미정렬
- test_p116·p117: 다중 연쇄 위상 미완성
- test_p118·p119·p120: ㅎ 약화 + ㅢ→ㅣ 모음 변동 미정
- test_p123·p124·p125: 자음군 단순화 분기
- test_p126·p127·p129: 비음화 붙임 §19

→ 결정론 보장 (동일 입력 동일 출력). 별도 ADR 후보 (ADR-033).

## ADR-010 사실성 분리

- ✅ 학술 출처: 국립국어원 표준발음법
- ✅ 면책 자동 포함 (rationale에 DISCLAIMER_KO)
- ✅ 한자어 식별 휴리스틱 (Default-allow 보수적, LLM 단정 회피)
- ✅ ㄴ첨가 Default-deny (단어 경계 결정론 회피)
- ✅ 결정론 (lru_cache + 정규식)

## 라이브 검증 예시

```python
>>> from engine.divination.name_aesthetic import phonetic_delta_score_v2
>>> phonetic_delta_score_v2("박철수")
{'input_name': '박철수', 'expected_phonetic': '박철쑤',
 'applied_rules': ['§26 한자어 경음화 (ㄹ+ㅅ→ㅆ)'], 'score_delta': -2, ...}
>>> phonetic_delta_score_v2("최빛나")
{'input_name': '최빛나', 'expected_phonetic': '최빈나',
 'applied_rules': ['§9+§18 평음화+비음화 (ㅊ→ㄴ / ㄴ_)'], 'score_delta': -2, ...}
>>> phonetic_delta_score_v2("박넓음")
{'input_name': '박넓음', 'expected_phonetic': '방널븜',
 'applied_rules': ['§9+§18 평음화+비음화', '§14 형식형태소 연음'], ...}
```

## 향후 작업

- ADR-033: ㅢ→ㅣ 모음 변동 + 자음군→경음화 연쇄 + 다중 위상 정렬
- 고유어 블랙리스트 250자 수집
- ㅎ 약화 후 모음 변동 처리

## 메타

- ADR-017 열세 번째 본문화
- ADR-028 잔여 영역 부분 해소 (Priority 3 10/30 PASS)
- v1 phonetic_delta_score 보존 (ADR-028 회귀 14/30 PASS 유지)
- 본 노트 immutable
