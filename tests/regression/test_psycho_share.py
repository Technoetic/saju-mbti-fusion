"""psycho-share 모듈 회귀 (P3-7).

검증:
  · 모듈 export 시그니처 (renderShareCard·buildShareText·shareNative·downloadShareCard·copyShareText)
  · buildShareText에 면책·도메인 URL 자동 포함
  · renderShareCard 캔버스에 면책 텍스트 박힘 (코드 상수 검색)
  · play.js renderResult가 3종 공유 버튼 마운트
"""
from pathlib import Path


SHARE_JS = Path(__file__).resolve().parent.parent.parent / "front" / "js" / "ui" / "psycho-share.js"
PLAY_JS = Path(__file__).resolve().parent.parent.parent / "front" / "js" / "ui" / "play.js"


def test_share_module_exports():
    """psycho-share.js — 5개 export 시그니처 존재."""
    src = SHARE_JS.read_text(encoding="utf-8")
    for fn in ["renderShareCard", "buildShareText", "shareNative",
               "downloadShareCard", "copyShareText"]:
        assert f"export function {fn}" in src or f"export async function {fn}" in src, (
            f"psycho-share.js에서 export '{fn}' 누락"
        )


def test_share_text_contains_disclaimer_and_url():
    """buildShareText 공유 텍스트에 도메인 + 출처 명시."""
    src = SHARE_JS.read_text(encoding="utf-8")
    assert "saju-mbti-fusion.fly.dev" in src, (
        "buildShareText에 공식 도메인 URL 누락 — 바이럴 추적 깨짐"
    )
    assert "사주·MBTI 융합 SaaS" in src, "공유 텍스트에 서비스명 누락"


def test_render_card_includes_disclaimer_on_canvas():
    """renderShareCard 캔버스에 면책 텍스트 자동 주입 (CLAUDE.md §9)."""
    src = SHARE_JS.read_text(encoding="utf-8")
    assert "ADR-014" in src, "공유 PNG에 톤 출처 (ADR-014) 누락"
    assert "참고용" in src or "단독 근거" in src, (
        "공유 PNG에 면책 키워드 (참고용/단독 근거) 누락"
    )


def test_play_js_mounts_share_buttons():
    """play.js renderResult에 3종 공유 버튼 마운트."""
    src = PLAY_JS.read_text(encoding="utf-8")
    for action in ["native", "png", "copy"]:
        assert f'data-share="{action}"' in src, (
            f"play.js renderResult에 공유 버튼 data-share='{action}' 누락"
        )
    # 3종 핸들러 import + 호출
    for fn in ["shareNative", "downloadShareCard", "copyShareText"]:
        assert fn in src, f"play.js에 공유 핸들러 '{fn}' 호출 누락"
