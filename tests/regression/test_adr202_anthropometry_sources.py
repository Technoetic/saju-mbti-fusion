"""ADR-202 - 12궁 부위별 학술 출처 영속 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_anthropometry_sources_exposed():
    """KOREAN_ANTHROPOMETRY_SOURCES 노출."""
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    assert isinstance(KOREAN_ANTHROPOMETRY_SOURCES, dict)
    assert len(KOREAN_ANTHROPOMETRY_SOURCES) >= 9


def test_face_overall_source_nature():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["face_overall"]
    assert "nature.com" in src["url"]
    assert "7,569" in src["label"] or "N=7,569" in src["label"]


def test_eye_source_palpebral_fissure():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["eye"]
    assert "24.81" in src["label"]
    assert "springer" in src["url"].lower() or "researchgate" in src["url"].lower()


def test_eyebrow_female_source():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["eyebrow_female"]
    assert "49.7" in src["label"]  # 너비 평균


def test_eyebrow_male_source():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["eyebrow_male"]
    assert "55" in src["label"]


def test_nose_source_miss_korea():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["nose"]
    assert "36.3" in src["label"]
    assert "5359635" in src["url"] or "PMC" in src["url"]


def test_mouth_source_koreascience():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["mouth"]
    assert "JAKO200810103458095" in src["url"]


def test_facial_color_source_springer():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["facial_color"]
    assert "10.1186/s41702-017-0002-7" in src["url"]
    assert "N=543" in src["label"]


def test_skin_clustering_source():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    src = KOREAN_ANTHROPOMETRY_SOURCES["skin_clustering"]
    assert "9907718" in src["url"]


def test_all_sources_have_url_and_label():
    from engine.divination.face.scoring import KOREAN_ANTHROPOMETRY_SOURCES
    for key, src in KOREAN_ANTHROPOMETRY_SOURCES.items():
        assert "url" in src and src["url"]
        assert "label" in src and src["label"]
        assert src["url"].startswith("http")
