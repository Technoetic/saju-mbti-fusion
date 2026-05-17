---
type: prompt_template
target: deepresearch
purpose: 관상학 통설 30+ 항목 (삼정·12궁·부위별 형상)을 코드 DB로 영속화하기 위한 KCI·학술 출처 검증 의뢰
created: 2026-05-17
related_module: engine/divination/physiognomy_knowledge.py (신규)
related_adr:
  - ADR-005 (Stage 2 통설 인용 정합)
  - ADR-010 (사실성 분리 — 가짜 인용 차단)
  - ADR-022 (face_shape 결정론 분류와 결합)
  - ADR-018 (golden set 정책)
priority: high
status: draft
related_report: ../reports/physiognomy-knowledge-db-research (예정)
deepresearch_input: PROMPT_physiognomy-knowledge-db.deepresearch.txt
post_traffic: false
---

# 관상학 통설 지식 DB — KCI·학술 출처 검증 의뢰

## 사용법

본 시스템은 Stage 1(Opus Vision 객관 묘사) + Stage 2(Gemini 자연어 풀이)
2단계 파이프라인 (ADR-005 Supplement 3·4·5·6·7). Stage 2가 Gemini
사전학습 운명 매핑을 사용하지 않고 **본 시스템 코드 DB 출처에서만**
학파 통설을 인용하도록 강제 (ADR-010 사실성 분리).

본 PROMPT는 옵션 C 결정 (사용자 2026-05-17) 후속:
- Opus = 객관 분석
- Gemini = 자연어 출력
- **코드 DB = 검증된 학파 통설 인용 출처** ← 본 PROMPT가 채울 결손

딥리서치 입력본은 페어 `PROMPT_physiognomy-knowledge-db.deepresearch.txt` 참조.

## 결손 영역 표

| 항목 | 현재 상태 | 결손 |
|---|---|---|
| 삼정(상정·중정·하정) 영역 정의 + 통설 매핑 | 부분 (Export.md 단일 출처 + face_scoring label_ko) | 학파별 표준 + KCI 검증 |
| 12궁(명궁·관록궁·재백궁 등) 영역 정의 + 통설 | 부분 (face_scoring label_ko + Export.md) | 학파별 일관성·표준 |
| 부위별 형상 분류 (복코·매부리코·초승달 눈썹·앙월구·삼백안·칼귀 등) | 부재 | 30+ 형상별 학파 통설 |
| 마의상법 vs 유장상법 vs 신상전편 학파 변천 | 부재 | 한국 통설의 학파 출처 분리 |
| 학파별 운명 매핑 (시간 운·재물·관운 등) | Export.md 단일 출처 | 다출처 교차 검증 |
| 현대 인체측정학과의 정합성 | korean-face-anthropometry.md(ADR-022) | 통설 형상 ↔ 정량 측정 매핑 |

## 본 시스템 채택 절차

1. 딥리서치 결과를 `vault/reports/physiognomy-knowledge-db-research.md`로 저장
2. `/squeeze-report` 호출 — ADR-010 사실성 분리 3등급 (팩트·구조·도그마)
3. Phase B Haiku 검증 — KCI·교보문고·민족문화대백과 라이브 URL 검증
4. ACCEPT 항목만 `engine/divination/physiognomy_knowledge.py` 신규 모듈로 영속화:
   - `PHYSIOGNOMY_KNOWLEDGE: dict[str, dict]` 통설 DB
   - `lookup_relevant_knowledge(anatomical_description, scores) -> dict` 매칭 함수
5. Stage 2 시스템 프롬프트에 "입력 3 (관상학 통설 DB)" 절 추가
6. ADR-005 Supplement 8 영속화 (운명 매핑은 코드 DB 출처에서만 인용)

## 면책

- 본 PROMPT는 ADR-010 사실성 분리 정신 의무 — 가짜 인용·빈 약속 금지
- ADR-006 자문 거절 — 의료·법률·금융 운명 단정 금지
- ADR-022 정합 — 결정론 분류와 학파 통설 인용 분리 유지
- 사용자 출력에 "옛 관상학에서 이르길~" 어조 명시 의무 (Gemini 사전학습이
  아닌 코드 DB 인용임을 사용자에게 투명하게 알림)
