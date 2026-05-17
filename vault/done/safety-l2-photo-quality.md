---
type: done
status: applied
date: 2026-05-17
domain: [safety, face, palm]
adr: ADR-020-l2-photo-quality-laplacian
related_report: reports/input-guardrails.md
commit: (본 커밋 SHA)
---

# L2 사진 품질 검증 — Laplacian Variance 결정론 점수 본문화

## 작업 요약

`engine/safety/photo_quality.py` 신규 모듈 본문화. 보고서 §3 권장 OpenCV
Laplacian variance 표준 알고리즘 + graceful degradation 패턴 적용.

L1 file_integrity (ADR-011) → **L2 photo_quality (본 ADR-020)** → L3 MediaPipe
Defense-in-Depth 파이프라인 L2 완성.

## 변경 사항

### 신규 파일
- [engine/safety/photo_quality.py](../../engine/safety/photo_quality.py) — 결정론 blur 점수 모듈
- [engine/safety/test_photo_quality.py](../../engine/safety/test_photo_quality.py) — 회귀 9 PASS
- [vault/decisions/ADR-020-l2-photo-quality-laplacian.md](../decisions/ADR-020-l2-photo-quality-laplacian.md) — 결정 영속화

### 갱신
- [vault/decisions/INDEX.md](../decisions/INDEX.md) — ADR-020 추가
- [vault/reports/input-guardrails.md](../reports/input-guardrails.md) — frontmatter `applied_to` + `permanently_rejected` + `already_implemented` + `deferred_pending_decision` 영속화

## 회귀 테스트 (9 PASS)

1. 임계값 상수 검증 (THRESHOLD_PALM=150, THRESHOLD_FACE=100, THRESHOLD_DEFAULT=100)
2. 도메인 분기 + graceful (palm·face·default 결과 객체 검증)
3. is_acceptable graceful (cv2 미설치 시 True)
4. ADR-010 인과 표현 0건 (사용자 메시지에 운·흉화·길흉·운명·예언 금지어 부재)
5. frozen dataclass (BlurResult 불변)
6. None 입력 graceful
7. palm > face 임계값 순서
8. cv2_available 플래그 존재
9. 예외 발생 0건

## 설계 선택

### Graceful Degradation 패턴
- cv2 설치 환경: Laplacian variance 결정론 산출
- cv2 미설치 환경: None 반환 + photo_guide.py 텍스트 가이드 fallback
- 외부 의존 최소화 (CLAUDE.md §0 + ADR-010 정합)

### 임계값 (보고서 §3.2)
- 손금 150.0 (미세 선 분석 절대)
- 관상 100.0 (조명·화장품 영향)
- 디폴트 100.0 (보수)

### ADR-010 정합
- 사용자 출력 메시지에 인과·예언 표현 0건
- 회귀 테스트로 자동 검증 (forbidden words 자동 점검)
- "사진이 흐려 분석이 어렵습니다. 밝은 곳에서..." (객관 표현만)

## 본 보고서로부터 추가 후속 작업

`vault/reports/input-guardrails.md` frontmatter `deferred_pending_decision`:
- L4 OpenAI Moderation API — 데이터 송신 정책 ADR 선행 필요 (🔵 사업 결정)
- L7 Llama Guard 3 — 운영 데이터 누적 후 ROI 평가 (post_traffic)

본 항목은 사용자 결정 영역으로 별도 본문화 대기.

## 메타

- ADR-017 절차 첫 적용 결과 첫 본문화 사례 (분석/판정 분리 → 본문화)
- 분석 에이전트 ADR-017 보강 후 오추정 0건 발견 (실 파일 직접 확인 의무 작동 입증)
- 본 노트 immutable
