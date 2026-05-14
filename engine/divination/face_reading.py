"""관상(觀相) — 운학 도사 페르소나 얼굴 풀이 에이전트.

흐름:
  1. 입력: 사용자 얼굴 사진(base64) + 보조 정보(나이/성별/질문)
  2. 운학 도사 시스템 프롬프트 + 멀티모달 메시지로 Gemini Vision 호출
  3. 결과 캐시 (이미지 hash + 보조정보 24h)

비전 입력은 OpenAI 호환 messages 의 content 배열을 사용한다.
Bizrouter(Gemini) 가 우선이며, 키 없으면 Anthropic Claude fallback.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.safety import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
    build_legal_footer,
)


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600
_MAX_TOKENS = 3000


_FACE_SYSTEM = (
    '당신은 "운학 도사(雲鶴道士)"입니다. 60대 후반에서 70대 초반의 한국 사극 속 인물로, '
    "구름과 학을 벗삼아 산중에서 수십 년간 관상학(觀相學)을 닦아온 노도사입니다.\n\n"
    "[페르소나 규칙 — 절대 준수]\n"
    "  • 친근한 어른의 반말체와 존중체의 중간 톤. 어미: \"~시게\", \"~하시게나\", \"~인고\", "
    "\"~이로구먼\", \"~이로세\". 사용자를 \"그대\" 또는 \"자네\"라 부른다.\n"
    "  • 습관어: \"허허\", \"이 늙은이가\", \"자, 보시게\".\n"
    "  • 본인을 '운학 도사' 또는 '이 늙은이'라 칭함. AI/모델/시스템 같은 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — \"~될 것이로세\" 같은 단언 X. 대신 \"~한 결이 보이는구먼\", "
    "\"~의 기운이 흐르는 듯하이\" 같은 경향성 표현.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수 같은 어휘 X).\n"
    "  • 외모 평가·미추 비교 금지 — 관상은 '상(相)'을 보는 것이지 미추를 따지는 것이 아님.\n"
    "  • 의료·법률·투자 자문 거절, '의원·전문가에게 물으시게'로 우회.\n"
    "  • 인종·민족 특질 일반화 금지. 그대 한 사람의 상에만 집중.\n\n"
    "[관상 풀이의 결 — 이 늙은이가 평생 짚어온 자리들]\n"
    "  ◇ 삼정(三停) — 얼굴을 위·가운데·아래로 나누어 인생 흐름을 본다:\n"
    "     • 상정(上停, 발제~눈썹) — 초년운, 부모복, 두뇌와 학문, 기획력. 넓고 환하면 지혜롭고, 좁고 어두우면 초년에 고생.\n"
    "     • 중정(中停, 눈썹~코끝) — 중년운, 기개, 직업적 성취, 의지력. 콧대가 곧고 광대가 든든하면 중년에 일어선다.\n"
    "     • 하정(下停, 인중~턱) — 말년운, 자녀운, 인덕, 주거 안정. 턱이 후하고 입이 단정하면 말년이 평안하다.\n"
    "     세 영역이 1:1:1로 균형 잡힌 것이 상격(上格), 한 자리만 두드러져도 그 시기에 빛난다.\n\n"
    "  ◇ 오관(五官) — 다섯 벼슬자리:\n"
    "     • 채청관(採聽官, 귀) — 듣는 자리. 두툼하고 윤기 있으면 명(命)이 길고 복이 두텁다.\n"
    "     • 보수관(保壽官, 눈썹) — 수명·형제·감정. 짙고 맑게 흐르면 형제·동료 운이 좋다.\n"
    "     • 감찰관(監察官, 눈) — 마음의 창. 신(神)이 맑으면 지혜롭고 신이 흐리면 마음이 무겁다.\n"
    "     • 심변관(審辨官, 코) — 자존과 재물. 콧대(연상·수상)가 곧고 콧방울(난대·정위)이 두툼하면 중년 재백(財帛)이 후하다.\n"
    "     • 출납관(出納官, 입) — 말과 복록. 입꼬리가 위로 향하면 인덕이 따르고, 입술이 두툼하면 정이 깊다.\n\n"
    "  ◇ 십이궁(十二宮) — 안면 열두 자리, 각각 인생의 한 결을 맡는다:\n"
    "     • 명궁(命宮, 미간) — 평생 운의 본자리. 환하고 넓으면 형통, 흐리고 좁으면 막힘.\n"
    "     • 관록궁(官祿宮, 이마 중앙) — 직업·명예·관운. 둥글고 평평하면 사회적 자리가 든든하다.\n"
    "     • 재백궁(財帛宮, 코 전체) — 재물의 그릇. 콧대가 굽지 않고 콧방울이 살집 있으면 재물이 모인다.\n"
    "     • 전택궁(田宅宮, 눈과 윗눈꺼풀) — 유산·부동산. 넓고 깨끗하면 주거가 안정된다.\n"
    "     • 형제궁(兄弟宮, 눈썹) — 형제·동료·사회관계. 눈썹 결이 고르고 맑으면 사람 복이 있다.\n"
    "     • 노복궁(奴僕宮, 턱 양옆) — 아랫사람·후배 운. 두툼하면 따르는 이가 많다.\n"
    "     • 처첩궁(妻妾宮, 눈꼬리 옆 어미) — 배우자·연애. 매끈하면 부부 화목, 주름·점 많으면 풍파.\n"
    "     • 자녀궁(子女宮, 눈 아래 와잠) — 자녀운·생식력. 도톰하면 자녀복이 있다.\n"
    "     • 질액궁(疾厄宮, 코 위 산근) — 건강과 시련. 끊기지 않고 곧으면 큰 병이 없다.\n"
    "     • 천이궁(遷移宮, 이마 양옆 역마) — 이동·해외·변화. 넓고 환하면 활동 영역이 크다.\n"
    "     • 복덕궁(福德宮, 이마 양옆 위쪽) — 타고난 복과 정신. 넓고 윤기 있으면 마음이 후하다.\n"
    "     • 부모궁(父母宮, 이마 위쪽 양변, 일각·월각) — 부모와의 인연. 두툼하고 환하면 부모복이 두텁다.\n\n"
    "  ◇ 오형(五形) 체질 — 골격이 말해주는 본바탕:\n"
    "     • 영양질(원형) — 살집이 둥글어 인덕·재물·화합에 능하다.\n"
    "     • 근골질(각진형) — 광대·턱이 굳세어 실천력·체력·뚝심이 강하다.\n"
    "     • 심성질(역삼각·이마가 가장 넓음) — 두뇌가 명석하고 기획·연구에 적합하나 예민하다.\n"
    "     • 지력질(상정 발달) — 학문·사색·정신노동의 자리.\n"
    "     • 체력질(하정 발달) — 실무·생업·생활력의 자리.\n\n"
    "  ◇ 기색(氣色)과 신(神):\n"
    "     • 기색 — 안색의 윤기와 화기. 환하고 윤택하면 운기가 좋고, 어둡고 거칠면 막힘이 있다.\n"
    "     • 신(神) — 눈빛의 활기. 신이 살아있으면 어떤 골상이든 결국 길로 향한다. 골상보다 신을 더 중히 본다.\n\n"
    "위 용어를 그대로 답에 늘어놓듯 쓰지 말고, 사극풍 자연 문장 속에 한두 마디만 자연스럽게 녹이게.\n"
    "예: \"산근(山根)이 곧고 흐트러짐이 없으니 ~한 결이 보이는구먼\", "
    "\"콧방울에 살집이 도타워 중년 재백의 자리가 든든하이\". 한 풀이당 전문 어휘는 3~5개 이내로.\n\n"
    "[작성 형식]\n"
    "  • 첫 문장: \"허허\"로 시작하는 인사 한 마디.\n"
    "  • 본문: 다음 다섯 자리를 자연스러운 흐름으로 풀어낸다 (각 한 단락):\n"
    "    1) 전체 인상과 기색 — 첫눈에 보이는 상의 결\n"
    "    2) 상정(이마) — 초년의 지혜와 학문의 자리\n"
    "    3) 중정(눈썹·눈·코) — 중년의 기개와 의지\n"
    "    4) 하정(입·턱) — 말년의 복록과 인덕\n"
    "    5) 그대만의 한 가지 — 가장 또렷한 특징 하나를 짚어 격려\n"
    "  • 마무리 한 줄: \"이 늙은이의 한 마디 — …\" 형식으로 그대에게 권하는 한 걸음.\n"
    "  • 800~1300자, 마크다운 없이 자연 문장. 사극풍 어조 일관 유지.\n\n"
    "[안전·태도]\n"
    "  • 사진이 너무 흐리거나, 얼굴이 보이지 않거나, 사람의 얼굴이 아닌 경우: "
    "\"허허, 이 늙은이의 눈에는 그대의 상이 잘 잡히지 않는구먼. 빛 좋은 곳에서 "
    "정면으로 한 번 더 담아 보시게나.\" 라고 한 줄로 답하고 끝낸다. 억지로 풀이하지 말 것.\n"
    "  • 미성년으로 보이는 경우: 어른스러운 격려와 학문의 자리(상정) 위주로 짧게.\n"
    "  • 어떤 경우에도 외모 점수·등급·평가를 매기지 말 것."
)


def _hash_payload(
    image_b64: str,
    age: int | None,
    gender: str | None,
    question: str | None,
    metrics: dict[str, Any] | None = None,
) -> str:
    """캐시 키 — 이미지 본문 + 보조 정보 + 메트릭."""
    h = hashlib.sha256()
    h.update(image_b64.encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update(str(age or "").encode())
    h.update(b"|")
    h.update((gender or "").encode())
    h.update(b"|")
    h.update((question or "").strip().encode("utf-8", errors="ignore"))
    if metrics:
        # 메트릭을 결정론적으로 직렬화 — 키 순서 고정
        h.update(b"|")
        h.update(json.dumps(metrics, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return h.hexdigest()[:24]


def _load_cache(key: str) -> dict[str, Any] | None:
    f = _CACHE_DIR / f"{key}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if time.time() - float(data.get("_ts", 0)) > _TTL_SEC:
            return None
        data["cached"] = True
        return data
    except Exception:
        return None


def _save_cache(key: str, data: dict[str, Any]) -> None:
    try:
        payload = {**data, "_ts": time.time()}
        (_CACHE_DIR / f"{key}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def _format_metrics_block(metrics: dict[str, Any] | None) -> list[str]:
    """클라이언트에서 MediaPipe Face Landmarker로 산출한 메트릭을 사극풍 안내 문장으로 변환.

    metrics 스키마(클라이언트 generate):
      {
        "three_thirds": [상정%, 중정%, 하정%],     # 합 100
        "alar_ratio": float,                        # 콧방울 너비 / 얼굴 너비
        "philtrum_to_chin_ratio": float,
        "mouth_corner_lift": float,                 # -1.0(처짐) ~ +1.0(올라감)
        "eye_distance_ratio": float,                # 미간 / 한눈 너비
        "face_shape": "round|square|inverted_tri|oval|long",
        "blendshapes": {
            "jaw_open": float, "mouth_smile": float,
            "brow_inner_up": float, "eye_blink": float
        },
        "head_tilt_deg": float,                     # 머리 기울기 (정규화 전)
        "asymmetry": float,                         # 좌우 거리 표준편차
        "z_variance": float                         # 라이브니스 단서 (평면 사진은 낮음)
      }
    """
    if not isinstance(metrics, dict) or not metrics:
        return []

    out = ["", "[그대의 상에서 측정된 자취 — 이 늙은이의 안목을 거든 수치라네]"]
    tt = metrics.get("three_thirds")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        out.append(
            f"  • 삼정 비율 (상:중:하) — {tt[0]:.0f}% : {tt[1]:.0f}% : {tt[2]:.0f}%"
        )
    alar = metrics.get("alar_ratio")
    if isinstance(alar, (int, float)):
        kind = "도탑다" if alar >= 0.34 else ("아담하다" if alar <= 0.28 else "고르다")
        out.append(f"  • 콧방울 너비 비율 — 약 {alar:.2f} ({kind})")
    mcl = metrics.get("mouth_corner_lift")
    if isinstance(mcl, (int, float)):
        if mcl >= 0.05:
            kind = "올라간 상"
        elif mcl <= -0.05:
            kind = "처진 상"
        else:
            kind = "단정한 상"
        out.append(f"  • 입꼬리 — {mcl:+.2f} ({kind})")
    edr = metrics.get("eye_distance_ratio")
    if isinstance(edr, (int, float)):
        out.append(f"  • 미간 폭 (한눈 길이 대비) — {edr:.2f}")
    fs = metrics.get("face_shape")
    if isinstance(fs, str) and fs:
        ko = {
            "round": "원형(영양질 경향)",
            "square": "각진형(근골질 경향)",
            "inverted_tri": "역삼각(심성질 경향)",
            "oval": "계란형",
            "long": "긴 얼굴(지력질 경향)",
        }.get(fs, fs)
        out.append(f"  • 얼굴형 결 — {ko}")
    asym = metrics.get("asymmetry")
    if isinstance(asym, (int, float)):
        out.append(f"  • 좌우 균형 편차 — {asym:.3f} (0에 가까울수록 균형)")

    bs = metrics.get("blendshapes")
    if isinstance(bs, dict):
        flags = []
        if isinstance(bs.get("jaw_open"), (int, float)) and bs["jaw_open"] >= 0.15:
            flags.append("입이 살짝 벌어진 상태")
        if isinstance(bs.get("mouth_smile"), (int, float)) and bs["mouth_smile"] >= 0.15:
            flags.append("미소 띤 상태")
        if isinstance(bs.get("brow_inner_up"), (int, float)) and bs["brow_inner_up"] >= 0.15:
            flags.append("눈썹이 올라간 상태")
        if flags:
            out.append("  • 표정 단서 — " + ", ".join(flags) + " (기본 상에 약간의 변형 있음)")

    out.append("")
    out.append(
        "위 수치는 객관적 측정치이니, 사진의 결(피부·눈빛·기색)과 함께 종합해 "
        "한두 군데만 자연스럽게 풀이에 녹여주시게. 수치를 그대로 나열하지는 말 것."
    )
    return out


def _build_user_text(
    age: int | None,
    gender: str | None,
    question: str | None,
    metrics: dict[str, Any] | None = None,
) -> str:
    """이미지와 함께 보낼 텍스트 부분."""
    lines = ["[그대의 정보]"]
    if age is not None:
        lines.append(f"  • 나이: 약 {age}세")
    if gender:
        lines.append(f"  • 성별: {gender}")
    q = (question or "").strip()
    lines.append(f"  • 화두: {q if q else '(특별한 화두 없이 전체 상을 봐주십시오)'}")

    lines.extend(_format_metrics_block(metrics))

    lines.append("")
    lines.append(
        "위 사진을 보고 운학 도사의 어조로 관상 풀이를 해주시게나. "
        "전체 인상 → 상정(이마) → 중정(눈·코) → 하정(입·턱) → 그대만의 한 가지 → 한 마디 권유 의 "
        "흐름으로 자연스럽게 풀어주시게."
    )
    return "\n".join(lines)


def _normalize_image_b64(image_b64: str) -> tuple[str, str]:
    """`data:image/...;base64,...` 또는 raw base64 → (mime, raw_base64)."""
    s = (image_b64 or "").strip()
    if s.startswith("data:") and "," in s:
        header, body = s.split(",", 1)
        mime = "image/jpeg"
        if ";" in header:
            mime_part = header.split(";", 1)[0]
            if mime_part.startswith("data:"):
                mime = mime_part[len("data:") :] or "image/jpeg"
        return mime, body
    return "image/jpeg", s


@lru_cache(maxsize=1)
def _bizrouter_client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get(
            "BIZROUTER_BASE_URL", "https://api.bizrouter.ai/v1"
        ),
    )


@lru_cache(maxsize=1)
def _anthropic_client():
    from anthropic import Anthropic

    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _bizrouter_enabled() -> bool:
    return bool((os.environ.get("BIZROUTER_API_KEY") or "").strip())


def _call_vision(system_prompt: str, user_text: str, image_b64: str) -> str:
    """비전 LLM 호출 — Bizrouter(Gemini) 우선, Anthropic Claude fallback."""
    mime, raw_b64 = _normalize_image_b64(image_b64)
    data_url = f"data:{mime};base64,{raw_b64}"

    if _bizrouter_enabled():
        client = _bizrouter_client()
        # Gemini 비전 모델 — Image generation 모델(flash-image)이 아닌
        # 일반 멀티모달 모델 사용. 환경변수로 오버라이드 가능.
        model = (
            os.environ.get("BIZROUTER_VISION_MODEL")
            or os.environ.get("BIZROUTER_MODEL")
            or "google/gemini-2.5-flash-lite"
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        if not resp.choices:
            raise ValueError("empty model response")
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("empty model response")
        return content

    # Anthropic fallback
    client = _anthropic_client()
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,  # type: ignore[typeddict-item]
                            "data": raw_b64,
                        },
                    },
                ],
            }
        ],
    )
    text = next(
        (
            getattr(b, "text", None)
            for b in msg.content
            if getattr(b, "type", "") == "text"
        ),
        None,
    )
    if not text:
        raise ValueError("empty model response")
    return text


def generate_face_reading(
    image_b64: str,
    age: int | None = None,
    gender: str | None = None,
    question: str | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """운학 도사 관상 풀이.

    Args:
        image_b64: 사용자 얼굴 사진 (data URL 또는 raw base64).
        age, gender, question: 보조 정보.
        metrics: 클라이언트(MediaPipe Face Landmarker)에서 산출한 정량 메트릭.
            None이면 LLM이 사진만 보고 풀이. 있으면 객관적 수치를 함께 제공.

    Returns:
        {
            "text": str,
            "cached": bool,
            "crisis_alert": dict | None,
            "legal_notice": str | None,
        }
    """
    # 0. 위기 신호 — 화두 본문 검사
    crisis = detect_crisis(question or "")
    if crisis["crisis_detected"]:
        return {
            "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
            "cached": False,
            "crisis_alert": {
                "severity": crisis["severity"],
                "hotlines": EMERGENCY_HOTLINES_KR,
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,
        }

    if not (image_b64 or "").strip():
        raise ValueError("image_b64 is required")

    # 1. 캐시 — 같은 이미지+보조정보+메트릭 24h 재사용
    key = _hash_payload(image_b64, age, gender, question, metrics)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached["text"] = cached.get("text", "") + ""
        return cached

    # 2. LLM 호출
    user_text = _build_user_text(age, gender, question, metrics)
    text = _call_vision(_FACE_SYSTEM, user_text, image_b64)
    legal = build_legal_footer(is_crisis=False)
    full_text = (text or "").strip() + legal

    out = {
        "text": full_text,
        "cached": False,
        "crisis_alert": None,
        "legal_notice": legal,
    }
    _save_cache(key, out)
    return out
