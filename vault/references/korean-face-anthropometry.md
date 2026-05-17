---
type: reference
status: accepted
date: 2026-05-17
domain: [face]
factuality: kci_verified
sources:
  - 송우철 외 (2017). 한국 성인의 얼굴 형태 인체측정학 분석.
  - 최윤경, 이경희 (2009). 한국 여성 안면 형태 분류 연구.
  - 노상훈 외 (1998). 한국인 하악각 통계 분석.
  - POSTECH HFES (2012). 한국인 안면 측정 데이터 (산소마스크 디자인용).
verified_url:
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895 (송우철 2017)
  - https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE09916734 (최윤경·이경희 2009)
  - https://www.jkaoms.org/journal/download_pdf.php?spage=129&volume=32&number=2 (노상훈 1998)
  - http://center.postech.ac.kr/homepage_data/publication_proceedings_international/12_HFES_OxygenMask.pdf (POSTECH 2012)
verified_date: 2026-05-17
related:
  - decisions/ADR-010-name-sibling-factuality
  - decisions/ADR-018-face-golden-set-policy
  - decisions/ADR-022-face-shape-classifier
  - reports/face-shape-classifier-research
related_module: engine/divination/face_shape.py (5형 결정론 분류)
---

# 한국인 안면 인체측정학 — KCI 검증 학술 출처

## 배경

본 시스템 관상 도메인 5형 결정론 분류 (ADR-022)에서 사용하는 임계값의 학술
출처. `engine/divination/face_shape.py` `_REFERENCE_PAPERS` dict 영속화 근거.

기존 face_scoring.py(MediaPipe 478 키포인트 12궁 점수)에 추가로, 본 학술
출처 기반 5형(목·화·토·금·수) 결정론 분류를 본문화.

## 1. 송우철 외 (2017)

- **DBpia URL**: https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895
- **활용**: face_width_height_ratio 임계값
  - 목형(< 0.82), 토형(>= 0.88) 분류 기준
- **인용 컨텍스트**: 보고서 §1.1 + ADR-022

## 2. 최윤경, 이경희 (2009)

- **DBpia URL**: https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE09916734
- **활용**: bizygomatic_to_bigonial_ratio 임계값
  - 화형(> 1.25) 분류 기준 — 광대/하악 비율
- **인용 컨텍스트**: 보고서 §1.1 + ADR-022

## 3. 노상훈 외 (1998)

- **JKAOMS URL**: https://www.jkaoms.org/journal/download_pdf.php?spage=129&volume=32&number=2
- **활용**: jaw_angle_deg (하악각) 임계값
  - 금형(< 112도) 분류 기준
- **인용 컨텍스트**: 보고서 §1.1 + ADR-022

## 4. POSTECH HFES (2012)

- **URL**: http://center.postech.ac.kr/homepage_data/publication_proceedings_international/12_HFES_OxygenMask.pdf
- **활용**: 한국인 안면 측정 평균치
  - 수형(0.83 <= ratio <= 0.88) 분류 기준 — 한국인 평균 수렴
- **인용 컨텍스트**: 보고서 §1.1 + ADR-022

## 본 시스템 활용

### ADR-022 본문화

`engine/divination/face_shape.py` _REFERENCE_PAPERS dict:
```python
_REFERENCE_PAPERS: dict[str, str] = {
    "목형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",
    "화형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE09916734",
    "토형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",
    "금형": "https://www.jkaoms.org/journal/download_pdf.php?spage=129&volume=32&number=2",
    "수형": "http://center.postech.ac.kr/homepage_data/publication_proceedings_international/12_HFES_OxygenMask.pdf",
    "복합형": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE07133895",
}
```

### ADR-010 사실성 분리 정합

- ✅ DBpia·JKAOMS·POSTECH 라이브 URL 검증 가능
- ✅ 저자·연도·학술지 명시 (가짜 인용 X)
- ✅ 본 시스템은 "기하학 형태 분류"로만 사용 (인과·운명 X)
- ✅ 학파(마의·유장상법) 인과 해석 채택 X

### 한계 명시

- 표본 한정 (성인 + 일부 여성·청소년 표본)
- 임계값은 보고서 §3 권장 — 실제 한국인 분포 보정 가능 (post_traffic)
- POSTECH 데이터는 산소마스크 디자인용 → 일반 인구 대표성 일부 부족

## 본 시스템 적용 면책

- 본 데이터는 **객관 기하학적 형태 분류 베이스라인**이며 운명·인과·길흉 무관
- 사용자 출력 시 ADR-006·010 면책 자동 포함 의무:
  - "객관 형태 분류이며 길흉화복과 무관"
  - "한국인 안면 인체측정학 KCI 학술 통계 비교"
  - "마의·유장상법 인과 해석 채택 X"
- EU AI Act §50(3) 감정 추론 명시 고지 적용

## 향후

- 표본 크기·p-value 보강 (원논문 직접 fetch)
- 운영 데이터 누적 후 임계값 보정 (별도 ADR, post_traffic)
- 연령·성별 차등 매핑 추가 가능
