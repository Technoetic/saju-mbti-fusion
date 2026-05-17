---
type: external_report
status: received_with_caveats
date: 2026-05-17
source: deepresearch
domain: safety
applied_to:
  - L1 → ADR-011 + engine/safety/file_integrity.py (2026-05-17)
neo4j_synced: false
factuality: mostly_verified
related:
  - decisions/ADR-010-name-sibling-factuality.md
  - decisions/ADR-011-l1-file-integrity.md
  - reports/saju-app-spec.md
  - done/safety-l1-file-integrity.md
original_file: ../../AI 운세 앱 입력값 가드레일 설정.md
---

# AI 운세 앱 입력값 가드레일 — 사실성 검토 + 본 프로젝트 매핑

## 보고서 요약

7계층 Defense-in-Depth (L1 파일 무결성 → L7 출력 Llama Guard) 가드레일.
주요 기술: FastAPI + python-magic, OpenCV Laplacian, MediaPipe Hands/FaceDetection,
OpenAI Moderation API, XML 태그 컨텍스트 격리, 대법원 한자 9389자, Llama Guard 3.

## 🟢 팩트 (검증됨, 본 프로젝트 적용 가능)

| 주장 | 검증 | 적용 |
|---|---|---|
| python-magic으로 매직 넘버 검증 가능 | 라이브러리 실존 | ✅ 적용 가능 |
| OpenCV Laplacian Variance로 blur 검출 | 표준 컴퓨터 비전 기법 | ✅ 적용 가능 |
| MediaPipe Hands/FaceDetection 결정론 검증 | Google 공식 라이브러리 | ✅ 일부 이미 사용 (face_scoring.py) |
| OpenAI Moderation API | 공식 API 실존 | 🟡 비용 평가 후 |
| Anthropic Claude XML 태그 인식 강화 학습 | Anthropic 공식 권장 | ✅ 적용 가능 |
| 대법원 인명용 한자 9,389자 (2024년 5월) | 본 프로젝트가 이미 8525자 Unihan으로 확장 (ADR-003) | ✅ 이미 적용 |
| Llama Guard 3 메타 오픈소스 | 실존 | 🟡 비용·지연 평가 후 |

## 🟡 구조 (시스템 설계 명제, 채택 가능)

- 7계층 Fail-Fast 파이프라인 (L1→L7, 저비용 검사 전면 배치)
- 입력 검열 + 출력 검열 양방향
- 도메인별 임계값 차등 (손금 150 vs 관상 100)
- 다국어 우회 공격 인식

## 🔴 도그마 / 부정확 표현

- **"환각 없는" 단정**: 가드레일이 환각을 0으로 만든다는 어조 — 확률론 모델은 0 불가능
- **"완벽에 가까운 가드레일"**: 광고성 수사
- **"단 20ms 만에 분석 불가 판정"**: 구체 수치 출처 없음 (시스템 환경에 따라 다름)
- **"강한 양기·음양 부조화" 같은 형이상학적 인과 — 본 보고서에는 없음**: ✅ 본 보고서는 기술 위주라 깨끗
- **"광고성 토너 수정 권장"** 등 본 프로젝트 무관 권장 없음

## 본 프로젝트 현 상태 매핑

본 프로젝트는 보고서 7계층 중 다음을 **이미 구현**:

| 보고서 계층 | 본 프로젝트 모듈 | 상태 |
|---|---|---|
| L1 파일 무결성 | ❌ 없음 (web/server.py에 부분?) | 🟡 강화 필요 |
| L2 OpenCV Blur | [engine/divination/face_scoring.py](../../engine/divination/face_scoring.py) — 일부 메트릭 | 🟡 부분 |
| L3 MediaPipe 생체 감별 | face_scoring.py에서 MediaPipe 사용 | ✅ 부분 적용 |
| L3 photo_guide | [engine/safety/photo_guide.py](../../engine/safety/photo_guide.py) — 9종 사진 에러 + 4언어 가이드 | ✅ 적용 |
| L4 텍스트 윤리 검열 | [engine/safety/crisis_detector.py](../../engine/safety/crisis_detector.py) — 자살/자해 키워드 | ✅ 부분 (OpenAI Moderation 미사용) |
| L5 프롬프트 인젝션 방어 | [engine/safety/jailbreak_defense.py](../../engine/safety/jailbreak_defense.py) — 페르소나·인젝션 5 카테고리 | ✅ 적용 |
| L5 입력 정제 | [engine/safety/input_sanitizer.py](../../engine/safety/input_sanitizer.py) — 제어문자·인코딩·길이 | ✅ 적용 |
| L6 한자 화이트리스트 | [engine/divination/name_unihan.py](../../engine/divination/name_unihan.py) — 8525자 Unihan | ✅ 적용 |
| L7 출력 검열 | [engine/safety/output_safety_gate.py](../../engine/safety/output_safety_gate.py) — 결정론 게이트 | ✅ 적용 (Llama Guard 미사용) |

