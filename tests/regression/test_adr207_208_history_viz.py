"""ADR-207+208 - 이력 + 시각화 schema 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ───── ADR-207 history ─────

def test_adr207_anonymize_user_id():
    from engine.divination.face.history import anonymize_user_id
    a = anonymize_user_id("test@example.com")
    assert len(a) == 24
    # 같은 입력 → 같은 출력 (확정성)
    assert anonymize_user_id("test@example.com") == a


def test_adr207_anonymize_empty():
    from engine.divination.face.history import anonymize_user_id
    assert anonymize_user_id("") == ""


def test_adr207_empty_timeline():
    from engine.divination.face.history import build_timeline
    r = build_timeline("user1", [])
    assert r.entry_count == 0
    assert "이력이 없습니다" in r.description_ko


def test_adr207_single_entry():
    from engine.divination.face.history import build_timeline
    r = build_timeline("user1", [
        {"timestamp_iso": "2026-05-23T10:00:00", "domain": "face",
         "top_label": "재백궁 환한", "palace_score_summary": {"jaebaek": 0.7}},
    ])
    assert r.entry_count == 1
    assert "첫 분석" in r.description_ko


def test_adr207_multi_entries_sorted():
    from engine.divination.face.history import build_timeline
    r = build_timeline("user1", [
        {"timestamp_iso": "2026-01-01T10:00", "domain": "face", "top_label": "A",
         "palace_score_summary": {}},
        {"timestamp_iso": "2026-05-23T10:00", "domain": "palm", "top_label": "B",
         "palace_score_summary": {}},
    ])
    assert r.entry_count == 2
    # 최신 우선
    assert r.entries[0].timestamp_iso > r.entries[1].timestamp_iso
    assert "운명 변화가 아닌 측정 변동성" in r.description_ko


def test_adr207_compute_score_drift():
    from engine.divination.face.history import build_timeline, compute_score_drift
    r = build_timeline("user1", [
        {"timestamp_iso": "2026-01-01", "domain": "face", "top_label": "A",
         "palace_score_summary": {"jaebaek": 0.5}},
        {"timestamp_iso": "2026-05-23", "domain": "face", "top_label": "B",
         "palace_score_summary": {"jaebaek": 0.7}},
    ])
    drift = compute_score_drift(list(r.entries), "jaebaek")
    assert drift is not None
    assert 0 < drift < 0.2


def test_adr207_invalid_entries_skipped():
    from engine.divination.face.history import build_timeline
    r = build_timeline("user1", [
        None,
        {"missing": "fields"},
        {"timestamp_iso": "2026-05-23", "domain": "face", "top_label": "C"},
    ])
    assert r.entry_count == 1


# ───── ADR-208 viz schema ─────

def test_adr208_radar_12_palaces():
    from engine.divination.face.viz_schema import to_radar_chart_data
    palace_scores = {
        "palaces": {
            "jaebaek": {"label_ko": "재백궁", "score": 0.6},
            "gwanrok": {"label_ko": "관록궁", "score": 0.4},
        }
    }
    r = to_radar_chart_data(palace_scores)
    assert r["type"] == "radar"
    assert "재백궁" in r["labels"]
    assert 0.6 in r["values"]
    assert "ADR-006" in r["disclaimer"]


def test_adr208_complexion_heatmap():
    from engine.divination.face.viz_schema import to_complexion_heatmap
    complexion = {
        "rois": {
            "forehead": {"L": 64, "a": 12, "b": 16, "L_zscore": 0.3, "label_short": "고르다"}
        },
        "overall_L_mean": 63,
    }
    r = to_complexion_heatmap(complexion)
    assert r["type"] == "heatmap"
    assert "forehead" in r["rois"]
    assert r["rois"]["forehead"]["label_ko"] == "이마"
    assert "의료 진단" in r["disclaimer"]


def test_adr208_samjeong_bar():
    from engine.divination.face.viz_schema import to_samjeong_bar
    palace_scores = {
        "samjeong": {
            "sangjeong": {"label_ko": "상정", "score": 0.5},
            "jungjeong": {"label_ko": "중정", "score": 0.7},
            "hajeong": {"label_ko": "하정", "score": 0.3},
        }
    }
    r = to_samjeong_bar(palace_scores)
    assert r["type"] == "bar"
    assert len(r["labels"]) == 3
    assert "ADR-006" in r["disclaimer"]


def test_adr208_full_viz_schema():
    from engine.divination.face.viz_schema import build_full_viz_schema
    fr_result = {
        "palace_scores": {"palaces": {"jaebaek": {"label_ko": "재백궁", "score": 0.6}}},
        "complexion": {"rois": {}, "overall_L_mean": 63},
    }
    r = build_full_viz_schema(fr_result)
    assert "radar_12_palaces" in r
    assert "heatmap_complexion" in r
    assert "bar_samjeong" in r
    assert r["metadata"]["persona"] == "운학 도사"
    assert "운명·길흉 단정이 아닙니다" in r["metadata"]["disclaimer_global"]


def test_adr208_empty_result_safe():
    from engine.divination.face.viz_schema import build_full_viz_schema
    r = build_full_viz_schema({})
    assert "radar_12_palaces" in r
    assert r["radar_12_palaces"]["labels"] == []
