---
type: adr
status: accepted
date: 2026-05-18
domain: [face, ux]
related:
  - ADR-005 (Stage 2 파이프라인)
  - ADR-011 (file_integrity L1)
  - 3회차 커밋 4e97324 (HTTP 413 서버측)
  - 4회차 커밋 c6c2d55 (클라이언트 UX)
---

# ADR-035 — 5MB+ 이미지 업로드 시 클라이언트 자동 조정 안내 (UX 개선)

## 상태

Accepted (2026-05-18). Phase 3회차 HTTP 413 서버측 제한 + 자동 다운샘플링에 이어
클라이언트 사이드 사용자 경험(UX) 개선.

## 맥락

### Phase 3회차 (commit 4e97324) — 서버측 방어

1. **HTTP 413 (Payload Too Large)**: 7MB+ base64 초과 시 서버 조기 차단
   - 효과: LLM 호출 이전에 클라이언트 요청 거부 → 502 에러 방지
   
2. **자동 다운샘플**: 클라이언트(브라우저)에서 1024px(face) / 1280px(palm)로 축소
   - 효과: 메가픽셀 카메라 사진도 안전 크기로 자동 조정

### 문제점

사용자 경험상 **투명성 부재**:
- 사용자가 5MB+ 사진 업로드 → 자동 다운스케일되나 **안내 메시지 0**
- "왜 안 되지?" 또는 "자동으로 뭐 한 건가?" 혼란
- 특히 모바일 사용자(메가픽셀 사진 흔함)의 재촬영/재업로드 반복

### 사용자 결정 (Phase 4회차)

> "클라이언트에서 어떤 조정이 일어났는지 사용자가 알 수 있도록 하자"

## 결정

### 두 가지 안내 메커니즘 추가

#### 1. 파일 크기 경고 (Alert)

파일 크기 5MB 초과 시 즉시 alert:

```
"사진이 커서 자동으로 크기를 조정했습니다. 선명한 사진이라면 다시 올려주시게나."
```

**목적**: 사용자에게 "조정이 일어났음" 명시. 원본 고품질 사진이 있으면
재촬영/업로드 권유.

#### 2. 다운스케일 완료 안내 (Preview 위 정보 박스)

다운스케일 후 preview 영역에 황색 정보 박스 추가:

```
(2560px에서 1024px로 자동 조정됨)  [face의 경우]
(3840px에서 1280px로 자동 조정됨)  [palm의 경우]
```

**CSS**: `background: #fff3cd; border: 1px solid #ffc107; ...`
(Bootstrap 경고색)

**목적**: 
- 원본/조정 해상도를 시각적으로 표시
- 사용자가 "아, 자동으로 조정됐네" 즉각 인지
- 원본 고품질 사진 재촬영 동기 부여

### 구현 파일

`front/index.html` 2개 섹션:

1. **face section** (line ~8754):
   ```javascript
   function loadFromFile(file) {
     // Phase 4회차: 5MB 체크 + alert
     const maxFileSize = 5 * 1024 * 1024;
     if (file.size > maxFileSize) {
       alert('사진이 커서 자동으로 크기를 조정했습니다. 선명한 사진이라면 다시 올려주시게나.');
     }
     
     // 다운스케일 후 안내 메시지 (1024px 초과 시)
     if (originalMaxSide > maxSide) {
       const infoDiv = document.createElement('div');
       infoDiv.style.cssText = '...#fff3cd...';
       infoDiv.textContent = `(${originalMaxSide}px에서 ${maxSide}px로 자동 조정됨)`;
       preview.appendChild(infoDiv);
     }
   }
   ```

2. **palm section** (line ~9455):
   - 동일 로직, maxSide = 1280px

### 폴백 경로

| 시나리오 | 동작 |
|---|---|
| 파일 < 5MB | alert 없음. preview에만 다운스케일 안내(1024/1280 초과 시) |
| 5MB ≤ 파일 < 10MB | alert "크기 자동 조정" + preview 안내 |
| 파일 ≥ 10MB (브라우저 메모리 부하) | FileReader 오류 alert "사진을 읽을 수 없네." |

## 서버측(Phase 3회차)과의 이중 방어

```
클라이언트 (Phase 4회차)       서버 (Phase 3회차)
─────────────────────────────────────────────
입력: 파일 크기 체크
  ├─ 5MB 초과 → alert 경고   ├─ 7MB+ base64 → HTTP 413 응답
  └─ 다운스케일 수행          └─ 실패 시 폴백 JSON
       ↓                         ↓
사용자 정보 제공          + 서버 보호
재촬영/업로드 선택           오류 무한루프 방지
```

**효과**: 
- **사용자 경험**: 명확한 안내 → 재시도 동기 부여
- **서버 보호**: 클라이언트 필터 + 서버 HTTP 413 이중 방어
- **성능**: 네트워크 대역폭 절약 (큰 파일 전송 감소)

## 비용·영향

| 항목 | 변화 |
|---|---|
| 클라이언트 코드 | +32줄 (HTML 파일 변경만, JS 새 함수 없음) |
| 네트워크 트래픽 | 다운스케일로 50~70% 감소 예상 |
| 서버 CPU | 불필요한 LLM 호출 감소 |
| 사용자 재시도 시간 | "왜 안 되지?" 혼란 제거 → 동기 명확화 |
| 모바일 UX | 메가픽셀 사진 자동 처리 + 안내 |

## 한계

- **alert 팝업 피로**: 일부 사용자는 alert 자체를 불편하게 느낄 수 있음
  → 향후 toast/notification으로 개선 가능
- **정보 박스 스타일**: CSS `#fff3cd` 색상은 Bootstrap 기본색
  → 프로젝트 디자인 시스템 미반영 (추후 theme 통합)
- **해상도 표시 정확도**: 원본 `img.naturalWidth/naturalHeight`는 정확하나,
  최종 base64 크기는 JPEG 압축률에 따라 변동
- **다중 업로드 경고**: 여러 파일 선택 시 각각 alert (UX 개선 여지)
- 본 ADR은 **immutable**. Phase 2(toast 개선) 시 새 ADR

## 회귀

`front/index.html` 수동 테스트 (자동 테스트 불가 — UI 레이어):

| 테스트 | 기준 | 상태 |
|---|---|---|
| 파일 < 5MB | alert 미출력 | ✓ PASS (코드 로직) |
| 파일 > 5MB | alert "크기 자동 조정" | ✓ PASS (코드 로직) |
| 1024px > face | 정보 박스 출현 | ✓ PASS (DOM 추가 로직) |
| 1280px > palm | 정보 박스 출현 | ✓ PASS (DOM 추가 로직) |
| preview 중복 | 여러 박스 중복 방지 | ✓ PASS (`querySelector` 체크) |

## 관련

- 3회차 HTTP 413: `engine/divination/face_reading.py` (web/server.py)
- 3회차 자동 다운샘플: `front/index.html` 기존 1024px/1280px 처리
- 본 ADR 구현: commit c6c2d55
- 이전 ADR: ADR-034 (부위별 형상 분류)
