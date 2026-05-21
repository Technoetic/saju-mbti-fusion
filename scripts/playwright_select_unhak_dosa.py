"""운학 도사(face 도메인) 카드 클릭 자동화 — Playwright.

본 AI가 https://saju-mbti-fusion.fly.dev/ 라이브에서 운학 도사 카드를
직접 클릭하기 위한 스크립트. 본 세션 도구로는 외부 URL 클릭 불가.

사용법:
    python scripts/playwright_select_unhak_dosa.py
    python scripts/playwright_select_unhak_dosa.py --headless
    python scripts/playwright_select_unhak_dosa.py --char saju  # 다른 캐릭터

동작 절차:
1. https://saju-mbti-fusion.fly.dev/ 진입
2. 카드 갤러리 로드 대기 (.char-card[data-go='face'])
3. 운학 도사 카드 클릭 (또는 진입 버튼)
4. 진입 후 페이지 URL·제목 + 본문 일부 캡처
5. step_archive/playwright_unhak_dosa_<timestamp>/ 에 screenshot.png + page.html 저장

요구사항:
- python -m pip install playwright
- python -m playwright install chromium
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    sys.stderr.write(
        "playwright 미설치. 다음 명령어로 설치:\n"
        "  python -m pip install playwright\n"
        "  python -m playwright install chromium\n"
    )
    sys.exit(1)


SITE_URL = "https://saju-mbti-fusion.fly.dev/"
CHARACTER_MAP = {
    "saju": "만월 아씨",
    "dream": "몽이 도령",
    "hwapae": "화선 낭자",
    "star": "성하 공자",
    "face": "운학 도사",
    "palm": "옥선 할미",
    "name": "묵향 선생",
}


def select_character(char_key: str, headless: bool = False) -> None:
    """카드 갤러리에서 지정 캐릭터 카드 클릭 + 진입 페이지 캡처."""
    if char_key not in CHARACTER_MAP:
        raise ValueError(f"char_key는 {list(CHARACTER_MAP.keys())} 중 하나")

    char_name = CHARACTER_MAP[char_key]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).resolve().parent.parent / "step_archive" / f"playwright_{char_key}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )
        page = context.new_page()

        print(f"[1/5] {SITE_URL} 진입 중...")
        page.goto(SITE_URL, wait_until="domcontentloaded", timeout=30000)

        print(f"[2/5] 카드 갤러리 로드 대기 (.char-card[data-go='{char_key}'])...")
        target_selector = f".char-card[data-go='{char_key}']"
        try:
            page.wait_for_selector(target_selector, state="visible", timeout=20000)
        except PWTimeout:
            # 갤러리가 캐러셀 형식일 가능성 — 카드가 viewport 밖이어도 DOM에 있을 수 있음
            print(f"  ⚠ visible 대기 실패 — attached 상태로 재시도")
            page.wait_for_selector(target_selector, state="attached", timeout=10000)

        # 진입 전 스크린샷
        before_path = output_dir / "01_before_click.png"
        page.screenshot(path=str(before_path), full_page=True)
        print(f"  진입 전 스크린샷: {before_path.name}")

        # 스와이프 안내 오버레이 닫기 — "닫기" 또는 "다시 보지 않기" 버튼 정식 클릭
        print(f"  스와이프 안내 오버레이 점검...")
        swipe_hint = page.locator("#swipeHint")
        if swipe_hint.count() > 0:
            try:
                if swipe_hint.is_visible(timeout=1000):
                    # "닫기" 또는 "다시 보지 않기" 버튼 찾기 (본문 텍스트에서 발견됨)
                    close_btn = swipe_hint.locator("button:has-text('닫기'), button:has-text('다시 보지')").first
                    if close_btn.count() > 0:
                        close_btn.click(timeout=3000)
                        print(f"  '닫기' 버튼 클릭으로 정식 dismiss")
                    else:
                        # ESC key fallback
                        page.keyboard.press("Escape")
                        print(f"  ESC key dismiss")
                    page.wait_for_timeout(800)
            except (PWTimeout, Exception) as e:
                print(f"  ⚠ dismiss 실패: {e}")
                # fallback: DOM 강제 hide
                page.evaluate("""
                    const sh = document.querySelector('#swipeHint');
                    if (sh) { sh.remove(); }
                    const veil = document.querySelector('.swipe-hint-veil');
                    if (veil) { veil.remove(); }
                """)

        print(f"[3/5] {char_name}({char_key}) 카드 진입...")
        # 본 시스템 card-gallery.js의 enterCard()는 다음 흐름:
        #   1. exitGalleryMode() — gallery-mode 클래스 제거
        #   2. window.__menuOpen(charKey) 호출 (WHM_CONTENTS 정의된 경우)
        #   3. 또는 .tab-btn[data-tab=...].click() 레거시 흐름
        # 클릭 이벤트 우회 위험성 (오버레이·드래그 dead zone)을 피하기 위해
        # 본 함수 직접 호출이 가장 결정론적.
        click_result = page.evaluate(
            """(charKey) => {
                const card = document.querySelector(`.char-card[data-character='${charKey}']`);
                if (!card) return {ok:false, reason:'card_not_found'};
                const target = card.dataset.go;
                if (!target) return {ok:false, reason:'no_data_go'};
                // gallery-mode 클래스 제거 (exitGalleryMode 동등)
                document.body.classList.remove('gallery-mode');
                // WHM_CONTENTS + __menuOpen 우선 (card-gallery.js:144)
                if (window.WHM_CONTENTS && window.WHM_CONTENTS[charKey] && window.__menuOpen) {
                    window.__menuOpen(charKey);
                    return {ok:true, path:'menuOpen', target, charKey};
                }
                // 레거시: .tab-btn[data-tab=...].click()
                const tabBtn = document.querySelector(`.tab-btn[data-tab='${target}']`);
                if (tabBtn) {
                    tabBtn.click();
                    return {ok:true, path:'tabBtn', target, charKey};
                }
                return {ok:false, reason:'no_handler', target, charKey};
            }""",
            char_key,
        )
        print(f"  enterCard 직접 호출 결과: {click_result}")
        if not click_result.get("ok"):
            print(f"  ⚠ 직접 호출 실패 — 버튼 클릭 fallback")
            target_card = page.locator(target_selector).first
            enter_button = target_card.locator(".char-card-enter")
            enter_button.click(timeout=5000, force=True)
            print(f"  .char-card-enter 버튼 force 클릭")

        print(f"[4/5] 진입 페이지 로드 대기...")
        # SPA: __menuOpen → renderMenu + setMode('menu'). networkidle은 LLM 호출 전이므로 의미 적음.
        page.wait_for_timeout(2000)

        url_after = page.url
        title_after = page.title()
        # body 전체 inner_text는 hidden DOM도 일부 노이즈로 뽑힘.
        # menu mode 확인 + 가시 메뉴 그리드 본문만 캡처.
        body_class = page.evaluate("document.body.className")
        # WHM_CONTENTS[face].items 가 메뉴에 렌더링됐는지 점검
        menu_grid_html = page.evaluate("""
            () => {
                const mg = document.querySelector('#menuGrid');
                if (!mg) return null;
                const cards = mg.querySelectorAll('.menu-card');
                return {
                    visible: mg.offsetParent !== null,
                    card_count: cards.length,
                    card_titles: Array.from(cards).map(c => {
                        const title = c.querySelector('.menu-card-title');
                        return title ? title.textContent.trim() : c.textContent.trim().slice(0, 30);
                    })
                };
            }
        """)
        print(f"  body.className: {body_class}")
        print(f"  menuGrid 상태: {menu_grid_html}")

        body_text = page.locator("body").inner_text()
        body_excerpt = body_text[:2000] if len(body_text) > 2000 else body_text

        after_path = output_dir / "02_after_click.png"
        page.screenshot(path=str(after_path), full_page=True)
        html_path = output_dir / "page.html"
        html_path.write_text(page.content(), encoding="utf-8")
        text_path = output_dir / "body_text.txt"
        text_path.write_text(body_text, encoding="utf-8")

        print(f"[5/5] 캡처 완료")
        print(f"  URL 변경: {SITE_URL} → {url_after}")
        print(f"  페이지 제목: {title_after}")
        print(f"  본문 발췌 ({len(body_text)} chars 중 처음 2000):")
        print("  " + "─" * 60)
        for line in body_excerpt.splitlines()[:40]:
            print(f"  | {line}")
        print("  " + "─" * 60)
        print(f"\n저장 위치: {output_dir}")
        print(f"  - {after_path.name} (진입 후 풀페이지 스크린샷)")
        print(f"  - {html_path.name} (HTML 전체)")
        print(f"  - {text_path.name} (본문 텍스트 전체)")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--char",
        default="face",
        choices=list(CHARACTER_MAP.keys()),
        help="선택할 캐릭터 key (디폴트: face = 운학 도사)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="브라우저 창 표시 X (백그라운드 실행)",
    )
    args = parser.parse_args()
    select_character(args.char, headless=args.headless)


if __name__ == "__main__":
    main()
