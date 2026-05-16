"""사진 촬영 가이드 — 운영표준 §7.2.9 본문화.

§7.2.1 사진 불량 9종 에러코드(ERR_FACE_*/WARN_FACE_*)에 대응하는 사용자 가이드를
4언어(ko/en/ja/zh)로 제공한다. 백엔드가 사진 거부 응답을 돌려보낼 때 첨부해
사용자가 다음 촬영에서 무엇을 고쳐야 할지 즉시 알 수 있게 한다.

§7.2.9 사진 촬영 사용자 가이드 (3계층):
  1) 사전 체크리스트 — 촬영 전 항상 안내 (조명·정면·가림·표정)
  2) 에러별 즉시 안내 — 불량 사유에 특화된 1~2문장 (사극풍 ko / 평이체 en·ja·zh)
  3) 재시도 팁 — 같은 사용자가 2회 이상 같은 에러를 낼 때 단계별 조치

본 모듈은 정상 풀이 응답에는 영향을 주지 않으며, ERR_FACE_*/WARN_FACE_* 코드가
발생했을 때만 가이드 텍스트를 동봉한다.
"""

from __future__ import annotations

from typing import Any


# ─────────────────────────── 1) 사전 체크리스트 ───────────────────────────

PHOTO_CHECKLIST_KO = [
    "정면을 바라보고 머리를 기울이지 마시게.",
    "빛 좋은 곳에서 얼굴 전체에 그늘이 지지 않도록 하시게.",
    "안경·마스크·모자는 잠시 벗어주시게 (가능한 경우).",
    "한 분만 화면에 담으시게.",
    "흔들리지 않도록 두 손으로 안정되게 잡으시게.",
]

PHOTO_CHECKLIST_EN = [
    "Face the camera straight on and keep your head level.",
    "Use bright, even lighting — avoid shadows across your face.",
    "Remove glasses, masks, and hats when possible.",
    "Only one person in the frame.",
    "Hold the device steady with both hands.",
]

PHOTO_CHECKLIST_JA = [
    "正面を向き、頭を傾けないでください。",
    "顔全体に均等に光が当たる明るい場所で撮影してください。",
    "メガネ・マスク・帽子はできるだけ外してください。",
    "画面には一人だけ写してください。",
    "両手でしっかり持って手ブレを防いでください。",
]

PHOTO_CHECKLIST_ZH = [
    "正对镜头,头部保持水平。",
    "选择光线明亮均匀的环境,避免脸部出现阴影。",
    "尽量摘下眼镜、口罩和帽子。",
    "画面中只保留一个人。",
    "双手稳握设备,避免抖动。",
]


# ─────────────────────────── 2) 에러별 즉시 안내 ───────────────────────────

# 운영표준 §7.2.1과 동일한 에러코드 키. 한국어는 사극풍, 그 외는 평이체.

_HINTS_KO = {
    "ERR_FACE_NOT_DETECTED": "허허, 상이 잘 잡히지 않는구먼. 빛 좋은 곳에서 정면으로 한 번 더 부탁하이.",
    "ERR_FACE_MULTIPLE": "허허, 그대 한 분의 상만 담아 보내시게.",
    "ERR_FACE_NON_HUMAN": "허허, 사람의 상으로만 풀이를 짚네.",
    "ERR_FACE_BLUR": "허허, 결이 흐려 짚지 못하네. 빛 좋은 곳에서 정면으로 다시 담아주시게.",
    "ERR_FACE_PROFILE": "허허, 옆모습은 한 자리만 보이네. 정면 한 장 더 부탁하이.",
    "ERR_FACE_BACKLIT": "허허, 기색은 흐려 짚지 못하네. 빛을 등지지 마시게.",
    "ERR_FACE_OCCLUDED": "허허, 가린 자리는 자네에게 묻네. 가리개를 풀고 한 장 더 부탁하이.",
    "WARN_FACE_FILTERED": "허허, 짙은 분바름은 상의 결을 가리는구먼. 다음엔 본래 결로 담아보시게.",
    "WARN_FACE_FLAT": "허허, 화면 속 그림은 입체가 없으니 곧 그대의 얼굴을 담아주시게.",
}