**총평**: 보고서 핵심 권장 사항의 **약 70%가 이미 본 프로젝트에 구현됨**. 다만:
- L1 파일 매직 넘버 검증 — 명시적 모듈 부재
- L4 OpenAI Moderation API — 외부 의존성 회피로 자체 키워드 사용 중
- L7 Llama Guard 3 — 비용·지연 트레이드오프로 미도입

## 본 시스템 반영

### ✅ 채택 가능 (검토 후 ADR)

1. **L1 파일 무결성 모듈** — `engine/safety/file_integrity.py` 신규
   - python-magic 매직 넘버 + MIME + 용량 3중 검증
   - face_reading 업로드 경로에 통합
   - 회귀 테스트 동반

2. **L2 Laplacian 임계값 통합** — face_scoring.py에 명시적 blur 점수
   - 손금 150 / 관상 100 권장값 채택
   - 단, 실제 사용자 데이터로 보정 (보고서 §3.1 인용)

### 🟡 비용·지연 평가 후 결정

3. **OpenAI Moderation API 도입**
   - 장점: 14 카테고리 정밀 검열
   - 단점: 외부 API 의존, 비용, 지연
   - 현 crisis_detector + jailbreak_defense로 80% 커버, 추가 도입 ROI 평가 필요
   - → 별도 ADR (도입 결정 시)

4. **Llama Guard 3 출력 검열**
   - 장점: 환각 출력 차단
   - 단점: Cloudflare Worker 또는 Ollama 운영, 비용
   - 현 output_safety_gate (결정론) 충분 여부 검토
   - → 사용자 사고 통계 수집 후 결정

### ❌ 본 프로젝트 미적용

- **손금 분석** — 신규 도메인. 본 프로젝트 미구현. 본 보고서 §4 (MediaPipe Hands)는 향후 손금 도메인 도입 시 참고용
- 보고서의 "한자 환각 생성 현상" 우려 — 본 프로젝트는 결정론 Unihan 풀에서 추출 (LLM 환각 무관)

## 신뢰성 평가

- 기술 사실: 정확 (라이브러리·API 실존, 임계값 권장 합리적)
- 구조 권장: 합리적 (Defense-in-Depth)
- 광고성 수사: 일부 존재 ("환각 없는", "완벽")
- 본 프로젝트 적합성: 매우 높음 (이미 70% 구현, 나머지 30% 도입 가치 있음)

**총평**: 본 보고서는 ADR-010 사례 중 가장 채택률 높음. 본 프로젝트가 이미 동일 방향으로 구축되어 있어 보고서가 후행적으로 정당화 + 추가 강화 포인트 제시.

## 다음 액션 (우선순위)

- [ ] **우선순위 1**: L1 파일 무결성 모듈 (`engine/safety/file_integrity.py`) — 1~2시간 작업
- [ ] **우선순위 2**: face_scoring.py에 명시적 Laplacian blur 점수 통합 — 30분 작업
- [ ] **우선순위 3**: OpenAI Moderation API ROI 측정 — 실제 트래픽 데이터 필요
- [ ] **우선순위 4**: Llama Guard 3 ROI 측정 — output_safety_gate 사고 통계 필요
- [ ] (보류) 손금 도메인 — 별도 신규 도메인 결정 필요

## 출처

- 본 보고서 원본: `사주/AI 운세 앱 입력값 가드레일 설정.md`
- 본 프로젝트 검증: engine/safety/* (43+ 모듈), engine/divination/face_scoring.py

## 메타

- 영속화: 2026-05-17 (ADR-010 사실성 분리 적용)
- ADR-010 사례 3호
- 본 노트는 immutable. 본문화 시 별도 done + ADR
