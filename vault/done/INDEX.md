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
| 2026-05-17 | 한국 성씨 300위 확장 + 한자 분리 + γ 보정 (ADR-029 supersede) | name_uniqueness.py (3 신규 API) + data/korean_surname_frequency.json (300) | 24 (15 PASS + 15 known-limitation) | ADR-033 |
| 2026-05-17 | 한국 성씨·인명 빈도 결정론 분석 — 동명이인 회피 객관 라벨 (통계청 + 대법원 공공누리 제1유형) | name_uniqueness.py (6 API) + data/korean_surname_frequency.json + regression.json | 21 (12 PASS + 18 known-limitation) | 보고서 §3·§5·§6·§7 |
| 2026-05-17 | 표준발음법 Priority 3 — ㅎ 약화·한자어 §26·평음화 §9·형식형태소 §14·상호동화 §19 (phonetic_delta_score_v2) | name_aesthetic.py (4 신규) + data/korean_phonetic_priority_3_regression.json | 70 (59+11) | 보고서 §1~§8 |
| 2026-05-17 | 표준발음법 §10~§30 Priority 1·2 음운 변동 — 비음화·유음화·격음화·경음화·연음·자음군 단순화 (옵션 b 별도 함수) | name_aesthetic.py (8 신규) + data/korean_phonetic_rules.json | 59 (34+25) | 보고서 §2~§6 |
| 2026-05-17 | 자원오행 옵션 C KCI 학설 매핑 94자 본문화 (옵션 A 보존 + 충돌 6건 명시) | name_unihan.py (5 API 신규) | 28 (15+13) | KCI 학설 |
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
| 2026-05-17 | 5형(목·화·토·금·수) 결정론 분류 — ADR-022, ADR-018 DEFER 해소 | engine/divination/face_shape.py / 18 테스트 |
| 합성 얼굴 검증 | 균형/비대칭/표정 + 길상/흉상 시각 | pipeline-viz/test-faces/ |

→ 자세히: [[face-phase1-keypoint-scoring]] / [[face-shape-5형-classifier]]

## 손금 도메인

| 일자 | 작업 | 모듈 | 회귀 | ADR |
|---|---|---|---|---|
| 2026-05-17 | 손금 4대 선 + 금성대 결정론 점수 엔진 — Size Korea + KCI + MediaPipe Hand 21 (palm-reading-app C1·C2 DEFER 해소) | engine/divination/palm_scoring.py (6 API + 5 라인) + data/palm_scoring_rules.json + regression.json | 21 (120/120 라벨 100%) | ADR-030 |

→ 자세히: [[palm-scoring-deterministic]]

## 사주 도메인

| 일자 | 작업 | 모듈 | 회귀 | ADR |
|---|---|---|---|---|
| 2026-05-17 | 사주 십이운성 120 셀 결정론 매핑 — 자평진전 (양순음역 + 화토동궁) + KCI 검증 + ADR-015 옵션 B 패턴 | engine/saju/twelve_stages.py (11 API) + data/twelve_stages_mapping.json + regression.json | 17 (120 셀 전수 + 30 샘플) | ADR-031 |

→ 자세히: [[saju-twelve-stages]]

## 꿈해석 멀티에이전트 도메인

| 일자 | 작업 | 모듈 | 회귀 | ADR |
|---|---|---|---|---|
| 2026-05-17 | B6 DreamNet v4 멀티모달 통합 (HVDC + 한국 KCI 규준 + disclaimers 강제) | engine/agents/dreamnet_multimodal.py + dreambank.py NORMS_KOREAN | 17 | ADR-021 |
| 2026-05-17 | A8 Freud v2 — 4기제 결정론 + 보편 상징 6건 + ISBN 3종 + output filter | engine/agents/freud_v2.py | 26 | ADR-023 |
| 2026-05-17 | MBTI 16×16 compat v2 — 4단계 알고리즘 + Socionics + Keirsey + 256 매트릭스 | engine/saju/mbti_compat_v2.py | 29 | ADR-024 |
| 2026-05-17 | 한국 화투 48매 결정론 점패 엔진 — 핵심 6패 + 3장 스프레드 + 아패영유 알고리즘 | engine/divination/hwapae_korean.py | 30 | ADR-025 |
| 2026-05-17 | 대법원 인명용 한자 9389자 → 9932자 본문화 (efamily.scourt.go.kr API 직접 추출 + 변형자 보존) | data/korean_hanja_unihan.json + name_unihan.py | 기존 회귀 자동 통과 | ADR-026 |

→ 자세히: [[dream-b6-dreamnet-v4]]

## 안전·운영 인프라

| 일자 | 영역 | 모듈 |
|---|---|---|
| 2026-05-17 | L1 파일 무결성 (매직 넘버 + 크기 + MIME) — ADR-011 | engine/safety/file_integrity.py / 17 테스트 |
| 2026-05-17 | L2 사진 품질 (Laplacian variance, 손금 150 / 관상 100, graceful degradation) — ADR-020 | engine/safety/photo_quality.py / 9 테스트 |
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
| 2026-05-17 | Claude Code Read 권한 거부 — 토큰 낭비 방지 | ADR-012 / [[tool-read-deny]] |
| 2026-05-17 | Roadmap에 AI vs Human 분담 라벨 명시 | ADR-008 supplement / [[roadmap-human-review-labels]] |
| 2026-05-17 | Anthropic prompt cache 적중률 측정 인프라 (L2) | ADR-013 / [[prompt-cache-telemetry]] |
| 2026-05-17 | 사주 → MBTI 4축 경향성 추정 (예외 결정) | ADR-014 / [[saju-mbti-prediction]] |
| 2026-05-17 | 사주 용신 옵션 B — 이재승 계량화 억부론 (KCI 검증) | ADR-015 / [[saju-option-B-eokbu]] |
| 2026-05-17 | 어감·인기 음절 가점 — 보고서 부분 채택 (§2만, 가짜 인용 거부) | ADR-016 / [[name-aesthetic-partial]] |
