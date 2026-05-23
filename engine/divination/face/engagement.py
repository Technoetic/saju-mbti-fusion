"""ADR-204+205+206 - 사용자 가치(재미) 향상 인프라.

ADR-204: 비교 묘사 (한국 평균/미인 표본과의 정량 비교)
ADR-205: prevalence 구체 묘사 (손금 형태 등 통계 베이스라인 묘사)
ADR-206: 공유 카드 메타데이터 (OpenGraph + JSON-LD)

ADR 정합:
  - ADR-006 자문 거절 (운명 단정 X — 통계 비교만)
  - ADR-010 사실성 분리 (학술 출처 명시 강제)
  - ADR-171 fate_assertion 사전 (모든 묘사 어휘 통과)
  - ADR-196 Miss Korea 3D photogrammetry (비교 표본)
  - ADR-178 화장품 베이스라인 (한국 평균 표본)
"""

from __future__ import annotations

from dataclasses import dataclass


# ───── ADR-204: 비교 묘사 ─────

# Miss Korea 표본 (ADR-196) — 미인 비교용
_MK_REFERENCE = {
    "face_width_mm": 95.7,
    "face_height_mm": 186.0,
    "alar_ratio": 0.379,
    "eye_fissure_mm": 26.78,  # Miss Korea 평균 (ADR-202)
}

# 일반 한국 여성 표본 (KCI/PMC 종합)
_GP_REFERENCE = {
    "alar_ratio": 0.32,        # ADR-179 scoring.py 기준
    "eye_fissure_mm": 24.81,   # 일반 평균 (ADR-202)
    "eyebrow_width_mm": 49.7,  # 여성 N=300 (ADR-202)
    "eyebrow_width_mm_male": 55.0,  # 남성 N=300 (ADR-202)
}


@dataclass(frozen=True)
class ComparisonResult:
    """비교 묘사 결과."""
    label: str            # "한국 미인 평균과 비교" 등
    user_value: float
    reference_value: float
    diff_pct: float       # 차이 비율 (사용자값/기준값 - 1) × 100
    description_ko: str
    source_url: str = ""


def compare_alar_ratio(user_alar: float, gender: str | None = "female") -> ComparisonResult | None:
    """alar_ratio 비교 묘사 — Miss Korea + 일반 평균."""
    if not isinstance(user_alar, (int, float)) or user_alar <= 0:
        return None
    gp = _GP_REFERENCE["alar_ratio"]
    diff_pct = round((user_alar / gp - 1) * 100, 1)
    if abs(diff_pct) < 5:
        adverb = "거의 같습니다"
    elif diff_pct > 0:
        adverb = f"{abs(diff_pct):.0f}% 정도 넓습니다"
    else:
        adverb = f"{abs(diff_pct):.0f}% 정도 좁습니다"
    return ComparisonResult(
        label="한국 평균 콧방울 비율과 비교",
        user_value=round(user_alar, 3),
        reference_value=gp,
        diff_pct=diff_pct,
        description_ko=(
            f"그대의 콧방울 비율은 한국 사람 평균(0.32)과 견주매 {adverb}. "
            f"이는 형태 묘사이며 운명 매핑이 아닙니다."
        ),
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5359635/",
    )


def compare_to_miss_korea(user_alar: float) -> ComparisonResult | None:
    """Miss Korea 표본과 비교 — 미인 baseline."""
    if not isinstance(user_alar, (int, float)) or user_alar <= 0:
        return None
    mk = _MK_REFERENCE["alar_ratio"]
    diff_pct = round((user_alar / mk - 1) * 100, 1)
    return ComparisonResult(
        label="미스 코리아 표본 콧방울 비율과 비교",
        user_value=round(user_alar, 3),
        reference_value=mk,
        diff_pct=diff_pct,
        description_ko=(
            f"미스 코리아 표본 평균(0.379)과 견주매 {abs(diff_pct):.0f}% 차이입니다. "
            f"이는 형태 비교일 뿐 미모·운명과 무관합니다."
        ),
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5359635/",
    )


# ───── ADR-205: prevalence 구체 묘사 ─────

