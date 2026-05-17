---
type: adr
adr_number: 20
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [safety, face, palm]
related:
  - ADR-010-name-sibling-factuality
  - ADR-011-l1-file-integrity
  - ADR-017-squeeze-report-command
related_module: ../../engine/safety/photo_quality.py
related_report: ../reports/input-guardrails.md
---

# ADR-020: L2 사진 품질 검증 — Laplacian Variance 결정론 점수

## 배경

`vault/reports/input-guardrails.md` 7계층 Defense-in-Depth 1차 처리에서
**L2 OpenCV Blur 검증**이 "다음 액션 우선순위 2"로 명시됐으나 미본문화 상태.

ADR-017 절차 첫 적용 재호출(2026-05-17)에서 오케스트레이터 직접 검증:
- engine/divination/face_scoring.py 532줄: **Laplacian·cv2 0건**
- engine/safety/photo_guide.py: blur **텍스트 가이드만** (정량 점수 0)
- engine/divination/palm_reading.py 351줄: **mediapipe·cv2·blur 0건** (Gemini Vision LLM만)

→ **L2 정량 blur 검증 모듈 실 결손 확인**.

보고서 §3.1·§3.2 권장:
- cv2.Laplacian(gray, cv2.CV_64F, ksize=3).var() 표준 OpenCV
- 임계값: **손금 150.0** (미세 선명도 절대), **관상 100.0** (조명·화장품)
- L1(file_integrity) → L2(blur) → L3(MediaPipe) Fail-Fast 파이프라인

## 결정

`engine/safety/photo_quality.py` 신규 모듈 본문화. ADR-020로 결정 영속화.

### 결정론 + Graceful Degradation 패턴

CLAUDE.md §0 "결정론 엔진 + LLM 작문 분리" 정신 유지:
- cv2 설치 환경: Laplacian variance 결정론 산출
- cv2 미설치 환경: None 반환 + photo_guide.py 텍스트 가이드 fallback

본 패턴은 **외부 의존 최소화** + **결정론 보장** 양립.

### 임계값 (보고서 §3.2 명시)

| 도메인 | 임계값 | 사유 |
|---|---|---|
| 손금 (palm) | 150.0 | 미세 선 분석 절대 — 흐릿하면 분석 불가 |
| 관상 (face) | 100.0 | 조명·화장품 영향, 약간 낮게 |
| 기타 (default) | 100.0 | 보수 디폴트 |

본 임계값은 보고서 본문 라인 122 권장 + OpenCV 표준 알고리즘이라 학파 회피
영역 외 (객관 정량 측정).

### 면책 의무 (ADR-010 정합)

사용자 출력 표현:
- ✅ "사진이 흐려 분석이 어렵습니다. 밝은 곳에서 다시 촬영하세요."
- ❌ "사진 품질이 낮아 운이 약합니다." (인과 단정)
- ❌ "선명한 사진일수록 정확한 운명 분석" (예언)

본 모듈은 **순수 입력 품질 검증**이며 운세·길흉과 무관.

### 회귀 테스트 의무

`test_photo_quality.py`:
1. cv2 미설치 시 None 반환 검증 (graceful degradation)
2. cv2 설치 시 임계값 동작 (mock 이미지 분산)
3. 도메인별 임계값 적용 (face=100, palm=150)
4. 사용자 출력 인과 표현 0건 자동 검증

## 검토한 옵션

### A. photo_quality.py 신규 모듈 + graceful degradation (채택)

- 장점:
  - 보고서 §3 본문 명시 임계값 그대로 채택
  - 외부 의존 최소화 (cv2 없어도 시스템 작동)
  - 결정론 보장 (CLAUDE.md §0)
  - face/palm 양쪽 적용
- 단점: cv2 미설치 환경에서는 L2 보호 X (photo_guide.py 텍스트 가이드만)

### B. face_scoring.py 직접 보강

- 장점: 기존 모듈 활용
- 단점:
  - face_scoring.py는 결정론 12궁 점수 전담 — 책임 분리 위반
  - palm_reading.py에 별도 통합 필요 (중복)

### C. cv2 강제 의존 + requirements 추가

- 장점: 항상 작동 보장
- 단점:
  - 배포 환경 영향 (운영 결정 🔵)
  - opencv-python 패키지 크기 큼
  - Railway 배포 빌드 시간 증가

## 채택

**A 채택**. graceful degradation 패턴으로 외부 의존 최소화 + 결정론 보장.

## 결과

### 신규 파일
- `engine/safety/photo_quality.py` (신규 모듈)
- `engine/safety/test_photo_quality.py` (회귀 테스트)
- `vault/decisions/ADR-020-l2-photo-quality-laplacian.md` (본 ADR)

### 호출 경로 (선택)
- face_reading.py 또는 palm_reading.py 입력단에서 `compute_blur_score()` 호출
- 결과가 임계값 미달 시 ERR_FACE_BLUR / ERR_PALM_BLUR 반환
- cv2 미설치 → None → 검증 스킵 (photo_guide.py 텍스트 가이드로 fallback)

### vault 영속화
- `vault/reports/input-guardrails.md` frontmatter `applied_to` 보강 (L2 추가)

## 면책

- 본 모듈은 **순수 입력 품질 측정** — 운세·길흉과 무관
- 사용자 출력에 인과 표현 절대 금지
- cv2 의존성 옵션 (graceful degradation)
- 회귀 테스트로 사용자 출력 인과 표현 자동 검증

## 한계

- cv2 미설치 환경에서 L2 보호 부재 → photo_guide.py 텍스트 가이드만
- 임계값은 보고서 §3.2 권장 — 실제 운영 데이터로 보정 가능 (post_traffic)
- Laplacian variance는 표준 알고리즘이나 도메인·조명 변수 영향 있음

## 향후

- 운영 트래픽 누적 후 임계값 보정 (별도 ADR)
- 추가 영상 품질 지표 (해상도·노이즈) 검토 가능
- ADR-020이 절차 정합 문제 발생 시 새 ADR로 superseded

## 메타

- 본 ADR은 ADR-011 (L1 파일 무결성)의 후속 — Defense-in-Depth L2 완성
- ADR-017 절차 첫 적용 결과 본문화 사례
