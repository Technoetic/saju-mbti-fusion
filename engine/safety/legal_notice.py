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


# ─────────────────────────── 통합 푸터 ───────────────────────────
LEGAL_NOTICE_FOOTER_KO = (
    "\n\n— — —\n"
    "[안내]\n"
    f"• {MEDICAL_DISCLAIMER_KO}\n"
    f"• {FORTUNE_DISCLAIMER_KO}\n"
    "• 위기 상황 시: 자살예방상담전화 1393 · 정신건강위기상담 1577-0199 (24시간 무료)"
)


# ─────────────────────────── 위기 시 전용 푸터 (의료 거부 톤) ───────────────────────────
CRISIS_FOOTER_KO = (
    "\n\n— — —\n"
    "[중요]\n"
    "• 본 서비스는 의료·심리 치료가 아니며, 위기 상황을 충분히 도울 수 없습니다.\n"
    "• 자살예방상담전화 1393 · 정신건강위기상담 1577-0199 (24시간 무료)\n"
    "• 응급 시 119 · 즉시 생명 위협 시 112"
)


# ─────────────────────────── 영어 면책 (§7.2.10) ───────────────────────────
LEGAL_NOTICE_FOOTER_EN = (
    "\n\n— — —\n"
    "[Notice]\n"
    "• This service is not medical diagnosis or treatment, and must not be the "
    "sole basis for decisions about mental or physical health. For depression, "
    "anxiety, sleep issues, or other medical concerns, please consult a "
    "qualified mental health professional or physician.\n"
    "• Saju, dream interpretation, and physiognomy readings are cultural "
    "reference content from Eastern and Western traditions, not scientific or "
    "medical statements. Important life decisions (medical, legal, financial, "
    "career) should be made with relevant professionals.\n"
    "• Crisis support: 988 Suicide & Crisis Lifeline (US, 24/7) · "
    "Samaritans 116 123 (UK/EU, 24/7)"
)

CRISIS_FOOTER_EN = (
    "\n\n— — —\n"
    "[Important]\n"
    "• This service is not medical or psychological treatment and cannot "
    "adequately support crisis situations.\n"
    "• 988 Suicide & Crisis Lifeline (US, 24/7 free)\n"
    "• Samaritans: 116 123 (UK/EU, 24/7 free)\n"
    "• Emergency: 911 (US) · 999 (UK) · 112 (EU)"
)


# ─────────────────────────── 일본어 면책 ───────────────────────────
LEGAL_NOTICE_FOOTER_JA = (
    "\n\n— — —\n"
    "[ご案内]\n"
    "• 本サービスの解釈は医学的診断・治療ではなく、精神や身体の健康に関する"
    "意思決定の唯一の根拠とすることはできません。うつ・不安・睡眠の問題など"
    "医学的判断が必要な場合は、精神科・心療内科などの専門医にご相談ください。\n"
    "• 四柱推命・夢占い・観相などの解釈は東洋・西洋の伝統的な文化コンテンツ"
    "としての参考であり、科学的・医学的事実の表明ではありません。\n"
    "• 危機時: よりそいホットライン 0120-279-338 (24時間無料)"
)

CRISIS_FOOTER_JA = (
    "\n\n— — —\n"
    "[重要]\n"
    "• 本サービスは医療・心理治療ではなく、危機状況に十分対応できません。\n"
    "• よりそいホットライン 0120-279-338 (24時間無料)\n"
    "• いのちの電話 0570-783-556\n"
    "• 緊急時: 119"
)


# ─────────────────────────── 중국어 면책 (간체) ───────────────────────────
LEGAL_NOTICE_FOOTER_ZH = (
    "\n\n— — —\n"
    "[提示]\n"
    "• 本服务的解读不是医学诊断或治疗，不能作为精神或身体健康决策的"
    "唯一依据。如有抑郁、焦虑、睡眠等问题，请咨询精神科或全科医生。\n"
    "• 四柱、解梦、观相等解读为东西方传统文化参考内容，非科学或医学陈述。\n"
    "• 危机援助: 北京心理危机研究中心 010-82951332 · 全国心理援助 400-161-9995"
)

CRISIS_FOOTER_ZH = (
    "\n\n— — —\n"
    "[重要]\n"
    "• 本服务非医疗或心理治疗，无法充分应对危机情况。\n"
    "• 北京心理危机研究中心 010-82951332 (24小时免费)\n"
    "• 全国心理援助 400-161-9995 (24小时免费)\n"
    "• 紧急: 120 (急救) · 110 (警察)"
)


# ─────────────────────────── 언어 코드 → 푸터 매핑 ───────────────────────────
_LEGAL_FOOTERS = {
    "ko": (LEGAL_NOTICE_FOOTER_KO, CRISIS_FOOTER_KO),
    "en": (LEGAL_NOTICE_FOOTER_EN, CRISIS_FOOTER_EN),
    "ja": (LEGAL_NOTICE_FOOTER_JA, CRISIS_FOOTER_JA),
    "zh": (LEGAL_NOTICE_FOOTER_ZH, CRISIS_FOOTER_ZH),
}


def _resolve_lang(lang: str | None) -> str:
    """BCP-47 또는 ISO 639-1 → 지원 언어 코드. 미지원은 'ko' fallback."""
    if not lang:
        return "ko"
    code = lang.lower().split("-")[0].split("_")[0]
    return code if code in _LEGAL_FOOTERS else "ko"


def build_legal_footer(
    *,
    is_crisis: bool = False,
    include_data_notice: bool = False,
    lang: str | None = None,
) -> str:
    """응답 푸터 생성.

    Args:
        is_crisis: 위기 상황 응답 시 True — 위기 전용 푸터 반환
        include_data_notice: 신규 사용자/첫 응답에 True — 데이터 처리 안내 포함
        lang: BCP-47 또는 ISO 639-1 ('ko' 'en' 'ja' 'zh'). 미지원 시 한국어.
    """
    code = _resolve_lang(lang)
    general, crisis = _LEGAL_FOOTERS[code]
    if is_crisis:
        return crisis

    parts = [general]
    if include_data_notice and code == "ko":
        # 데이터 처리 안내는 한국어 정책 기반이므로 한국어에만 우선 부착
        parts.append(f"\n• {DATA_NOTICE_KO}")
    return "".join(parts)


__all__ = [
    "MEDICAL_DISCLAIMER_KO",
    "FORTUNE_DISCLAIMER_KO",
    "DATA_NOTICE_KO",
    "LEGAL_NOTICE_FOOTER_KO",
    "CRISIS_FOOTER_KO",
    "LEGAL_NOTICE_FOOTER_EN",
    "CRISIS_FOOTER_EN",
    "LEGAL_NOTICE_FOOTER_JA",
    "CRISIS_FOOTER_JA",
    "LEGAL_NOTICE_FOOTER_ZH",
    "CRISIS_FOOTER_ZH",
    "build_legal_footer",
]
