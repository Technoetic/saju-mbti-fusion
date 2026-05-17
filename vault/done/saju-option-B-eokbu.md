---
type: done
status: applied
date: 2026-05-17
domain: saju
related:
  - decisions/ADR-015-saju-option-B-eokbu.md
  - decisions/ADR-002-saju-option-A.md
  - reports/saju-option-B-school.md
  - references/lee-jaeseung-2019.md
commit: TBD
---

# 사주 용신 옵션 B — 이재승 계량화 억부론 본문화

## 무엇

[[../reports/saju-option-B-school]] (🟢 외부 입력 대기) 완료. 딥리서치
보고서 수신 + ADR-010 사실성 분리 검증 + KCI 출처 라이브 검증 통과 후
본문화.

## 변경

### 신규 모듈
- [engine/divination/name_saju_school.py](../../engine/divination/name_saju_school.py)
  · `derive_yongshin(pillars)` — 이재승 계량화 (총합 120점)
  · `format_yongshin_for_user(result)` — 면책 자동 포함 출력
  · STEM_OH_MAP / BRANCH_OH_MAP / O_HAENG_MAP / WEIGHTS / 4단계 임계치
  · `DISCLAIMER_KO` 상수

### 신규 테스트
- [engine/divination/test_name_saju_school.py](../../engine/divination/test_name_saju_school.py) — 24 PASS
  · 매핑 테이블 정합성 4
  · 보고서 §4 검증 개별 케이스 8 (1건은 보고서 오류 보정 — ADR-010 적용)
  · ADR-015 사용자 출력 의무 3 (면책·인과 거부·학설 명시)
  · 결정론 보장 2
  · 보고서 §4 50건 전체 매개변수화 회귀 5 (천간 10개 ×5 커버, 4 강약 단계 분포)

### 데이터셋
- [data/saju_school_regression_50.json](../../data/saju_school_regression_50.json) — 보고서 §4 50건 완전 추출

### vault
- ADR-015 신규 (옵션 B 채택, ADR-002 병행 유지)
- references/lee-jaeseung-2019.md 신규 (KCI 출처 영속화)
- reports/saju-option-B-school.md 영속화 (검증 + 적용 상태)
- INDEX 2개 갱신
- roadmap/saju-option-B-school.md → done 이동 예정

## ADR-002와 ADR-015 병행 정책

| 항목 | 옵션 A (ADR-002, 디폴트) | 옵션 B (ADR-015, 추가) |
|---|---|---|
| 출력 | 추천 자원오행 (작명) | 용신 (명리학) |
| 학파 | 학파 회피 | 이재승(2019) 억부론 |
| 사용자 노출 | 항상 | 선택적 |

ADR-002 superseded 하지 않음. 옵션 A는 디폴트로 계속 출력. 옵션 B는 추가 정보.

## ADR-010 사실성 분리 적용 사례

본 작업에서 ADR-010 원칙 2가지 작동:

1. **KCI 출처 라이브 검증** — DBpia/koreascholar에서 이재승(2019) 논문
   실재 확인. 가중치·임계치가 논문 원문과 일치.
2. **보고서 §4 수동 계산 오류 4건 발견** (50건 전체 회귀 후 확인):
   - case 5 (`壬辰 壬寅 甲午 丙寅`): 보고서 65점 / 알고리즘 80점
   - case 33 (`壬子 壬寅 庚午 癸未`): 보고서 20점 / 알고리즘 35점
   - case 37 (`丁巳 丙午 辛卯 乙未`): 보고서 20점 / 알고리즘 35점
   - case 38 (`癸亥 甲寅 辛亥 壬辰`): 보고서 20점 / 알고리즘 35점
   - 모두 동일 패턴: 보고서가 일부 궁의 생조 오행 가산 누락
   - 결정: §3 코드 명세 우선 — 본 알고리즘이 정답
   - **용신 결과는 4건 모두 일치** (강약 임계 동일 범위)
   - 회귀 테스트에 보정 명시 (학술적 정직성)

## 검증

```
python -m pytest engine/divination/test_name_saju_school.py --no-skip-all
24 passed in 1.35s
```

### 50건 전체 회귀 결과 (보고서 §4 데이터셋)
- 용신 결과: **50건 모두 일치** ✅
- 점수 일치: 46건
- 점수 불일치: 4건 (보고서 수동 계산 오류, 본 알고리즘 정답)
- 천간 10개 커버 (각 5건씩)
- 4 강약 단계(신약·중화신약·중화신강·신강) 모두 포함

### 보고서 검증 케이스 일치 (4건)
- 甲子 丙寅 甲子 甲子 → 110점 신강 火土金 ✅
- 戊申 庚申 甲戌 戊辰 → 20점 신약 水木 ✅
- 癸亥 甲子 甲寅 乙亥 → 120점 신강 火土金 ✅
- 己巳 丁卯 甲申 辛未 → 50점 중화신약 水木 ✅

### 라이브 시나리오
1990-05-15 14:00 (庚午 壬午 乙巳 癸未):
- 일간 乙 (목)
- 점수 40점 → 신약
- 용신 水·木 (인성·비겁)

## 통합 정책

본 PR은 **모듈 신설만**. 만월 아씨 페르소나 또는 사용자 UI 통합은 별도
PR (🔵 사업 단계, 사용자 결정 영역):
- 사주 풀이에 옵션 B 자동 노출?
- 별도 섹션 분리?
- 옵션 A·B 비교 표 노출?

## 면책

- ADR-002 학파 회피는 디폴트 출력에 유지
- ADR-014 매핑(사주→MBTI)은 옵션 A 정신 위 그대로 — 영향 0
- 합충형해파·외격·종격은 의도된 설계 제약 (이재승 논문도 한계 인정)
- 사용자 출력에 학설 명시 + 인과 예언 금지 의무

## 결과

[[../reports/saju-option-B-school]] 완료 — 본 프로젝트의 가장 중요한
"🟢 외부 입력 대기" 항목 해소.
