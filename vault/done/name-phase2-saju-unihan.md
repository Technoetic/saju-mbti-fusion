---
type: done
date: 2026-05-17
phase: name
domain: [name, saju]
related_adr: [decisions/ADR-002-saju-option-A, decisions/ADR-003-unihan-fallback]
report_sections: [§3, §4]
commits: [91d311e, 264ae63, 7e0fbe7]
tests_added: 28
loc_added: 1200
---

# 작명 Phase 2 — 사주 통합 + 한자 풀 8525자

## 무엇

§3 만세력 활용 (옵션 A) + §4 인명용 한자 풀 250자 → 8525자.

## 왜

- §3: 사주에 따른 자원오행 추천이 작명 차별화의 핵심
  - 단, 용신 도출은 학파 분쟁 영역 → 단순 오행 카운팅으로 우회
- §4: 보고서가 강조한 "9,389자 풀"을 250자에서 확장하지 않으면 운영 한계

## 어떻게

### `name_saju_ohaeng.py` — 옵션 A
- 기존 `engine/saju/pillars` + `wuxing` wrapper
- `compute_saju_ohaeng(y, m, d, h)` → SajuOhaengReport
  - 4기둥 한자 / 일간 / 오행 분포 8.0 / 추천 자원오행 / 균형 점수
- **용신 도출 학파 회피** — 단순 분포에서 weakest/missing 추천
- "참고용·학파별 차이 있음" 면책

### `name_unihan.py` + `data/korean_hanja_unihan.json`
- Unicode Unihan database 8.5MB zip 다운로드 + 파싱
- `kHangul` 있는 한자 8,525자 추출
- 컬럼: char / hangul / kangxi_strokes / radical / resource_ohaeng
- 자원오행 41% 부수 기반 자동 매핑 (3524자)
- `name_strokes` fallback 연동:
  1. 수동 250자 (변형 부수 보정 정확) — 우선
  2. Unihan 8525자 — fallback

### Dockerfile 수정
- `COPY data ./data` 추가
- `.dockerignore`에 `data/unihan/` (49MB 원본 zip) 제외

## 검증

### 로컬
- 단위 테스트 28/28 (saju_ohaeng 13 + unihan 15)
- 전체 회귀 189/189

### 라이브
- 첫 배포 후 라이브 0자 발견 → Dockerfile 수정 → 재배포 8525자 정상
- 1990-05-15 14시 → 사주 庚午/壬午/乙巳/癸未 (乙 일간) → 추천 木
- 花 (변형 부수 보정 10) / 鴻·煌·叡 (Unihan fallback) 모두 정상

## 면책·한계

- §3 용신 도출 학파별 결과는 안 함 — 단순 오행 분포만
- §4 자원오행 59% (5001자) 미정 — 추상 부수, 학파 결정 후 수동 필요
- Unihan 단순 필획 ≠ 강희자전 원획 (변형 부수 보정 X) — 수동 표 우선

## 다음 단계

- 자원오행 59% 수동 매핑 (외부 보고서 받으면)
- 용신 학파 선택 (딥리서치 받으면 옵션 B 가능)
