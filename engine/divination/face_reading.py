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
    build_photo_guidance,
    inject_emotion_disclosure,
    get_disclosure_metadata,
    detect_jailbreak,
    build_jailbreak_response,
)


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "face_reading_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600
_MAX_TOKENS = 3000

# 운영 표준 §7.2.1 — 사진 불량 9종 에러코드.
# 클라이언트 안내·서버 로그·운영 대시보드 집계의 단일 식별자.
# 명명 규약: ERR_FACE_<CASE> (전체 거부) / WARN_FACE_<CASE> (경고만, 풀이 정상 산출)
ERR_FACE_NOT_DETECTED = "ERR_FACE_NOT_DETECTED"   # 얼굴 미감지
ERR_FACE_MULTIPLE = "ERR_FACE_MULTIPLE"           # 다중 얼굴
ERR_FACE_NON_HUMAN = "ERR_FACE_NON_HUMAN"         # 사람 아님(반려동물·캐릭터)
ERR_FACE_BLUR = "ERR_FACE_BLUR"                   # 강한 흐림
ERR_FACE_PROFILE = "ERR_FACE_PROFILE"             # 강한 측면 (yaw>40°)
ERR_FACE_BACKLIT = "ERR_FACE_BACKLIT"             # 강한 역광/저조도
ERR_FACE_OCCLUDED = "ERR_FACE_OCCLUDED"           # 마스크·선글라스 가림
WARN_FACE_FILTERED = "WARN_FACE_FILTERED"         # 강한 메이크업/필터 (감지 불가, 사후 안내만)
WARN_FACE_FLAT = "WARN_FACE_FLAT"                 # 평면 사진 (스크린 촬영 의심)

# 한 줄 안내 — 사극풍 어조 일관 (운영 표준 §7.2.1 사용자 안내 열)
_ERR_HINTS_KO = {
    ERR_FACE_NOT_DETECTED: "허허, 상이 잘 잡히지 않는구먼. 빛 좋은 곳에서 정면으로 한 번 더 부탁하이.",
    ERR_FACE_MULTIPLE: "허허, 그대 한 분의 상만 담아 보내시게.",
    ERR_FACE_NON_HUMAN: "허허, 사람의 상으로만 풀이를 짚네.",
    ERR_FACE_BLUR: "허허, 결이 흐려 짚지 못하네. 빛 좋은 곳에서 정면으로 다시 담아주시게.",
    ERR_FACE_PROFILE: "허허, 옆모습은 한 자리만 보이네. 정면 한 장 더 부탁하이.",
    ERR_FACE_BACKLIT: "허허, 기색은 흐려 짚지 못하네. 빛을 등지지 마시게.",
    ERR_FACE_OCCLUDED: "허허, 가린 자리는 자네에게 묻네. 가리개를 풀고 한 장 더 부탁하이.",
}


def classify_metric_issue(metrics: dict[str, Any] | None) -> str | None:
    """메트릭에서 §7.2.1 사진 불량을 분류. 정상이면 None, 불량이면 에러코드 반환.

    클라이언트 가드가 통과한 경우라도 메트릭 자체가 불량이면 백엔드도 거부.
    분류 우선순위(엄격도 순):
      1) face_count == 0 → ERR_FACE_NOT_DETECTED
      2) face_count >= 2 → ERR_FACE_MULTIPLE
      3) blendshapes 합 0 근접 → ERR_FACE_NON_HUMAN
      4) head_tilt_deg > 40° → ERR_FACE_PROFILE
      5) brightness < 0.10 → ERR_FACE_BACKLIT (역광/저조도)
      6) z_variance < 0.0001 → WARN_FACE_FLAT (경고만, 풀이는 진행)
    """
    if not isinstance(metrics, dict) or not metrics:
        return None
    fc = metrics.get("face_count")
    if isinstance(fc, int):
        if fc == 0:
            return ERR_FACE_NOT_DETECTED
        if fc >= 2:
            return ERR_FACE_MULTIPLE
    bs = metrics.get("blendshapes")
    if isinstance(bs, dict):
        total = sum(v for v in bs.values() if isinstance(v, (int, float)))
        if total == 0 and any(isinstance(v, (int, float)) for v in bs.values()):
            # blendshape 키는 있는데 모두 0 → 사람 얼굴이 아닐 가능성
            return ERR_FACE_NON_HUMAN
    tilt = metrics.get("head_tilt_deg")
    if isinstance(tilt, (int, float)) and abs(tilt) > 40:
        return ERR_FACE_PROFILE
    br = metrics.get("brightness")
    if isinstance(br, (int, float)) and br < 0.10:
        return ERR_FACE_BACKLIT
    zv = metrics.get("z_variance")
    if isinstance(zv, (int, float)) and 0 < zv < 0.0001:
        return WARN_FACE_FLAT
    return None


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