_HINTS_EN = {
    "ERR_FACE_NOT_DETECTED": "We couldn't detect a face. Please try again facing the camera in bright light.",
    "ERR_FACE_MULTIPLE": "Please include only one person in the frame.",
    "ERR_FACE_NON_HUMAN": "We can only read human faces.",
    "ERR_FACE_BLUR": "The photo is too blurry. Hold steady and try again in good light.",
    "ERR_FACE_PROFILE": "Please face the camera straight on, not in profile.",
    "ERR_FACE_BACKLIT": "Too much backlight — please move so light is on your face, not behind it.",
    "ERR_FACE_OCCLUDED": "Please remove any masks, sunglasses, or items covering your face.",
    "WARN_FACE_FILTERED": "Heavy makeup or filters may affect the reading. Try a natural photo next time.",
    "WARN_FACE_FLAT": "This looks like a screen photo. Please take a live photo of yourself.",
}

_HINTS_JA = {
    "ERR_FACE_NOT_DETECTED": "顔を検出できませんでした。明るい場所で正面を向いて撮り直してください。",
    "ERR_FACE_MULTIPLE": "画面には一人だけ写してください。",
    "ERR_FACE_NON_HUMAN": "人の顔のみ鑑定できます。",
    "ERR_FACE_BLUR": "写真がぼやけています。手ブレを抑えて明るい場所で撮り直してください。",
    "ERR_FACE_PROFILE": "横顔ではなく正面で撮影してください。",
    "ERR_FACE_BACKLIT": "逆光が強すぎます。光源を背にしない位置で撮ってください。",
    "ERR_FACE_OCCLUDED": "マスク・サングラスなど顔を覆うものを外してください。",
    "WARN_FACE_FILTERED": "濃いメイクやフィルターは結果に影響することがあります。次回は自然な写真をお試しください。",
    "WARN_FACE_FLAT": "画面の撮影に見えます。ご自身の顔を直接撮影してください。",
}

_HINTS_ZH = {
    "ERR_FACE_NOT_DETECTED": "未能识别面部。请在光线充足处正面再拍一次。",
    "ERR_FACE_MULTIPLE": "画面中请只保留一人。",
    "ERR_FACE_NON_HUMAN": "仅可解读人脸。",
    "ERR_FACE_BLUR": "照片过于模糊。请在光线良好处稳握设备重拍。",
    "ERR_FACE_PROFILE": "请正对镜头,不要侧脸。",
    "ERR_FACE_BACKLIT": "逆光过强。请调整位置,让光源照在面部而非身后。",
    "ERR_FACE_OCCLUDED": "请取下口罩、墨镜等遮挡物。",
    "WARN_FACE_FILTERED": "浓妆或滤镜可能影响判读,下次请使用自然照。",
    "WARN_FACE_FLAT": "看起来是屏幕翻拍。请直接拍摄您本人。",
}

_HINTS_BY_LANG = {
    "ko": _HINTS_KO,
    "en": _HINTS_EN,
    "ja": _HINTS_JA,
    "zh": _HINTS_ZH,
}

_CHECKLISTS_BY_LANG = {
    "ko": PHOTO_CHECKLIST_KO,
    "en": PHOTO_CHECKLIST_EN,
    "ja": PHOTO_CHECKLIST_JA,
    "zh": PHOTO_CHECKLIST_ZH,
}


# ─────────────────────────── 3) 재시도 팁 (단계별) ───────────────────────────

