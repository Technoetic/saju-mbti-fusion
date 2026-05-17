---
type: done
status: applied
date: 2026-05-17
domain: [safety, face, palm]
related:
  - decisions/ADR-011-l1-file-integrity.md
  - reports/input-guardrails.md
commit: TBD
---

# Safety L1 — 파일 무결성 가드레일

## 무엇

[[../reports/input-guardrails]] L1 계층(파일 무결성 검증) 본문화.
순수 파이썬 매직 넘버 + 크기 + MIME 3중 검증. face_reading / palm_reading
LLM 호출 전 단락 차단.

## 변경 사항

### 신규 모듈
- [engine/safety/file_integrity.py](../../engine/safety/file_integrity.py)
  - `validate_image_bytes(data, claimed_mime, max_bytes)` — 바이트 직접 검증
  - `validate_image_base64(image_b64, max_bytes)` — data URL 또는 raw base64 검증
  - `IntegrityResult` 결과 모델 (valid, reason, detected_mime, size_bytes, error_code)

### 신규 테스트
- [engine/safety/test_file_integrity.py](../../engine/safety/test_file_integrity.py) — 17 테스트 PASS
  - 유효 케이스: JPEG / PNG / WebP
  - 거부 케이스: 빈 파일 / 크기 초과 / 텍스트 위장 / GIF / 실행파일(MZ) / MIME 불일치
  - base64 인터페이스: raw / data URL / MIME 일치/불일치 / 잘못된 base64 / 잘못된 data URL
  - 메시지 검증: 사용자 한국어 / 의료·법률 표현 없음

### 통합
- [engine/divination/face_reading.py](../../engine/divination/face_reading.py):292 — 캐시 조회 전 검증
- [engine/divination/palm_reading.py](../../engine/divination/palm_reading.py):293 — 캐시 조회 전 검증

### 응답 형식

악의적 입력 시 반환:
```python
{
    "text": "<integrity.reason> + <legal_footer>",
    "cached": False,
    "crisis_alert": None,
    "legal_notice": None,
    "palace_scores": None,  # face_reading만
    "file_integrity_error": "<error_code>",  # 내부 로그용
}
```

## 검증

### 회귀
```
python -m pytest engine/safety/test_file_integrity.py --no-skip-all
17 passed in 0.96s
```

### 라이브 시나리오
| 입력 | 결과 |
|---|---|
| 유효 PNG data URL | valid=True, mime=image/png |
| PNG가 JPEG라 주장 | valid=False, code=mime_mismatch |
| Windows PE (MZ) 헤더 | valid=False, code=unknown_format |
| 텍스트 base64 | valid=False, code=unknown_format |
| 빈 입력 | valid=False, code=empty_file |
| face_reading + 텍스트 위장 | LLM 호출 없이 차단 + 한국어 메시지 + legal_footer |
| palm_reading + 텍스트 위장 | 동일하게 차단 |

### 기존 테스트 영향
- file_integrity 테스트: +17 (모두 PASS)
- 기존 87 fail (face_reading 87건)은 [[../roadmap/ci-conftest-cleanup]] 부채 — 본 PR 무관
- git stash 검증: 본 PR 전후 face_reading fail 수 동일 (87) → 본 PR이 깨뜨리지 않음

## 결과

- 본 프로젝트 7계층 가드레일 중 L1 추가 완료 (이전: 6/7 → 현재: 7/7 부분 적용)
- 의존성 추가 0 (순수 파이썬)
- 사용자 메시지 한국어 + ADR-010 사실성 분리 적용 (의료·법률 표현 없음)

## 면책

- L2 (Laplacian blur), L3 (MediaPipe 생체 감별), L4 (OpenAI Moderation), L7 (Llama Guard) 등은 별도 ADR 필요
- 현재 ALLOWED_MIMES는 image/jpeg, image/png, image/webp 3종. GIF·HEIC 등 추가 필요 시 코드 수정

## 관련

- ADR-011: 본 작업 결정
- reports/input-guardrails.md: 원본 보고서 (L1 계층)
- ADR-010: 사실성 분리 원칙 (사용자 메시지 검증에 적용)
