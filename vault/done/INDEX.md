---
type: index
section: done
last_updated: 2026-05-17
---

# 완료 작업 인덱스

지금까지 본 시스템에 적용된 작업 누적. 시간순 역순(최신 위).

## 작명 도메인 (보고서 §1~§5 본문화)

| 일자 | 작업 | 모듈 | 회귀 | 보고서 § |
|---|---|---|---|---|
| 2026-05-17 | 가족 서열 한자 선호 모듈 (ADR-010 사실성 분리) | name_sibling_preference.py | 20 | §1 (별도 보고서) |
| 2026-05-17 | 인명용 한자 풀 8525자 확장 (Unihan) | name_unihan.py | 15 | §4 |
| 2026-05-17 | 사주 → 추천 자원오행 (옵션 A) | name_saju_ohaeng.py | 13 | §3 |
| 2026-05-17 | 81수 라벨 1~81 완성 + 종성 발음오행 + 한자 풀 1200 + 개명 트랙 | name_scoring·baleum·hangul_hanja·gaemyeong | 34 | §2·§3·§4·§5-A |
| 2026-05-17 | 두음법칙·음양·발음오행·개자 트랙 | name_dueum·eumyang·baleum·gaeja | 67 | §3·§4·§5-B |
| 2026-05-17 | 불용한자·강희자전 원획수·81수리 4격 | name_bulyong·strokes·scoring | 60 | §1·§2 |

→ 자세히: [[name-phase1-bulyong-strokes-scoring]] / [[name-phase2-saju-unihan]] / [[name-phase3-sibling-preference]]

## 관상 도메인

| 일자 | 작업 | 모듈 |
|---|---|---|
| 2026-05-16 | claude-opus-4.7 vision primary | face_reading._call_vision |
| 2026-05-16 | 12궁 결정론 점수표 (Phase 1) | face_scoring.py |
| 합성 얼굴 검증 | 균형/비대칭/표정 + 길상/흉상 시각 | pipeline-viz/test-faces/ |

→ 자세히: [[face-phase1-keypoint-scoring]]

## 안전·운영 인프라

| 일자 | 영역 | 모듈 |
|---|---|---|
| 2026-05-14~16 | 운영표준 §5~§14 본문화 | engine/safety/ 43+ 모듈 |
| EU AI Act §50(3) | 감정 추론 명시 고지 | emotion_disclosure.py |
| §7.3.2 SLO·KPI | 측정 모듈 | slo.py |
| §14.13 의존성 그래프 | DAG 검증 | dependency_graph.py |

→ 자세히: 별도 정리 예정

## 인프라

- Railway 배포 + CI/CD GitHub Actions
- Docker 이미지 + data/ 폴더 포함 (8525자 JSON 라이브 로드)
- conftest.py로 단위 테스트 일시 skip (다른 컴 동기화 PR 대기 중)

## 메타·AI 협업

| 일자 | 작업 | 관련 |
|---|---|---|
| 2026-05-17 | Obsidian Vault 도입 (25개 파일) | ADR-007 |
| 2026-05-17 | CLAUDE.md 프로젝트 전용 분리 | ADR-008 |
| 2026-05-17 | Hook 정리 — destructive-guard만 유지 | ADR-009 / [[hook-cleanup]] |
