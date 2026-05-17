---
type: prompt_template
target: deepresearch
purpose: 통계청 KOSIS 2015 인구주택총조사 성씨 상위 300위 전수 추출 — ADR-029 잔여 영역 해소 + 한자 동음이의 구분
created: 2026-05-17
related_module: engine/divination/name_uniqueness.py + data/korean_surname_frequency.json
related_adr:
  - ADR-001-name-deterministic-engine (결정론 보장)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-026-hanja-9389-scourt-api (API 직접 추출 패턴)
  - ADR-029-korean-name-uniqueness (15 성씨 본문화)
priority: medium
status: draft
related_report: ../reports/korean-name-frequency-statistics.md (ADR-029 18/30 known-limitation)
post_traffic: false
---

# 딥리서치 프롬프트 — 통계청 KOSIS 2015 성씨 300위 전수 + 한자 동음이의 구분

## 사용법

ADR-029 (2026-05-17) 한국 성씨·인명 빈도 결정론 분석 본문화. 보고서
"작명 SaaS 백엔드 결손 영역 보강을 위한 한국 성씨·인명 빈도 통계" 본문
명시 15건 성씨만 본문화. 30쌍 회귀 12 PASS + 18 known-limitation.

### 18 known-limitation 영역

- **성씨 DB 누락 (15건)**: 4·5·6·7·8·9·10·11위 등 보고서 "중략" 영역
  - freq_004 최서윤, freq_005 정하준, freq_006 강지훈, freq_007 조은주,
    freq_008 윤영숙, freq_009 장영수, freq_010 임도현, freq_011 남궁민,
    freq_012 제서연
- **한자 동음이의 (1건)**: freq_019 방(龐)지훈 (한글 '방' = 方/龐 구분 불가)
- **음절 미인기 결합 (3건)**: freq_024 김탁구, freq_025 이삼순, freq_026 박을룡
  (성씨 1·2·3위 + 비인기 음절 → uncommon 추정 필요)

본 프롬프트는 통계청 KOSIS 직접 추출 + 한자 동음이의 데이터 보강 의뢰.

## 본 시스템 현 상태 (DEFER 영역)

- `data/korean_surname_frequency.json`: 15 entries (보고서 본문 명시)
- `engine/divination/name_uniqueness.py`: 한글 surname 분리, 한자 미인식
- `total_surnames() = 14` (한글 키 충돌로 14)

## 딥리서치 프롬프트 본문

