---
type: done
status: applied
date: 2026-05-17
domain: [meta]
related:
  - decisions/ADR-008-ai-work-protocol.md
  - reports/saas-claude-obsidian-methodology.md
commit: TBD
---

# Roadmap에 AI vs Human 분담 라벨 명시

## 무엇

[[../reports/saas-claude-obsidian-methodology]] §2.2 (Session Handoff "Needs
Human Review" 패턴)을 본 프로젝트 roadmap 분류 라벨에 반영. AI 단독 진행
가능 / Human 필요 항목을 즉시 식별 가능하게 명시.

## 배경

본 세션에서 roadmap 분류(🟢🟡🔵⚪)가 이미 함의했으나 명시되지 않아
"AI가 시작해도 되는가?" 판단이 매번 반복 발생.

보고서 권장 Session_Handoff.md 신설은 done + roadmap과 중복이라 거부.
대신 **분류 라벨에 Human 필요 사유를 명시**하는 더 가벼운 적용.

## 변경

`vault/roadmap/INDEX.md`:
- 분류 4종에 "Human Input / Review / Decision 필요" 또는 "AI 단독 가능" 라벨 추가
- "AI vs Human 분담" 절 신설 — 표 형태로 즉시 식별 가능

## 영향

- 새 세션에서 AI가 작업 시작 시 ⚪(기술 부채)부터 검토하면 사용자 개입 0
- 🟢🟡🔵 항목은 사용자 결정 대기 명시 → AI가 추측 진행 방지

## 변경 미발생

- Session_Handoff.md 신설 거부 (보고서 권장이지만 done + roadmap과 중복)
- ADR 신규 거부 (작은 라벨 추가, ADR-008 supplement로 충분)

## 결과

ADR-008 `supplemented_by` 필드로 본 노트 추적.
보고서 §2.2 정신만 추출, 형식은 본 프로젝트 맥락에 맞게 변형 (Session_Handoff X, roadmap 라벨 보강).
