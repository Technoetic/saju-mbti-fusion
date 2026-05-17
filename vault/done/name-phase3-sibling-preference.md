---
type: done
status: applied
date: 2026-05-17
domain: name
related:
  - decisions/ADR-001-name-deterministic-engine.md
  - decisions/ADR-006-legaltech-rejected.md
  - decisions/ADR-010-name-sibling-factuality.md
  - reports/name-sibling-bulyong.md
  - references/baekjungsukgye.md
commit: TBD
---

# 작명 Phase 3 — 가족 서열 한자 선호 모듈 (ADR-010 사실성 분리)

## 무엇

외부 딥리서치 보고서(`한국 정통 성명학의 서열별 상대적 불용한자 판정
알고리즘 및 데이터베이스 구축 심층 보고.md`)를 ADR-010 사실성 분리
원칙으로 본문화. 호칭 위계와 한자 의미의 직접 연관만 채택, 인과적
흉화 주장은 폐기.

## 사실성 분리 결과

- 🟢 팩트 채택: 한자 어휘·백중숙계 호칭(의례·예기 출전)·현대 가정 사실
- 🟡 구조 채택: 4 카테고리 / 3단계 부적합도 / gender / 5 현대 예외 / 우선순위
- 🔴 도그마 폐기: 흉화 물리 발현·"통계적 유의성" 수사·학파 빈도·우주 기운·마스킹 출전

## 변경 사항

### 신규 데이터
- **`data/name_sibling_preference.json`** — 125자 (firstborn 40 / lastborn 33 / middleborn 32 / only_child 20)
  - severity: STRONG 44 / WEAK 45 / CONDITIONAL 36
  - gender: neutral 101 / male 20 / female 4
  - reason 객관 묘사 (인과 표현 0)

### 신규 모듈
- **`engine/divination/name_sibling_preference.py`**
  - `SiblingEntry` / `SiblingDiagnosis` 데이터 모델
  - `diagnose_char()` — 단일 한자 진단
  - `diagnose_name()` — 이름 전체 진단
  - `_apply_modern_exceptions()` — 5 현대 가정 예외 (외동·재혼·입양·쌍둥이·큰누나)
  - `_soften_severity_for_twin()` — 쌍둥이 STRONG → WEAK 완화
  - `_build_user_message()` — 객관 묘사 메시지 빌더 (면책 포함)

### 신규 테스트
- **`engine/divination/test_name_sibling_preference.py`** — 20 테스트
  - 데이터 무결성 2
  - 기본 매칭 5
  - 외동 정책 4
  - 현대 예외 4
  - **ADR-010 사실성 분리 검증 2** (사용자 메시지 인과 표현 0 + 면책 포함)
  - 이름 단위 3

### conftest.py 확장
- `--no-skip-all` 옵션 + `PYTEST_RUN_ALL=1` 환경변수로 일괄 skip 우회 가능 (신규 모듈 회귀 가능)
- 기본 동작은 그대로 유지 (CI 영향 0)

### vault 동반
- `vault/reports/name-sibling-bulyong.md` — 사실성 분리 재작성
- `vault/references/baekjungsukgye.md` — 호칭 체계 원전 노트 신규
- `vault/decisions/ADR-010-name-sibling-factuality.md` — 사실성 분리 원칙 영속화
- `vault/decisions/INDEX.md` — ADR-010 행 추가
- `vault/references/INDEX.md` — 마의상법·유장상법 라벨 정정 (관상 학파 / 작명 학파 오인 정정)
- `CLAUDE.md` §3 — 외부 보고서 절차에 사실성 분리 의무화 + "절대 금지" 추가
- `vault/roadmap/gamily-hierarchy-bulyong.md` — done 이동

## 검증

### 회귀 테스트
```
python -m pytest engine/divination/test_name_sibling_preference.py --no-skip-all
20 passed in 1.06s
```

### 작명 도메인 회귀 (영향 없음 확인)
```
python -m pytest engine/divination/test_name_*.py --no-skip-all
109 passed in 1.20s
```

### 라이브 시나리오
- 차남 + `甲` → 부적합 STRONG, 메시지에 면책 포함
- 외동 + `壹` → 적합 (외동 전용 길자)
- 외동 + `孤` → hard_block_always (외동이라도 부적합)
- 큰누나(위 오빠) + `元` → eldest_sister_with_older_brother 예외 적용 → 부적합
- 쌍둥이 차남 + `甲` → severity STRONG → WEAK 완화
- 이름 `元秀` (차남) → any_strong_mismatch=True

### ADR-010 준수 검증
- 사용자 메시지에 금지 표현(단명·요절·이혼·관재 등) 0건
- 모든 부적합 메시지에 "참고용이며 의료·법률 자문이 아닙니다." 면책 포함
- reason 필드는 어휘 의미만 (인과 주장 없음)

## 결과

- 보고서 125자 본문화 (보고서 128자 중 `二`·`二`·`二` 같은 중복 제거)
- ADR-010 원칙이 데이터 + 코드 + 테스트로 영속화
- 차후 외부 보고서 수신 시 본 모듈이 사실성 분리의 reference 사례

## 면책

- 본 모듈은 **참고용**이며 의료·법률 자문이 아님 (ADR-006 + ADR-010)
- 인과적 흉화 예언 제공 안 함
- 한자 어휘 의미는 자전 검증 필요 (개별 한자 단위 추후 검토 가능)
- 보고서가 명시한 학파(마의상법·유장상법·신상전편)는 **관상학 문헌**이며 작명
  전문서가 아님 — references/INDEX.md에 정정 라벨 추가됨

## 향후

- `name_scoring.score_name()`에 `sibling_order` 파라미터 통합 (별도 PR)
- 기존 `name_bulyong.py` 도그마 표현 retroactive 정리 (ADR-010 적용 범위 확장, 별도 ADR)
- 외동 정책의 CONDITIONAL 글자 사주 일간 결합 로직 (옵션 B 학파 결정 후)
