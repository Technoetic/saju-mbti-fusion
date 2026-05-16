---
type: roadmap
status: waiting_external_input
priority: medium
report_section: §1
created: 2026-05-17
blocked_by: 딥리서치 보고서
estimated_effort: 2-3 hours (보고서 받은 후)
---

# 가족 서열 상대 불용한자 (§1)

## 무엇

장자·차자·막내·외동에 따라 다른 불용한자를 추가 진단.

## 왜

- 보고서 §1 마지막 문장에서 "더 정밀한 진단을 위한 옵션"
- 현 시스템: 절대 불용 80자만 처리
- 추가하면 "이 글자는 장자에게만 적합" 같은 미세 경고 가능

## 필요한 외부 입력

[[../templates/REPORT_TEMPLATE]] 형식으로 받기:

- 카테고리 4종: firstborn_only / lastborn_only / middleborn_only / only_child_only
- 각 카테고리 30~50자 + 흉화 사유 + 학파 출처
- 성별 구분 여부
- 흉화 강도 (absolute/advisory/conditional)
- 현대 가정 예외 처리 규칙
- JSON 데이터 형식 제공

## 본문화 계획 (보고서 받은 후)

### 신규 모듈: `engine/divination/name_hierarchy.py`

```python
CATEGORY_FIRSTBORN_ONLY = "firstborn_only"
CATEGORY_LASTBORN_ONLY = "lastborn_only"
# ...

@dataclass
class HierarchyEntry:
    char: str
    category: str
    reason: str
    severity: str  # absolute / advisory / conditional
    source: str

def diagnose_hierarchy(
    name_hanja: str,
    sibling_order: int,
    total_siblings: int,
    gender: str | None = None,
) -> dict:
    ...
```

### 기존 모듈 영향

- `name_bulyong.py`: 영향 없음 (절대 불용 유지)
- `name_scoring.score_name()`: hierarchy 진단 결과 envelope에 추가
- API 시그니처: `sibling_order` 파라미터 추가 (선택)

## 면책

- 학파별 차이 큼 → 채택 학파 명시
- 현대 가정(외동·재혼·입양) 예외는 보수적 처리
- 사용자 응답에 "참고용" 면책

## 딥리서치 프롬프트

→ [[../templates/REPORT_TEMPLATE]] 참조 + 본 노트의 "필요한 외부 입력" 섹션 그대로 사용
