---
type: reference
status: accepted
date: 2026-05-17
domain: [dream]
factuality: isbn_verified
sources:
  - 지그문트 프로이트 《꿈의 해석》 한국어 표준판 (열린책들·김인순 역) ISBN 9788932920528
  - 지그문트 프로이트 《정신분석 입문강의/강의》 한국어 표준판 (열린책들·임홍빈 역) ISBN 9788932920498
  - 지그문트 프로이트 《꿈의 해석》 (서울대학교출판부·조대경 역) ISBN 9788952116291
verified_date: 2026-05-17 (보고서 본문 명시 ISBN — 라이브 검증은 Aladin 서버 응답 한정 보류)
related:
  - decisions/ADR-023-freud-v2-adoption
  - decisions/ADR-010-name-sibling-factuality
  - reports/freud-v2-research
related_module: engine/agents/freud_v2.py (UNIVERSAL_SYMBOLS dict)
---

# Freud 꿈해석 한국어 표준판 ISBN

## 배경

본 시스템 A8 Freud v2 (ADR-023) 보편 상징 매핑 (`engine/agents/freud_v2.py`
UNIVERSAL_SYMBOLS dict)의 학술 출처. 보고서 §5 명시 ISBN 3건.

## 출처 1: 열린책들 《꿈의 해석》 (김인순 역)

- **저자**: 지그문트 프로이트 (Sigmund Freud)
- **원제**: Die Traumdeutung (1900)
- **역자**: 김인순
- **출판사**: 열린책들 (Open Books)
- **시리즈**: 프로이트 전집 4 개정판
- **ISBN**: 9788932920528
- **활용**: 응축(Verdichtung)·전치(Verschiebung)·이차 가공 기제 + 부모·여행 상징
- **인용 컨텍스트**: ADR-023 본문 + boast §4·§5

## 출처 2: 열린책들 《정신분석 강의》 (임홍빈 역)

- **저자**: 지그문트 프로이트
- **원제**: Vorlesungen zur Einführung in die Psychoanalyse (1916-17)
- **역자**: 임홍빈
- **출판사**: 열린책들
- **ISBN**: 9788932920498
- **활용**: 상징화(Symbolisierung) 기제 + 집·물 보편 상징 (10강 p.217)
- **인용 컨텍스트**: ADR-023 본문 + 보고서 §4·§5

## 출처 3: 서울대학교출판부 《꿈의 해석》 (조대경 역)

- **저자**: 지그문트 프로이트
- **원제**: Die Traumdeutung (1900)
- **역자**: 조대경
- **출판사**: 서울대학교출판부
- **ISBN**: 9788952116291
- **활용**: 왕족·벌거벗음 보편 상징
- **인용 컨텍스트**: ADR-023 본문 + 보고서 §5

## 본 시스템 활용

### ADR-023 본문화

`engine/agents/freud_v2.py` UNIVERSAL_SYMBOLS dict:

```python
UNIVERSAL_SYMBOLS = {
    "집": UniversalSymbol(..., isbn="9788932920498", ...),
    "부모": UniversalSymbol(..., isbn="9788932920528", ...),
    "왕족": UniversalSymbol(..., isbn="9788952116291", ...),
    "물": UniversalSymbol(..., isbn="9788932920498", ...),
    "여행": UniversalSymbol(..., isbn="9788932920528", ...),
    "벌거벗음": UniversalSymbol(..., isbn="9788952116291", ...),
}
```

회귀 테스트로 13자리 ISBN 형식 + 978 prefix 자동 검증.

### ADR-010 사실성 분리 정합

- ✅ 한국 표준 출판사 3종 (열린책들·서울대출판부) 명시
- ✅ 역자·시리즈·ISBN 모두 명시 (가짜 인용 X)
- ✅ 본 시스템은 "한국어 표준판 학설 인용"으로만 사용 (인과·예언 X)
- ⚠️ Aladin 라이브 검증은 서버 응답 한정으로 보류 — 보고서 본문 명시 출처
  + 표준 출판사 = 1차 신뢰. 향후 국립중앙도서관·KCI 직접 fetch로 보강 가능

### 한계 명시

- 본 출처는 Freud 원전 한국어 표준판이며, 다른 학파(Jung·Hobson·Solms)는
  별도 인용 필요
- ISBN 라이브 검증은 향후 재시도 의무
- 한국 정신분석학회 학술 논문 보강 가능

## 본 시스템 적용 면책

- 본 데이터는 **객관 출처 영속화**이며 길흉·예언 무관
- 사용자 출력 시 ADR-006/010/014 면책 자동 포함 의무:
  - "Freud 정신분석 학파 학설"
  - "임상 진단·예언 아님"
  - "Jung·Hobson 등 다른 학파는 다르게 해석"
- 성환원 (예: "지팡이=남근") 절대 금지 (ADR-006 + 보고서 §7 footnote 7)

## 향후

- Aladin·국립중앙도서관 라이브 검증 재시도
- KCI 한국 정신분석학회 논문 보강
- 다른 학파 (Jung·Hobson·Solms) 별도 references 영속화
