"""동의 화면 텍스트 — 운영표준 §14.1 본문화.

얼굴 사진 업로드 전 사용자에게 보여야 할 동의서 텍스트를 4언어(ko/en/ja/zh)로
제공한다. UI는 이 텍스트를 그대로 표시하고, 사용자가 모든 필수 동의 항목에
동의했을 때만 사진 업로드를 진행한다.

§14.1 구조:
  1) 타이틀 — "얼굴 사진 분석 동의 안내"
  2) 항목 4종 (동의 강제, REQUIRED_CONSENT_FIELDS와 정확히 매칭):
     · processing       — 사진 분석을 위한 일시적 처리
     · storage          — 캐시 보관 (24시간 후 자동 폐기)
     · training         — 익명화된 형태의 모델 개선 (옵션)
     · third_party_sharing — 외부 LLM API 호출 (Google Vision / Anthropic Vision)
  3) 권리 — GDPR Art.15-22 / 한국 개인정보보호법 §35-37 (열람·정정·삭제·이의제기)
  4) 면책 — 본 결과는 오락·문화 콘텐츠로, 의료·법률·금융 판단 근거 아님.

본 모듈은 텍스트 + 메타데이터(필수/선택)만 반환. 실제 동의 수집·저장 UI는
프론트엔드 책임. 백엔드는 receive_consent()로 동의 정보를 받아 §7.3.3 거버넌스
메타데이터에 반영한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# REQUIRED_CONSENT_FIELDS와 정확히 동일한 키 순서 — engine/safety/data_governance.py와 일치
CONSENT_FIELDS = ("processing", "storage", "training", "third_party_sharing")


@dataclass(frozen=True)
class ConsentItem:
    """한 항목의 동의 안내 + 필수/선택 표시."""
    key: str
    title: str
    description: str
    required: bool  # True면 미동의 시 서비스 차단, False면 옵션


# ─────────────────────────── 4언어 텍스트 ───────────────────────────

_TITLE = {
    "ko": "얼굴 사진 분석 동의 안내",
    "en": "Face Photo Analysis — Consent",
    "ja": "顔写真分析の同意のお願い",
    "zh": "面部照片分析同意书",
}

_INTRO = {
    "ko": (
        "이 늙은이가 그대의 상을 짚기 전에, 그대의 사진을 어찌 쓰는지 먼저 일러주려 하네. "
        "아래 항목을 천천히 살펴보시고 동의 여부를 정해주시게."
    ),
    "en": (
        "Before we analyze your face photo, please review how your image will be used. "
        "Each item below has its own consent — please review and decide individually."
    ),
    "ja": (
        "顔写真を分析する前に、お写真の使用方法をご確認ください。"
        "下記の各項目について個別にご同意の意思をお決めください。"
    ),
    "zh": (
        "在分析您的面部照片前,请先了解照片的使用方式。"
        "请逐项查看以下条款并决定是否同意。"
    ),
}

_ITEMS_KO = (
    ConsentItem(
        key="processing",
        title="① 사진 분석을 위한 일시적 처리 [필수]",
        description=(
            "그대가 올린 사진은 얼굴 윤곽·비율·기색을 짚어보는 데에만 쓰이네. "
            "분석 즉시 본문에 쓸 메모로 변환되며, 원본 픽셀은 응답 후 곧 폐기되네."
        ),
        required=True,
    ),
    ConsentItem(
        key="storage",
        title="② 캐시 보관 (24시간) [필수]",
        description=(
            "같은 사진을 다시 올리실 때 빠르게 풀이를 돌려드리고자, "
            "사진의 해시값과 분석 결과만 24시간 보관한 뒤 자동 폐기하네. "
            "사진 자체는 저장되지 않네."
        ),
        required=True,
    ),
    ConsentItem(
        key="training",
        title="③ 익명화된 형태의 모델 개선 [선택]",
        description=(
            "그대가 동의하시면, 얼굴이 식별되지 않는 메트릭(비율·각도·기색 수치)만을 "
            "모델 개선에 쓸 수 있게 하네. 거부하셔도 풀이는 동일하게 제공되네."
        ),
        required=False,
    ),
    ConsentItem(
        key="third_party_sharing",
        title="④ 외부 분석 API 호출 [필수]",
        description=(
            "풀이는 Google Gemini Vision 또는 Anthropic Claude Vision의 도움을 빌리네. "
            "사진은 두 회사의 처리 약관에 따라 전송되며, 그들 또한 사진을 보관하지 않네 "
            "(엔터프라이즈 약관 기준)."
        ),
        required=True,
    ),
)

_ITEMS_EN = (
    ConsentItem(
        key="processing",
        title="1. Temporary processing for analysis [required]",
        description=(
            "Your photo is processed only to extract facial geometry, ratios, and complexion. "
            "Raw pixels are converted to features at inference time and discarded after the response."
        ),
        required=True,
    ),
    ConsentItem(
        key="storage",
        title="2. Cache storage (24 hours) [required]",
        description=(
            "Only a hash of the photo and the resulting reading are cached for 24 hours, "
            "so a re-upload returns instantly. The photo itself is never stored."
        ),
        required=True,
    ),
    ConsentItem(
        key="training",
        title="3. Anonymized model improvement [optional]",
        description=(
            "If you agree, only de-identified metrics (ratios, angles, color values) "
            "may be used to improve the model. Declining does not affect your reading."
        ),
        required=False,
    ),
    ConsentItem(
        key="third_party_sharing",
        title="4. Third-party vision API [required]",
        description=(
            "Analysis uses Google Gemini Vision or Anthropic Claude Vision. "
            "Your photo is sent under those vendors' enterprise terms, which prohibit "
            "training-data retention."
        ),
        required=True,
    ),
)

_ITEMS_JA = (
    ConsentItem(
        key="processing",
        title="① 分析のための一時的処理 [必須]",
        description=(
            "お写真は、顔の輪郭・比率・血色を読み取るためにのみ使用されます。"
            "推論直後に特徴量に変換され、元の画素データは応答後すぐに破棄されます。"
        ),
        required=True,
    ),
    ConsentItem(
        key="storage",
        title="② キャッシュ保管(24時間)[必須]",
        description=(
            "同じお写真を再度アップロードされた際に迅速にお答えするため、"
            "写真のハッシュ値と分析結果のみを24時間保管し、その後自動で削除します。"
            "お写真自体は保管されません。"
        ),
        required=True,
    ),
    ConsentItem(
        key="training",
        title="③ 匿名化されたモデル改善 [任意]",
        description=(
            "ご同意いただいた場合のみ、個人が特定できない数値データ(比率・角度・色値)を"
            "モデル改善に利用させていただきます。同意されなくても鑑定内容は変わりません。"
        ),
        required=False,
    ),
    ConsentItem(
        key="third_party_sharing",
        title="④ 外部分析APIの呼び出し [必須]",
        description=(
            "鑑定にはGoogle Gemini VisionまたはAnthropic Claude Visionを利用します。"
            "両社のエンタープライズ規約に基づき、写真は学習用データとして保存されません。"
        ),
        required=True,
    ),
)

_ITEMS_ZH = (
    ConsentItem(
        key="processing",
        title="① 用于分析的临时处理 [必须]",
        description=(
            "您的照片仅用于提取面部轮廓、比例与气色等特征。"
            "推断后原始像素将被转换为特征值,响应完成后立即销毁。"
        ),
        required=True,
    ),
    ConsentItem(
        key="storage",
        title="② 缓存保留(24小时)[必须]",
        description=(
            "为方便您再次上传时快速获得结果,我们仅保留照片的哈希值与分析结果24小时,"
            "之后自动删除。照片本身不会被保存。"
        ),
        required=True,
    ),
    ConsentItem(
        key="training",
        title="③ 匿名化数据用于模型改进 [可选]",
        description=(
            "如您同意,我们将仅使用不可识别个人身份的数值(比例、角度、色值)用于改进模型。"
            "若拒绝,您的解读内容不会因此改变。"
        ),
        required=False,
    ),
    ConsentItem(
        key="third_party_sharing",
        title="④ 调用外部分析API [必须]",
        description=(
            "解读由Google Gemini Vision或Anthropic Claude Vision协助生成。"
            "照片依据两家服务商的企业协议传输,且不会被用于训练数据。"
        ),
        required=True,
    ),
)

_RIGHTS = {
    "ko": (
        "그대는 언제든 이 늙은이에게 \"내 사진을 어찌 다루었는가\" 물으실 수 있고, "
        "잘못된 부분이 있으면 바로잡으라 명하실 수 있네. "
        "동의를 거두시려거든 그 또한 자유라네 (GDPR Art.15-22 / 한국 개인정보보호법 §35-37)."
    ),
    "en": (
        "You have the right to access, correct, erase, or restrict the processing of your data, "
        "and to withdraw consent at any time (GDPR Art.15-22 / Korean PIPA §35-37)."
    ),
    "ja": (
        "お客様はいつでもご自身のデータの開示・訂正・削除・処理停止を請求でき、"
        "同意を撤回することも可能です(GDPR Art.15-22 / 韓国個人情報保護法§35-37)。"
    ),
    "zh": (
        "您可随时查阅、更正、删除或限制您数据的处理,并可随时撤回同意"
        "(GDPR Art.15-22 / 韩国个人信息保护法§35-37)。"
    ),
}

_DISCLAIMER = {
    "ko": (
        "이 늙은이가 짚는 결은 정성껏 살핀 결이긴 하나, 의원의 진단이나 법관의 판결, "
        "재물 운용의 자문이 아니라네. 마음의 결을 비추는 한 거울로 삼아주시게."
    ),
    "en": (
        "This reading is offered as a cultural and entertainment service. It is not medical, "
        "legal, or financial advice."
    ),
    "ja": (
        "本鑑定は文化・娯楽のためのサービスです。医療・法律・金融に関する助言ではありません。"
    ),
    "zh": (
        "本解读为文化娱乐服务,不构成医疗、法律或金融建议。"
    ),
}

_ITEMS_BY_LANG = {
    "ko": _ITEMS_KO,
    "en": _ITEMS_EN,
    "ja": _ITEMS_JA,
    "zh": _ITEMS_ZH,
}


# ─────────────────────────── Public API ───────────────────────────

def get_consent_screen(lang: str = "ko") -> dict[str, Any]:
    """동의 화면 텍스트 묶음 — 4언어. 미지원 언어는 영어로 대체.

    Returns:
        {
            "lang": "ko",
            "title": "...",
            "intro": "...",
            "items": [{"key", "title", "description", "required"}, ...],
            "rights": "...",
            "disclaimer": "...",
            "required_keys": ["processing", "storage", "third_party_sharing"],
        }
    """
    norm = lang if lang in _ITEMS_BY_LANG else "en"
    items = _ITEMS_BY_LANG[norm]
    return {
        "lang": norm,
        "title": _TITLE[norm],
        "intro": _INTRO[norm],
        "items": [
            {
                "key": it.key,
                "title": it.title,
                "description": it.description,
                "required": it.required,
            }
            for it in items
        ],
        "rights": _RIGHTS[norm],
        "disclaimer": _DISCLAIMER[norm],
        "required_keys": [it.key for it in items if it.required],
    }


def validate_consent_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """프론트에서 받은 동의 payload가 §14.1 필수 항목을 모두 충족하는지 검증.

    Args:
        payload: {"processing": True, "storage": True, ...}.
                 None 또는 빈 dict면 즉시 거부.

    Returns:
        {
            "ok": bool,                  # 모든 필수 항목 동의 시 True
            "missing_required": [...],   # 필수인데 누락
            "denied_required": [...],    # 필수인데 거부
            "training_opt_in": bool,     # 선택 항목 ③ 동의 여부
        }
    """
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "missing_required": [
                k for k, req in _required_map().items() if req
            ],
            "denied_required": [],
            "training_opt_in": False,
        }
    required = _required_map()
    missing: list[str] = []
    denied: list[str] = []
    for key, is_required in required.items():
        if not is_required:
            continue
        if key not in payload:
            missing.append(key)
        elif payload.get(key) is not True:
            denied.append(key)
    return {
        "ok": not missing and not denied,
        "missing_required": missing,
        "denied_required": denied,
        "training_opt_in": bool(payload.get("training") is True),
    }


def _required_map() -> dict[str, bool]:
    """ko 기준(모든 언어 동일 구조)으로 항목별 필수 여부 맵."""
    return {it.key: it.required for it in _ITEMS_KO}
