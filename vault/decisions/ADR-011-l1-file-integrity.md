---
type: adr
adr_number: 11
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [safety, face, palm]
related:
  - ADR-010-name-sibling-factuality
  - reports/input-guardrails.md
related_file: ../../engine/safety/file_integrity.py
---

# ADR-011: L1 파일 무결성 가드레일 — 순수 파이썬 매직 넘버 검증

## 배경

[[../reports/input-guardrails]] (입력 가드레일 7계층 보고서) 검토 결과,
본 프로젝트는 보고서 권장 7계층 중 6개를 이미 구현했으나 **L1 파일 무결성**
(매직 넘버 검증)이 누락된 상태. face_reading / palm_reading의 base64
이미지 입력이 검증 없이 직접 LLM에 전달됨.

위험:
- 텍스트·실행파일을 이미지로 위장한 입력이 고비용 LLM API 호출 유발
- 변조된 파일로 인한 잠재적 처리 오류
- 토큰 낭비

## 검토한 옵션

### A. python-magic 라이브러리 도입
- 장점: 보고서 권장
- 단점: libmagic 시스템 의존성, Railway/Docker 빌드 복잡도 증가, 새 dependency

### B. 순수 파이썬 매직 넘버 헤더 비교 (채택)
- 장점: 의존성 0, 빌드 영향 0, 본 프로젝트가 지원하는 3종(JPEG/PNG/WebP) 매직 넘버 단순
- 단점: GIF 등 추가 포맷 지원 시 직접 추가 필요 (현재 무관)

### C. 미구현 유지
- 장점: 추가 코드 없음
- 단점: 보고서 검증된 보안 결점 방치

## 채택

**B 채택**. 순수 파이썬 구현. JPEG/PNG/WebP 3종 매직 넘버를 표준 헤더 바이트와
직접 비교. python-magic, cv2 등 외부 의존성 0.

### 검증 정책

1. **크기**: 기본 5MB 초과 시 차단 (보고서 권장값)
2. **매직 넘버**: 헤더 바이트로 실제 포맷 식별. JPEG(`FF D8 FF`), PNG(`89 PNG\r\n\x1a\n`), WebP(`RIFF????WEBP`)만 허용
3. **MIME 일치**: 클라이언트 주장 MIME(data URL `data:image/jpeg;base64`)과 매직 넘버 식별 결과 불일치 시 차단 — 확장자/MIME 조작 공격 차단

### 통합 지점

- [engine/safety/file_integrity.py](../../engine/safety/file_integrity.py) — 신규 모듈
- [engine/divination/face_reading.py](../../engine/divination/face_reading.py) — `generate_face_reading()` 캐시 조회 전
- [engine/divination/palm_reading.py](../../engine/divination/palm_reading.py) — `generate_palm_reading()` 캐시 조회 전

### 실패 처리

- crisis 응답과 동일한 형식의 dict 반환 (LLM 호출 전 단락)
- 사용자 출력: 한국어 면책 메시지 + `legal_footer`
- 내부 로그: `error_code` 필드 (사용자 비노출)

## 결과

- 신규 17 테스트 모두 통과 (정상 케이스 3 + 거부 케이스 6 + base64 인터페이스 5 + 사용자 메시지 검증 2 + 명시적 보안 위반 케이스)
- 텍스트·실행파일·MIME 조작 차단 라이브 검증
- face_reading / palm_reading 통합 — 악의적 입력 → LLM 호출 없이 차단 + 사용자 메시지 + legal_notice

## 면책

- 본 ADR은 L1 계층 한정. L2 (광학 품질·Laplacian) / L3 (MediaPipe 생체 감별) 등 보고서 다른 계층은 별도 ADR 필요
- python-magic·cv2 도입 결정은 향후 트래픽 데이터 + ROI 평가 후 별도 ADR

## 향후

- L2 Laplacian blur 점수 — cv2 도입 결정 후 (현 시점 cv2 미설치)
- L3 MediaPipe 생체 감별 — 현재 클라이언트 측 메트릭 추출에 의존 (face_scoring.py가 메트릭 수신)
- L7 Llama Guard 3 출력 검열 — output_safety_gate 사고 통계 누적 후 ROI 평가
