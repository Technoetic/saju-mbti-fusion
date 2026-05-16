---
type: external_report
status: applied
date: 2026-05-15
source: 외부 작성 (사용자 제공)
domain: name
applied_to: [§1, §2, §3 옵션 A, §4, §5-A, §5-B]
rejected: [§6 리걸테크]
boring: [§3 옵션 B (학파 채택)]
related_done: [done/name-phase1-bulyong-strokes-scoring, done/name-phase2-saju-unihan]
related_adr: [decisions/ADR-001, ADR-002, ADR-003, ADR-006]
file: "../../../작명 및 개명 특화 애플리케이션 개발을 위한 성명학 도메인 지식 및 시스템 설계 심층 분석 보고서.md"
---

# 작명·개명 특화 앱을 위한 성명학 도메인 지식·시스템 설계 보고서

## 원본 위치

프로젝트 루트의 `작명 및 개명 특화 애플리케이션 개발을 위한 성명학 도메인 지식 및 시스템 설계 심층 분석 보고서.md` (29KB, 167줄).

## 핵심 요약

작명·개명 앱을 "제약 조건 만족 알고리즘 엔진"으로 구현하기 위한 8장 보고서.
한국 정통 성명학 도메인 지식 + 대법원 행정 + 시스템 설계.

## 적용 상태 (2026-05-17 기준)

### ✅ 적용 완료
- §1 불용한자 진단 (80자/13 카테고리)
- §2 강희자전 원획수 + 변형 부수 8종 + 81수원도 + 4격
- §3 만세력 활용 + 자원오행 매칭 + 음양 + 발음오행
- §4 두음법칙 + 인명용 한자 풀 8525자 (90.8%)
- §5-A 개명 트랙
- §5-B 개자 트랙

→ 자세히: [[../done/name-phase1-bulyong-strokes-scoring]] / [[../done/name-phase2-saju-unihan]]

### 🟡 보류
- §3 용신 학파별 도출 → [[../decisions/ADR-002-saju-option-A]] (단순 분포 채택)
- §4 9389자 - 8525자 = 864자 부족
- §1 가족 서열 → [[../roadmap/gamily-hierarchy-bulyong]] 대기

### ⛔ 거부
- §6 법원 신청서 자동 생성 → [[../decisions/ADR-006-legaltech-rejected]]
- §6 1개월 CRM 알림 → 동 ADR

## 다음 액션

[[../roadmap/INDEX]] 참조.
