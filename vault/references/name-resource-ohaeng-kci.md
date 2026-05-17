---
type: reference
status: accepted
date: 2026-05-17
domain: name
factuality: kci_verified + isbn_verified
sources:
  - 김기승 (2024). 자원오행 성명학 (다산글방)
  - 이재승 (2025). 명리·용신 성명학 원론
  - 김만태 (2018). 한국 성씨한자(姓氏漢字)의 자원오행(字源五行)에 대한 고찰 — 문화와융합 40(3)
  - 이재승 (2024). 인명 한자 214 부수의 자원(字源)에 의한 성명학적 오행 배속 — 국제인문사회연구학회
verified_url:
  - https://product.kyobobook.co.kr/detail/S000215915474   # 이재승 2025
  - https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=39422376   # 김기승 자원오행 성명학
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07484682   # 김만태 2018
  - https://scholar.kyobobook.co.kr/article/detail/4010027471613   # 김만태 2018 (학지사)
  - https://www.shss.kr/board_eng_publication01/view.php?uid=298&gid=292   # 이재승 2024
verified_date: 2026-05-17 (WebFetch 라이브 검증 완료)
isbn:
  - 이재승 (2025): 9791173182693
  - 김기승 자원오행 성명학: 알라딘/교보 일치
doi:
  - 김만태 (2018): 10.33645/cnc.2018.06.40.3.339
---

# 자원오행 KCI 학설 매핑 출처 (94자 본문화)

## 출전 검증

### 김기승 (2024) — 자원오행 성명학

- **저자**: 김기승 (다산글방 발간, 인문/사상 분야)
- **검증 URL**: 알라딘 ItemId=39422376, 교보 eBook 4808994384092
- **이론 위치**: 부수·자원·자의를 결합한 자원오행 매핑 6판
- **본 시스템 채택**: 94자 중 다수 (예: 義·禮·美·賢·宗·寶 등)

### 이재승 (2025) — 명리·용신 성명학 원론

- **저자**: 이재승 (성명학 박사, 동방문화대학원대학교)
- **검증 URL**: 교보문고 S000215915474
- **ISBN**: 9791173182693
- **이론 위치**: 명리 용신 + 자원오행 통합 성명학 원론서
- **본 시스템 채택**: 94자 중 다수 (예: 仁·宇·宙·宛·寧·寬·東·西 등)

### 김만태 (2018) — 한국 성씨한자(姓氏漢字)의 자원오행에 대한 고찰

- **저자**: 김만태
- **저널**: 문화와융합 (Culture & Convergence) 제40권 3호
- **DOI**: 10.33645/cnc.2018.06.40.3.339
- **검증 URL**: DBpia NODE07484682, 학지사 4010027471613
- **이론 위치**: 성씨한자에 대한 자원오행 분류 체계화 (강·중·약·무의미·불명)
- **본 시스템 채택**: 94자 중 일부 (예: 字·勺·刺·慈·滋·作·殘·暫·莊·張·長 등)

### 이재승 (2024) — 인명 한자 214 부수의 자원에 의한 성명학적 오행 배속

- **저자**: 이재승
- **학회**: 국제인문사회연구학회
- **검증 URL**: shss.kr uid=298&gid=292
- **이론 위치**: 214 부수 전체에 대한 자원 추적 형태론
- **본 시스템 채택**: 추상부수 매핑 논리(宀·亠·力·勹·又) 근거

## 본 시스템 적용 위치

| 모듈 | 적용 영역 |
|---|---|
| data/korean_hanja_unihan.json | 94자 `resource_ohaeng_kci`, `kci_reason`, `kci_school_source` 필드 |
| engine/divination/name_unihan.py | `resource_ohaeng_kci()`, `kci_reason()`, `kci_school_source()`, `preferred_ohaeng()`, `total_with_kci()` |
| engine/divination/test_name_unihan.py | KCI 회귀 13건 |

## 옵션 분류 (보고서 §4)

| 옵션 | 방법 | 채택 |
|---|---|---|
| A | 부수 (214) 자동 매핑 | ✅ `resource_ohaeng` (기존) |
| B | 한자 의미 직접 매핑 | ❌ 주관 개입 (보고서 거부) |
| C | 자원·본의 형태론 추적 | ✅ `resource_ohaeng_kci` (신규) |

옵션 A·C 충돌 시 `preferred_ohaeng()` 가 C 우선.

## 학파 이견 처리 (보고서 §6 미본문화)

보고서 §6 disputed characters (辰·康·詠·豕·智) primary+alternative
구조는 본 ADR-027 범위 외 (별도 ADR-028 후보).

## 면책 의무 (ADR-010)

사용자 출력에 KCI 매핑 표시 시:
- 학파 출처 동반 노출 (`김기승(2024), 이재승(2025)`)
- 부수 자동 매핑(A)과 충돌 시 명시
- 예언적 인과 금지 (운세·길흉·건강과 자원오행 무관)

## 관련

- ADR-027: [[../decisions/ADR-027-resource-ohaeng-kci-option-c]]
- 보고서: [[../reports/resource-ohaeng-kci-mapping]]
- 본문화: [[../done/resource-ohaeng-kci-94chars]]
- 이재승 KCI 추가 자료: [[lee-jaeseung-2019]]
