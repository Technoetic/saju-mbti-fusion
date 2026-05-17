---
type: prompt_template
target: deepresearch
purpose: SaaS 운영 사고 대응·incident playbook 객관 표준 수집
created: 2026-05-17
related_runbook: runbook/INDEX.md (현재 TODO 상태)
related_adr:
  - ADR-010-name-sibling-factuality (사실성 분리)
---

# 딥리서치 프롬프트 — SaaS Incident Playbook 객관 표준

## 사용법

본 프롬프트는 SaaS 운영표준 §14.7 incident playbook 신설용 객관 정보 수집.
runbook/INDEX.md에 "TODO: 운영표준 §14.7 incident_playbook 모듈 매핑" 명시 상태.

---

## 프롬프트 본문

```
한국 소형 SaaS (2인 개발 + Railway 배포 + FastAPI 백엔드)의 운영 사고 대응
체계 (Incident Playbook) 객관 표준을 다음 요구사항에 맞춰 조사·정리해주세요.

## 본 SaaS 컨텍스트

기술 스택:
- Python 3.12 + FastAPI 0.136
- Railway 자동 배포 (GitHub Actions)
- SQLite (data/app.db, Railway volume)
- LLM 외부 호출: Anthropic Claude + Bizrouter
- 클라이언트: 단일 HTML + Vanilla JS

운영 규모:
- 2인 개발팀
- 현재 트래픽 0 (운영 시작 전)
- 사용자 데이터: 사주·이름·사진·꿈 텍스트

기존 관찰성:
- engine/safety/kpi_dashboard.py (cache_hit_rate·persona_pass·crisis_block 등)
- engine/safety/quick_check.py (SLO 윈도우)
- engine/safety/alert_router.py (P0/P1/P2/P3 등급)
- Railway 로그 (railway logs)
- GitHub Actions 워크플로

미결정 (본 조사 필요):
- 사고 등급 정의·SLO 임계값
- 사고 감지 → 알림 → 대응 → 복구 → 사후 분석 절차
- 2인 개발팀 온콜 로테이션 가능성
- 사용자 통보 의무

## 요구사항

### 1. 사고 등급 정의 (Severity Levels)

다음 등급의 객관 기준 (응답 시간·영향 범위·통보 의무):

- P0 / SEV-1: 전체 서비스 장애·데이터 손실·보안 침해
- P1 / SEV-2: 부분 기능 장애·심각한 성능 저하
- P2 / SEV-3: 단일 사용자·간헐 오류
- P3 / SEV-4: 미세 결함·기능 요청

소형 SaaS(2인 팀) 맥락에서 PagerDuty·Slack 같은 고급 도구 없이도 운영 가능한
경량 표준 권장.

출처:
- Google SRE Book 사고 관리 챕터
- AWS Well-Architected Framework Operational Excellence
- Atlassian Incident Management Handbook
- 한국 KISA 침해사고 대응 가이드 (보안 사고 한정)

### 2. 사고 감지 (Detection)

객관 데이터:
- Railway 자체 알림 기능 (어떤 메트릭·임계값?)
- GitHub Actions 워크플로 실패 알림
- FastAPI + Prometheus·OpenTelemetry 도입 비용·복잡도
- Anthropic·Bizrouter API 장애 시 본 시스템 감지 방법

조사 항목:
- 본 SaaS 규모에 적합한 감지 도구 (Datadog 비싸고 Grafana Cloud 무료 한계)
- 자체 SLO (engine/safety/kpi_dashboard.py) 임계값 기준 자동 알림 구현 방법

### 3. 사고 대응 절차 (Response Playbook)

단계별 객관 표준:
- 사고 인지 → 분류 (등급) → 알림 → 대응 → 복구 → 사후 분석
- 각 단계 최대 시간 (P0의 경우 5분 이내 알림 등)
- 임시 대응 (rollback·circuit breaker·rate limit)
- 복구 우선순위 (서비스 회복 > 근본 원인 분석)

본 SaaS 특화 시나리오:
- LLM API 장애 (Anthropic 5xx) — fallback 정책
- Railway 배포 실패 — rollback 절차
- 사용자 데이터 손실 (SQLite 손상)
- 사진 처리 무한 루프 (face_reading.py timeout)
- 위기 신호 false negative (crisis_detector 우회)

### 4. 사후 분석 (Postmortem)

객관 표준:
- 5 Whys / Root Cause Analysis
- Blameless Postmortem 원칙
- 사용자 통보 의무 (개인정보보호법 §34 — 침해 통지)
- 외부 보고 의무 (KISA·개인정보보호위원회)

template 예시 요청:
- 사건 요약
- 시간선 (감지 → 대응 → 복구)
- 영향 범위 (사용자 수·데이터 손실)
- 근본 원인
- 재발 방지 조치

### 5. 2인 개발팀 온콜 로테이션

소형 팀 현실:
- 주말·휴일 대응 불가능 시 SLA 어떻게 정의?
- "최선 노력" vs 명시적 보장 시간
- 자동 복구 (auto-restart·health check) 비중

출처:
- 소형 SaaS 운영 사례 (Indie Hackers·Hacker News 토론)
- 한국 스타트업 운영 케이스 스터디

### 6. 사용자 통보 (Status Page)

객관 표준:
- 무료 상태 페이지 도구 (Statuspage·Instatus 무료 티어·Atlassian Statuspage)
- 상태 페이지 표시 의무 (전자상거래법·약관 관점)
- 한국 사용자에게 적합한 알림 채널 (이메일·카카오톡·SMS)

## 절대 조건

- 단정·과장 표현 금지 ("이것이 표준입니다" 대신 "○○ 표준에 따르면")
- 검증 불가 출처 거부 (Google SRE Book·AWS Well-Architected 같은 공인 자료만)
- 가짜 통계 거부 ("99.99% 가용성 보장은 ○○$/월" 같은 단정 — 실제 사례 출처 필요)
- 본 SaaS 규모를 무시한 엔터프라이즈 표준 강요 금지

## 출력 형식

마크다운 보고서:
1. 사고 등급 정의표 (소형 SaaS 한정)
2. 감지 도구 비교 (Datadog / Grafana Cloud / Sentry / Railway 자체)
3. 사고 대응 플레이북 (단계별 시간 + 본 SaaS 특화 시나리오)
4. Postmortem 템플릿
5. 2인 팀 온콜 로테이션 옵션
6. 사용자 통보·상태 페이지 도구 비교
7. 출처 (Google SRE / AWS WAF / KISA / 공식 문서 URL)
8. 본 SaaS engine/safety 모듈과의 매핑

## 메타

본 조사 결과로 vault/runbook/INDEX.md의 "TODO: 운영표준 §14.7 incident_playbook
모듈 매핑" 항목 해소 가능. 필요 시 engine/safety/incident_playbook.py 신규 모듈
설계 근거 제공.
```

---

## 결과물 처리 절차

1. 결과 .md를 `사주/[보고서명].md`로 저장
2. `/squeeze-report` 명령어로 처리
3. ACCEPT 항목: runbook/INDEX.md 업데이트 + 필요 시 engine/safety/incident_playbook.py 신규
4. DEFER 항목: 운영 데이터 누적 후 보강

## 우선순위

🟡 **SaaS 운영 시작 시점 권장** — 결제·계정 도입과 비슷한 시기.

## 면책

본 조사로 수집된 정보는 객관 표준 자료. 실제 사고 대응 계획은 본 SaaS 운영
환경·팀 규모·법무 의무를 반영한 사용자 결정 필요.
