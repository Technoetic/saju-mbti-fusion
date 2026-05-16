"""감정·정서 추론 명시 고지 — EU AI Act §5(f) / §50(3) 본문화.

EU AI Act는 다음을 의무화한다:
  · Art.5(f)   — 직장·교육 환경의 감정 추론 금지
  · Art.50(3)  — 감정 인식·정서 추론을 수행하는 AI는 이용자에게 명시 고지 의무
  · Art.10(5)  — 생체정보 처리 시 동의·목적·보유기간 명시

관상 분석은 표정·신(神)·기색을 통한 정서 추론을 수반하므로 EU 지역
사용자에게는 응답 본문에 명시 고지를 첨부해야 한다.

본 모듈은:
  1) is_emotion_disclosure_required(region) — 지역별 의무 여부 판정
  2) build_emotion_disclosure(lang) — 4언어 고지문 생성
  3) inject_emotion_disclosure(text, region, lang) — 응답에 자동 첨부

ko/ja/zh도 호환 텍스트를 제공하지만, 법적 의무는 EU(+UK는 별도 EHRR 권고)에 한정.
"""

from __future__ import annotations


# §5(f) / §50(3) 의무 적용 지역 — BCP-47 region 또는 RegulationProfile.region_code.
# 'EU'는 27개 회원국 통합 코드, 개별 회원국 코드도 동일 적용.
_EU_REGIONS = {
    "EU",
    # 일부 운영 환경에서 회원국 ISO 3166-1 alpha-2를 region으로 받을 수 있어 매핑.
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
}

# UK는 EU 탈퇴 후에도 EHRR §6 권고로 동등 수준 고지 권장 (의무 아님, 권고).
_UK_REGIONS = {"UK", "GB"}


def is_emotion_disclosure_required(region: str | None) -> bool:
    """EU AI Act §50(3) 명시 고지 의무 지역인지 판정 (UK는 권고로 별도 함수)."""
    if not region:
        return False
    return region.strip().upper() in _EU_REGIONS


def is_emotion_disclosure_recommended(region: str | None) -> bool:
    """의무는 아니나 권고되는 지역 (UK EHRR §6 등)."""
    if not region:
        return False
    return region.strip().upper() in _UK_REGIONS


# ─────────────────────────── 4언어 고지문 ───────────────────────────

# 한국어는 운학 도사 페르소나(사극풍)와 일관. ko/ja/zh도 호환용으로 제공.

_DISCLOSURE_KO = (
    "\n\n[감정 추론 안내] "
    "이 늙은이가 짚는 결은 그대의 표정·기색·눈빛에서 마음의 흐름을 살피는 것이라네. "
    "이 풀이에는 감정·정서를 가늠하는 자리가 있음을 미리 일러주이 (EU AI Act §50(3)). "
    "그대는 언제든 이 풀이를 거절하거나 거두실 수 있네."
)

_DISCLOSURE_EN = (
    "\n\n[AI Emotion Recognition Notice] "
    "This reading involves AI-based inference of your emotional and affective state "
    "from facial expressions, complexion, and gaze. You are informed of this in "
    "accordance with EU AI Act Article 50(3). You may decline or withdraw at any time."
)

_DISCLOSURE_JA = (
    "\n\n[AI感情推論のお知らせ] "
    "本鑑定には、お顔の表情・血色・目つきから感情や情緒を推論するAI機能が含まれます。"
    "EU AI Act 第50条(3)に基づきお知らせいたします。"
    "いつでも本鑑定を辞退・撤回いただけます。"
)

_DISCLOSURE_ZH = (
    "\n\n[AI情绪推断告知] "
    "本解读包含通过面部表情、气色与目光推断您的情绪与情感状态的AI功能。"
    "依据欧盟人工智能法第50条第3款向您告知。您可随时拒绝或撤回本解读。"
)

_DISCLOSURE_BY_LANG = {
    "ko": _DISCLOSURE_KO,
    "en": _DISCLOSURE_EN,
    "ja": _DISCLOSURE_JA,
    "zh": _DISCLOSURE_ZH,
}


def build_emotion_disclosure(lang: str = "en") -> str:
    """4언어 명시 고지문 — EU 지역 응답에 자동 첨부.

    미지원 언어는 영어로 대체 (EU AI Act 영어 원문 기반 표준 문구).
    반환 문자열은 앞에 "\\n\\n" 두 줄 띄움이 포함되어 응답 본문에 그대로 concat 가능.
    """
    return _DISCLOSURE_BY_LANG.get(lang, _DISCLOSURE_EN)


def inject_emotion_disclosure(
    text: str,
    *,
    region: str | None,
    lang: str = "en",
) -> str:
    """응답 본문 + (EU/UK일 때) 감정 추론 고지를 합쳐 반환.

    EU(의무): 명시 고지 자동 첨부.
    UK(권고): 동일 텍스트 첨부 (호환성 — 의무는 없으나 자율 준수).
    그 외: 원본 텍스트 그대로.
    """
    if is_emotion_disclosure_required(region) or is_emotion_disclosure_recommended(region):
        return text + build_emotion_disclosure(lang)
    return text


def get_disclosure_metadata(region: str | None, lang: str = "en") -> dict[str, object]:
    """응답 JSON에 첨부할 메타데이터 — 운영표준 §7.3.4 트레이싱 + UI 노출용.

    Returns:
        {
            "required": bool,      # EU 의무
            "recommended": bool,   # UK 권고
            "lang": "en",
            "legal_basis": "EU AI Act Art.50(3)" | None,
            "disclosure_text": str | None,  # required/recommended일 때만
        }
    """
    required = is_emotion_disclosure_required(region)
    recommended = is_emotion_disclosure_recommended(region)
    out: dict[str, object] = {
        "required": required,
        "recommended": recommended,
        "lang": lang,
        "legal_basis": None,
        "disclosure_text": None,
    }
    if required:
        out["legal_basis"] = "EU AI Act Art.50(3)"
        out["disclosure_text"] = build_emotion_disclosure(lang)
    elif recommended:
        out["legal_basis"] = "UK EHRR §6 (recommended)"
        out["disclosure_text"] = build_emotion_disclosure(lang)
    return out
