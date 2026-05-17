---
type: done
status: applied
date: 2026-05-17
domain: [saju]
adr: ADR-031-saju-twelve-stages
related_report: reports/saju-twelve-stages-jangsaeng
---

# 사주 십이운성(十二運星) 결정론 매핑 본문화 (ADR-031)

## 작업 요약

외부 보고서 "운세 SaaS 백엔드 사주 모듈의 십이운성 결정론 매핑 및
아키텍처 통합 연구 보고서" (378줄) §2·§4·§5·§6 본문화. engine/saju/
명시 결손 영역(twelve_stages.py) 해소. shensha.py 패턴 차용.

ADR-017 절차 **열두 번째 본문화 사례**. ADR-015 옵션 B 패턴 두 번째 적용
(이재승 억부론 후 자평진전).

## 변경 사항

### 데이터 (신규 2건)

- [data/twelve_stages_mapping.json](../../data/twelve_stages_mapping.json) — 120 셀 (10 천간 × 12 지지)
  - 자평진전 학파 + 양순음역 + 화토동궁
  - KCI 출처: NODE10738496 + NODE08998998
- [data/twelve_stages_regression.json](../../data/twelve_stages_regression.json) — 자동 생성 30쌍
  - 양간 12 + 음간 12 + 화토동궁 6 (random.seed=42)

### 코드 (신규)

- [engine/saju/twelve_stages.py](../../engine/saju/twelve_stages.py) — 신규 모듈 11 API
  - `get_twelve_stage(day_stem, branch)` 핵심 함수
  - `get_twelve_stage_with_rationale(day_stem, branch)` ADR-010 면책 포함
  - `evaluate_four_pillars_stages(...)` 4주 종합
  - `total_mappings()` / `total_stems()` / `list_stages()` 메타
  - `is_valid_stem()` / `is_valid_branch()` 검증
  - `kci_sources()` 학술 출처
  - `TwelveStageResult` 불변 dataclass

### 회귀 테스트

- [engine/saju/test_twelve_stages.py](../../engine/saju/test_twelve_stages.py) — **17/17 PASS**
  - 120 셀 전수 검증 (`test_each_stem_has_12_stages`)
  - 자동 생성 30쌍 회귀
  - 양순음역 + 화토동궁 원칙 검증
  - 4주 종합 + 학파 명시 + 면책 자동
  - 인과 단어 차단 (반드시·확정·예언·무조건)
  - 결정론 보장

### 신규 ADR

- [vault/decisions/ADR-031-saju-twelve-stages.md](../decisions/ADR-031-saju-twelve-stages.md)

### 신규 보고서

- [vault/reports/saju-twelve-stages-jangsaeng.md](../reports/saju-twelve-stages-jangsaeng.md)

## 자평진전 학파 원칙

| 천간 | 음양 | 장생 위치 | 방향 |
|---|---|---|---|
| 甲 | 양목 | 亥 | 순행 |
| 乙 | 음목 | 午 | 역행 (甲의 사지) |
| 丙 | 양화 | 寅 | 순행 |
| 丁 | 음화 | 酉 | 역행 (丙의 사지) |
| 戊 | 양토 | 寅 | 화토동궁 (丙과 동일) |
| 己 | 음토 | 酉 | 화토동궁 (丁과 동일) |
| 庚 | 양금 | 巳 | 순행 |
| 辛 | 음금 | 子 | 역행 (庚의 사지) |
| 壬 | 양수 | 申 | 순행 |
| 癸 | 음수 | 卯 | 역행 (壬의 사지) |

## 라이브 검증 예시

```python
>>> from engine.saju.twelve_stages import get_twelve_stage, get_twelve_stage_with_rationale
>>> get_twelve_stage("甲", "亥")
'장생'
>>> get_twelve_stage("壬", "子")
'제왕'
>>> get_twelve_stage("戊", "寅")  # 화토동궁
'장생'
>>> r = get_twelve_stage_with_rationale("甲", "亥")
>>> r.school
'자평진전 (양순음역 + 화토동궁)'
>>> r.stage
'장생'
```

## ADR-010 사실성 분리 자동 검증

회귀 테스트 `test_rationale_no_causal_words` 자동:
- 인과 단정 단어 차단: "반드시", "확정", "예언", "고독·단명", "무조건"
- rationale 자동 포함:
  - 자평진전 학파 명시
  - "운명·길흉화복과 인과관계는 없습니다"
  - "타 학파(동생동사·수토동궁) 이견 존재"
  - "사·묘 단계는 실제 죽음이 아닌 추상적 상태"

## 학술 출처 (KCI 라이브 검증 통과)

- **최산태·김만태 (2021)**: 영산대 동양문화연구 NODE10738496 — 화토동궁
- **김계성 (2016)**: 단국대 동양학 제65호 NODE08998998 — 양순음역

`kci_sources()` 함수로 사용자 출력 시 노출 가능.

## REJECT/DEFER 영역

- **§8 합충형해파 동적 확장 (REJECT)**: ADR-002 학파 회피 침해, 별도 ADR
- **참고 자료 5·9번 (REJECT)**: 카페 출처 학술 검증 불가
- **U2·U3 (DEFER)**: UI/API 사업 결정

## 향후 작업

- 합충형해파 동적 확장 (별도 ADR-NNN, KCI 학파 검증 후)
- API 엔드포인트 사업 결정 후 노출
- 일간 신강/신약 통합 → 십이운성 + 억부론 (ADR-015) 결합 해석

## 메타

- ADR-017 열두 번째 본문화
- ADR-015 옵션 B 패턴 두 번째 사례 (이재승 → 자평진전)
- shensha.py 패턴 완벽 차용 (60갑자 해시 → 십이운성 매핑)
- 보고서 빈 약속 (회귀 30쌍) 자율 생성으로 해소
- 본 노트 immutable
