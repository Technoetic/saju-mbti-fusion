"""psychotest 결과 모달 면책 자동 주입 회귀 (CLAUDE.md §9).

본 시스템 사용자 출력 의무:
  · "참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
  · ADR-006 자문 거절 정합

psychotest renderResult + psycho runPsycho renderResult 두 모달에
면책 텍스트가 코드 상수로 박혀 있는지 회귀.
"""
from pathlib import Path


PLAY_JS = Path(__file__).resolve().parent.parent.parent / "front" / "js" / "ui" / "play.js"


def test_psychotest_result_disclaimer_present():
    """psychotest renderResult — 면책 자동 주입 (CLAUDE.md §9)."""
    src = PLAY_JS.read_text(encoding="utf-8")
    assert "참고용이며 의료·법률·금융" in src, (
        "play.js renderResult에 면책 텍스트 누락 — CLAUDE.md §9 위반"
    )
    assert "단독 근거가 될 수 없습니다" in src, (
        "play.js 면책 결구 '단독 근거가 될 수 없습니다' 누락"
    )


def test_psychotest_result_adr_attribution():
    """psychotest 결과 모달 — ADR-014 (MBTI 단정 회피) 출처 명시."""
    src = PLAY_JS.read_text(encoding="utf-8")
    # 두 면책 중 하나는 ADR-014, 다른 하나는 PCL-R 인포테인먼트 명시
    assert "ADR-014" in src or "일상 심리 카테고리" in src, (
        "psychotest 면책에 톤 출처 (ADR-014 또는 일상 심리) 명시 누락"
    )
    assert "PCL-R" in src or "임상 사이코패스" in src, (
        "psycho 추리 면책에 출처 (PCL-R) 명시 누락"
    )


def test_disclaimer_class_present():
    """면책 표시 클래스 .psycho-card-disclaimer가 결과 모달 양쪽에 존재."""
    src = PLAY_JS.read_text(encoding="utf-8")
    occurrences = src.count("psycho-card-disclaimer")
    # JS 양쪽 모달 = 2회 이상 (CSS 정의 별도 파일)
    assert occurrences >= 2, (
        f"psycho-card-disclaimer 클래스가 {occurrences}회만 사용됨 "
        f"(목표: ≥2, psychotest + psycho 양쪽 모달)"
    )
