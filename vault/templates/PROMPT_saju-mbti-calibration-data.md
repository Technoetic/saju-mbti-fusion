---
type: prompt_template
target: deepresearch
purpose: ADR-014 매핑 임계값 보정용 검증 데이터 수집
created: 2026-05-17
related_roadmap: null
related_reports:
  - reports/saju-mbti-correlation.md (거부)
  - reports/saju-mbti-ml-model.md (거부)
related_adr:
  - ADR-014-saju-mbti-prediction-exception (현 매핑, 임계값 직관 추측)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-002-saju-option-A (학파 회피)
---

# 딥리서치 프롬프트 — ADR-014 매핑 임계값 보정 데이터

## 본 프롬프트의 방향 결정

거부된 두 보고서 (saju-mbti-correlation / saju-mbti-ml-model)가 권장한
**학설 매핑** 또는 **ML 모델**은 본 시스템에서 채택 불가:
- 학설 매핑: ADR-002 학파 회피 위반
- ML 모델: 학습 데이터 부재 + ADR-014 단정 회피 위반

본 시스템 ADR-014 매핑은 결정론·자체 규칙이나 **임계값(0.55 / 0.45 / 0.4 등)이
모두 직관 추측**. 5개 샘플 측정 결과 **평균 45% 미정** — 사용자 가치 ↓.

따라서 딥리서치는 본 시스템 매핑의 **임계값을 보정할 검증 데이터** 수집에
집중. ML 모델이 아닌, **임계값 통계 분석**용.

## 사용법

본 프롬프트를 ChatGPT Deep Research / Claude Research / Gemini Deep
Research에 입력. 결과 데이터셋 받으면:
1. 사실성 검증 (ADR-010)
2. 통계 분석으로 임계값 재산출
3. ADR-014 매핑 함수 임계값 갱신 (코드 변경 작음)
4. 회귀 테스트 통과 확인

---

## 프롬프트 본문

