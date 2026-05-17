---
type: external_report
status: applied
date: 2026-05-17
source: deepresearch
domain: saju
applied_to:
  - 이재승(2019) 억부론 계량화 → ADR-015 + engine/divination/name_saju_school.py
neo4j_synced: false
factuality: kci_verified
related:
  - decisions/ADR-002-saju-option-A (옵션 A 디폴트 유지)
  - decisions/ADR-010-name-sibling-factuality (사실성 분리 통과)
  - decisions/ADR-015-saju-option-B-eokbu
  - references/lee-jaeseung-2019.md
  - done/saju-option-B-eokbu.md
original_file: ../../사주 용신 학파 채택 연구 보고서.md
verified_against:
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10750186 (2026-05-17 fetch)
  - https://db.koreascholar.com/article/Detail/369719
---

# 사주 용신 학파 채택 연구 보고서 — 사실성 검증 및 본문화

## 본 보고서의 등급

본 프로젝트 모든 외부 보고서 중 **가장 ADR-010 정합도 높음**:

1. KCI 등재 논문 출처 라이브 검증 완료 (이재승 2019, DBpia)
2. 가중치·임계치가 논문 원문과 일치
3. 학파 내 이견 명시 (의도된 설계 제약 — 학술적 정직성)
4. ADR-010 면책 의무 자체 인용
5. 인과 예언 거부 자체 선언

## 🟢 팩트 (KCI 검증 완료)

| 주장 | 검증 |
|---|---|
| 4 학파 4대 원전 (자평진전·궁통보감·연해자평·적천수천미) | ✅ 명리학 통설 |
| 이재승(2019) 계량화 가중치 (연간5/연지9/월간10/월지30/일간20/일지21/시간10/시지15) | ✅ KCI 라이브 검증 |
| 4단계 임계치 (45/60/75) | ✅ 논문 명시 |
| 합충형해파 동적 변화 미반영 = 의도된 설계 제약 | ✅ 학술적 정직성 |

## 🟡 구조 (시스템 명제)

- 결정론 함수 설계 — 멱등성 보장
- 옵션 A vs 옵션 B 병행 — ADR-002 학파 회피 디폴트 + 옵션 B 추가 정보

## 🔴 도그마 / 부정확

| 항목 | 평가 |
|---|---|
| "압도적 1위 점유율" | 작명 시장 점유율 직접 통계 출처 없음 (자체 평가) |
| §4 검증 데이터셋 일부 케이스 | **수동 계산 오류 1건 발견** — `壬辰 壬寅 甲午 丙寅`은 80점이 정답, 보고서 65점은 오류. 본 모듈은 §3 코드 명세 우선 |

본 문제는 ADR-010 사실성 분리 적용 사례 — **보고서를 무비판 채택하지 않고
§3 명세 vs §4 정답 충돌 시 코드 명세 우선** 처리.

## 본 시스템 반영 (완료)

### 코드
- [engine/divination/name_saju_school.py](../../engine/divination/name_saju_school.py)
- [engine/divination/test_name_saju_school.py](../../engine/divination/test_name_saju_school.py) — 19 PASS
  · 매핑 테이블 4
  · 보고서 §4 검증 케이스 8 (1건은 §4 오류 보정)
  · ADR-015 사용자 출력 의무 3
  · 결정론 보장 2

### vault
- [vault/decisions/ADR-015-saju-option-B-eokbu.md](../decisions/ADR-015-saju-option-B-eokbu.md)
- [vault/references/lee-jaeseung-2019.md](../references/lee-jaeseung-2019.md) — KCI 출처 영속화
- [vault/done/saju-option-B-eokbu.md](../done/saju-option-B-eokbu.md)
- [vault/roadmap/saju-option-B-school.md](../roadmap/saju-option-B-school.md) — done 이동

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| 학파 비교 분석 | ✅ 명리학 통설 + KCI 검증 |
| 결정론 알고리즘 명세 | ✅ 코드와 일치 |
| 검증 데이터셋 | 🟡 50건 중 1건 수동 오류 발견 — §3 명세 우선 처리 |
| 출처 (KCI · ISBN) | ✅ 모두 검증 가능 |
| 면책 의무 | ✅ ADR-010 정신 자체 인용 |
| 본 프로젝트 적합성 | ✅ 최상 (이미 채택 완료) |

## 다음 액션

- [x] ADR-015 작성 (옵션 B 채택, ADR-002 병행)
- [x] engine/divination/name_saju_school.py 본문화
- [x] 19 회귀 PASS
- [x] vault/references/lee-jaeseung-2019.md 신규
- [x] vault/done/saju-option-B-eokbu.md
- [x] roadmap → done 이동
- [ ] (선택) 사용자 출력 UI 통합 — 사용자 결정 영역 (🔵 사업 단계)

## 출처

- 본 보고서 원본: `사주/사주 용신 학파 채택 연구 보고서.md`
- KCI 검증 (2026-05-17 라이브 fetch):
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10750186
  - https://db.koreascholar.com/article/Detail/369719

## 메타

- 영속화: 2026-05-17 (검증 + 본문화)
- ADR-010 사실성 분리 적용 — 보고서 §4 오류 발견·보정
- 본 노트 immutable
