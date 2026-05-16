---
type: adr
adr_number: 1
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [name]
related: [done/name-phase1-bulyong-strokes-scoring]
---

# ADR-001: 작명 모듈은 결정론 엔진 + LLM 작문 분리

## 배경

- 다른 컴 PR(0ade7a5)이 face_reading + safety 모듈을 단순 상태로 되돌림
- 작명은 캐릭터 페르소나(묵향 선생) 단순 LLM 응답만 존재
- 보고서가 강조한 "제약 조건 만족 알고리즘 엔진" 부재
- 운영표준: 결정론 우선·LLM 작문만

## 검토한 옵션

### A. 모든 작명 진단을 LLM에 위임
- 장점: 구현 빠름
- 단점: 재현성 X, 검증 X, 운영표준 위배, "흉상" 단정 위험

### B. 결정론 엔진 + LLM 분리 (채택)
- 장점: 재현성·검증성·법적 안전·시각화 데이터 노출
- 단점: 도메인 데이터 수동 정리 필요

## 채택

**B 채택**. 관상 face_scoring과 동일한 패턴:
- 결정론 코드 = 진단·점수
- LLM = 사극풍 작문만
- 안전 가드 = 후처리 검증

## 결과

- `name_bulyong`, `name_strokes`, `name_scoring` 3개 모듈 신규
- 회귀 60/60 + 라이브 검증 통과
- 운영표준 §5.2~§7.2와 일관

## 면책

- 불용한자·81수 분류는 학파 통설 기준 → 학파별 차이 있음 명시
- "흉" 분류라도 사용자에게 단정 X (참고용 표시)