```
한국 사주 + MBTI 자기보고 페어 데이터셋을 다음 요구사항에 맞춰
조사·정리해주세요. 본 데이터는 ML 학습용이 아닌 임계값 통계 보정용입니다.

## 본 시스템 컨텍스트

본 시스템은 사주 → MBTI 4축 경향성 매핑을 결정론으로 수행:
- E vs I: 8글자 양 비율 ≥ 0.55 → E, ≤ 0.45 → I
- S vs N: (土+金)/total ≥ 0.4 → S, (木+水)/total ≥ 0.4 → N
- T vs F: 金 비율 + 양간 / 火水 + 음간
- J vs P: 오행 분포 표준편차 < 0.5 → J, > 1.0 → P

각 임계값은 직관 추측이라 5개 샘플 측정 시 평균 45% 미정. 본 시스템은
ML 학습 불가 (사실성 분리 원칙). 대신 **자기보고 데이터로 임계값 분포 통계**
만 산출하여 임계값을 데이터 기반으로 재설정하려 함.

## 절대 조건

다음은 본 시스템 영구 정책 (변경 불가):
- ML 분류기 학습 X (단정 출력 → 위반)
- 학파별 십성·격국 매핑 X (학파 회피)
- "예측 정확도" 표시 X (자기실현적 예언)
- 16유형 단정 X

## 요구사항

### 1. 데이터셋 수집 (필수)

다음 페어 데이터를 검증 가능한 출처에서 수집:

```json
[
  {
    "id": "anonymous_001",
    "birth_date": "1990-05-15",  // 연-월-일 (시는 선택)
    "birth_time": "14:00",  // 선택
    "self_reported_mbti": "ENFJ",
    "self_report_confidence": "verified" | "self_test" | "unverified",
    "source": "공개 설문조사 / 학술 연구 / SNS 자기 공개",
    "source_url": "검증 가능 URL"
  },
  ...
]
```

목표: 1000개 이상의 페어. 출처별로 분할:
- 학술 연구 페어 (KCI 검색 가능 논문)
- 공개 설문조사 (출처·표본 크기·연도 명시)
- SNS 자기 공개 (개인정보 비식별화)

### 2. 출처 신뢰도 분류 (ADR-010 의무)

각 데이터 포인트의 신뢰도:
- **verified**: 학술 연구 + IRB 승인 + 표본 크기 명시
- **self_test**: 16personalities.com 등 자기 검사 + 결과 공개
- **unverified**: SNS 자기 공개 (검증 X)

각 등급별 데이터 수와 출처 URL 명시.

### 3. 통계 분석 (필수, 사실성 분리 의무)

수집된 페어를 본 시스템 매핑 규칙에 통과시켜 **임계값 분포**를 산출:

```json
{
  "E_I_axis": {
    "yang_ratio_for_self_reported_E": {
      "n": 412,
      "mean": 0.58,
      "median": 0.57,
      "p25": 0.51,
      "p75": 0.64,
      "stdev": 0.11
    },
    "yang_ratio_for_self_reported_I": {
      "n": 388,
      "mean": 0.43,
      "median": 0.44,
      "p25": 0.37,
      "p75": 0.50,
      "stdev": 0.09
    },
    "recommended_threshold": {
      "E_at": "p25 of E group",
      "I_at": "p75 of I group",
      "uncertain_range": "between"
    }
  },
  "S_N_axis": {...},
  "T_F_axis": {...},
  "J_P_axis": {...}
}
```

### 4. 거부할 내용 (절대 미포함)

- "이 사주는 ENFJ를 예측합니다" 같은 단정 매핑표
- "강한 통계적 유의성" 수사 (실제 p-value·표본·검정 방법 없으면)
- ML 분류기 학습 코드
- 학파별 십성→MBTI 매핑 (학설 채택)
- "사주가 MBTI보다 정확하다" 등 비교 평가

### 5. 한계 명시 (ADR-010 의무)

다음 한계를 보고서 본문에 명시:
- 자기보고 MBTI는 측정 오차 큼 (재검사 신뢰도 ~70%)
- 사주는 출생 시각 정확성에 의존
- 페어 데이터는 자기선택 편향 (SNS 공개자는 일반 인구와 다름)
- 본 통계는 "분포 정보"일 뿐 "예측 정확도" 아님

### 6. 결과물 형식

마크다운 보고서 + JSON 데이터:
1. 데이터 수집 절차 + 출처별 분포 (마크다운)
2. 1000+ 페어 JSON (개인정보 비식별화)
3. 4축별 임계값 분포 통계 (JSON)
4. 임계값 권장값 + 근거 (마크다운)
5. 한계 명시 (마크다운)
6. ADR-010 사실성 분리 검증 자료 (출처 URL 모두 검증 가능)

## 검증 데이터셋 50건 (회귀 테스트용)

페어 데이터 중 50건을 본 시스템 회귀 테스트용으로 분리:

```json
[
  {
    "id": "regression_001",
    "saju_pillars": {"year": "庚午", "month": "壬午", "day": "乙巳", "hour": "癸未"},
    "wuxing_dist": {"목": 1.0, "화": 3.0, "토": 1.0, "금": 1.0, "수": 2.0},
    "day_master_han": "乙",
    "expected_yang_ratio": 0.50,
    "expected_axis_signals": {
      "E_I": "uncertain",  // 본 시스템 매핑 출력
      "S_N": "uncertain",
      "T_F": "F",
      "J_P": "uncertain"
    },
    "self_reported_mbti": "INFP",
    "agreement_axes": ["F"],  // 일치한 축만
    "disagreement_axes": [],  // 미정은 disagreement 아님
    "purpose": "F축 매핑 검증 회귀"
  }
]
```

본 50건은 본 시스템 [engine/divination/test_saju_mbti_predictor.py](github
URL)에 그대로 추가됩니다.
```

---

## 결과물 처리 절차

1. 결과 보고서 `사주/[보고서명].md`로 저장
2. `vault/reports/saju-mbti-calibration-data.md` ADR-010 사실성 분리 영속화
3. 임계값 통계 분석:
   - p25 of E group / p75 of I group → E_I 새 임계값
   - 동일하게 다른 3축
4. ADR-014 매핑 함수 임계값 갱신 (1줄 변경)
5. 회귀 테스트 50건 추가
6. 평균 미정율 측정 (목표: 45% → 25% 이하)

## 우선순위 평가

본 프롬프트 실행은 **현 시점 중간 우선순위**:

✅ 즉시 가능 이유:
- ADR-014 이미 결정 (예외 영속화 완료)
- 매핑 모듈 존재, 임계값만 데이터 기반 보정
- 코드 변경 최소 (임계값 상수 갱신)

⏸️ 보류 가능 이유:
- 1000+ 페어 데이터 수집 자체가 큰 작업
- 자기보고 MBTI 신뢰도 한계
- SaaS 운영 후 실제 사용자 페어 데이터 누적이 더 정확

→ **결정**: 본 프롬프트 영속화. 실행 시점은 SaaS 운영 시작 전후 사용자
결정. 운영 전 = 외부 데이터 활용 / 운영 후 = 자체 누적 데이터 활용.

## 면책

- 본 프롬프트는 **임계값 통계 보정** 목적. ML 학습 아님
- 결과 데이터로 ADR-014 매핑 정밀도 ↑ 가능하나 **정확도 표시는 영구 금지**
- 자기보고 MBTI는 측정 오차 있음을 사용자 출력에서 명시 유지