# 운영표준 §7.2.8 — _FACE_SYSTEM 변경 시 캐시 자동 무효화.
# 시스템 프롬프트 SHA256 앞 8자를 캐시 키 prefix로 포함.
# 프롬프트 1글자만 바뀌어도 prefix가 달라지므로 기존 캐시 hit 안 됨.
_SYSTEM_PROMPT_HASH = hashlib.sha256(_FACE_SYSTEM.encode("utf-8")).hexdigest()[:8]


def _hash_payload(
    image_b64: str,
    age: int | None,
    gender: str | None,
    question: str | None,
    metrics: dict[str, Any] | None = None,
) -> str:
    """캐시 키 — 시스템 프롬프트 + 이미지 본문 + 보조 정보 + 메트릭."""
    h = hashlib.sha256()
    # §7.2.8 prefix — 프롬프트 해시 변경 시 전 캐시 자동 폴드아웃
    h.update(_SYSTEM_PROMPT_HASH.encode("ascii"))
    h.update(b"|")
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
        # 관상 고전 5등분(눈 1 : 미간 1 : 눈 1 …) 기준으로 분류
        if edr < 0.90:
            kind = "명궁이 좁다 — 집중력 강하나 답답할 수 있다"
        elif edr <= 1.10:
            kind = "명궁이 고르다 — 사유의 폭이 균형"
        else:
            kind = "명궁이 트였다 — 시야가 넓고 포용력 있다"
        out.append(f"  • 미간 폭 (한눈 길이 대비) — {edr:.2f} ({kind})")
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
        if asym < 0.010:
            qual = "거의 대칭 — 음양이 고르다"
        elif asym < 0.020:
            qual = "은은한 비대칭 — 자연스러운 결"
        else:
            qual = "또렷한 비대칭 — 한쪽 결이 더 두드러진다"
        out.append(f"  • 좌우 균형 편차 — {asym:.3f} ({qual})")
    cc = metrics.get("cheo_cheop_ratio")
    if isinstance(cc, (int, float)):
        if cc >= 0.30:
            ck = "처첩궁이 넓다 — 인연의 자리가 후하다"
        elif cc >= 0.22:
            ck = "처첩궁이 고르다"
        else:
            ck = "처첩궁이 좁다 — 인연의 자리가 단출하다"
        out.append(f"  • 처첩궁 폭 비율 — {cc:.2f} ({ck})")
    wj = metrics.get("wajam_ratio")
    if isinstance(wj, (int, float)):
        if wj >= 0.18:
            wk = "와잠이 도톰하다 — 자녀궁의 결이 두텁다"
        elif wj >= 0.12:
            wk = "와잠이 고르다"
        else:
            wk = "와잠이 옅다"
        out.append(f"  • 자녀궁(와잠) 비율 — {wj:.2f} ({wk})")

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

    # 신(神) — 눈빛의 활기 (운영표준 §5.5 "골상보다 신을 중히")
    shen = metrics.get("shen")
    if isinstance(shen, dict):
        kind = shen.get("kind")
        score = shen.get("shen_score")
        _shen_ko = {
            "bright": "신(神)이 맑고 또렷하다 — 눈빛에 활기가 있다",
            "steady": "신(神)이 단정하다 — 눈빛이 차분히 깃들어 있다",
            "flat": "신(神)이 평이하다",
            "dim": "신(神)이 옅다 — 안정·휴식이 필요한 결",
        }
        if kind and isinstance(score, (int, float)):
            out.append(f"  • 신(神) — {_shen_ko.get(kind, kind)} (점수 {score:.2f})")

    # 기색(氣色) — 부위별 색 분석 (운영표준 §5.5 + 심층분석 §2 황제내경)
    comp = metrics.get("complexion")
    if isinstance(comp, dict) and comp:
        # 황제내경 5색 → 사극풍 어휘
        _kind_ko = {
            "red": "붉은 결 (열의 기운)",
            "pale": "옅고 흰 결 (서늘한 기운)",
            "yellow": "노란 결 (소화·가래의 기운)",
            "green": "푸르스름한 결 (독·정체의 기운)",
            "dark": "어두운 결 (정체·피로의 기운)",
            "neutral": "단정한 결",
        }
        _region_ko = {
            "forehead": "이마(상정)",
            "cheek_l": "좌 뺨",
            "cheek_r": "우 뺨",
            "nose": "코",
            "chin": "턱(하정)",
        }
        notable = []
        for region, info in comp.items():
            if not isinstance(info, dict):
                continue
            kind = info.get("kind")
            if kind and kind != "neutral":
                notable.append(f"{_region_ko.get(region, region)}={_kind_ko.get(kind, kind)}")
        if notable:
            out.append("  • 기색(氣色) 단서 — " + " / ".join(notable))
        else:
            out.append("  • 기색(氣色) — 전체적으로 단정한 결")

    # 측정 신뢰도 가드 — 헤드 틸트가 크거나 얼굴이 가장자리에 있으면 LLM에 주의 표시
    quality_notes = []
    tilt = metrics.get("head_tilt_deg")
    if isinstance(tilt, (int, float)) and abs(tilt) > 10:
        quality_notes.append(f"고개가 {abs(tilt):.0f}° 기울어졌으나 좌표는 회전 보정됨")
    offset = metrics.get("face_center_offset")
    if isinstance(offset, (int, float)) and offset > 0.18:
        quality_notes.append("얼굴이 프레임 가장자리에 있어 광각 왜곡 가능성")
    zv = metrics.get("z_variance")
    if isinstance(zv, (int, float)) and 0 < zv < 0.0001:
        quality_notes.append("입체감이 옅음 — 평면 사진 가능성")
    br = metrics.get("brightness")
    if isinstance(br, (int, float)):
        if br < 0.20:
            quality_notes.append(f"조도가 낮음(~{br:.2f}) — 기색 판단 보수적으로")
        elif br > 0.85:
            quality_notes.append(f"조도가 과강(~{br:.2f}) — 역광/하이라이트 가능성")
    if quality_notes:
        out.append("  • 측정 신뢰도 단서 — " + "; ".join(quality_notes))

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