# 같은 에러를 N회 반복 시 노출할 추가 팁. §7.2.9 단계적 안내.
_RETRY_TIPS_BY_CODE_KO = {
    "ERR_FACE_NOT_DETECTED": [
        "카메라와 얼굴의 거리를 30~50cm로 두시게.",
        "낮 시간이나 책상등 켜진 자리에서 다시 담아주시게.",
        "전면 카메라라면 화면 위쪽 가운데를 보시게.",
    ],
    "ERR_FACE_BACKLIT": [
        "창문·조명을 등지지 말고 마주 보시게.",
        "밝기는 자네 얼굴이 화면에서 환하게 보일 정도면 충분하이.",
        "스마트폰의 HDR을 켜두면 도움 되네.",
    ],
    "ERR_FACE_OCCLUDED": [
        "마스크·선글라스·모자를 잠시 벗으시게.",
        "앞머리가 이마를 많이 가리면 살짝 넘기시게 — 이마 자리도 상의 한 결이라.",
        "손으로 얼굴을 가리지 마시게.",
    ],
    "ERR_FACE_PROFILE": [
        "코끝이 카메라 중앙을 향하게 하시게.",
        "고개를 좌우로 30도 이상 돌리지 마시게.",
        "두 눈썹과 두 입꼬리가 모두 보이도록 하시게.",
    ],
    "ERR_FACE_BLUR": [
        "두 손으로 단단히 잡고 한 박자 멈춘 뒤 누르시게.",
        "초점이 자네 눈에 맞도록 화면을 한 번 두드리시게.",
        "어두운 자리에서 손이 떨리면 결이 흐려지네.",
    ],
}

_RETRY_TIPS_BY_CODE_EN = {
    "ERR_FACE_NOT_DETECTED": [
        "Hold the camera 30–50 cm (12–20 in) from your face.",
        "Try again in daylight or under a desk lamp.",
        "On a selfie camera, look at the top-center of the screen.",
    ],
    "ERR_FACE_BACKLIT": [
        "Face the light source instead of having it behind you.",
        "Aim for even lighting that makes your face clearly visible.",
        "Enabling HDR on your phone usually helps.",
    ],
    "ERR_FACE_OCCLUDED": [
        "Remove masks, sunglasses, and hats.",
        "If bangs cover your forehead, sweep them aside — the forehead matters for the reading.",
        "Keep your hands away from your face.",
    ],
    "ERR_FACE_PROFILE": [
        "Point the tip of your nose toward the camera center.",
        "Avoid turning your head more than 30° to either side.",
        "Make sure both eyebrows and both corners of your mouth are visible.",
    ],
    "ERR_FACE_BLUR": [
        "Hold the device with both hands and pause briefly before tapping.",
        "Tap the screen on your eyes to set focus.",
        "Shaky hands in low light produce blurry photos.",
    ],
}

_RETRY_TIPS_BY_CODE_JA = {
    "ERR_FACE_NOT_DETECTED": [
        "カメラと顔の距離は30〜50cmが目安です。",
        "日中、または机のライトの下で撮り直してください。",
        "インカメラなら画面上部中央を見てください。",
    ],
    "ERR_FACE_BACKLIT": [
        "窓や照明を背にせず、光と向き合ってください。",
        "顔がはっきり明るく写る程度の光量が理想です。",
        "スマホのHDR機能をオンにすると効果的です。",
    ],
    "ERR_FACE_OCCLUDED": [
        "マスク・サングラス・帽子を一度外してください。",
        "前髪で額が大きく隠れる場合は少し横に流してください — 額も判読の一部です。",
        "顔を手で覆わないでください。",
    ],
    "ERR_FACE_PROFILE": [
        "鼻先がカメラの中央を向くようにしてください。",
        "左右に30度以上首を回さないでください。",
        "両眉と口角が両方写るようにしてください。",
    ],
    "ERR_FACE_BLUR": [
        "両手でしっかり構え、ひと呼吸おいてから撮影してください。",
        "目に焦点が合うよう画面を一度タップしてください。",
        "暗い場所では手ブレで写真がぼやけます。",
    ],
}

