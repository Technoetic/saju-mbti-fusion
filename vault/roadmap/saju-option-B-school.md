---
type: roadmap
status: waiting_external_input
priority: medium
report_section: §3
created: 2026-05-17
blocked_by: 딥리서치 보고서 + 학파 채택 ADR
related_adr: [decisions/ADR-002-saju-option-A]
estimated_effort: 4-6 hours (보고서 받은 후)
---

# 사주 용신 옵션 B — 단일 학파 채택

## 무엇

ADR-002 옵션 A(단순 오행 카운팅) 외에 단일 학파(조후·억부 등) 1개 채택해
참고용 정보 추가 노출.

## 왜

옵션 A는 "균형 보강 지표"일 뿐. 정통 용신 추천이 필요한 사용자에겐 부족.

## 필요한 외부 입력

딥리서치 프롬프트 (참고):

```
한국 작명 시장에서 가장 널리 쓰이는 사주 용신 도출 방법 1개를
정확한 규칙·알고리즘으로 정리.

- 일간 강약·왕쇠·한습조열·월령 분석
- 결정론 if-then 규칙
- 사주 50건 예시 + 도출된 용신 + 추론 근거
- 권위 문헌 출처 (자평진전·적천수·궁통보감·연해자평)
- 다른 학파와의 차이 명시
```

## 본문화 계획

### 학파 채택 ADR 먼저 작성

- ADR-NNN: "사주 용신은 OO론 채택"
- 면책 강화: 다른 학파 차이 명시

### 신규 모듈: `engine/divination/name_saju_school.py`

```python
def derive_yongshin(
    pillars: dict,
    school: str = "조후",  # 채택 학파
) -> dict:
    """단일 학파 용신 도출.

    Returns:
        {
            "yongshin": "화",
            "rationale": "사주가 한습 → 火 보조",
            "school": "조후론",
            "confidence": 0.8,  # 학파 내 합의도
        }
    """
```

### 응답 envelope

- 옵션 A 유지 (단순 분포 = 균형 지표)
- 옵션 B 추가 (학파 용신 = 정통 추천)
- 둘 다 표시, 사용자 선택

## 면책

- "학파별 차이 있음 — 다른 학파는 다른 답 가능"
- AI는 학파 통설을 모사한 알고리즘, 명리학자 자문 대체 X
- 결정론으로 동작하되 정답이라 단정 X

## 우선순위 낮은 이유

- 옵션 A로 작명 추천은 이미 동작
- 옵션 B는 정확도 ↑이지만 책임 ↑
- 명리학자 자문·파트너십 후가 안전