def build_openai_user_message(user_text: str, image_b64: str) -> dict[str, Any]:
    """신 명세서 §3.2 — 멀티모달 사용자 메시지 페이로드 (OpenAI/Bizrouter 호환).

    공식 구조:
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "<엔진 지표 + 화두>"},
          {"type": "image_url", "image_url": {"url": "data:image/...;base64,..."}}
        ]
      }

    별도 함수로 분리해 페이로드 골격을 회귀 테스트로 보호 (§5.1 단위 테스트).
    """
    mime, raw_b64 = _normalize_image_b64(image_b64)
    data_url = f"data:{mime};base64,{raw_b64}"
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }


def _call_vision(system_prompt: str, user_text: str, image_b64: str) -> str:
    """비전 LLM 호출 — Bizrouter(Gemini) 우선, Anthropic Claude fallback."""
    # raw_b64는 Anthropic fallback에서 직접 사용
    mime, raw_b64 = _normalize_image_b64(image_b64)

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
                build_openai_user_message(user_text, image_b64),  # type: ignore[list-item]
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


def _region_to_lang(region: str | None) -> str:
    """region 코드 → 면책 언어 자동 매핑 (§7.2.10).

    KR → ko, US-* → en, UK → en, EU → en (다국어 시장이지만 영문 기본), JP → ja, CN → zh.
    """
    if not region:
        return "ko"
    r = region.upper().strip()
    if r.startswith("KO") or r == "KR":
        return "ko"
    if r.startswith("JA") or r == "JP":
        return "ja"
    if r.startswith("ZH") or r == "CN":
        return "zh"
    if r.startswith("EN") or r in ("US-CA", "US-IL", "UK", "EU"):
        return "en"
    return "ko"


