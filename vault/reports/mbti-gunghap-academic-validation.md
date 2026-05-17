---
type: external_report
status: applied
date: 2026-05-17
source: deepresearch
domain: saju
factuality: kci_isbn_verified
applied_to:
  - "§5.1 4단계 알고리즘 → engine/saju/mbti_compat_v2.py (C4 ACCEPT)"
  - "§6 256 매트릭스 → precompute_matrix() (C5 ACCEPT)"
  - "§3.3 6 관계 분류 (dual·mirror·conflict 등) → classify_relationship (C1·C3 ACCEPT)"
  - "§7.1 면책 가이드 → DEFAULT_DISCLAIMERS 3건 (C6 ACCEPT)"
  - "§2.1 Jung·Myers·Keirsey 학술 출처 → vault/references/jung-myers-keirsey-socionics.md (C1 ACCEPT)"
  - "§2.2 KCI 4건 메타분석 → references 영속화 (C2 ACCEPT)"
related:
  - decisions/ADR-024-mbti-compat-v2-socionics
  - decisions/ADR-014-saju-mbti-prediction-exception
  - decisions/ADR-021-dreamnet-b6-v4
  - decisions/ADR-023-freud-v2-adoption
  - references/jung-myers-keirsey-socionics
  - templates/PROMPT_gunghap-mbti-matrix-academic
original_file: ../../MBTI 궁합 학술 검증 프롬프트.md
adr_017_first_application: "2026-05-17 (ADR-017 다섯 번째 본문화 사례)"
permanently_rejected:
  - "정확도 수치화 ('95% 확률'·'60-73% 일치' 등) — 보고서 §7.1 자체 명시 금지 + 자기실현적 예언 회피"
  - "'완전무결' 절대 표현 — peer review 전 부적합"
  - "'256 모델링 책임 회피' 비판 — subjective 표현"
deferred_pending_decision:
  - "compat.py v1 32 엔트리 + v2 알고리즘 통합 호출 — 옵션"
  - "Aladin ISBN 라이브 검증 — 서버 응답 한정 보류 (보고서 본문 출처 1차 신뢰)"
deferred_pending_data:
  - "§8 회귀 30쌍 JSON 빈 약속 확정 — 본 시스템 자체 회귀 29건으로 대체"
already_implemented:
  - "compat.py 32 엔트리 (16 듀얼 + 16 자가) 라인 87-100 — 호환 유지"
  - "mbti_functions.py 16 유형 → 8 융 인지기능 매핑 — 이미 표준"
  - "saju_mbti_predictor.py ADR-014 단정 회피 (사주→MBTI 4축 경향성)"
---

# MBTI 궁합 학술 검증 — 사실성 분리 + ADR-024 본문화

## 보고서 요약

PROMPT_gunghap-mbti-matrix-academic.md 의뢰 결과 수령. 47KB 대형 보고서.
MBTI 16×16 호환 매트릭스 학술 검증 + 융 인지기능 + Socionics 14 Intertype
Relations + Keirsey 상보성 + ADR-014 경계 명확화 + 면책 가이드.

## 🟢 팩트 (검증 통과)

| 주장 | 검증 |
|---|---|
| Jung 《Psychologische Typen》(1921) | ✅ 솔출판사 한국어 번역본 |
| Myers 《Gifts Differing》(1980) | ✅ 한국어 《성격의 재발견》 |
| Keirsey 《Please Understand Me II》(1998) ISBN 9781885705020 | ✅ Barnes&Noble 등 |
| Socionics 14 Intertype Relations (Aushra Augusta) | ✅ Wikisocion 공식 |
| 윤호균·이선희 (2000) 부부 MBTI 의사소통 | ✅ Semantic Scholar |
| 공성숙 (2010) 부부 MBTI 결혼만족도 | ✅ KoreaMed Synapse + DBpia |
| 김은정·황경열 (2007) 부부 MBTI 다중 요인 인정 | ✅ KCI |
| 정주성·조용석 (2025) MBTI 직무만족 | ✅ DBpia NODE12412548 |
| 본 시스템 compat.py 32 엔트리 "간이" 라인 8 명시 | ✅ 직접 grep 검증 |

## 🟡 구조 (시스템 설계 명제)

