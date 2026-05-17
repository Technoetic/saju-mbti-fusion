---
type: prompt_template
target: deepresearch
purpose: B6 DreamNet v4 — 멀티모달 꿈 네트워크 (현재 TODO, 운영 데이터 의존)
created: 2026-05-17
related_module: engine/agents/dreamnet_multimodal.py (v4 TODO)
related_adr:
  - ADR-006-legaltech-rejected (자문 거절)
  - ADR-010-name-sibling-factuality (사실성 분리)
  - ADR-014-saju-mbti-prediction-exception (단정 회피)
priority: low
status: draft
post_traffic: true  # 운영 데이터 누적 후 가치 평가
---

# 딥리서치 프롬프트 — B6 DreamNet v4 (멀티모달 꿈 네트워크)

## 사용법

본 프롬프트는 본 시스템 꿈해석 멀티에이전트 오케스트레이터의 명시
TODO 영역 (`engine/agents/__init__.py` B6 v4) 보강용. 운영 데이터 누적
의존 영역 — 학술 근거 단계만 우선 영속화.

DreamBank·Hall-Van de Castle 시스템·HVDC LLM 등 기존 모듈
(`dream_lex/dreambank.py`, `hallvandecastle.py`, `hvdc_llm.py`)과
정합되어야 함. 멀티모달은 텍스트 + 시각 + 음성 + 시간 패턴 통합.

---

## 프롬프트 본문

```
꿈해석 멀티모달 네트워크(DreamNet) 학술 근거 + 본 시스템 결손 영역
조사·정리해주세요. 본 자료는 꿈해석 SaaS의 멀티모달 통합 에이전트
(B6 v4) 보강용이며, ADR-010 사실성 분리 + ADR-014 단정 회피
정신을 따라야 합니다.

### 요구사항

#### 1. 학술 출처 라이브 검증

- DreamBank (G. William Domhoff) 공식 DB URL
- Hall-Van de Castle (1966) 꿈 내용 코딩 시스템 ISBN
- IDREAM·DreamScore 등 현대 멀티모달 꿈 연구 KCI/Pubmed URL
- 한국 수면·꿈 학회 KCI 등재 논문

#### 2. 멀티모달 입력 명세

본 시스템 B6 v4 입력 후보:
- 꿈 텍스트 보고 (기본)
- 잠들기 전 음성 일기 (감정 톤·발화 속도)
- 수면 단계 (REM 비율, 만일 wearable 연동)
- 시간 패턴 (반복 꿈·시각·요일)
- 사용자 일상 컨텍스트 (스트레스·이벤트)

각 모달별 학술 근거 + 한국어 적용 사례:

```yaml
modality: "text"
features:
  - "emotional_arc (긍정→부정 전환)"
  - "character_density (등장 인물 수)"
  - "setting_type (실내/실외/추상)"
academic_source: "<KCI URL: Hall-VdC 한국 적용 논문>"
korean_baseline: "<한국 표준 분포 데이터>"
```

#### 3. ADR-014 단정 회피 정합

다음은 채택 불가:
- ❌ "당신은 우울증입니다" (의료법 §27 + ADR-006)
- ❌ "수면 단계 분석으로 정신질환 진단" (의료 단정)
- ❌ "꿈 패턴 = 미래 사건 예측" (예언)

채택 가능:
- ✅ "당신의 꿈 보고에서 부정 정서 비율이 한국 표준 분포 대비 높습니다.
  단, 본 결과는 자기 보고 분석이며 임상 진단이 아닙니다."
- ✅ 학파 명시 ("Hall-VdC 시스템 적용")
- ✅ 다중 모달 통합 표시 (텍스트만 vs 텍스트+음성)

#### 4. 결정론 통합 알고리즘 명세

본 시스템 B6 v4 신규 모듈 후보:

```python
def integrate_multimodal_dream(
    text: str,
    voice_audio: bytes | None = None,
    sleep_stages: dict | None = None,
    user_baseline: dict | None = None,
) -> dict:
    """
    꿈 보고 멀티모달 통합 분석 (결정론).

    Returns:
        {
            "text_features": {...},        # HVDC 기반
            "voice_features": {...} | None,
            "sleep_features": {...} | None,
            "integration_score": "...",
            "korean_baseline_delta": {...},  # 한국 표준 분포 대비
            "available_modalities": ["text", "voice"],  # 입력된 것만
            "disclaimers": [...]
        }
    """
```

#### 5. 본 시스템 정합 점검

기존 모듈 점검:
- ✅ engine/agents/text_cleaner.py (A1 Schredl/HvDC 자동 추출)
- ✅ engine/dream_lex/hvdc_llm.py (A2 HVDC LLM)
- ✅ engine/dream_lex/dreambank.py (DreamBank 인터페이스)
- ✅ engine/dream_lex/hallvandecastle.py (HVDC 코딩)
- ✅ engine/agents/biomarker.py (A11 디지털 바이오마커)
- ❌ engine/agents/dreamnet_multimodal.py B6 v4 (TODO)

B6 v4는 위 모듈들 **통합 오케스트레이션** + 한국 표준 분포 비교.

#### 6. 운영 데이터 의존성

본 후보는 운영 트래픽 누적 후 가치 발현:
- 한국 사용자 꿈 보고 누적 → 한국 표준 분포 도출
- 음성 입력 옵션 → 사용자 동의 + GDPR/개인정보보호법 점검
- wearable 연동 → 별도 사업 단계 결정

본 프롬프트는 **학술 근거 + 알고리즘 명세만 영속화**.

#### 7. 회귀 테스트 데이터셋

본 시스템 회귀 검증용 20쌍 (텍스트 단독):

```json
[
  {
    "id": "dreamnet_001",
    "dream_text": "...",
    "modalities_available": ["text"],
    "expected_integration": {
      "hvdc_emotional_arc": "negative_to_positive",
      "korean_baseline_delta": {"negative_pct": "+15%"}
    },
    "expected_disclaimer": "자기 보고 분석"
  }
]
```

### 출력 형식

1. **학술 출처 표** (DreamBank·HVDC·KCI 라이브 검증)
2. **멀티모달 입력 명세 YAML** (모달별 학술 근거)
3. **결정론 통합 함수 명세**
4. **본 시스템 모듈 정합 점검 표**
5. **사용자 출력 면책 가이드라인**
6. **운영 데이터 의존성 명시**
7. **회귀 데이터셋 JSON** (20쌍)

### 검증 기준

- 모든 학술 인용 라이브 검증 가능
- 가짜 인용 0건
- 의료 단정·예언 표현 0건
- 다중 모달 통합 시 면책 의무
- 회귀 20쌍 이상

위 조건 미충족 시 ADR-010 + ADR-006 + ADR-014에 따라 거부됩니다.
```

---

## 본 시스템 채택 절차

1. `/squeeze-report` 사실성 분리 + 라이브 검증
2. ACCEPT 후보:
   - 신규 ADR (B6 DreamNet v4 통합 정책)
   - `engine/agents/dreamnet_multimodal.py` v4 신설
   - 기존 모듈 (text_cleaner·hvdc_llm·biomarker) 정합 검증
   - 회귀 20건
3. 운영 데이터 누적 후 한국 표준 분포 (별도 ADR)

## 면책

- 본 후보는 운영 데이터 누적 전 학술 근거 + 알고리즘 명세만
- 의료 단정·예언 절대 금지
- 음성·wearable 입력은 GDPR + 개인정보보호법 별도 점검 (🔵 사업 단계)
- 모달별 학파 명시 (HVDC ≠ DreamBank ≠ 한국 수면 학회)