@dataclass(frozen=True)
class PrevalenceDescription:
    """prevalence 구체 묘사 (한국 표본 분포 묘사)."""
    crease_type: str
    percent: float
    rank_label: str   # "가장 흔한"·"보기 드문" 등
    description_ko: str
    source_url: str


def describe_palm_prevalence(crease_type: str) -> PrevalenceDescription | None:
    """ADR-192 palm prevalence → 사극풍 묘사."""
    try:
        from engine.divination.palm.prevalence import get_prevalence
    except ImportError:
        return None
    p = get_prevalence(crease_type)
    if not p:
        return None
    pct = round(p.prevalence_pct * 100, 1)
    if p.rank == "most_common":
        rank_label = "가장 흔한"
        adverb = f"한국 사람 열 가운데 여덟이 갖는 형태이외다"
    elif p.rank == "variant":
        rank_label = "흔한 변종"
        adverb = f"한국 사람 가운데 약 {pct:.0f}%에서 보이는 결이로구먼"
    elif p.rank == "rare":
        rank_label = "보기 드문"
        adverb = f"한국 사람 가운데 1% 안에서만 보이는 희소한 결이로다"
    else:
        rank_label = "기타 변종"
        adverb = f"기타 변종 형태이외다"
    return PrevalenceDescription(
        crease_type=p.crease_type,
        percent=pct,
        rank_label=rank_label,
        description_ko=(
            f"그대의 손금은 {p.crease_type} 형태로, {adverb}. "
            f"이는 통계 분포이며 운명·인격 평가가 아닙니다."
        ),
        source_url=p.source_urls[0] if p.source_urls else "",
    )


# ───── ADR-206: 공유 카드 메타데이터 (OpenGraph + JSON-LD) ─────

@dataclass(frozen=True)
class ShareCardMeta:
    """공유 카드 메타데이터 (SNS 공유·SEO)."""
    og_title: str
    og_description: str
    og_image_url: str
    og_url: str
    twitter_card: str   # "summary_large_image"
    json_ld: dict       # schema.org JSON-LD
    disclaimer_ko: str


def build_share_card(
    domain: str,                  # 'face' | 'palm' | 'name' | 'dream' | 'hwapae'
    top_label: str,               # 가장 두드러진 형태 라벨 (예: "재백궁이 환한")
    base_url: str = "https://saju-mbti-fusion.fly.dev",
    image_path: str = "/static/share/default.png",
) -> ShareCardMeta:
    """ADR-206 공유 카드 메타데이터 생성.

    Args:
        domain: 도메인 식별자.
        top_label: 사용자에게 표시할 가장 두드러진 결과 라벨.
            ADR-006 위반 어휘 금지 (호출자 책임).
        base_url: 본 시스템 URL.
        image_path: og:image 절대/상대 경로.

    Returns:
        ShareCardMeta — HTML head에 직렬화 가능.
    """
    domain_ko = {
        "face": "관상", "palm": "손금", "name": "성명",
        "dream": "해몽", "hwapae": "화패",
    }.get(domain, "운세")

    title = f"{domain_ko} 분석 결과 — 운학 도사 결정론 풀이"
    desc = (
        f"{domain_ko} 결정론 분석: {top_label}. "
        f"한국 학술 출처 검증된 정량 측정 — 운명 단정 아님."
    )
    return ShareCardMeta(
        og_title=title,
        og_description=desc,
        og_image_url=f"{base_url}{image_path}",
        og_url=base_url,
        twitter_card="summary_large_image",
        json_ld={
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "사주·MBTI 융합 SaaS",
            "applicationCategory": "LifestyleApplication",
            "description": (
                "한국 학술 출처 검증 결정론 + 안전망 인프라 기반 운세 분석. "
                "운명 단정 금지 (ADR-006 자문 거절 정신)."
            ),
            "isAccessibleForFree": True,
            "inLanguage": "ko-KR",
        },
        disclaimer_ko=(
            "본 결과는 형태·통계 분석이며 운명·길흉 단정이 아닙니다. "
            "참고용으로만 활용해 주십시오."
        ),
    )