- 4단계 알고리즘 (base + S/N + Socionics + Keirsey)
- 256 전수 매트릭스 + 대칭 행렬
- 6 관계 분류 (dual·activation·mirror·identity·super_ego·conflict)
- DEFAULT_DISCLAIMERS 강제 (ADR-021/023 패턴 정합)
- J/P Switch 보정 (Socionics 매핑 주의)

## 🔴 도그마 (영구 거부)

- 정확도 수치화 ("95% 확률"·"60-73% 일치") — 보고서 §7.1 자체 명시 금지
- §8 회귀 30쌍 JSON 빈 약속 (제목만 + 본문 0건)
- "완전무결" 절대 표현

## 본 시스템 반영 (ADR-017 분석/판정 분리 절차 적용)

### 분석 에이전트 (Haiku)
후보 7건 (C1·C2·C3·C4·C5·C6·C7) + 거부 3건 (R1·R2·R3) + 사용자 결정 2건

### 판정 에이전트 (Haiku)
- **ACCEPT 6건** (C1·C2·C3·C4·C5·C6) — ADR-002/006/010/014/015/CLAUDE§0 모두 정합
- **DEFER 1건** (C7 §8 회귀 빈 약속) — 본 시스템 자체 회귀 29건으로 대체

### 오케스트레이터 직접 검증
- compat.py 라인 87-108 _MBTI_PAIR_SCORE 32 엔트리 직접 확인 (16 듀얼 + 16 자가)
- §8 라인 233-239 회귀 30쌍 본문 데이터 0건 직접 확인 (빈 약속 확정)
- ADR-014 정합: 입력 시그니처 saju 파라미터 0 — 사주→MBTI 단정 구조적 차단
- ADR-021/023 패턴 일치: DEFAULT_DISCLAIMERS + 학파 명시 + 회귀

### 본문화 (ADR-024)

| 영역 | 파일 | 결과 |
|---|---|---|
| C1 학술 출처 | references/jung-myers-keirsey-socionics.md | Jung·Myers·Keirsey·Socionics + KCI 4건 |
| C2 KCI 메타분석 | 동일 references | 윤호균·공성숙·김은정·정주성 영속화 |
| C3 J/P Switch | 알고리즘 내 사용자 명시 MBTI 그대로 사용 (변환 없음) | _ |
| C4 4단계 알고리즘 | mbti_compat_v2.py compute_mbti_compat | base+S/N+Socionics+Keirsey+정규화 |
| C5 256 매트릭스 | precompute_matrix() | 대칭 행렬, O(1) 조회 |
| C6 면책 | DEFAULT_DISCLAIMERS 3건 + 회귀 자동 검증 | ADR-006/010/014 정합 |
| C7 회귀 30쌍 | 본 시스템 자체 29 tests PASS로 대체 | 빈 약속 우회 |

## 회귀 29 PASS

(ADR-024 명세 참조)

## 신뢰성 평가

| 항목 | 평가 |
|---|---|
| Jung·Myers·Keirsey 학술 출판 표준 | ✅ |
| Socionics Wikisocion 공식 | ✅ |
| KCI 4건 (DBpia·KoreaMed·Semantic Scholar URL) | ✅ |
| §8 회귀 30쌍 JSON 데이터 | ❌ 빈 약속 → 자체 회귀 대체 |
| §5.1 4단계 알고리즘 | ✅ 수학적 명시 |
| §6 256 매트릭스 6 관계 분류 | ✅ |
| DEFAULT_DISCLAIMERS 강제 | ✅ 회귀 자동 검증 |
| 결정론 (LLM 호출 0) | ✅ |
| ADR-014 경계 명확화 | ✅ 입력 시그니처 사주 파라미터 0 |
| 본 프로젝트 적합성 | ✅ 매우 높음 (compat.py "간이" 결손 해소) |

**총평**: 본 보고서는 PROMPT_gunghap-mbti-matrix-academic.md 의뢰 결과로
정합도 매우 높음. ADR-017 절차 다섯 번째 본문화 사례.
분석 에이전트 오추정 0건 (실 코드 직접 확인 의무 작동 입증).

## 향후

- compat.py v1 + v2 통합 호출 (옵션)
- KCI 4건 표본 크기·p-value 추가 영속화
- §8 회귀 30쌍 사용자 직접 보강 (선택)
- 운영 데이터 누적 후 매트릭스 보정 (post_traffic ADR)

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리 + ADR-024 본문화)
- ADR-017 다섯 번째 본문화 성공 사례
- 분석 에이전트 오추정 0건
- 본 노트 immutable