_RETRY_TIPS_BY_CODE_ZH = {
    "ERR_FACE_NOT_DETECTED": [
        "镜头与脸的距离保持在30~50厘米。",
        "请在白天或台灯下重拍。",
        "使用前置摄像头时,请看屏幕上方中央。",
    ],
    "ERR_FACE_BACKLIT": [
        "请正对光源,不要背对窗户或灯具。",
        "光线足以让面部清晰可见即可。",
        "开启手机的HDR模式通常会有帮助。",
    ],
    "ERR_FACE_OCCLUDED": [
        "请暂时摘下口罩、墨镜、帽子。",
        "刘海若大面积遮住额头,请轻轻拨开 — 额头也是相貌判读的一部分。",
        "请勿用手遮挡脸部。",
    ],
    "ERR_FACE_PROFILE": [
        "请将鼻尖对准镜头中央。",
        "左右转头不要超过30度。",
        "请保证两侧眉毛和两侧嘴角都在画面内。",
    ],
    "ERR_FACE_BLUR": [
        "双手稳握设备,停顿片刻再按下快门。",
        "可在屏幕上点击眼睛位置以对焦。",
        "光线不足时手抖会导致照片模糊。",
    ],
}

_RETRY_TIPS_BY_LANG = {
    "ko": _RETRY_TIPS_BY_CODE_KO,
    "en": _RETRY_TIPS_BY_CODE_EN,
    "ja": _RETRY_TIPS_BY_CODE_JA,
    "zh": _RETRY_TIPS_BY_CODE_ZH,
}


# ─────────────────────────── Public API ───────────────────────────

def get_photo_checklist(lang: str = "ko") -> list[str]:
    """촬영 전 체크리스트 — 4언어 지원. 미지원 언어는 영어로 대체."""
    return _CHECKLISTS_BY_LANG.get(lang, PHOTO_CHECKLIST_EN)


def get_error_hint(error_code: str, lang: str = "ko") -> str:
    """에러코드별 1~2문장 안내. 코드 미상 시 빈 문자열, 미지원 언어는 영어."""
    table = _HINTS_BY_LANG.get(lang, _HINTS_EN)
    return table.get(error_code, "")


def get_retry_tips(error_code: str, lang: str = "ko") -> list[str]:
    """같은 에러 반복 시 노출할 단계별 팁. 해당 코드 팁이 없으면 빈 리스트."""
    table = _RETRY_TIPS_BY_LANG.get(lang, _RETRY_TIPS_BY_CODE_EN)
    return list(table.get(error_code, []))


def build_photo_guidance(
    error_code: str | None,
    lang: str = "ko",
    *,
    retry_count: int = 0,
) -> dict[str, Any]:
    """ERR_FACE_*/WARN_FACE_* 발생 시 응답에 첨부할 사용자 가이드 payload.

    Args:
        error_code: §7.2.1 에러코드. None이면 빈 가이드(checklist만).
        lang: ko/en/ja/zh (BCP-47 단순화).
        retry_count: 같은 사용자의 동일 코드 반복 횟수.
                     >=1이면 retry_tips를 포함.

    Returns:
        {
            "lang": "ko",
            "checklist": [...],         # 5개 사전 체크리스트
            "error_code": "ERR_...",    # None이면 키 자체 없음
            "hint": "허허, ...",        # 한 줄 안내 (error_code가 있을 때만)
            "retry_tips": [...],        # retry_count>=1 일 때만, 단계별 팁
        }
    """
    norm_lang = lang if lang in _CHECKLISTS_BY_LANG else "en"
    payload: dict[str, Any] = {
        "lang": norm_lang,
        "checklist": get_photo_checklist(norm_lang),
    }
    if error_code:
        payload["error_code"] = error_code
        hint = get_error_hint(error_code, norm_lang)
        if hint:
            payload["hint"] = hint
        if retry_count >= 1:
            tips = get_retry_tips(error_code, norm_lang)
            if tips:
                payload["retry_tips"] = tips
    return payload
