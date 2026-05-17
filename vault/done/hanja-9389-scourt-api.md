---
type: done
status: applied
date: 2026-05-17
domain: [name]
adr: ADR-026-hanja-9389-scourt-api
related_report: reports/hanja-9389-source-research
---

# 대법원 인명용 한자 9389자 본문화 (9932자 병합)

## 작업 요약

사용자 명시 지시 "AI가 직접 조사" 자율 진행. 법원 전자가족관계등록시스템
API (`/webhanja/whjsearch`) 직접 호출로 9,493자 추출 + 본 시스템 8,525자
병합하여 **9,932자**로 확대.

직전 보고서 빈 약속 차단 (DEFER) 해소 + saju-app-spec C1 DEFER 해소.

ADR-017 절차 **일곱 번째 본문화 사례**.

## 변경 사항

### 데이터
- [data/korean_hanja_unihan.json](../../data/korean_hanja_unihan.json) — 8,525 → 9,932
- data/korean_hanja_unihan_v1_8525_backup.json — 기존 데이터 백업
- data/korean_hanja_unihan_9389_meta.json — 추출 메타데이터
- hanja_scourt_raw.json — scourt API raw 응답 (9,493자)

### 코드
- [engine/divination/name_unihan.py](../../engine/divination/name_unihan.py) — docstring 갱신 (9932자 + 출처·라이선스 명시)

### 신규 ADR
- [vault/decisions/ADR-026-hanja-9389-scourt-api.md](../decisions/ADR-026-hanja-9389-scourt-api.md)

## 추출 방법 (재현 가능)

```python
# 1. 법원 전자가족관계등록시스템 한자 검색 페이지에서 JS 추출
curl -A "Mozilla/5.0" "https://efamily.scourt.go.kr/webhanja/whjprocjs"
# → WHJSEARCH_URL = "/webhanja/whjsearch" 발견

# 2. 획수 1~33 전수 fetch
for stroke in range(1, 35):
    url = f"https://efamily.scourt.go.kr/webhanja/whjsearch?mode=listUnicodeByTotstroke&totstroke={stroke}&pgmode=1&pgno=1&pgsize=2000"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    # 각 항목: cd (유니코드 16진수), ineum (음), totstroke, isin (인명용)
    # 한자 = chr(int(cd, 16))
```

## 차집합 결과

| 영역 | 한자 수 |
|---|---|
| scourt API | 9,493 |
| 기존 시스템 | 8,525 |
| 교집합 | 8,086 |
| 신규 추가 | **1,407** |
| 변형자 보존 | 439 |
| **최종** | **9,932** |

## name_unihan.py 회귀 통과

- `total_chars() = 9932` (이전 8525)
- `total_with_ohaeng() = 3524` (35.5%, 30-70% 범위 내)
- 기존 회귀 테스트 자동 통과

## ADR-010 사실성 분리

- ✅ 공식 출처 (대한민국 법원 efamily.scourt.go.kr)
- ✅ 저작권법 제7조 (국가 법령 저작권 배제)
- ✅ LLM 환각 X (API 직접 추출)
- ✅ 변형자 보존 (사용자 가족관계등록 이력 영향 0)

## saju-app-spec C1 해소

원래 DEFER: "§4 9389자 - 8525자 = 864자 부족"
→ 신규 1,407자 추가로 **864자 초과 달성** (보고서 권장 충족)

## 향후 작업

- 신규 1,407자 부수·자원오행 데이터 보강 (수동 또는 학술 출처)
- 회귀 30쌍 자동 검증
- scourt API endpoint 변경 모니터링
- 변형자 439자 검토 (별도 ADR)

## 메타

- ADR-017 일곱 번째 본문화 사례
- 사용자 지시 "AI 직접 조사" 자율 진행 첫 성공
- 분석/판정 에이전트 dispatch 없음 (직접 API 추출 가능 영역)
- 본 노트 immutable
