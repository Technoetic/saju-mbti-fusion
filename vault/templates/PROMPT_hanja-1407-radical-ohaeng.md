---
type: prompt_template
target: deepresearch
purpose: ADR-026 신규 1,407자 (법원 efamily.scourt.go.kr API 추출) 부수 + KCI 자원오행 학술 매핑 — ADR-027 잔여 영역 해소
created: 2026-05-17
related_module: engine/divination/name_unihan.py + data/korean_hanja_unihan.json
related_adr:
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-026-hanja-9389-scourt-api (1407자 추출 출처)
  - ADR-027-resource-ohaeng-kci-option-c (KCI 옵션 C 매핑 패턴)
priority: high
status: draft
related_report: ../reports/resource-ohaeng-kci-mapping.md (ADR-027 DEFER 영역)
post_traffic: false
---

# 딥리서치 프롬프트 — 신규 1,407자 부수 + 자원오행 KCI 학술 매핑

## 사용법

본 시스템은 ADR-026 (efamily.scourt.go.kr API 직접 추출) 으로 대법원
인명용 한자 9,932자를 본문화했으나, 신규 1,407자는 부수(radical)와
자원오행(resource_ohaeng)이 모두 비어있음. ADR-027에서 옵션 C KCI
학설 매핑을 94자 본문화했으나 신규 1,407자에는 학술 출처 부재로
DEFER 처리.

본 프롬프트는 신규 1,407자에 대한 **부수 자동 매핑 + KCI 학설 매핑**
2단계 학술 출처 조사 의뢰.

### 본 시스템 현 상태 (DEFER 영역)

- data/korean_hanja_unihan.json 9,932 entries 중 1,407자는 radical=null
- engine/divination/name_unihan.py `radical_of()`, `resource_ohaeng()`,
  `resource_ohaeng_kci()` 모두 None 반환
- ADR-026 done 노트: "신규 1,407자 부수·자원오행 데이터 보강 (수동 또는 학술 출처)"
- ADR-027 정확: 학파 자료 없으면 매핑 불가

## 딥리서치 프롬프트 본문

