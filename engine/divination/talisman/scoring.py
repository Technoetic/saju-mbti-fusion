"""ADR-121 — 한국 정통 부적 4 표준 결정론 메타.

본 모듈은 ADR-002·006·010 정합.

영역:
  · 합격부·재물부·연애부·건강부 — 한국 무속 정통 4 표준
  · 각 부적 메타: 핵심 한자·전통 색상·기원 표현 (단정 X)
  · 이미지 생성 옵션은 사용자 결단 (Stable Diffusion·Imagen)

출처:
  · 한국학중앙연구원 한국민족문화대백과사전 부적 표제
  · 국립민속박물관 부적 4 표준 (조선시대 무속)
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────── 4 부적 메타 ───────────────────────────

@dataclass(frozen=True)
class TalismanType:
    """한국 정통 부적 단일 표준.

    Attributes:
        key: 영문 키 (hapgyeok·jaemul·yeonae·geongang)
        label_ko: 한국어 명
        hanja: 한자
        purpose_flow_ko: 기원 흐름 톤 (단정 X)
        traditional_color: 전통 색상 (적색·황색·청색 등)
        symbol_hanja: 부적 핵심 한자
        description: 한국 무속 정통 의미 (학파 인용)
    """
    key: str
    label_ko: str
    hanja: str
    purpose_flow_ko: str
    traditional_color: str
    symbol_hanja: str
    description: str


TALISMAN_TYPES: tuple[TalismanType, ...] = (
    TalismanType(
        key="hapgyeok",
        label_ko="합격부",
        hanja="合格符",
        purpose_flow_ko="배움의 결을 다지는 흐름",
        traditional_color="황색 (土 안정)",
        symbol_hanja="格",
        description=(
            "한국 무속 정통 — 학업·시험·자격 분야의 결을 다지는 부적. "
            "조선시대 과거 시험 응시자가 휴대한 전통. 결정론 의식의 메타이며 "
            "합격을 단정·보장하는 부적이 아님 (ADR-006 정합)."
        ),
    ),
    TalismanType(
        key="jaemul",
        label_ko="재물부",
        hanja="財物符",
        purpose_flow_ko="재물의 결을 다지는 흐름",
        traditional_color="황색 + 금색 (土生金)",
        symbol_hanja="財",
        description=(
            "한국 무속 정통 — 재정 안정·노력의 결실의 결을 기원하는 부적. "
            "재물 단정·복권 당첨 보장 X — 흐름 톤만의 의식 메타."
        ),
    ),
    TalismanType(
        key="yeonae",
        label_ko="연애부",
        hanja="戀愛符",
        purpose_flow_ko="인연의 결을 살피는 흐름",
        traditional_color="홍색 (火 정념)",
        symbol_hanja="戀",
        description=(
            "한국 무속 정통 — 인연·관계의 결을 살피는 부적. "
            "결혼·이별·재결합 단정 X — 흐름 톤만 (ADR-006·113 정합)."
        ),
    ),
    TalismanType(
        key="geongang",
        label_ko="건강부",
        hanja="健康符",
        purpose_flow_ko="건강의 결을 살피는 흐름",
        traditional_color="청색 (水 정화)",
        symbol_hanja="健",
        description=(
            "한국 무속 정통 — 건강·치병·평안의 결을 기원하는 부적. "
            "의료 진단 X (ADR-006) — 의식 의례의 메타이며 의사 진단 대체 절대 X."
        ),
    ),
)


def talisman_by_key(key: str) -> TalismanType | None:
    """영문 키로 부적 조회."""
    for t in TALISMAN_TYPES:
        if t.key == key:
            return t
    return None


# ─────────────────────────── 결과 dataclass ───────────────────────────

@dataclass(frozen=True)
class TalismanReading:
    """부적 결정론 풀이.

    ★ 의도적 부재 필드 (ADR-006):
      - guaranteed_outcome — 효과 보장 단정 X
      - cures_disease — 치병 단정 X
    """
    talisman_key: str
    talisman_label_ko: str
    talisman_hanja: str
    purpose_flow_ko: str
    traditional_color: str
    symbol_hanja: str
    description: str
    disclaimer: str


_DISCLAIMER = (
    "본 부적은 한국 무속 정통 (국립민속박물관·한국학중앙연구원) 의식 메타로, "
    "효과 보장 X, 치병·재물·합격·결혼 단정 X. 한국 전통 문화 콘텐츠 참고용 — "
    "의료·법률·금융 의사결정 단독 근거 X. ADR-006 자문 거절 정신."
)


def compute_talisman_reading(talisman_key: str) -> TalismanReading | None:
    """부적 키 → 결정론 메타."""
    t = talisman_by_key(talisman_key)
    if t is None:
        return None
    return TalismanReading(
        talisman_key=t.key,
        talisman_label_ko=t.label_ko,
        talisman_hanja=t.hanja,
        purpose_flow_ko=t.purpose_flow_ko,
        traditional_color=t.traditional_color,
        symbol_hanja=t.symbol_hanja,
        description=t.description,
        disclaimer=_DISCLAIMER,
    )


def format_talisman_for_prompt(r: TalismanReading) -> str:
    """Stage 2 시스템 프롬프트 주입용 부적 메타."""
    return (
        f"[부적 결정론 메타 — 한국 정통 (ADR-121)]\n"
        f"  · 부적: {r.talisman_label_ko} ({r.talisman_hanja})\n"
        f"  · 핵심 한자: {r.symbol_hanja}\n"
        f"  · 전통 색상: {r.traditional_color}\n"
        f"  · 기원 흐름: {r.purpose_flow_ko}\n"
        f"  · 의미: {r.description}\n"
        f"[안전 장치 — ADR-006] 효과 보장·치병·재물·합격·결혼 단정 절대 금지. "
        f"의식 메타 흐름 톤만.\n"
        f"{r.disclaimer}"
    )


__all__ = [
    "TalismanType", "TALISMAN_TYPES",
    "talisman_by_key",
    "TalismanReading",
    "compute_talisman_reading",
    "format_talisman_for_prompt",
]