def generate_face_reading(
    image_b64: str,
    age: int | None = None,
    gender: str | None = None,
    question: str | None = None,
    metrics: dict[str, Any] | None = None,
    region: str | None = None,
    lang: str | None = None,
) -> dict[str, Any]:
    """운학 도사 관상 풀이.

    Args:
        image_b64: 사용자 얼굴 사진 (data URL 또는 raw base64).
        age, gender, question: 보조 정보.
        metrics: 클라이언트(MediaPipe Face Landmarker)에서 산출한 정량 메트릭.
            None이면 LLM이 사진만 보고 풀이. 있으면 객관적 수치를 함께 제공.
        region: 사용자 지역 코드 (BCP-47 또는 ISO). 위기 응답 시 지역별
            핫라인 라우팅에 사용. None이면 KR fallback.
        lang: 법적 면책 언어 ('ko'/'en'/'ja'/'zh'). None이면 region에서 자동 추출.
            §7.2.10 본문화 — 한국 외 사용자는 자국 면책 동봉.

    Returns:
        {
            "text": str,
            "cached": bool,
            "crisis_alert": dict | None,
            "legal_notice": str | None,
            "a11y": dict,
        }
    """
    # lang 미지정 시 region에서 자동 매핑
    resolved_lang = lang or _region_to_lang(region)

    # §7.2.3 — 화두 언어 감지 + 외국어 시 모국어 안내
    from engine.safety.language import detect_language, get_language_advisory
    detected_lang = detect_language(question or "")
    # 화두가 비어 있으면 advisory 불필요 (사용자가 외국어로 묻지도 않았으니)
    language_advisory = (
        get_language_advisory(detected_lang) if (question or "").strip() else None
    )

    # §7.3.4 — 요청 진입 시각 캡처 (각 반환 직전에 emit_face_reading_event 호출)
    from engine.safety.tracing import emit_face_reading_event, _now_ms
    _trace_started_at = _now_ms()
    _trace_base: dict[str, Any] = {
        "request_started_at_ms": _trace_started_at,
        "region": region,
        "lang": resolved_lang,
        "detected_language": detected_lang,
        "age": age,
        "gender": gender,
        "question": question,
        "metrics_keys": sorted(metrics.keys()) if isinstance(metrics, dict) else None,
    }

    # 0. §5.2.4 적대적 프롬프트(jailbreak) 사전 차단 — 위기 검사보다 우선.
    # 위기 신호가 함께 잡혀도 자해 방법 등 정보 요청은 jailbreak로 분류해 거절.
    jb_hits = detect_jailbreak(question or "")
    if jb_hits:
        jb_resp = build_jailbreak_response(jb_hits, lang=resolved_lang)
        jb_legal = build_legal_footer(is_crisis=False, lang=resolved_lang)
        jb_text = jb_resp["text"] + jb_legal
        emit_face_reading_event(
            event_type="jailbreak_blocked",
            error_code=jb_resp["primary_category"],
            text_length=len(jb_text),
            **_trace_base,
        )
        return {
            "text": jb_text,
            "cached": False,
            "crisis_alert": None,
            "legal_notice": jb_legal,
            "error_code": jb_resp["primary_category"],
            "jailbreak_categories": jb_resp["categories"],
            "a11y": _extract_a11y_metadata(jb_resp["text"], jb_legal),
            "detected_language": detected_lang,
            "language_advisory": language_advisory,
        }

    # 0.5 위기 신호 — 화두 본문 검사
    crisis = detect_crisis(question or "")
    if crisis["crisis_detected"]:
        crisis_legal = build_legal_footer(is_crisis=True, lang=resolved_lang)
        # §7.2.12 — 지역별 위기 자원 라우팅 (KR fallback 보장)
        from engine.safety.crisis_resources import (
            get_crisis_resources, format_hotlines_text,
        )
        regional_hotlines = get_crisis_resources(region)
        # 본문에 지역별 핫라인 자동 부착 (CRISIS_RESPONSE_KO는 현재 한국어 고정,
        # 향후 별도 모국어 위기 본문 본문화 시 함께 확장)
        crisis_text = (
            CRISIS_RESPONSE_KO + "\n\n" + format_hotlines_text(regional_hotlines)
            + crisis_legal
        )
        # §7.3.4 — 위기 차단 로깅
        emit_face_reading_event(
            event_type="crisis_blocked",
            crisis_detected=True,
            text_length=len(crisis_text),
            **_trace_base,
        )
        return {
            "text": crisis_text,
            "cached": False,
            "crisis_alert": {
                "severity": crisis["severity"],
                # KR 핫라인은 호환성 위해 유지, 지역별은 별도 키
                "hotlines": EMERGENCY_HOTLINES_KR,
                "regional_hotlines": [
                    {
                        "name_ko": h.name_ko,
                        "name_local": h.name_local,
                        "phone": h.phone,
                        "available_24h": h.available_24h,
                        "language": h.language,
                    }
                    for h in regional_hotlines
                ],
                "region": region or "KR",
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,
            # a11y는 지역별 핫라인이 부착된 새 본문 기준
            "a11y": _extract_a11y_metadata(
                CRISIS_RESPONSE_KO + "\n\n" + format_hotlines_text(regional_hotlines),
                crisis_legal,
            ),
            # §7.2.3 — 화두 언어 감지 + 외국어 안내
            "detected_language": detected_lang,
            "language_advisory": language_advisory,
        }

    if not (image_b64 or "").strip():
        raise ValueError("image_b64 is required")

    # 0.5 §7.2.1 사진 불량 분류 — 전체 거부 코드면 한 줄 안내 후 종료 (억지 풀이 금지)
    issue = classify_metric_issue(metrics)
    if issue and issue in _ERR_HINTS_KO:
        legal = build_legal_footer(is_crisis=False, lang=resolved_lang)
        # §7.3.4 — ERR 거부 로깅
        emit_face_reading_event(
            event_type="err_rejected",
            error_code=issue,
            text_length=len(_ERR_HINTS_KO[issue]),
            **_trace_base,
        )
        return {
            "text": _ERR_HINTS_KO[issue] + legal,
            "cached": False,
            "crisis_alert": None,
            "legal_notice": legal,
            "error_code": issue,
            "a11y": _extract_a11y_metadata(_ERR_HINTS_KO[issue], legal),
            "detected_language": detected_lang,
            "language_advisory": language_advisory,
            # §7.2.9 — 사진 가이드 첨부 (체크리스트 + 에러별 안내)
            "photo_guidance": build_photo_guidance(issue, resolved_lang),
        }
    # 경고만 (WARN_FACE_*) 인 경우는 풀이 정상 진행, 단 응답에 코드 노출
    warn_code = issue if issue and issue.startswith("WARN_") else None

    # 1. 캐시 — 같은 이미지+보조정보+메트릭 24h 재사용
    key = _hash_payload(image_b64, age, gender, question, metrics)
    cached = _load_cache(key)
    if cached is not None:
        cached.setdefault("crisis_alert", None)
        cached.setdefault("legal_notice", None)
        cached["text"] = cached.get("text", "") + ""
        # §7.3.4 — 캐시 히트 로깅
        emit_face_reading_event(
            event_type="cached_hit",
            cached=True,
            text_length=len(cached.get("text", "")),
            **_trace_base,
        )
        return cached

    # 2. LLM 호출
    user_text = _build_user_text(age, gender, question, metrics)
    text = _call_vision(_FACE_SYSTEM, user_text, image_b64)
    legal = build_legal_footer(is_crisis=False, lang=resolved_lang)
    # EU AI Act §50(3) — EU 지역일 때 감정 추론 명시 고지 자동 첨부
    body_with_legal = (text or "").strip() + legal
    full_text = inject_emotion_disclosure(body_with_legal, region=region, lang=resolved_lang)
    emotion_meta = get_disclosure_metadata(region, resolved_lang)

    out: dict[str, Any] = {
        "text": full_text,
        "cached": False,
        "crisis_alert": None,
        "legal_notice": legal,
        # §7.2.6 a11y — 스크린 리더·인지장애 어댑터를 위한 구조화 메타데이터
        "a11y": _extract_a11y_metadata(text or "", legal),
        # §7.2.3 — 화두 언어 감지 + 외국어 안내
        "detected_language": detected_lang,
        "language_advisory": language_advisory,
        # EU AI Act §50(3) — 감정 추론 명시 고지 메타데이터
        "emotion_disclosure": emotion_meta,
    }
    if warn_code:
        out["error_code"] = warn_code  # 풀이는 정상이나 경고 동봉 (WARN_FACE_*)
        # §7.2.9 — 경고도 사진 가이드 첨부 (다음 촬영 개선용)
        out["photo_guidance"] = build_photo_guidance(warn_code, resolved_lang)
    _save_cache(key, out)
    # §7.3.4 — LLM 호출 성공 로깅
    emit_face_reading_event(
        event_type="request_completed",
        error_code=warn_code,
        text_length=len(full_text),
        **_trace_base,
    )
    return out


def _extract_a11y_metadata(text: str, legal: str) -> dict[str, Any]:
    """운영표준 §7.2.6 — 접근성(a11y) 어댑터용 구조화 메타데이터.

    클라이언트가 스크린 리더·TTS·간결 요약 옵션을 만들 때 사용.
    풀이 본문을 단락별로 분리하고 각 길이·역할을 제공한다.

    출력:
      {
        "paragraph_count": int,
        "total_length": int,
        "has_greeting": bool,
        "has_closing": bool,
        "paragraphs": [{"length": int, "role": str}, ...]
        "legal_footer_length": int,
      }
    """
    body = (text or "").strip()
    # 빈 줄 기준 단락 분리 (운영표준 §6.4.1 단락별 길이 가이드 정합)
    raw_paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    paragraphs = []
    has_greeting = False
    has_closing = False
    for i, p in enumerate(raw_paragraphs):
        role = "body"
        if i == 0 and p.startswith("허허"):
            role = "greeting"
            has_greeting = True
        elif p.startswith("이 늙은이의 한 마디"):
            role = "closing"
            has_closing = True
        paragraphs.append({"length": len(p), "role": role})
    return {
        "paragraph_count": len(paragraphs),
        "total_length": len(body),
        "has_greeting": has_greeting,
        "has_closing": has_closing,
        "paragraphs": paragraphs,
        "legal_footer_length": len(legal or ""),
    }
