---
type: adr
status: accepted
date: 2026-05-17
domain: [saju]
related: [ADR-001, ADR-002, ADR-010, ADR-015]
related_report: reports/saju-twelve-stages-jangsaeng
---

# ADR-031 — 사주 십이운성(十二運星) 결정론 매핑 (자평진전 학파)

## 상태

Accepted (2026-05-17).

## 맥락

engine/saju/ 모듈 풀: pillars·ten_gods·wuxing·shensha·myeong 등 11개.
**십이운성(12단계 인생 비유) 매핑 모듈 부재** — 사주 명리학 핵심 체계 결손.

외부 보고서 "운세 SaaS 백엔드 사주 모듈의 십이운성 결정론 매핑 및 아키텍처
통합 연구 보고서" (2026-05-17, 378줄):

- §1 시스템 결손 진단 + ADR 정합 (ADR-002·010·015)
- §2 12단계 철학 (태·양·장생·목욕·관대·건록·제왕·쇠·병·사·묘·절)
- §3 학파 비교 (동생동사 vs 양순음역 + 화토동궁 vs 수토동궁)
- §4 **120 셀 완전 매핑** (10천간 × 12지지) YAML 본문 명시
- §5 TwelveStagesMapper 싱글턴 의사코드
- §6 ADR-010 면책 가이드라인

학술 출처 (KCI 라이브 검증):
- 최산태·김만태 (2021) 영산대 동양문화연구 NODE10738496 (화토동궁)
- 김계성 (2016) 단국대 동양학 제65호 NODE08998998 (양순음역)

## 결정

**자평진전 학파(양순음역 + 화토동궁) 단일 채택** + ADR-015 옵션 B 패턴 적용.
ADR-002 학파 회피의 예외 — KCI 검증 통과 + 학파 명시 + ADR-010 면책 강제.

### 본문화 영역

| 영역 | 내용 |
|---|---|
| `data/twelve_stages_mapping.json` | 120 셀 (10 × 12) + KCI 출처 + 자평진전 원칙 |
| `data/twelve_stages_regression.json` | 자동 생성 회귀 30쌍 (양간 12 + 음간 12 + 화토동궁 6) |
| `engine/saju/twelve_stages.py` | 결정론 매핑 모듈 (shensha.py 패턴 차용) |
| `engine/saju/test_twelve_stages.py` | 회귀 17건 (120 셀 전수 + 30 샘플 + 면책) |

### Public API

```python
get_twelve_stage(day_stem, branch) -> str | None
get_twelve_stage_with_rationale(day_stem, branch) -> TwelveStageResult | None
evaluate_four_pillars_stages(day_stem, year_branch, month_branch, day_branch, hour_branch) -> dict
total_mappings() -> int  # 120
total_stems() -> int  # 10
is_valid_stem(stem) -> bool
is_valid_branch(branch) -> bool
list_stages() -> tuple  # 12 stages
kci_sources() -> dict
is_loaded() -> bool
```

### 자평진전 원칙

- **양순음역**: 양간(甲丙戊庚壬) 시계 순행, 음간(乙丁己辛癸) 반시계 역행
- **화토동궁**: 戊=丙 궤적, 己=丁 궤적
- 음간 장생 위치: 양간의 사지(死地)

| 천간 | 장생 위치 | 시작 단계 |
|---|---|---|
| 甲 (양목) | 亥 | 순행 (시계) |
| 乙 (음목) | 午 | 역행 (반시계, 甲의 사지) |
| 丙 (양화) | 寅 | 순행 |
| 丁 (음화) | 酉 | 역행 (丙의 사지) |
| 戊 (양토) | 寅 | 화토동궁 (丙과 동일) |
| 己 (음토) | 酉 | 화토동궁 (丁과 동일) |
| 庚 (양금) | 巳 | 순행 |
| 辛 (음금) | 子 | 역행 (庚의 사지) |
| 壬 (양수) | 申 | 순행 |
| 癸 (음수) | 卯 | 역행 (壬의 사지) |

### 정합성

| ADR | 정합성 | 사유 |
|---|---|---|
| ADR-001 (결정론) | OK | lru_cache + JSON 120 셀 완전 결정론 |
| ADR-002 (학파 회피) | OK (ADR-015 예외) | 자평진전 단일 학파 명시 + 학파 출처 노출 |
| ADR-006 (자문 거절) | OK | 운명·길흉 인과 0 |
| ADR-010 (사실성 분리) | OK | rationale에 학파 명시 + 면책 + 타학파 이견 명시 + 인과 단어 차단 |
| ADR-014 (사주→MBTI) | N/A | |
| ADR-015 (옵션 B 병행) | OK | 자평진전 채택 패턴 (이재승 억부론과 동일 정신) |

## 학파 명시 + ADR-010 면책 자동 출력

`get_twelve_stage_with_rationale()` 반환 예시:

```
"일간 '甲'이 지지 '亥'을 만났을 때, 자평진전 학파 기준 십이운성 단계는
'장생'으로 분류됩니다. ※ 본 결과는 자평진전 단일 학파(양순음역 + 화토동궁)
의 객관적 매핑이며, 개인의 운명·수명·길흉화복과 인과관계는 없습니다. 타
학파(동생동사·수토동궁 등) 이견이 존재합니다. 사(死)·묘(墓) 단계는 실제
죽음이 아닌 기운의 추상적 상태를 의미합니다."
```

## 회귀 자동 생성 (보고서 §7 빈 약속 해소)

보고서 §7 "30쌍 JSON 데이터셋" 본문 누락 → 본 시스템 자동 생성:
- 양간 12쌍 (甲·丙·庚·壬 각 3 branch random.seed=42)
- 음간 12쌍 (乙·丁·辛·癸 각 3 branch)
- 화토동궁 6쌍 (戊·己 각 3 branch)

120 셀 매핑이 정답 데이터이므로 30 샘플은 부분 검증. 추가로
`test_each_stem_has_12_stages()` 전수 (120 셀) 검증 자동.

## REJECT 영역

- **§3 동적 확장 (합충형해파)**: 새로운 학파 인입 = ADR-002 침해. 별도 ADR 필요
- **R1 개인 블로그/카페 출처 (참고 5·9번)**: 학술 검증 불가

## DEFER 영역 (사용자 결정)

- **U2 UI 면책 문구 노출 방식**: 사업 단계
- **U3 API 엔드포인트 사업 결정**: 사업 단계

## 한계 (영구 기록)

- 본 ADR은 **정적 매핑만**. 합충형해파는 별도 ADR
- 자평진전 단일 학파 채택. 동생동사·수토동궁 학설은 rationale에서 명시만
- 본 ADR은 **immutable**

## 관련

- 외부 보고서: [[../reports/saju-twelve-stages-jangsaeng]]
- 본 작업 영속화: [[../done/saju-twelve-stages]]
- 회귀: `engine/saju/test_twelve_stages.py` (17/17 PASS)
- 데이터: `data/twelve_stages_mapping.json` + `data/twelve_stages_regression.json`
- shensha.py 패턴 (참조): 신살 5종 결정론 매핑