```
당신은 한자 자형학·동양 성명학·KCI 등재 논문 전문가입니다. 본 한국 사주·작명
SaaS 시스템(https://saju-mbti-fusion-production.up.railway.app/)의
ADR-026 신규 1,407자에 대한 부수 + 자원오행 학술 매핑 데이터 보강을 의뢰합니다.

## 본 시스템 컨텍스트

본 시스템 ADR-026 (2026-05-17) — 법원 전자가족관계등록시스템 API
(efamily.scourt.go.kr/webhanja/whjsearch) 직접 추출로 대법원규칙 제3151호
(2024-06-11 시행) 인명용 한자 9,389자를 본문화했습니다 (기존 8,525자
+ 신규 1,407자 + 변형자 439자 = 9,932자).

본 시스템 ADR-027 (2026-05-17) — 자원오행 옵션 C (KCI 학설 매핑) 94자를
본문화했습니다. 학설 출처:
- 김기승 (2024): 『자원오행 성명학』 (다산글방)
- 이재승 (2025): 『명리·용신 성명학 원론』 (ISBN 9791173182693)
- 김만태 (2018): KCI 「한국 성씨한자의 자원오행 고찰」
  (문화와융합 40-3, DOI 10.33645/cnc.2018.06.40.3.339)
- 이재승 (2024): KCI 「인명 한자 214 부수의 자원에 의한 성명학적 오행 배속」

**결손 영역**: 신규 1,407자는 부수 자동 매핑 + KCI 학설 매핑 모두 부재.

## 1차 의뢰: 신규 1,407자 부수 자동 매핑

본 시스템에서 추출한 1,407자 한자 목록(별첨 JSON 또는 본 시스템 API
재호출로 추출 가능)에 대해, 각 한자의 강희자전 부수(1-214) + 강희자전
원획수를 학술 출처 기반으로 매핑하시오.

### 부수 자동 매핑 출처 (라이브 검증 의무)

각 출처의 라이브 URL + 마지막 검증 일자 명시 필수:

- Unicode Unihan Database (Kangxi Radical, Total Strokes, Adobe-Japan1)
  · https://www.unicode.org/charts/unihan.html
- 강희자전 (康熙字典) 디지털판
  · 漢典 (zdic.net), 教育部異體字字典 (variants.moe.edu.tw)
- 표준 한자 자전 (네이버 한자사전·디지털한자사전)
- 법원 efamily.scourt.go.kr/webhanja API (참조: ADR-026)

### 출력 형식 (1차)

JSON 배열, 각 entry:
```json
{
  "char": "㔂",
  "kangxi_strokes": 8,
  "radical": 18,
  "radical_source": "Unihan kRSKangXi 18.6 + zdic.net 검증",
  "verified_date": "2026-05-XX"
}
```

**금지 사항**:
- 부수·획수를 검증 없이 추측하기 (Unihan kRSKangXi 미확인 한자 폐기)
- 변형자(이체자) 음·획수를 본자와 혼동
- 강희자전 원획수 ≠ 표준 획수 혼용

## 2차 의뢰: 신규 1,407자 KCI 학설 자원오행 매핑 (옵션 C)

1차 부수 매핑 완료 후, 다음 학설 출처를 적용해 각 한자의 자원오행
(목·화·토·금·수)을 KCI 학설 우선으로 매핑하시오.

### 학설 우선순위 (ADR-027 정합)

1. **이재승 (2024) KCI 214 부수 자원오행 배속** — 부수 기반 자동 우선
2. **김기승 (2024) 자원오행 성명학** — 빈출 인명 한자 직접 매핑
3. **김만태 (2018) KCI 문화와융합** — 성씨한자 보강
4. **이재승 (2025) 명리·용신 성명학 원론** — 의미·자원 추가 매핑

### 옵션 A (부수 자동) vs 옵션 C (학설) 충돌 처리

ADR-027 충돌 보존 정책: 부수 매핑(`resource_ohaeng`) 보존 + KCI 매핑
(`resource_ohaeng_kci`) 신규 필드. 두 매핑이 다르면 충돌 명시.

### 출력 형식 (2차)

각 entry에 다음 4 필드 추가:
```json
{
  "char": "㔂",
  ...1차 결과...,
  "resource_ohaeng": "금",  // 부수 18 칼(刀) → 금
  "resource_ohaeng_kci": "금",  // 학설 일치
  "kci_reason": "칼(刀)의 자원 — 단호한 결단력의 숙살지기",
  "kci_school_source": "이재승(2024)"
}
```

학설 출처 부재 시 `resource_ohaeng_kci`, `kci_reason`,
`kci_school_source` 모두 빈 문자열. 단정 추측 금지.

## 3차 의뢰 (선택): 학설 이견(disputed) 한자 식별

신규 1,407자 중 학설 간 자원오행 이견이 있는 한자를 별도 식별:

```json
{
  "char": "...",
  "primary_ohaeng": "...",
  "alternatives": [
    {"ohaeng": "...", "school": "...", "reason": "..."}
  ]
}
```

ADR-028 (옵션 C disputed 스키마) 본문화에 활용.

## 회귀 데이터셋 (의무)

본 보고서 채택 시 자동 검증할 회귀 30쌍:

| char | expected_radical | expected_ohaeng | expected_source |
|---|---|---|---|

빈 약속 금지. 30쌍 실 데이터 본문에 명시 의무.

## ADR-010 사실성 분리 필수

본 보고서가 다음을 단정하지 않아야 합니다:

- 자원오행이 사용자의 운세·길흉·건강과 인과관계 (자원오행 ≠ 예언)
- 단일 학파가 절대 진리 (학파 명시 + 출처 노출 의무)
- 부수 매핑 vs KCI 학설 매핑 중 하나가 절대 우수 (선택 가능 정책)

## 본 보고서 출력 검증 의무

본 보고서 출력은 다음 자동 검증 통과 의무:

1. 1,407 entries 100% 매칭 (현 시스템 char 리스트와 일치)
2. radical ∈ {1..214} 또는 null
3. kangxi_strokes ∈ {1..50} 또는 null
4. resource_ohaeng·resource_ohaeng_kci ∈ {목·화·토·금·수} 또는 빈 문자열
5. kci_school_source 기재 시 학파 이름(김기승·이재승·김만태) 최소 1건
6. KCI/ISBN URL 라이브 검증 통과 (DBpia·교보문고·알라딘·shss.kr)

## 본 시스템 채택 절차

1. 본 보고서 받으면 `/squeeze-report` 호출
2. ADR-017 분석/판정 분리 절차 적용 (Haiku × 2)
3. ACCEPT 영역 본문화:
   - data/korean_hanja_unihan.json 신규 1,407 entries 4 필드 갱신
   - engine/divination/name_unihan.py `total_with_kci()` 카운터 +N
   - 회귀 테스트 30쌍 + 1,407자 매칭 검증
4. ADR-028 또는 ADR-027 supplement 작성
5. vault 영속화 + 커밋·푸시·라이브 검증

## 면책

본 프롬프트는 ADR-002·006·010·014·015·027 정합 의무.
딥리서치 응답이 ADR 위반 시 ACCEPT 거부.
```

## 본 시스템 채택 절차

1. 본 보고서 받으면 `/squeeze-report C:\Users\Admin\Desktop\사주\<보고서명>.md` 호출
2. 분석/판정 에이전트(Haiku) dispatch 후 ADR 정합성 검증
3. ACCEPT 영역 본문화:
   - 1,407 entries 부수 + KCI 매핑 데이터 주입
   - `total_with_kci()` 카운터 갱신
   - 회귀 30쌍 검증
4. ADR-028 (또는 ADR-027 supplement) 작성
5. saju-app-spec / hanja-9389-source-research / resource-ohaeng-kci-mapping
   DEFER 영역 해소 명시
6. 커밋·푸시·CI·Railway 라이브 검증

## 면책

본 프롬프트는 ADR-002 (학파 회피) + ADR-006 (자문 거절) +
ADR-010 (사실성 분리) + ADR-027 (옵션 C 충돌 보존) 정합 의무.
보고서 응답이 ADR 위반 시 `/squeeze-report` 거부 처리.
