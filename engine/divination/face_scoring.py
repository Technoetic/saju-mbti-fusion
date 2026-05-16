"""키포인트 기반 12궁 점수 산출 — 결정론 해석 엔진.

MediaPipe Face Landmarker가 478 키포인트에서 산출한 정량 메트릭을 받아,
한국 관상학 12궁(十二宮) + 오관(五官) + 삼정(三停)의 각 자리별 점수(0.0~1.0)를
**LLM 없이** 산출한다.

목적:
  · 재현성    — 같은 사진은 항상 동일 점수
  · 검증성    — 응답 JSON에 정량 노출 (프론트 시각화 가능)
  · 모순 검출 — LLM 풀이가 점수와 충돌하면 폴백 트리거 (다음 Phase)

본 모듈은 LLM 의존도 0. 모든 임계값·매핑은 코드에 명시. 임계값은 관상학
문헌·운영표준 §5.5 + 본 시스템 시스템 프롬프트의 기존 어휘와 정합.

12궁 점수의 의미:
  0.0~0.3 — 약함/좁음/흐림 (해당 자리의 결이 두드러지지 않음)
  0.3~0.6 — 평이/고름 (보통)
  0.6~1.0 — 강함/넓음/환함 (해당 자리의 결이 또렷)

점수는 "좋다/나쁘다"가 아니라 "두드러짐의 정도". 외모 평가 X.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# 12궁 식별자
PALACE_MYEONG = "myeong"           # 명궁(命宮) — 미간
PALACE_GWANROK = "gwanrok"         # 관록궁(官祿宮) — 이마 중앙
PALACE_JAEBAEK = "jaebaek"         # 재백궁(財帛宮) — 코 전체
PALACE_JEONTAEK = "jeontaek"       # 전택궁(田宅宮) — 눈·윗눈꺼풀
PALACE_HYEONGJE = "hyeongje"       # 형제궁(兄弟宮) — 눈썹
PALACE_NOBOK = "nobok"             # 노복궁(奴僕宮) — 턱 양옆
PALACE_CHEOCHEOP = "cheocheop"     # 처첩궁(妻妾宮) — 눈꼬리(어미)
PALACE_JANYEO = "janyeo"           # 자녀궁(子女宮) — 와잠
PALACE_JILEK = "jilek"             # 질액궁(疾厄宮) — 산근
PALACE_CHEONI = "cheoni"           # 천이궁(遷移宮) — 이마 양옆
PALACE_BOKDEOK = "bokdeok"         # 복덕궁(福德宮) — 이마 양옆 위쪽
PALACE_BUMO = "bumo"               # 부모궁(父母宮) — 일각·월각

ALL_PALACES = (
    PALACE_MYEONG, PALACE_GWANROK, PALACE_JAEBAEK, PALACE_JEONTAEK,
    PALACE_HYEONGJE, PALACE_NOBOK, PALACE_CHEOCHEOP, PALACE_JANYEO,
    PALACE_JILEK, PALACE_CHEONI, PALACE_BOKDEOK, PALACE_BUMO,
)

# 삼정 식별자
SAMJEONG_UPPER = "sangjeong"       # 상정(上停) — 발제~눈썹
SAMJEONG_MIDDLE = "jungjeong"      # 중정(中停) — 눈썹~코끝
SAMJEONG_LOWER = "hajeong"         # 하정(下停) — 인중~턱

# 오관 식별자
GWAN_CHE = "chae_cheong"           # 채청관(귀)
GWAN_BO = "bo_su"                  # 보수관(눈썹)
GWAN_GAM = "gam_chal"              # 감찰관(눈)
GWAN_SIM = "sim_byeon"             # 심변관(코)
GWAN_CHUL = "chul_nap"             # 출납관(입)


@dataclass(frozen=True)
class PalaceScore:
    """단일 자리(궁/관/정)의 점수.

    Attributes:
        key: 식별자
        label_ko: 한국어 명칭
        score: 0.0~1.0 (두드러짐의 정도)
        label_short: "환하다" / "고르다" / "흐리다" 같은 1단어 라벨
        evidence: 점수 근거 메트릭 이름 + 값 (디버깅용)
    """
    key: str
    label_ko: str
    score: float
    label_short: str
    evidence: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FaceScoreReport:
    """전체 점수 리포트 — face_reading 응답 envelope에 첨부."""
    palaces: dict[str, PalaceScore]      # 12궁
    samjeong: dict[str, PalaceScore]     # 삼정 3자리
    ogwan: dict[str, PalaceScore]        # 오관 5자리
    shen_score: float                    # 신(神) 0.0~1.0
    qi_score: float                      # 기색(氣色) 0.0~1.0
    overall_balance: float               # 전체 균형(삼정 1:1:1 근접도)
    top_palace: str                      # 가장 두드러진 궁
    weakest_palace: str                  # 가장 옅은 궁
    metrics_used: list[str] = field(default_factory=list)


# ─────────────────────────── 임계값 ───────────────────────────

# 모든 임계값은 운영표준 §5.5 + face_reading.py 기존 임계와 정합.

def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _score_from_ratio(value: float, ideal: float, tolerance: float) -> float:
    """ideal 근처에서 1.0, 멀어질수록 0.0으로 감쇠 (선형)."""
    if not isinstance(value, (int, float)):
        return 0.5
    diff = abs(value - ideal)
    if diff >= tolerance:
        return 0.0
    return _clip(1.0 - diff / tolerance)


def _score_in_range(value: float, lo: float, hi: float) -> float:
    """[lo, hi] 사이면 1.0, 밖이면 거리에 따라 감쇠."""
    if not isinstance(value, (int, float)):
        return 0.5
    if lo <= value <= hi:
        return 1.0
    span = hi - lo
    if value < lo:
        return _clip(1.0 - (lo - value) / (span if span > 0 else 1.0))
    return _clip(1.0 - (value - hi) / (span if span > 0 else 1.0))


def _label_for_score(score: float) -> str:
    if score >= 0.75:
        return "환하다"
    if score >= 0.55:
        return "고르다"
    if score >= 0.35:
        return "은은하다"
    return "옅다"


# ─────────────────────────── 12궁 산출 ───────────────────────────

def _score_myeong(metrics: dict[str, Any]) -> PalaceScore:
    """명궁(미간) — eye_distance_ratio 1.0 근처가 이상적."""
    edr = metrics.get("eye_distance_ratio")
    score = _score_from_ratio(edr, ideal=1.00, tolerance=0.40) if isinstance(edr, (int, float)) else 0.5
    ev = {"eye_distance_ratio": float(edr)} if isinstance(edr, (int, float)) else {}
    return PalaceScore(
        key=PALACE_MYEONG, label_ko="명궁(命宮·미간)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_gwanrok(metrics: dict[str, Any]) -> PalaceScore:
    """관록궁(이마 중앙) — 상정 비율이 클수록 발달."""
    tt = metrics.get("three_thirds")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        upper = float(tt[0])
        score = _score_in_range(upper, 30.0, 38.0)
        ev = {"upper_third_pct": upper}
    else:
        score = 0.5
        ev = {}
    return PalaceScore(
        key=PALACE_GWANROK, label_ko="관록궁(官祿宮·이마)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_jaebaek(metrics: dict[str, Any]) -> PalaceScore:
    """재백궁(코 전체) — alar_ratio 0.28~0.36 + 중정 비율 1:1:1 균형."""
    alar = metrics.get("alar_ratio")
    tt = metrics.get("three_thirds")
    s_alar = _score_in_range(float(alar), 0.28, 0.36) if isinstance(alar, (int, float)) else 0.5
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        mid = float(tt[1])
        s_mid = _score_in_range(mid, 30.0, 38.0)
    else:
        s_mid = 0.5
    score = (s_alar + s_mid) / 2.0
    ev: dict[str, float] = {}
    if isinstance(alar, (int, float)):
        ev["alar_ratio"] = float(alar)
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        ev["middle_third_pct"] = float(tt[1])
    return PalaceScore(
        key=PALACE_JAEBAEK, label_ko="재백궁(財帛宮·코)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_jeontaek(metrics: dict[str, Any]) -> PalaceScore:
    """전택궁(눈) — 비대칭이 낮을수록 안정."""
    asym = metrics.get("asymmetry")
    if isinstance(asym, (int, float)):
        score = _clip(1.0 - float(asym) * 30.0)  # 0.033 이상은 0
        ev = {"asymmetry": float(asym)}
    else:
        score = 0.5
        ev = {}
    return PalaceScore(
        key=PALACE_JEONTAEK, label_ko="전택궁(田宅宮·눈)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_hyeongje(metrics: dict[str, Any]) -> PalaceScore:
    """형제궁(눈썹) — blendshape brow_inner_up이 자연스러우면(0.0~0.2) 결 고름."""
    bs = metrics.get("blendshapes")
    if isinstance(bs, dict):
        biu = bs.get("brow_inner_up")
        if isinstance(biu, (int, float)):
            # 너무 올라가지도 너무 처지지도 않은 자연 상태가 이상
            score = _score_from_ratio(float(biu), ideal=0.10, tolerance=0.30)
            ev = {"brow_inner_up": float(biu)}
        else:
            score = 0.5
            ev = {}
    else:
        score = 0.5
        ev = {}
    return PalaceScore(
        key=PALACE_HYEONGJE, label_ko="형제궁(兄弟宮·눈썹)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_nobok(metrics: dict[str, Any]) -> PalaceScore:
    """노복궁(턱 양옆) — 하정 비율이 충분하고 face_shape이 둥글/각진형이면 두툼."""
    tt = metrics.get("three_thirds")
    fs = metrics.get("face_shape")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        lower = float(tt[2])
        s_lower = _score_in_range(lower, 30.0, 38.0)
    else:
        s_lower = 0.5
    bonus = 0.1 if fs in ("round", "square", "oval") else 0.0
    score = _clip(s_lower + bonus)
    ev: dict[str, float] = {}
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        ev["lower_third_pct"] = float(tt[2])
    return PalaceScore(
        key=PALACE_NOBOK, label_ko="노복궁(奴僕宮·턱)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_cheocheop(metrics: dict[str, Any]) -> PalaceScore:
    """처첩궁(눈꼬리 어미) — cheo_cheop_ratio 직접 매핑."""
    cc = metrics.get("cheo_cheop_ratio")
    if isinstance(cc, (int, float)):
        # 0.22 미만은 좁고, 0.30 이상은 후함
        score = _clip((float(cc) - 0.16) / 0.20)
        ev = {"cheo_cheop_ratio": float(cc)}
    else:
        score = 0.5
        ev = {}
    return PalaceScore(
        key=PALACE_CHEOCHEOP, label_ko="처첩궁(妻妾宮·어미)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_janyeo(metrics: dict[str, Any]) -> PalaceScore:
    """자녀궁(와잠) — wajam_ratio 직접 매핑."""
    wj = metrics.get("wajam_ratio")
    if isinstance(wj, (int, float)):
        # 0.12 미만 옅고, 0.18 이상 도톰
        score = _clip((float(wj) - 0.08) / 0.14)
        ev = {"wajam_ratio": float(wj)}
    else:
        score = 0.5
        ev = {}
    return PalaceScore(
        key=PALACE_JANYEO, label_ko="자녀궁(子女宮·와잠)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_jilek(metrics: dict[str, Any]) -> PalaceScore:
    """질액궁(산근) — head_tilt이 작고 asymmetry가 낮으면 결 끊김 없음."""
    tilt = metrics.get("head_tilt_deg")
    asym = metrics.get("asymmetry")
    s_tilt = _clip(1.0 - abs(float(tilt)) / 40.0) if isinstance(tilt, (int, float)) else 0.5
    s_asym = _clip(1.0 - float(asym) * 30.0) if isinstance(asym, (int, float)) else 0.5
    score = (s_tilt + s_asym) / 2.0
    ev: dict[str, float] = {}
    if isinstance(tilt, (int, float)):
        ev["head_tilt_deg"] = float(tilt)
    if isinstance(asym, (int, float)):
        ev["asymmetry"] = float(asym)
    return PalaceScore(
        key=PALACE_JILEK, label_ko="질액궁(疾厄宮·산근)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_cheoni(metrics: dict[str, Any]) -> PalaceScore:
    """천이궁(이마 양옆 역마) — 상정 비율 + face_shape이 inverted_tri/long이면 발달."""
    tt = metrics.get("three_thirds")
    fs = metrics.get("face_shape")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        upper = float(tt[0])
        s_upper = _score_in_range(upper, 30.0, 38.0)
    else:
        s_upper = 0.5
    bonus = 0.15 if fs in ("inverted_tri", "long") else 0.0
    score = _clip(s_upper + bonus)
    ev: dict[str, float] = {}
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        ev["upper_third_pct"] = float(tt[0])
    return PalaceScore(
        key=PALACE_CHEONI, label_ko="천이궁(遷移宮·역마)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_bokdeok(metrics: dict[str, Any]) -> PalaceScore:
    """복덕궁(이마 양옆 위쪽) — 기색이 좋고 신이 살아있으면 마음 후함."""
    shen = metrics.get("shen")
    comp = metrics.get("complexion")
    s_shen = 0.5
    if isinstance(shen, dict):
        ss = shen.get("shen_score")
        if isinstance(ss, (int, float)):
            s_shen = _clip(float(ss))
    s_comp = 0.5
    if isinstance(comp, dict):
        # complexion이 "황(黃)" 또는 "백(白)" 윤기 위주면 좋음
        # 단순화: 가장 강한 색의 비율
        max_pct = 0.0
        for v in comp.values():
            if isinstance(v, dict) and isinstance(v.get("pct"), (int, float)):
                max_pct = max(max_pct, float(v["pct"]))
        s_comp = _clip(max_pct)
    score = (s_shen + s_comp) / 2.0
    ev: dict[str, float] = {"shen_score": s_shen, "comp_max": s_comp}
    return PalaceScore(
        key=PALACE_BOKDEOK, label_ko="복덕궁(福德宮)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


def _score_bumo(metrics: dict[str, Any]) -> PalaceScore:
    """부모궁(일각·월각) — 상정 비율 + 좌우 대칭이 좋으면 두텁다."""
    tt = metrics.get("three_thirds")
    asym = metrics.get("asymmetry")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        upper = float(tt[0])
        s_upper = _score_in_range(upper, 30.0, 38.0)
    else:
        s_upper = 0.5
    s_asym = _clip(1.0 - float(asym) * 30.0) if isinstance(asym, (int, float)) else 0.5
    score = (s_upper + s_asym) / 2.0
    ev: dict[str, float] = {}
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        ev["upper_third_pct"] = float(tt[0])
    if isinstance(asym, (int, float)):
        ev["asymmetry"] = float(asym)
    return PalaceScore(
        key=PALACE_BUMO, label_ko="부모궁(父母宮·일각·월각)",
        score=round(score, 3), label_short=_label_for_score(score),
        evidence=ev,
    )


# ─────────────────────────── 삼정·오관 산출 ───────────────────────────

def _score_samjeong(metrics: dict[str, Any]) -> dict[str, PalaceScore]:
    """삼정 3자리 + 1:1:1 균형 점수."""
    tt = metrics.get("three_thirds")
    if not (isinstance(tt, (list, tuple)) and len(tt) == 3):
        return {
            SAMJEONG_UPPER: PalaceScore(SAMJEONG_UPPER, "상정(上停·이마)", 0.5, "고르다"),
            SAMJEONG_MIDDLE: PalaceScore(SAMJEONG_MIDDLE, "중정(中停·눈썹~코)", 0.5, "고르다"),
            SAMJEONG_LOWER: PalaceScore(SAMJEONG_LOWER, "하정(下停·입~턱)", 0.5, "고르다"),
        }
    upper, mid, lower = float(tt[0]), float(tt[1]), float(tt[2])
    s_u = _score_in_range(upper, 30.0, 38.0)
    s_m = _score_in_range(mid, 30.0, 38.0)
    s_l = _score_in_range(lower, 30.0, 38.0)
    return {
        SAMJEONG_UPPER: PalaceScore(SAMJEONG_UPPER, "상정(上停·이마)",
                                    round(s_u, 3), _label_for_score(s_u),
                                    {"pct": upper}),
        SAMJEONG_MIDDLE: PalaceScore(SAMJEONG_MIDDLE, "중정(中停·눈썹~코)",
                                     round(s_m, 3), _label_for_score(s_m),
                                     {"pct": mid}),
        SAMJEONG_LOWER: PalaceScore(SAMJEONG_LOWER, "하정(下停·입~턱)",
                                    round(s_l, 3), _label_for_score(s_l),
                                    {"pct": lower}),
    }


def _score_ogwan(metrics: dict[str, Any]) -> dict[str, PalaceScore]:
    """오관 5자리."""
    bs = metrics.get("blendshapes") if isinstance(metrics.get("blendshapes"), dict) else {}
    # 채청관(귀) — 현 메트릭에서 직접 측정 X. 얼굴형으로 간접 추정.
    fs = metrics.get("face_shape")
    s_chae = 0.7 if fs in ("round", "oval") else 0.55
    # 보수관(눈썹)
    biu = bs.get("brow_inner_up") if isinstance(bs, dict) else None
    s_bo = _score_from_ratio(float(biu), 0.10, 0.30) if isinstance(biu, (int, float)) else 0.5
    # 감찰관(눈) — 신(神) 점수
    shen = metrics.get("shen")
    s_gam = 0.5
    if isinstance(shen, dict) and isinstance(shen.get("shen_score"), (int, float)):
        s_gam = _clip(float(shen["shen_score"]))
    # 심변관(코) — alar
    alar = metrics.get("alar_ratio")
    s_sim = _score_in_range(float(alar), 0.28, 0.36) if isinstance(alar, (int, float)) else 0.5
    # 출납관(입) — mouth_corner_lift
    mcl = metrics.get("mouth_corner_lift")
    if isinstance(mcl, (int, float)):
        # 0.0~0.15 입꼬리 올라감이 이상
        s_chul = _score_from_ratio(float(mcl), 0.07, 0.25)
    else:
        s_chul = 0.5
    return {
        GWAN_CHE: PalaceScore(GWAN_CHE, "채청관(귀)",
                              round(s_chae, 3), _label_for_score(s_chae)),
        GWAN_BO: PalaceScore(GWAN_BO, "보수관(눈썹)",
                             round(s_bo, 3), _label_for_score(s_bo)),
        GWAN_GAM: PalaceScore(GWAN_GAM, "감찰관(눈)",
                              round(s_gam, 3), _label_for_score(s_gam)),
        GWAN_SIM: PalaceScore(GWAN_SIM, "심변관(코)",
                              round(s_sim, 3), _label_for_score(s_sim)),
        GWAN_CHUL: PalaceScore(GWAN_CHUL, "출납관(입)",
                               round(s_chul, 3), _label_for_score(s_chul)),
    }


# ─────────────────────────── 통합 진입점 ───────────────────────────

def score_face(metrics: dict[str, Any] | None) -> FaceScoreReport:
    """메트릭 dict → FaceScoreReport. None/빈 dict면 0.5 균등 점수.

    Args:
        metrics: 클라이언트(MediaPipe)에서 산출한 정량 메트릭. _format_metrics_block
            스키마와 동일.

    Returns:
        FaceScoreReport — 12궁·삼정·오관 점수 + top/weakest + overall_balance.
    """
    metrics = metrics or {}

    palaces = {
        PALACE_MYEONG: _score_myeong(metrics),
        PALACE_GWANROK: _score_gwanrok(metrics),
        PALACE_JAEBAEK: _score_jaebaek(metrics),
        PALACE_JEONTAEK: _score_jeontaek(metrics),
        PALACE_HYEONGJE: _score_hyeongje(metrics),
        PALACE_NOBOK: _score_nobok(metrics),
        PALACE_CHEOCHEOP: _score_cheocheop(metrics),
        PALACE_JANYEO: _score_janyeo(metrics),
        PALACE_JILEK: _score_jilek(metrics),
        PALACE_CHEONI: _score_cheoni(metrics),
        PALACE_BOKDEOK: _score_bokdeok(metrics),
        PALACE_BUMO: _score_bumo(metrics),
    }
    samjeong = _score_samjeong(metrics)
    ogwan = _score_ogwan(metrics)

    # 신(神)
    shen_score = 0.5
    shen = metrics.get("shen")
    if isinstance(shen, dict) and isinstance(shen.get("shen_score"), (int, float)):
        shen_score = _clip(float(shen["shen_score"]))

    # 기색(氣色) — complexion 최댓값
    qi_score = 0.5
    comp = metrics.get("complexion")
    if isinstance(comp, dict) and comp:
        max_pct = 0.0
        for v in comp.values():
            if isinstance(v, dict) and isinstance(v.get("pct"), (int, float)):
                max_pct = max(max_pct, float(v["pct"]))
        qi_score = _clip(max_pct)

    # 전체 균형 — 삼정 1:1:1 근접도
    overall_balance = 0.5
    tt = metrics.get("three_thirds")
    if isinstance(tt, (list, tuple)) and len(tt) == 3:
        deviation = sum(abs(float(p) - 33.33) for p in tt) / 3.0
        overall_balance = _clip(1.0 - deviation / 20.0)

    # top / weakest 12궁
    sorted_palaces = sorted(palaces.items(), key=lambda kv: kv[1].score, reverse=True)
    top_palace = sorted_palaces[0][0]
    weakest_palace = sorted_palaces[-1][0]

    # 사용된 메트릭 목록 (디버깅용)
    metrics_used = sorted(set(metrics.keys()) - {"_internal"})

    return FaceScoreReport(
        palaces=palaces,
        samjeong=samjeong,
        ogwan=ogwan,
        shen_score=round(shen_score, 3),
        qi_score=round(qi_score, 3),
        overall_balance=round(overall_balance, 3),
        top_palace=top_palace,
        weakest_palace=weakest_palace,
        metrics_used=metrics_used,
    )


def report_to_dict(report: FaceScoreReport) -> dict[str, Any]:
    """FaceScoreReport → 응답 JSON 직렬화 가능 dict."""
    def _ps(p: PalaceScore) -> dict[str, Any]:
        return {
            "key": p.key,
            "label_ko": p.label_ko,
            "score": p.score,
            "label_short": p.label_short,
            "evidence": dict(p.evidence),
        }
    return {
        "palaces": {k: _ps(v) for k, v in report.palaces.items()},
        "samjeong": {k: _ps(v) for k, v in report.samjeong.items()},
        "ogwan": {k: _ps(v) for k, v in report.ogwan.items()},
        "shen_score": report.shen_score,
        "qi_score": report.qi_score,
        "overall_balance": report.overall_balance,
        "top_palace": report.top_palace,
        "weakest_palace": report.weakest_palace,
        "metrics_used": list(report.metrics_used),
    }
