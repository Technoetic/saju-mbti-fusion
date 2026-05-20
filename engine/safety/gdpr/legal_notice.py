"""법정 면책 고지 텍스트 — 모든 사용자 응답에 자동 첨부.

근거:
  - 의료기기법 제6조: "진단" 표방 시 의료기기 인증 필요 → 명시적 면책으로 회피
  - 의료법 제27조: 무면허 의료행위 금지 → "참고용·진단 아님" 명시
  - 개인정보보호법 제23조: 정신건강 데이터는 민감정보 → 별도 동의 필요
  - 정보통신망법: 만 14세 미만 법정대리인 동의 의무
"""

from __future__ import annotations


# ─────────────────────────── 의료 면책 ───────────────────────────
MEDICAL_DISCLAIMER_KO = (
    "본 서비스의 해석은 의학적 진단·치료가 아니며, 정신건강 또는 신체 건강 관련 "
    "의사결정의 단독 근거가 될 수 없습니다. 우울·불안·수면 문제 등 의학적 판단이 "
    "필요한 경우 정신건강의학과·가정의학과 전문의 상담을 권합니다."
)


# ─────────────────────────── 운세·전통 콘텐츠 면책 ───────────────────────────
FORTUNE_DISCLAIMER_KO = (
    "사주·해몽·화패 등의 해석은 동·서양 전통 문화 콘텐츠로서의 참고이며, "
    "과학적·의학적 사실 진술이 아닙니다. 중요한 인생 결정(의료·법률·투자·진로)은 "
    "해당 분야 전문가와 상의해 주시기 바랍니다."
)


# ─────────────────────────── 데이터 처리 안내 ───────────────────────────
DATA_NOTICE_KO = (
    "입력하신 꿈·사주 데이터는 해석 처리를 위해 일시적으로 사용되며, "
    "민감 정보(정신건강 정보)는 별도 동의 없이 영구 저장되지 않습니다."
)


# ─────────────────────────── EU AI Act §50 — AI 생성 라벨 (ADR-058) ───────────────────────────
# 사용자에게 본 응답이 AI 시스템에 의해 생성됐음을 명시. machine-readable 메타와
# human-readable 텍스트 둘 다 응답에 포함하여 §50 의무 충족.
AI_GENERATED_LABEL_KO = (
    "본 풀이는 AI 시스템에 의해 생성된 콘텐츠입니다. (EU AI Act §50 의무 고지)"
)


# ─────────────────────────── EU AI Act §52 — AI 리터러시 면책 (ADR-059) ───────────────────────────
# 사용자에게 AI 시스템의 한계·정확도 미보증·오작동 가능성을 명시적으로 고지하여
# §52 (AI literacy) 의무 충족. 운세 도메인 특수성 (참고용·재미용) 강조.
AI_LITERACY_DISCLAIMER_KO = (
    "본 AI 시스템은 사주·관상·작명·해몽·손금 풀이에 통계·결정론·LLM 추론을 결합합니다. "
    "정확도를 보증하지 않으며, 오작동·편향·예상치 못한 결과가 발생할 수 있습니다. "
    "본 풀이는 참고용이며 의료·법률·금융·진로 의사결정의 단독 근거가 될 수 없습니다."
)


# ─────────────────────────── 통합 푸터 ───────────────────────────
LEGAL_NOTICE_FOOTER_KO = (
    "\n\n— — —\n"
    "[안내]\n"
    f"• {MEDICAL_DISCLAIMER_KO}\n"
    f"• {FORTUNE_DISCLAIMER_KO}\n"
    f"• {AI_GENERATED_LABEL_KO}\n"
    f"• {AI_LITERACY_DISCLAIMER_KO}\n"
    "• 위기 상황 시: 자살예방상담전화 1393 · 정신건강위기상담 1577-0199 (24시간 무료)"
)


# ─────────────────────────── AI 생성 메타 (machine-readable) ───────────────────────────
def build_ai_generation_meta(
    *,
    model_label: str | None = None,
    confidence: float | None = None,
) -> dict[str, object]:
    """EU AI Act §50 machine-readable AI 생성 표시 메타.

    응답 envelope에 별도 필드(`ai_generation`)로 첨부. 클라이언트가
    `<meta name="ai-generated" content="true">` 같은 HTML 메타로 변환 가능.

    Args:
        model_label: LLM 모델 라벨 (예: 'claude-opus-4.7', 'gemini-2.5-flash-lite').
                     None이면 'unspecified' 사용.
        confidence: 분류기·점수 신뢰도 0.0~1.0. None이면 omit.
    """
    meta: dict[str, object] = {
        "ai_generated": True,
        "framework": "EU AI Act §50",
        "model_label": model_label or "unspecified",
        "human_readable_label_ko": AI_GENERATED_LABEL_KO,
    }
    if confidence is not None:
        meta["confidence"] = float(max(0.0, min(1.0, confidence)))
    return meta


# ─────────────────────────── 위기 시 전용 푸터 (의료 거부 톤) ───────────────────────────
CRISIS_FOOTER_KO = (
    "\n\n— — —\n"
    "[중요]\n"
    "• 본 서비스는 의료·심리 치료가 아니며, 위기 상황을 충분히 도울 수 없습니다.\n"
    "• 자살예방상담전화 1393 · 정신건강위기상담 1577-0199 (24시간 무료)\n"
    "• 응급 시 119 · 즉시 생명 위협 시 112"
)


def build_legal_footer(
    *,
    is_crisis: bool = False,
    include_data_notice: bool = False,
    lang: str = "ko",
) -> str:
    """응답 푸터 생성.

    Args:
        is_crisis: 위기 상황 응답 시 True — 위기 전용 푸터 반환
        include_data_notice: 신규 사용자/첫 응답에 True — 데이터 처리 안내 포함
        lang: 언어 코드 ('ko' 기본). 현재 한국어만 구현, 향후 i18n 확장 자리.
    """
    # ADR-051: lang 인자는 옛 호출자 호환용 (request_pipeline.py 등). 현재 ko 단일.
    del lang  # 미구현 i18n 자리, 호출자 시그니처 호환
    if is_crisis:
        return CRISIS_FOOTER_KO

    parts = [LEGAL_NOTICE_FOOTER_KO]
    if include_data_notice:
        parts.append(f"\n• {DATA_NOTICE_KO}")
    return "".join(parts)


__all__ = [
    "MEDICAL_DISCLAIMER_KO",
    "FORTUNE_DISCLAIMER_KO",
    "DATA_NOTICE_KO",
    "AI_GENERATED_LABEL_KO",
    "AI_LITERACY_DISCLAIMER_KO",
    "LEGAL_NOTICE_FOOTER_KO",
    "CRISIS_FOOTER_KO",
    "build_legal_footer",
    "build_ai_generation_meta",
]
