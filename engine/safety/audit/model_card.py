"""모델 카드 + 데이터 카드 — 운영표준 §7.2.10 본문화.

Mitchell et al. 2019 "Model Cards for Model Reporting" + Gebru et al. 2021
"Datasheets for Datasets" 양식을 따른다. 규제기관·감사자·사용자에게
시스템 사양·의도된 사용·한계·평가 결과를 표준 형식으로 공개한다.

규제 매핑:
  · EU AI Act Annex IV §1-7 (high-risk system 기술 문서)
  · NIST AI RMF §Govern-1.1 (책임성)
  · 한국 AI 안전성 평가체계 §I-3 (시스템 사양 공시)

본 모듈은 정적 사실(모델 ID·평가 결과)을 dict로 반환한다. 평가 결과 수치는
실 회귀 결과(N건 회귀 통과·골든 셋 평균 점수)로 자동 채우도록 외부 워커가
주입할 수 있다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


# §7.2.10 — 모델 카드 섹션 키 (Mitchell et al. 2019 표 3 기준 축약)
MODEL_CARD_SECTIONS = (
    "model_details",        # 1. 식별·버전·라이선스
    "intended_use",         # 2. 의도된 사용 + 범위 외
    "factors",              # 3. 관련 요인 (성별·연령·인종)
    "metrics",              # 4. 평가 지표
    "evaluation_data",      # 5. 평가 데이터셋
    "training_data",        # 6. 학습 데이터 (관상 LLM은 fine-tune 없음)
    "quantitative_analyses", # 7. 정량 분석
    "ethical_considerations", # 8. 윤리적 고려사항
    "caveats_and_recommendations", # 9. 한계·권고
)

DATA_CARD_SECTIONS = (
    "motivation",           # 1. 데이터셋 동기
    "composition",          # 2. 구성
    "collection_process",   # 3. 수집 과정
    "preprocessing",        # 4. 전처리
    "uses",                 # 5. 활용
    "distribution",         # 6. 배포
    "maintenance",          # 7. 유지보수
)


@dataclass(frozen=True)
class ModelCard:
    """단일 모델/시스템에 대한 §7.2.10 표준 카드.

    Attributes:
        system_id: 식별자 (예: "face_reading.v1.0").
        version: 시맨틱 버전.
        published_at: 발간일.
        sections: MODEL_CARD_SECTIONS 키 → 본문 dict.
    """
    system_id: str
    version: str
    published_at: str
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class DataCard:
    """단일 데이터셋(골든 셋·평가셋)에 대한 §7.2.10 표준 카드."""
    dataset_id: str
    version: str
    published_at: str
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)


# ─────────────────────────── face_reading 시스템 카드 ───────────────────────────

def _today_iso() -> str:
    return date.today().strftime("%Y-%m-%d")


def get_face_reading_model_card(
    *,
    eval_metrics: dict[str, Any] | None = None,
    version: str = "1.0",
) -> ModelCard:
    """face_reading 시스템의 표준 모델 카드 — §7.2.10.

    Args:
        eval_metrics: 외부 워커가 실 회귀 결과를 주입 가능. 미주입 시 정적 값.
        version: 시맨틱 버전 (default 1.0).
    """
    metrics_block = dict(eval_metrics or {})
    metrics_block.setdefault("regression_tests_passed", None)
    metrics_block.setdefault("golden_set_mean_score", None)

    sections = {
        "model_details": {
            "name": "운학 도사 관상 분석 시스템",
            "system_id": "face_reading",
            "version": version,
            "type": "vertical_engine_with_llm_conductor",
            "engines": ["bone_structure", "ratios", "complexion", "spirit_gaze", "safety"],
            "backbone_llm": [
                "Google Gemini Vision (primary)",
                "Anthropic Claude Vision (fallback)",
            ],
            "license": "Internal — see LICENSE for distribution terms",
            "owner": "Saju MBTI Fusion",
            "contact": "operator (privacy & safety)",
        },
        "intended_use": {
            "primary": (
                "오락·문화 콘텐츠로서 한국 전통 관상학 어휘로 풀이를 제공한다."
            ),
            "out_of_scope": [
                "의료 진단·예후 추정",
                "법률 판단·범죄 예측",
                "고용·신용·보험 결정",
                "EU AI Act §5(f)에 따른 직장·교육 환경 감정 추론",
            ],
            "intended_users": "성인 일반 사용자 (만 18세 이상).",
        },
        "factors": {
            "relevant_groups": [
                "age_bucket (20s–60s+)",
                "gender (자기보고)",
                "detected_language (ko/en/ja/zh)",
                "region (KR/EU/UK/US-CA/US-IL/JP/CN)",
            ],
            "instrumentation": "MediaPipe Face Landmarker (478 landmarks + 52 blendshapes)",
        },
        "metrics": {
            "persona_tone_hits_min": 3,
            "persona_forbidden_words_max": 0,
            "medical_legal_forbidden_max": 0,
            "crisis_block_rate": "모든 감지된 위기 신호 100% 차단",
            "p95_latency_threshold_ms": 5000,
            "p99_latency_threshold_ms": 8000,
            "runtime": metrics_block,
        },
        "evaluation_data": {
            "golden_set_id": "face_reading.golden.v1",
            "size_target": 21,
            "regression_suite": "engine/divination/test_face_reading.py",
            "judge_suite": "engine/divination/test_persona_judge.py",
            "governance": "engine.safety.gdpr.data_governance audit (LICIT_SOURCES만)",
        },
        "training_data": {
            "fine_tuning": "없음 — 외부 LLM(Gemini/Claude)을 비변형 사용 (제로샷 + 시스템 프롬프트)",
            "system_prompt_locale": "ko",
        },
        "quantitative_analyses": {
            "regression_pass_rate": metrics_block.get("regression_tests_passed"),
            "golden_set_mean_score": metrics_block.get("golden_set_mean_score"),
            "language_distribution_target": {"ko": 0.7, "en": 0.1, "ja": 0.1, "zh": 0.1},
        },
        "ethical_considerations": {
            "high_risk_areas": ["감정·정서 추론", "외모 평가 가능성"],
            "mitigations": [
                "EU AI Act §50(3) 명시 고지 (engine.safety.crisis.emotion_disclosure)",
                "외모 평가·미추 비교 금지 (시스템 프롬프트)",
                "위기 신호 결정론 차단 (engine.safety.crisis.detector)",
                "법정 면책 고지 자동 첨부 (engine.safety.gdpr.legal_notice)",
                "PII 자동 마스킹 (engine.safety.gdpr.pii)",
            ],
        },
        "caveats_and_recommendations": {
            "limitations": [
                "단일 사진 분석 — 시간 흐름·표정 변화 미반영",
                "필터·메이크업 강한 사진은 정확도 낮음",
                "특정 인종·민족 일반화 금지",
            ],
            "human_oversight": "모든 응답에 의료·법률·금융 자문 거부 + 전문가 안내 포함",
            "audit": "engine.safety.slo.slo.tracing 이벤트 + engine.safety.slo.slo 측정",
        },
    }
    return ModelCard(
        system_id="face_reading",
        version=version,
        published_at=_today_iso(),
        sections=sections,
    )


def get_face_reading_data_card(
    *,
    version: str = "1.0",
) -> DataCard:
    """face_reading 골든 셋의 표준 데이터 카드."""
    sections = {
        "motivation": {
            "purpose": (
                "운영표준 §6.5 + §6.7 케이스를 회귀 시점에 100% 결정적으로 재현하기 위한 골든 셋."
            ),
            "creators": "내부 운영팀",
            "funding": "내부",
        },
        "composition": {
            "instances": "이미지 + 보조 메트릭 + 기대 페르소나 톤 조건",
            "target_count": 21,
            "labels": "페르소나 어휘 ≥3 / 금지어 0 / 의료·법률 단정 0",
            "minor_subjects": "없음 (만 18세 이상만)",
        },
        "collection_process": {
            "sources": [
                "consented_user_upload",
                "internal_employee_test",
                "synthetic_generated",
            ],
            "consent_record": "engine.safety.gdpr.data_governance.validate_provenance 통과 필수",
            "iac_filter": "engine.safety.gdpr.data_governance.ILLICIT_SOURCES 즉시 격리",
        },
        "preprocessing": {
            "metrics_extraction": "MediaPipe Face Landmarker 478점 + 블렌드셰이프",
            "pii_handling": "이메일·전화는 engine.safety.pii로 마스킹",
        },
        "uses": {
            "primary": "CI 회귀 + LLM-as-Judge 평가",
            "out_of_scope": "외부 데이터 판매·공유 금지",
        },
        "distribution": {
            "license": "Internal — 외부 공개 시 별도 동의 절차",
            "retention_max_days": 365,
        },
        "maintenance": {
            "audit_cadence": "분기별 (engine.safety.gdpr.data_governance.audit_dataset)",
            "expiry_alert_days": 30,
        },
    }
    return DataCard(
        dataset_id="face_reading.golden.v1",
        version=version,
        published_at=_today_iso(),
        sections=sections,
    )


# ─────────────────────────── 검증 ───────────────────────────

def validate_model_card(card: ModelCard) -> list[str]:
    """모델 카드의 §7.2.10 9개 섹션이 모두 존재하고 비어있지 않은지 검사."""
    missing: list[str] = []
    for key in MODEL_CARD_SECTIONS:
        if key not in card.sections:
            missing.append(f"missing_section:{key}")
        elif not card.sections[key]:
            missing.append(f"empty_section:{key}")
    return missing


def validate_data_card(card: DataCard) -> list[str]:
    """데이터 카드 7개 섹션 검증."""
    missing: list[str] = []
    for key in DATA_CARD_SECTIONS:
        if key not in card.sections:
            missing.append(f"missing_section:{key}")
        elif not card.sections[key]:
            missing.append(f"empty_section:{key}")
    return missing


def card_to_dict(card: ModelCard | DataCard) -> dict[str, Any]:
    """JSON 직렬화 가능한 dict 표현 — API 응답·문서 생성에 사용."""
    base: dict[str, Any] = {
        "version": card.version,
        "published_at": card.published_at,
        "sections": card.sections,
    }
    if isinstance(card, ModelCard):
        base["system_id"] = card.system_id
        base["kind"] = "model_card"
    else:
        base["dataset_id"] = card.dataset_id
        base["kind"] = "data_card"
    return base
