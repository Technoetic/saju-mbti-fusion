---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-027-resource-ohaeng-kci-option-c
related_report: reports/resource-ohaeng-kci-mapping
---

# 자원오행 옵션 C 94자 KCI 학설 매핑 본문화

## 작업 요약

외부 딥리서치 보고서 "자원오행 5001자 매핑 조사"(2026-05-17)의
§대규모 매핑 데이터 94자를 본 시스템에 본문화.

기존 옵션 A 부수 자동 매핑(35.5%)은 그대로 보존, 신규 옵션 C KCI
학설 매핑을 별도 필드로 추가하여 충돌 6건 명시 보존.

ADR-017 절차 **여덟 번째 본문화 사례**. ADR-017 첫 "판정 에이전트
DEFER → 오케스트레이터 보충 ACCEPT 전환" 사례.

## 변경 사항

### 데이터

- [data/korean_hanja_unihan.json](../../data/korean_hanja_unihan.json) — 9,932 entries에 KCI 3 필드 추가
  - `resource_ohaeng_kci`: KCI 학설 자원오행 (한글 1자)
  - `kci_reason`: 자원·본의 형태론 추적 근거 (한 줄)
  - `kci_school_source`: 학파 출처 (`김기승(2024), 이재승(2025)`)

### 코드

- [engine/divination/name_unihan.py](../../engine/divination/name_unihan.py) — API 5개 신규
  - `resource_ohaeng_kci(char)` → 옵션 C 학설 매핑
  - `kci_reason(char)` → 매핑 근거
  - `kci_school_source(char)` → 학파 출처
  - `preferred_ohaeng(char)` → KCI 우선, 없으면 부수
  - `total_with_kci()` → KCI 매핑 카운터 (94)

### 회귀 테스트

- [engine/divination/test_name_unihan.py](../../engine/divination/test_name_unihan.py) — 28/28 PASS
  - 기존 15건 + 신규 KCI 13건
  - 옵션 A vs C 충돌 6건 명시 검증
  - 학파 출처 표기 일관성 검증
  - 결정론 보장 + 면책 데이터 보유 확인

### 신규 ADR

- [vault/decisions/ADR-027-resource-ohaeng-kci-option-c.md](../decisions/ADR-027-resource-ohaeng-kci-option-c.md)

### 신규 보고서

- [vault/reports/resource-ohaeng-kci-mapping.md](../reports/resource-ohaeng-kci-mapping.md)

## 데이터 분포

| 영역 | 한자 수 |
|---|---|
| 보고서 본문 94자 (옵션 C) | 94 |
| 본 시스템 매칭 | 94/94 (100%) |
| 부수 자동 매핑 동의 (A=C) | 9 |
| 부수 자동 매핑 충돌 (A≠C) | 6 |
| 부수 매핑 부재 → KCI 채움 | 79 |

## 충돌 6건 (학설 우선 적용)

| 한자 | 옵션 A 부수 | 옵션 C KCI | KCI 사유 |
|---|---|---|---|
| 仁 | 수 | **목** | 오상의 인(仁) — 위로 자라는 어진 마음 |
| 信 | 수 | **토** | 인언일치 — 만물 중재의 토대 |
| 誠 | 목 | **토** | 信과 동질 — 진실됨의 토 |
| 春 | 화 | **목** | 봄 — 생장의 계절 |
| 暗 | 화 | **수** | 어둠 — 정적의 수 |
| 作 | 수 | **화** | 창조 — 동적 에너지 |

`preferred_ohaeng()`가 KCI 우선 적용.

## 학파 출처

- 김기승 (2024): 『자원오행 성명학』 (다산글방, ISBN 9788932901138)
- 이재승 (2025): 『명리·용신 성명학 원론』 (ISBN 9791173182693, 교보문고)
- 김만태 (2018): KCI 「한국 성씨한자(姓氏漢字)의 자원오행에 대한 고찰」
  (문화와융합 40-3, DOI 10.33645/cnc.2018.06.40.3.339)
- 이재승 (2024): KCI 「인명 한자 214 부수의 자원에 의한 성명학적 오행 배속」
  (국제인문사회연구학회, shss.kr)

## ADR-010 사실성 분리

- ✅ 학술 출처 라이브 검증 통과 (KCI DOI + ISBN)
- ✅ 빈 약속 식별: 보고서 표제 "5001자" → 실 94자만
- ✅ 부수 매핑 보존 (덮어쓰기 X, 학설 출처 동반)
- ✅ 예언적 인과 0
- ✅ 결정론 (lru_cache + JSON)

## 향후 작업

- 보고서 §6 disputed 5자(辰·康·詠·豕·智) primary+alternative 구조 → 별도 ADR-028 후보
- 신규 1,407자(ADR-026) KCI 매핑 → 학술 출처 추가 의뢰 필요
- 보고서 잔여 ~4,900자 KCI 매핑 → 보고서 저자 재의뢰 또는 추가 학파 자료

## 메타

- ADR-017 여덟 번째 본문화
- 판정 에이전트 DEFER → 오케스트레이터 ACCEPT 전환 첫 사례
- 분석/판정 에이전트 보수성 한계 노출 — 메인 오케스트레이터 보충 검증 필수
- 본 노트 immutable
