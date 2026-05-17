---
type: reference
status: accepted
date: 2026-05-17
domain: [hwapae]
factuality: institutional_verified
sources:
  - 한국민족문화대백과사전 (encykorea.aks.ac.kr)
  - 국립민속박물관 e-museum (유물 일본 568)
  - Wikipedia Korean Hanafuda
  - Fuda Wiki (Hwatu section)
  - 아패영유(雅牌靈遊) 국문필사본 (3회 추첨 + 합산 알고리즘)
verified_date: 2026-05-17
related:
  - decisions/ADR-025-hwapae-korean-deterministic
  - decisions/ADR-002-saju-option-A
  - decisions/ADR-010-name-sibling-factuality
  - reports/hwapae-card-meanings-research
related_module: engine/divination/hwapae_korean.py
---

# 한국 화투 48패 전통 학술 출처

## 배경

본 시스템 한국 화투 48매 결정론 점패 엔진 (ADR-025) 학술 근거.
`engine/divination/hwapae_korean.py` HWAPAE_CARDS dict + 알고리즘 출처.

기존 hwapae.py(364줄)는 타로 78매 변형 시스템 (메이저·봉·잔·도·전).
본 모듈은 별개 시스템 — 한국 전통 화투 48매.

## 1. 한국민족문화대백과사전

- **URL**: encykorea.aks.ac.kr
- **활용**: 화투 48장 구성·일본 하나후다 원형·한국 11/12월 역전 (오동·비)
- **관리**: 한국학중앙연구원

## 2. 국립민속박물관 e-museum

- **유물**: 화패 (일본 568)
- **활용**: 카드 외형·계절 기호·민속 점술 용도
- **출처**: emuseum.go.kr

## 3. Wikipedia Korean Hanafuda

- **활용**: 일본 하나후다 원형 + 한국 화투 변형 비교
- **검증**: November/December 위치 역전 명시

## 4. Fuda Wiki (Hwatu section)

- **활용**: 광·열끗·띠·피 4 카테고리 + 게임 규칙
- **점수 체계**: 광 20 / 열끗 10 / 띠 5 / 피 1 (게임 규칙 표준)

## 5. 아패영유(雅牌靈遊) 국문필사본

- **내용**: 한국 전통 골패점 알고리즘
- **방식**: 3회 추첨 + 수치 합산
- **구간**: 13+ 상상 / 10~12 상중 / 그 이하 하하
- **활용**: ADR-025 three_card_spread() + total_score 구간 (35+·20~34·~20)

## 본 시스템 활용

### ADR-025 본문화

`engine/divination/hwapae_korean.py`:

```python
HWAPAE_CARDS: dict[str, HwapaeCard] = {
    "01-01-gwang": HwapaeCard(month=1, category="광", score=20, ...),
    ...
    "11-01-gwang": HwapaeCard(month=11, name_ko="오동 (광)", ...),  # 한국 통설
    "12-01-gwang": HwapaeCard(month=12, name_ko="비 (광)", ...),    # 한국 통설
}
```

본 핵심 6패 + 알고리즘 본문화. 48패 전수는 후속 보강.

### ADR-010 사실성 분리

- ✅ 출처 4종 모두 권위 기관 (한국학중앙연구원·국립민속박물관·Wikipedia·Fuda Wiki)
- ✅ 아패영유 학술 문헌 인용 (전통 골패점 알고리즘)
- ✅ 본 시스템은 객관 기호학 + 결정론 알고리즘만 채택 (운명론 X)

### 한계 명시

- 본 모듈은 핵심 6패만 본문화 (48패 전수는 후속 보강)
- school_variants (일본 원형) 메타 격리는 후속 ADR
- 회귀 30건 (보고서 §6)은 6패 한정으로 일부 채택

## 본 시스템 적용 면책

- 본 데이터는 **객관 학술 출처 영속화** — 운명·예언 무관
- 사용자 출력 시 ADR-006/010 면책 자동 포함 (DEFAULT_DISCLAIMERS 3건)
- permitted_keywords 범위 묘사만 채택
- forbidden_keywords (대성공 확정·로또 당첨·운명적 결정·재난 확정 등) 차단
- 한국 전통 화투 + 아패영유 골패점 학파 명시 의무

## 향후

- 48패 전수 본문화 (data/hwapae_korean_48.json 별도 영속화)
- 회귀 30건 전수 보강
- school_variants (일본 원형 11/12월 역전) 메타 격리 ADR
- hwapae.py(타로 변형) ↔ hwapae_korean.py(전통 화투) 페르소나 분리
