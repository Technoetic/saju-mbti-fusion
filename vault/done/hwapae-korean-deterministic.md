---
type: done
status: applied
date: 2026-05-17
domain: [hwapae]
adr: ADR-025-hwapae-korean-deterministic
related_report: reports/hwapae-card-meanings-research
related_reference: references/korean-hwapae-traditional
related_prompt: templates/PROMPT_hwapae-card-meanings
---

# 한국 화투 48매 결정론 점패 엔진 본문화

## 작업 요약

화패 보고서 모듈 정체성 충돌 (현 hwapae.py 타로 변형 vs 보고서 한국 화투
48매)을 사용자 명시 지시("자꾸 묻지말기") 하에 합리적 단독 진행:

**선택지 B 채택** — 신규 hwapae_korean.py 별도 구축 (기존 hwapae.py 보존).

ADR-017 절차 **여섯 번째 본문화 사례** (ADR-020·021·022·023·024 다음).

## 변경 사항

### 신규 파일
- [engine/divination/hwapae_korean.py](../../engine/divination/hwapae_korean.py) — 결정론 화투 48매 엔진
  - HWAPAE_CARDS dict (핵심 6패)
  - HwapaeCard frozen dataclass
  - HwapaeSpreadResult frozen dataclass
  - three_card_spread() — 3장 결정론 분석
  - DEFAULT_DISCLAIMERS 3건
  - FORBIDDEN_OUTPUT_PATTERNS 12건
  - has_forbidden_output() 사후 검증
  - get_permitted_keywords() 페르소나 입력용
- [engine/divination/test_hwapae_korean.py](../../engine/divination/test_hwapae_korean.py) — 회귀 30 PASS
- [vault/decisions/ADR-025-hwapae-korean-deterministic.md](../decisions/ADR-025-hwapae-korean-deterministic.md)
- [vault/references/korean-hwapae-traditional.md](../references/korean-hwapae-traditional.md)

### 갱신
- vault/decisions/INDEX.md — ADR-025 추가
- vault/done/INDEX.md — 화패 도메인 행 추가
- vault/reports/hwapae-card-meanings-research.md frontmatter (status: applied)
- vault/roadmap/INDEX.md (DEFER → done)

## 회귀 30 PASS

- 카드 데이터 4 + 3장 스프레드 3 + 계절 3 + 카테고리 우세 2
- 점수 합산 2 + Disclaimers 5 + Forbidden 4 + Permitted 2
- School 1 + Frozen 2 + to_dict 1 + facts 1

## 핵심 6패 본문화 (월 1·2·3·8·11·12)

| ID | 카드 | 카테고리 | 점수 |
|---|---|---|---|
| 01-01-gwang | 송학 (광) | 광 | 20 |
| 02-01-yeol | 매조 (열끗) | 열끗 | 10 |
| 03-01-gwang | 사쿠라 (광) | 광 | 20 |
| 08-01-gwang | 공산 (광) | 광 | 20 |
| 11-01-gwang | 오동 (광) | 광 | 20 |
| 12-01-gwang | 비 (광) | 광 | 20 |

한국 통설 (11월 오동·12월 비) 채택, 일본 원형(11월 비·12월 오동) 역전.

## 학술 출처

- 한국민족문화대백과사전 (encykorea.aks.ac.kr)
- 국립민속박물관 e-museum (유물 일본 568)
- Wikipedia Korean Hanafuda
- Fuda Wiki (Hwatu section)
- 아패영유(雅牌靈遊) 국문필사본

## ADR-006/010 자동 회귀

`DEFAULT_DISCLAIMERS` 3건:
1. 한국 전통 민속 + 결혼·연애·재물·수명 단정 X
2. 한국민족문화대백과사전·아패영유 출처 명시
3. permitted_keywords + forbidden_keywords 강제

`FORBIDDEN_OUTPUT_PATTERNS` 12건:
- 대성공 확정·무병장수·로또 당첨·운명적 결정
- 출세 확정·권력 획득·재난 확정·파산·이별의 영속
- 100% 성공·운명이 결정·큰 돈을 벌게 됨

회귀 자동 검증.

## 후속 작업

- 48패 전수 본문화 (data/hwapae_korean_48.json)
- 회귀 30건 전수 (보고서 §6)
- school_variants 메타 격리 (일본 원형 옵션)
- 페르소나 LLM 연동 (옵션)

## 메타

- ADR-017 여섯 번째 본문화 사례
- 사용자 명시 지시 ("자꾸 묻지말기") 단독 진행 첫 사례
- ADR-024 패턴 정합 (별도 모듈 신설)
- 본 노트 immutable