```
당신은 한국 인구통계·통계청 KOSIS·동성동본 한자 분류 전문가입니다.
본 작명 SaaS 시스템(https://saju-mbti-fusion-production.up.railway.app/)
ADR-029 잔여 영역 (18/30 known-limitation) 해소 의뢰합니다.

## 본 시스템 컨텍스트

ADR-029 (2026-05-17) 본문화 완료:
- data/korean_surname_frequency.json: 15 entries (보고서 §3.2 본문 명시
  rank 1·2·3·55~59·151~157)
- engine/divination/name_uniqueness.py: 6 신규 API (UniquenessResult)
- 회귀 21 PASS (12 보고서 회귀 + 18 known-limitation)

학술/공식 출처 (이미 검증 완료):
- 통계청 2015 인구주택총조사 성씨·본관 편 (KOSIS, 공공누리 제1유형)
- 대법원 efamily.scourt.go.kr (ADR-026 영속화)
- 공공누리 KOGL 제1유형 (영리 사용 + 출처표시 의무)

## 의뢰 영역 1: 통계청 KOSIS 2015 성씨 300위 전수 데이터

본 시스템 15건만 본문화. 잔여 ~285건 (특히 상위 4~50위) 부재로 회귀
30쌍 중 9건 fail.

각 entry 필드 (보고서 §3.2 스키마):
- rank: int (1~300)
- surname: str (한글 1글자 또는 복성 2글자)
- hanja: str (한자, 동음이의 시 별도 entry로 분리)
- count: int (2015년 인구수)
- pct: float (전체 대비 비율, 소수점 4자리)
- source: "통계청 2015 인구주택총조사"

### 검증 필요 영역

1. **통계청 KOSIS 라이브 URL** (학술 검증):
   - kosis.kr 성씨·본관 통계 직접 추출 가능 URL
   - 또는 통계청 발표 보고서 (보도자료) URL
2. **공공누리 제1유형 확인**:
   - 각 데이터셋의 KOGL 유형 명시 (제1유형만 채택)
   - kogl.or.kr/info/license.do 검증

### 출력 형식

JSON 배열 300 entries:
```json
[
  {"rank": 1, "surname": "김", "hanja": "金", "count": 9959154, "pct": 21.5, "source": "통계청 2015"},
  {"rank": 4, "surname": "최", "hanja": "崔", "count": ..., "pct": ..., "source": "통계청 2015"},
  ...
]
```

### 한자 동음이의 처리 (보고서 §3 명시)

같은 한글 surname이 여러 한자로 나타나는 경우 (예: 방 = 方/龐) 별도
entry 분리:
- 방(方) rank 55: 94,831명
- 방(龐) rank 156: 893명

→ 본 시스템 `split_korean_name()`은 한글 분리만 — 한자 명시 입력 지원
   추가 필요.

## 의뢰 영역 2: 한자 명시 성명 분리 알고리즘

본 시스템 현재: `split_korean_name("방지훈")` → ("방", "지훈")
한자 미인식 → 동음이의 구분 불가.

### 권장 알고리즘

`split_korean_name_with_hanja(name_kr: str, hanja: str | None) -> tuple`:
- name_kr: 한글 성명 (필수)
- hanja: 한자 성명 (선택, 명시 시 동음이의 구분)

예시:
- `split_korean_name_with_hanja("방지훈", "龐志訓")` → ("방", "龐", "지훈")
- `split_korean_name_with_hanja("방지훈", "方志訓")` → ("방", "方", "지훈")
- `split_korean_name_with_hanja("방지훈", None)` → ("방", None, "지훈") — 보수적 (최상위 rank 적용)

학술 출처 의뢰:
- 한국 동성동본 한자 분류 가이드라인 (국립국어원 or 대법원)
- 한자 입력 UX 패턴 (한국어 텍스트 처리)

## 의뢰 영역 3: 음절 미인기 결합 보정 알고리즘

본 시스템 현재 freq_024 김탁구 (성씨 1위 + 음절 미인기 '탁') → very_common 잘못 추정.
보고서 expected: uncommon.

### 분석

- "탁구"는 보통명사적 발음 ("탁" "구" 각각 인명 음절 빈도 낮음)
- 결합 확률: 성씨 21.5% × 음절 미수록 (0.001%) = 매우 낮음 → uncommon

본 시스템 음절 데이터 (ADR-016): 17건+17건 → 대부분 음절 미수록
→ rank None → rank_to_pct(None) = 0.001 적용 → estimated_count 보수적
하지만 성씨 1위 매우 큰 비율로 인해 결합 확률이 still very_common 추정.

### 권장 보정

음절 매우 비인기 (rank > 100 또는 None) 시 감산 가중치:
- if 첫 음절 + 끝 음절 모두 매우 비인기 → joint_pct 1/10 추가 감산
- 보고서 §5.1 γ factor (쏠림 보정) 학술 근거 명시

학술 출처 의뢰:
- 신지영 (2014) 『말소리의 이해』 — 음절 결합 확률 보정
- 조성문 (2025) KCI — 비인기 음절 인명 통계 처리

## 의뢰 영역 4: 시계열 음절 데이터 (선택)

ADR-016 본문화 데이터 (name_aesthetic_syllable_freq.json) 시간차원 없음.
보고서 §4 시계열 데이터 (2010/2015/2020/2025) 미제공.

### 권장 데이터 구조

```json
{
  "year": 2025,
  "gender": "M",
  "position": "first",
  "syllables": {"준": 18500, "하": 12300, "도": 8200, ...}
}
```

대법원 efamily.scourt.go.kr 출생 신고 통계 (ADR-026 동일 API)에서
연도별 추출 가능.

학술 출처 의뢰:
- 대법원 efamily.scourt.go.kr 연도별 인기 이름 통계 API
- 통계청 KOSIS 출생 통계 (인명 음절 별도 추출 가능 여부)

## 회귀 데이터셋 (의무)

본 보고서 채택 시 회귀 추가 18쌍 (ADR-029 known-limitation 해소):
- freq_004~012 (성씨 DB 누락 9건) → 본 보고서 데이터로 PASS 전환
- freq_019 한자 동음이의 → 본문에서 한자 명시 입력 PASS 전환
- freq_024·025·026 음절 미인기 결합 → 보정 알고리즘으로 uncommon 전환
- freq_013·027·028·029·030 → 추가 검증

빈 약속 금지. 18쌍 expected_phonetic + expected_combined_frequency 본문
명시 의무.

## ADR-010 사실성 분리 필수

본 보고서가 다음을 단정하지 않아야 합니다:
- 통계 빈도가 사용자 운세·길흉과 인과관계 (객관 라벨만)
- 동음이의 한자가 절대적 분류 (한자 미명시 시 보수적 처리 명시)

## 본 보고서 출력 검증 의무

1. 통계청 KOSIS URL 라이브 검증 (kosis.kr 접근 가능)
2. 공공누리 제1유형 확인 (kogl.or.kr)
3. 300 entries JSON 본문 명시 (빈 약속 차단)
4. 한자 동음이의 entry 별도 분리
5. 회귀 18쌍 expected 데이터 본문 명시

## 본 시스템 채택 절차

1. 본 보고서 받으면 `/squeeze-report` 호출
2. ADR-017 분석/판정 분리 절차 적용
3. ACCEPT 영역 본문화:
   - data/korean_surname_frequency.json 300 entries 갱신
   - name_uniqueness.py split_korean_name_with_hanja 추가
   - 음절 미인기 보정 알고리즘
   - test_name_uniqueness.py 회귀 18쌍 추가
4. ADR-030 작성 (또는 ADR-029 supplement)
5. korean-name-frequency-statistics 노트 deferred_pending 해소
```

## 본 시스템 채택 절차

1. 본 보고서 받으면 `/squeeze-report C:\Users\Admin\Desktop\사주\<보고서명>.md` 호출
2. 분석/판정 에이전트(Haiku) dispatch 후 ADR 정합성 검증
3. ACCEPT 영역 본문화:
   - 300 entries 성씨 데이터 본문화
   - 한자 동음이의 split_korean_name_with_hanja 함수
   - 음절 미인기 결합 보정
   - 회귀 18쌍 추가
4. ADR-030 작성
5. 커밋·푸시·CI·Railway 라이브 검증

## 면책

본 프롬프트는 ADR-001 (결정론) + ADR-002 (학파 회피) +
ADR-006 (자문 거절) + ADR-010 (사실성 분리) + ADR-026 (출처 검증) +
ADR-029 (객관 라벨) 정합 의무. 보고서 응답이 ADR 위반 시 `/squeeze-report`
거부 처리.
