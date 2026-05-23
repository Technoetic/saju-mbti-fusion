"""ADR-179 - scoring.py 학술 출처 영속 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_anthropometry_source_url_exposed():
    """scoring.py에 SOURCE_URL_ANTHROPOMETRY 노출 (학술 출처 영속)."""
    from engine.divination.face.scoring import SOURCE_URL_ANTHROPOMETRY
    assert "pubmed" in SOURCE_URL_ANTHROPOMETRY.lower()
    assert "15262719" in SOURCE_URL_ANTHROPOMETRY


def test_mouth_source_url_exposed():
    """입꼬리 학술 출처도 함께 노출."""
    from engine.divination.face.scoring import SOURCE_URL_MOUTH
    assert "koreascience" in SOURCE_URL_MOUTH.lower()
    assert "JAKO200810103458095" in SOURCE_URL_MOUTH


def test_score_jaebaek_works_with_known_metrics():
    """기존 alar_ratio·삼정 임계값 작동 — ADR-179 출처 추가 후에도 회귀 0."""
    from engine.divination.face.scoring import _score_jaebaek
    score = _score_jaebaek({
        "alar_ratio": 0.32,
        "three_thirds": [33.0, 34.0, 33.0],
    })
    # 임계값 한가운데 → 점수 1.0 근처
    assert score.score > 0.9
    assert score.key == "jaebaek"


def test_score_jaebaek_extreme_alar_low():
    """alar_ratio 0.05 (극단) → 낮은 점수."""
    from engine.divination.face.scoring import _score_jaebaek
    score = _score_jaebaek({
        "alar_ratio": 0.05,
        "three_thirds": [33.0, 34.0, 33.0],
    })
    assert score.score < 0.6


def test_module_docstring_mentions_adr179():
    """모듈 docstring에 ADR-179 학술 출처 명시."""
    from engine.divination.face import scoring
    assert "ADR-179" in scoring.__doc__
    assert "15262719" in scoring.__doc__ or "anthropometry" in scoring.__doc__.lower()
