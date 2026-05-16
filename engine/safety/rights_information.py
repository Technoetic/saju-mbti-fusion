"""권리 행사 안내 — 운영표준 §14.2 본문화.

GDPR Art.15-22 / 한국 개인정보보호법 §35-37 / CCPA §1798.100-1798.135 등에 따른
사용자 권리를 표준화된 4언어 텍스트 + 운영 측 처리 메타데이터로 제공한다.

§14.2 권리 7종:
  · access           — 열람권 (어떤 데이터가 처리되는지)
  · rectify          — 정정권 (잘못된 정보 수정)
  · erase            — 삭제권 / 잊혀질 권리
  · restrict         — 처리 제한 (분석은 멈추되 데이터는 보관)
  · portability      — 이동권 (구조화된 형식으로 받기)
  · object           — 이의 제기 (자동화된 의사결정 거부)
  · withdraw_consent — 동의 철회 (언제든)

운영 측 메타데이터:
  · automation_status: AUTO / MANUAL / NA — 처리 자동화 수준
  · sla_business_days: 응답 SLA (GDPR 30일·KR 10일 등 지역별 최단)
  · authentication_required: bool — 본인 인증 필요 여부
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# §14.2 — 권리 식별자
RIGHT_KEYS = (
    "access",
    "rectify",
    "erase",
    "restrict",
    "portability",
    "object",
    "withdraw_consent",
)

# 처리 자동화 수준
AUTOMATION_AUTO = "auto"       # 운영자 개입 없이 셀프서비스
AUTOMATION_MANUAL = "manual"   # 운영팀 수동 처리
AUTOMATION_NA = "na"           # 해당 데이터 없음 (즉시 종결)


@dataclass(frozen=True)
class RightInfo:
    key: str
    title: str
    description: str
    automation_status: str
    sla_business_days: int
    authentication_required: bool


# ─────────────────────────── 4언어 텍스트 ───────────────────────────

_RIGHTS_KO = (
    RightInfo(
        key="access",
        title="① 열람권 — 내 사진과 풀이가 어찌 쓰였는지 알고 싶네",
        description=(
            "그대의 캐시(사진 해시 + 풀이 결과)가 어찌 보관되고 있는지 확인해 드리네. "
            "캐시는 24시간 후 자동 폐기되니, 그 안에 요청하시게."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=10,  # KR 개인정보보호법 §35
        authentication_required=True,
    ),
    RightInfo(
        key="rectify",
        title="② 정정권 — 잘못된 풀이를 바로잡고 싶네",
        description=(
            "풀이는 LLM의 일회성 산출이라 \"정정\"이 곧 \"새 풀이\"라네. "
            "다시 사진을 올리시거나, 풀이 캐시 삭제 후 재요청하시게."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=10,
        authentication_required=True,
    ),
    RightInfo(
        key="erase",
        title="③ 삭제권 — 내 흔적을 모두 지워주시게",
        description=(
            "사진 해시·풀이·익명 피드백 카운트까지 모두 삭제하네. "
            "단, 본인 인증을 위한 최소 식별값(요청 ID)은 처리 완료 후 30일까지 보관."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=10,
        authentication_required=True,
    ),
    RightInfo(
        key="restrict",
        title="④ 처리 제한 — 분석은 멈추되 데이터는 그대로 두어주시게",
        description=(
            "원치 않는 추가 분석을 멈추되, 법정 보존 의무 데이터는 그대로 두는 자리라네."
        ),
        automation_status=AUTOMATION_MANUAL,
        sla_business_days=15,
        authentication_required=True,
    ),
    RightInfo(
        key="portability",
        title="⑤ 이동권 — 풀이 결과를 구조화된 형식으로 내보내주시게",
        description=(
            "그대의 풀이 응답을 JSON 형식으로 내려드리네 (text + a11y + 메트릭). "
            "사진 자체는 보관하지 않으므로 이동 대상에서 제외."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=10,
        authentication_required=True,
    ),
    RightInfo(
        key="object",
        title="⑥ 이의 제기 — 자동화된 풀이를 거부하네",
        description=(
            "이 늙은이의 풀이를 더 이상 받지 않으시려거든 알려주시게. "
            "이후의 모든 사진 분석 요청을 차단해 드리네 (GDPR Art.22)."
        ),
        automation_status=AUTOMATION_MANUAL,
        sla_business_days=15,
        authentication_required=True,
    ),
    RightInfo(
        key="withdraw_consent",
        title="⑦ 동의 철회 — 동의를 거두고 싶네",
        description=(
            "처음 동의하신 항목(분석·캐시·모델개선·외부 API) 중 어느 것이든 거두실 수 있네. "
            "철회 즉시 캐시는 모두 폐기되고, 이전 풀이는 영향받지 않네."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=5,
        authentication_required=True,
    ),
)


_RIGHTS_EN = (
    RightInfo(
        key="access",
        title="1. Right of access — what data do you hold on me?",
        description=(
            "We confirm what cache (photo hash + reading) is currently held for you. "
            "Cache expires automatically after 24 hours."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=30,  # GDPR Art.12(3)
        authentication_required=True,
    ),
    RightInfo(
        key="rectify",
        title="2. Right to rectification",
        description=(
            "Readings are one-shot LLM outputs, so 'rectification' typically means "
            "deleting the cache and re-running with a corrected input."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=30,
        authentication_required=True,
    ),
    RightInfo(
        key="erase",
        title="3. Right to erasure",
        description=(
            "All photo hashes, readings, and anonymous feedback counts are deleted. "
            "A minimal request ID is retained for 30 days post-completion (audit only)."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=30,
        authentication_required=True,
    ),
    RightInfo(
        key="restrict",
        title="4. Right to restriction of processing",
        description=(
            "We stop new analysis but retain data needed for legal record-keeping."
        ),
        automation_status=AUTOMATION_MANUAL,
        sla_business_days=30,
        authentication_required=True,
    ),
    RightInfo(
        key="portability",
        title="5. Right to data portability",
        description=(
            "Your readings are exported as JSON (text + a11y + metrics). "
            "Photos themselves are not retained and thus not exportable."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=30,
        authentication_required=True,
    ),
    RightInfo(
        key="object",
        title="6. Right to object",
        description=(
            "You may object to automated decision-making (GDPR Art.22). "
            "We then block all subsequent face-reading requests from your account."
        ),
        automation_status=AUTOMATION_MANUAL,
        sla_business_days=30,
        authentication_required=True,
    ),
    RightInfo(
        key="withdraw_consent",
        title="7. Right to withdraw consent",
        description=(
            "Withdraw consent for any item (processing / storage / training / "
            "third-party sharing). Cache is purged immediately on withdrawal."
        ),
        automation_status=AUTOMATION_AUTO,
        sla_business_days=5,
        authentication_required=True,
    ),
)


_RIGHTS_JA = (
    RightInfo("access", "① 開示請求", "現在保管中のキャッシュ(写真ハッシュ+鑑定結果)をお知らせします。キャッシュは24時間後に自動削除されます。", AUTOMATION_AUTO, 14, True),
    RightInfo("rectify", "② 訂正請求", "鑑定は一度きりのLLM出力のため、「訂正」は実質的にキャッシュ削除+再依頼となります。", AUTOMATION_AUTO, 14, True),
    RightInfo("erase", "③ 削除請求", "写真ハッシュ・鑑定結果・匿名フィードバック数をすべて削除します。リクエストIDのみ30日間監査用に保管。", AUTOMATION_AUTO, 14, True),
    RightInfo("restrict", "④ 処理停止請求", "新たな分析は停止しつつ、法定保存対象のデータのみ残します。", AUTOMATION_MANUAL, 30, True),
    RightInfo("portability", "⑤ ポータビリティ請求", "鑑定結果をJSON形式でお渡しします(text + a11y + 数値)。写真本体は保管していません。", AUTOMATION_AUTO, 14, True),
    RightInfo("object", "⑥ 異議申立", "自動意思決定への異議を受け付け、以後の鑑定リクエストを遮断します(GDPR Art.22準拠)。", AUTOMATION_MANUAL, 30, True),
    RightInfo("withdraw_consent", "⑦ 同意撤回", "同意項目のいずれでも撤回可能です。撤回と同時にキャッシュを破棄します。", AUTOMATION_AUTO, 5, True),
)


_RIGHTS_ZH = (
    RightInfo("access", "① 查阅权", "我们将告知您目前缓存中的内容(照片哈希+解读结果)。缓存24小时后自动删除。", AUTOMATION_AUTO, 15, True),
    RightInfo("rectify", "② 更正权", "解读为一次性LLM输出,因此「更正」实质为删除缓存后重新生成。", AUTOMATION_AUTO, 15, True),
    RightInfo("erase", "③ 删除权", "我们将删除所有照片哈希、解读结果与匿名反馈计数。仅保留请求ID 30天用于审计。", AUTOMATION_AUTO, 15, True),
    RightInfo("restrict", "④ 限制处理", "停止新增分析,仅保留法律要求留存的数据。", AUTOMATION_MANUAL, 30, True),
    RightInfo("portability", "⑤ 数据可携权", "您的解读结果可导出为JSON(text + a11y + 指标)。照片本身未保存,无法导出。", AUTOMATION_AUTO, 15, True),
    RightInfo("object", "⑥ 反对权", "您可反对自动化决策,我们将屏蔽后续所有面相分析请求(依据GDPR Art.22)。", AUTOMATION_MANUAL, 30, True),
    RightInfo("withdraw_consent", "⑦ 撤回同意", "您可随时撤回任意同意项目,撤回的同时立即销毁缓存。", AUTOMATION_AUTO, 5, True),
)


_RIGHTS_BY_LANG = {
    "ko": _RIGHTS_KO,
    "en": _RIGHTS_EN,
    "ja": _RIGHTS_JA,
    "zh": _RIGHTS_ZH,
}


# ─────────────────────────── Public API ───────────────────────────

def get_rights_information(lang: str = "en") -> dict[str, Any]:
    """4언어 권리 안내 텍스트 묶음.

    Returns:
        {
            "lang": "ko",
            "rights": [{"key", "title", "description",
                        "automation_status", "sla_business_days",
                        "authentication_required"}, ...],
            "contact_method": "https://example.com/privacy" 또는 None
        }
    """
    norm = lang if lang in _RIGHTS_BY_LANG else "en"
    rights = _RIGHTS_BY_LANG[norm]
    return {
        "lang": norm,
        "rights": [
            {
                "key": r.key,
                "title": r.title,
                "description": r.description,
                "automation_status": r.automation_status,
                "sla_business_days": r.sla_business_days,
                "authentication_required": r.authentication_required,
            }
            for r in rights
        ],
        "contact_method": None,  # 외부 운영 환경에서 주입 (privacy@... 등)
    }


def get_right_by_key(key: str, lang: str = "en") -> dict[str, Any] | None:
    """단일 권리 항목 — UI 상세 화면 렌더링용. 미상 key면 None."""
    if key not in RIGHT_KEYS:
        return None
    info = get_rights_information(lang)
    for r in info["rights"]:
        if r["key"] == key:
            return r
    return None


def list_automatable_rights(lang: str = "en") -> list[str]:
    """자동화 가능한 권리 key 목록 — 셀프서비스 UI 노출 대상."""
    info = get_rights_information(lang)
    return [r["key"] for r in info["rights"] if r["automation_status"] == AUTOMATION_AUTO]


def get_sla_for_region(key: str, region: str | None) -> int:
    """지역별 SLA(영업일) — GDPR/KR/JP/CN 각각의 최단 응답일.

    EU = 30 (GDPR), KR = 10 (개인정보보호법), JP = 14 (個人情報保護法),
    CN = 15 (PIPL), 기타 = 영어판 SLA.
    """
    base_lang = {
        "KR": "ko", "EU": "en", "DE": "en", "FR": "en", "UK": "en", "GB": "en",
        "JP": "ja", "CN": "zh",
    }.get((region or "").strip().upper(), "en")
    r = get_right_by_key(key, base_lang)
    if not r:
        return -1
    return int(r["sla_business_days"])
