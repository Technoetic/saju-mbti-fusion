---
type: adr
adr_number: 3
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [name]
related: [done/name-phase2-saju-unihan]
report_section: §4
---

# ADR-003: 한자 풀은 수동 250자 우선 + Unihan 8525자 fallback

## 배경

보고서 §4: 9,389자 인명용 한자 풀 권고.
현 수동 250자만 — 운영 가능하나 풀 작음.

## 검토한 옵션

### A. 수동 9389자 전체 정리
- 정확도 최고, 시간 수주~수개월

### B. Unihan만 사용 (8525자)
- 자동, 빠름
- 단점: Unihan kTotalStrokes는 **변형 부수 보정 없는 단순 필획**
- 花 = 7획 (Unihan) vs 10획 (보고서 §2 강희자전 보정)

### C. 수동 + Unihan fallback (채택)
- 수동 250자: 변형 부수 보정 정확 → 우선
- Unihan 8525자: 미수록 한자 자동 매핑 → fallback

## 채택

**C 채택**. 정확도와 풀 크기를 모두 잡음.

## 결과

- `engine/divination/name_unihan.py` 신규 (지연 로딩)
- `name_strokes.kangxi_strokes()` fallback 패턴:
  1. 수동 `_BY_CHAR` lookup
  2. None이면 `name_unihan.kangxi_strokes()` 호출
- `data/korean_hanja_unihan.json` 728KB
- Dockerfile에 `COPY data ./data` 추가

## 자원오행 한계

- 부수 기반 자동 매핑 41% (3524자)
- 추상 부수(亠·勹·宀 등) 59% 미정 — 학파 결정 후 수동 필요
- 학파별 합의 없음 → 미정 한자는 `""` 빈 문자열

## 면책

- Unihan 데이터는 표준이지만 "강희자전 원획"과 미세 차이
- 변형 부수 8종(氵→水 등) 보정은 수동 표만 정확

## 향후

- 9,389자 - 8,525자 = 864자 부족
- 대법원 인명용 한자 PDF 별도 파싱 시 충족 가능
- 자원오행 5001자 수동 매핑은 외부 보고서 누적 시 진행
