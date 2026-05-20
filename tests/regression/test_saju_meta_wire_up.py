"""ADR-086 wire-up 회귀 — server.py saju 분기에 십성 메타 통합.

ADR-086 한계 회복: 메타 라벨 (사길신·사흉신·재극인 등)을 LLM 컨텍스트로 직접 주입.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def test_imports_classify_gilhyung():
    """server.py가 classify_gilhyung import."""
    src = _src()
    assert "classify_gilhyung" in src
    assert "detect_special_combinations" in src


def test_meta_label_block_present():
    """결정론 블록에 '십성 메타 분류 (ADR-086)' 명시."""
    src = _src()
    assert "십성 메타 분류 (ADR-086)" in src


def test_special_combos_block_present():
    """결정론 블록에 '특수 구조 조합' 명시."""
    src = _src()
    assert "특수 구조 조합" in src


def test_meta_disclaimer_block_present():
    """메타 블록에 ADR-006 길흉 단정 차단 지시 명시."""
    src = _src()
    assert "구조 라벨이며 길흉 단정 X (ADR-006)" in src


def test_gan_class_uses_classify_gilhyung():
    """천간 십성에 classify_gilhyung 적용."""
    src = _src()
    assert "gan_class = classify_gilhyung(today_tengod_gan)" in src
    assert "ji_class = classify_gilhyung(today_tengod_ji)" in src


def test_combos_uses_detect_special_combinations():
    """특수 조합 detect_special_combinations 호출."""
    src = _src()
    assert "detect_special_combinations(ten_gods_data)" in src


def test_ten_gods_data_dict_initialized():
    """ten_gods_data dict 타입 명시 초기화 (Exception 시 빈 dict)."""
    src = _src()
    assert "ten_gods_data: dict = {}" in src


def test_live_meta_for_user_case():
    """라이브 사례 사용자 (1990-05-15 庚辰 ↔ 2026-05-20 甲午)."""
    from engine.saju.ten_gods import (
        compute_ten_gods, classify_gilhyung, detect_special_combinations,
    )
    r = compute_ten_gods({
        "year": "庚辰", "month": "庚辰", "day": "庚辰", "hour": "甲午"
    })
    # 천간 편재 (중립), 지지 정관 (사길신)
    assert classify_gilhyung(r["hour_gan"]) is None  # 편재 = 중립
    assert classify_gilhyung(r["hour_ji"]) == "사길신"  # 정관 = 사길신
    assert "재극인" in detect_special_combinations(r)


def test_meta_label_format():
    """meta_label 형식: '천간 X={등급} · 지지 Y={등급}'."""
    src = _src()
    assert 'f"천간 {today_tengod_gan}={gan_class}"' in src
    assert 'f"지지 {today_tengod_ji}={ji_class}"' in src


def test_combos_label_includes_none():
    """combos_label에 '(없음)' fallback 명시."""
    src = _src()
    assert '"(없음)"' in src
