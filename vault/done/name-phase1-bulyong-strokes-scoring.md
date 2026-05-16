---
type: done
date: 2026-05-17
phase: name
domain: [name]
related_adr: [decisions/ADR-001-name-deterministic-engine]
report_sections: [§1, §2]
commits: [cd04847]
tests_added: 60
loc_added: 730
---

# 작명 Phase 1 — 불용한자·강희자전·81수리 4격

## 무엇

보고서 §1~§2의 결정론 도메인 엔진 본문화. 3개 모듈 신규.

## 왜

- 다른 컴 PR이 face_reading + safety 모듈들을 단순 상태로 되돌린 직후
- 작명은 캐릭터 페르소나만 있고 결정론 진단 엔진 부재
- 보고서가 강조한 "제약 조건 만족 알고리즘 엔진" 기반 마련 필요

## 어떻게

### `name_bulyong.py` — §1 불용한자
- 보고서 §1 명시 12자(星·吉·極·錦·敏·二·小·末·終·天·地·月)
- 프론트 기존 80자 흡수
- 13개 흉화 카테고리 (death/illness/disaster/celestial 등)
- 항목별: char + reason + source(학파)
- `scan_name()` / `diagnose_name()` + severity (none/minor/major/severe)

### `name_strokes.py` — §2 강희자전 원획수
- 250+ 자주 쓰는 인명용 한자
- **변형 부수 8종 보정** (氵→水 4 / 艹→艸 6 / 扌→手 4 등)
- 보고서 예시 검증: 花 = 7획(필) → **10획(원획)** ✅
- 자원오행 컬럼 (木/火/土/金/水)

### `name_scoring.py` — §2 81수원도 + 4격
- 채구봉 81수원도 — 1~81 GOOD/NEUTRAL/BAD 분류 + 라벨
- 4격(원·형·이·정) 산출
- 외자/복성 예외 처리 (빈 자리 가상 수 1 대입)
- `score_name()` — strokes + four_gyeok + bulyong 통합 envelope

## 검증

- 단위 테스트 60/60 통과
- 라이브 검증: 이성민(李星敏)
  - 원획 [7, 9, 11]
  - 4격: 원20(BAD)·형16(GOOD)·이18(GOOD)·정27(NEUTRAL) → 종합 neutral
  - 불용한자: 星·敏 검출, severity=major

## 면책·한계

- 불용한자 분류는 학파별 차이 있음 → 본 시스템은 "통설" 기준 + 출처 명시
- 외자/복성 예외는 보고서 §2 "가상 수 1 대입" 채택
- "흉상/흉명" 평가어를 사용자 응답에 단정 X — 참고용 표시만

## 다음 단계 (이후 진행됨)

- §3 음양·발음오행·종성 → `name_eumyang.py` / `name_baleum.py`
- §4 두음법칙·한자풀 → `name_dueum.py` / `name_hangul_hanja.py`
- §5 개명·개자 → `name_gaemyeong.py` / `name_gaeja.py`
