"""카드 갤러리 7명 캐릭터 순회 자동화 — Playwright.

본 시스템 메인 카드 갤러리 (만월 아씨·몽이 도령·화선 낭자·성하 공자·
운학 도사·옥선 할미·묵향 선생) 7명을 좌우 ArrowRight 키로 넘기면서
각 카드 활성 시점에 스크린샷 + active 카드 메타 캡처.

card-gallery.js line 74-79: gallery-mode일 때 ArrowRight/ArrowLeft 키
바인딩으로 next()/prev() 동작 확인됨.

사용법:
    python scripts/playwright_swipe_all_characters.py
    python scripts/playwright_swipe_all_characters.py --headless

저장:
    step_archive/playwright_swipe_<timestamp>/
      - 00_initial.png
      - 01_saju.png ~ 07_name.png
      - summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    sys.stderr.write("python -m pip install playwright + python -m playwright install chromium\n")
    sys.exit(1)


SITE_URL = "https://saju-mbti-fusion.fly.dev/"
EXPECTED_ORDER = [
    ("saju", "만월 아씨"),
    ("dream", "몽이 도령"),
    ("hwapae", "화선 낭자"),
    ("star", "성하 공자"),
    ("face", "운학 도사"),
    ("palm", "옥선 할미"),
    ("name", "묵향 선생"),
]


def dismiss_swipe_hint(page) -> None:
    """스와이프 안내 모달 정식 dismiss — '다시 보지 않기' 버튼 우선.

    "닫기"는 일회 dismiss, "다시 보지 않기"는 localStorage 영구 dismiss.
    스크린샷에서 모달이 카드를 가리는 문제 발견 후 강화.
    """
    swipe_hint = page.locator("#swipeHint")
    if swipe_hint.count() == 0:
        return
    # 1차: "다시 보지 않기" — localStorage flag로 다음 진입도 차단
    try:
        if swipe_hint.is_visible(timeout=1000):
            for label in ["다시 보지 않기", "다시 보지", "닫기"]:
                btn = swipe_hint.locator(f"button:has-text('{label}')").first
                if btn.count() > 0:
                    try:
                        btn.click(timeout=3000)
                        page.wait_for_timeout(500)
                        # 모달이 실제로 사라졌는지 검증
                        if not swipe_hint.is_visible(timeout=500):
                            return
                    except (PWTimeout, Exception):
                        continue
    except (PWTimeout, Exception):
        pass
    # 2차 fallback: DOM 강제 제거 + display:none CSS 주입
    page.evaluate("""
        // localStorage 플래그 사전 설정 (스크립트 재진입 시도)
        try {
            localStorage.setItem('whm.swipeHint.home.dismissed', '1');
            localStorage.setItem('whm.swipeHint.gallery.dismissed', '1');
            localStorage.setItem('whm.swipeHint.dismissed', '1');
        } catch (e) {}
        // DOM 제거
        const sh = document.querySelector('#swipeHint');
        if (sh) sh.remove();
        const veil = document.querySelector('.swipe-hint-veil');
        if (veil) veil.remove();
        // CSS로 재출현 차단
        const style = document.createElement('style');
        style.textContent = '#swipeHint, .swipe-hint, .swipe-hint-veil { display: none !important; visibility: hidden !important; }';
        document.head.appendChild(style);
    """)


def get_active_card_meta(page) -> dict:
    """본관 #cardDeck 내 활성 카드 메타 (.char-card.is-active).

    주의: 본 시스템에는 #cardDeck (메인 7 캐릭터)와 chwiseon-card (취선루 별도 갤러리)
    가 공존. data-character='ya' 등 chwiseon 키는 본 7명 순회 대상 아님.
    """
    return page.evaluate("""
        () => {
            // 본관 갤러리 #cardDeck 내부 한정
            const deck = document.getElementById('cardDeck');
            if (!deck) return {error: 'no_cardDeck'};
            const active = deck.querySelector('.char-card.is-active');
            if (!active) return {error: 'no_active_in_cardDeck'};
            const name = active.querySelector('.char-card-name');
            const sub = active.querySelector('.char-card-sub');
            const quote = active.querySelector('.char-card-quote');
            const enter = active.querySelector('.char-card-enter');
            return {
                data_go: active.dataset.go,
                data_character: active.dataset.character,
                name: name ? name.textContent.trim() : null,
                sub: sub ? sub.textContent.trim() : null,
                quote: quote ? quote.textContent.trim() : null,
                enter_label: enter ? enter.textContent.trim() : null,
                body_class: document.body.className,
            };
        }
    """)


def goto_card_index(page, idx: int) -> dict:
    """본관 #cardDeck 갤러리의 idx 번째 카드로 직접 전환.

    card-gallery.js의 goTo()는 IIFE 내부라 직접 호출 불가.
    DOM 조작 + 인디케이터 점 click() 으로 동등 효과.
    """
    return page.evaluate(
        """(idx) => {
            // galleryDots의 idx번째 점 클릭으로 goTo(idx) 트리거
            const dots = document.getElementById('galleryDots');
            if (!dots) return {ok:false, reason:'no_dots'};
            const dotBtns = Array.from(dots.children);
            if (idx < 0 || idx >= dotBtns.length) {
                return {ok:false, reason:'idx_out_of_range', n: dotBtns.length};
            }
            dotBtns[idx].click();
            return {ok:true, n: dotBtns.length};
        }""",
        idx,
    )


def swipe_all(headless: bool = False) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).resolve().parent.parent / "step_archive" / f"playwright_swipe_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    with sync_playwright() as p:
        # Chromium headless는 HW 가속 비디오 디코딩 출력이 PNG 캡처에 안 그려지는
        # 알려진 이슈. --headless=new 모드 + 비디오 디코더 flags 강제.
        launch_args = [
            "--autoplay-policy=no-user-gesture-required",
            "--disable-features=UseOzonePlatform",
            "--use-gl=swiftshader",  # SW 렌더링 강제 → 비디오 프레임이 캡처에 포함
        ]
        browser = p.chromium.launch(
            headless=headless,
            args=launch_args,
        )
        # 본 시스템은 모바일 우선 — 카드 갤러리 transform translateX가 viewport 폭 기준.
        # 데스크탑 1280 폭에서는 비활성 카드가 화면 밖으로 정확 이동하지 않아
        # is-active 외 카드 본문이 빈 영역으로 보이는 캡처 발생.
        context = browser.new_context(
            viewport={"width": 414, "height": 896},  # iPhone XR / 11 표준
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="ko-KR",
        )
        page = context.new_page()

        print(f"[init] {SITE_URL} 진입")
        page.goto(SITE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".char-card", state="attached", timeout=20000)
        page.wait_for_timeout(800)

        # 갤러리 모드 진입 — card-gallery.js의 키보드 핸들러는 gallery-mode일 때만 동작
        body_class_before = page.evaluate("document.body.className")
        print(f"  초기 body.className: {body_class_before!r}")
        if "gallery-mode" not in body_class_before:
            # 본 시스템은 toGalleryBtn 또는 직접 호출
            entered = page.evaluate("""
                () => {
                    if (window.__galleryEnter) { window.__galleryEnter(); return 'fn'; }
                    const btn = document.getElementById('toGalleryBtn');
                    if (btn) { btn.click(); return 'btn'; }
                    document.body.classList.add('gallery-mode');
                    return 'class';
                }
            """)
            print(f"  galleryEnter 트리거: {entered}")
            page.wait_for_timeout(600)

        dismiss_swipe_hint(page)
        page.wait_for_timeout(400)

        # 초기 스크린샷
        page.screenshot(path=str(output_dir / "00_initial.png"), full_page=False)
        initial_meta = get_active_card_meta(page)
        print(f"  초기 활성 카드: {initial_meta.get('name')} ({initial_meta.get('data_character')})")

        # 본관 #cardDeck 갤러리 점 인디케이터 점검
        dot_count = page.evaluate("""
            () => {
                const dots = document.getElementById('galleryDots');
                return dots ? dots.children.length : 0;
            }
        """)
        print(f"  galleryDots 점 개수: {dot_count}")

        # ★ 캡처 시각 문제 해결책 통합:
        # 1. transition 0.45s + opacity 0.6s 완전 제거 → 즉시 최종 상태
        # 2. 모든 카드 본문 visibility 강제 (saju만 보이는 idx=0 누적 효과 무효화)
        # 3. .char-card 자체에 강한 색상·텍스트 강제 → headless 비디오 디코더 누락 우회
        page.add_style_tag(content="""
            /* transition 전부 제거 — 즉시 최종 상태 캡처 */
            .card-deck, .char-card-video, .char-card, .char-card-body,
            .char-card-veil, .char-card-name, .char-card-sub, .char-card-quote {
                transition: none !important;
                animation: none !important;
            }
            /* 비디오 디코더 누락 우회: 모든 카드에 캐릭터별 색상 그라데이션 강제 */
            .char-card-video { display: none !important; }
            .char-card { background: linear-gradient(180deg, #2a1a3a 0%, #0f0820 100%) !important; }
            body.char-saju .char-card[data-character="saju"] {
                background: linear-gradient(180deg, #2d1b3d 0%, #1a0f25 100%) !important;
            }
            .char-card[data-character="dream"] { background: linear-gradient(180deg, #1a2540, #0a1428) !important; }
            .char-card[data-character="hwapae"] { background: linear-gradient(180deg, #3d1a2a, #200810) !important; }
            .char-card[data-character="star"] { background: linear-gradient(180deg, #0a1535, #050820) !important; }
            .char-card[data-character="face"] { background: linear-gradient(180deg, #1a2a1a, #081505) !important; }
            .char-card[data-character="palm"] { background: linear-gradient(180deg, #2a2010, #150f05) !important; }
            .char-card[data-character="name"] { background: linear-gradient(180deg, #1a1a2a, #0a0a15) !important; }
            /* veil 약화 → 텍스트 가시성 */
            .char-card-veil {
                background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.4) 100%) !important;
                opacity: 1 !important;
            }
            /* 본문 중앙 정렬 + 강한 대비 */
            .char-card-body {
                justify-content: center !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
            .char-card-name {
                font-size: 38px !important;
                color: #f5d676 !important;
                text-shadow: 0 0 8px rgba(0,0,0,0.95), 0 2px 4px rgba(0,0,0,1) !important;
                letter-spacing: 6px !important;
            }
            .char-card-sub {
                color: #ecd9a8 !important;
                font-size: 14px !important;
                text-shadow: 0 0 6px rgba(0,0,0,0.95) !important;
            }
            .char-card-quote {
                color: #f8e8b8 !important;
                font-size: 16px !important;
                text-shadow: 0 0 6px rgba(0,0,0,0.95) !important;
            }
            .char-card-enter {
                background: rgba(50, 38, 18, 0.95) !important;
                color: #f5d676 !important;
                border: 2px solid #d4af37 !important;
            }
        """)
        page.wait_for_timeout(400)

        # 7명 순회 — galleryDots[i].click() 으로 본관 갤러리 직접 전환
        for i, (key, expected_name) in enumerate(EXPECTED_ORDER):
            goto_result = goto_card_index(page, i)
            # transition 0.45s 제거됐으므로 짧게 대기 (DOM 업데이트 + layout)
            page.wait_for_timeout(400)
            # 매 전환마다 모달 재출현 점검 (안전망)
            dismiss_swipe_hint(page)

            # 비디오 첫 프레임 보장: readyState >= 2 (HAVE_CURRENT_DATA) 대기 + 시점 forward
            # card-gallery.js:54는 currentTime=0으로 리셋 → headless에서 첫 프레임 미렌더 위험
            video_status = page.evaluate(
                """(key) => {
                    const card = document.querySelector(`.char-card[data-character='${key}']`);
                    if (!card) return {error:'no_card'};
                    const v = card.querySelector('.char-card-video');
                    if (!v) return {error:'no_video', has_video: false};
                    // 강제 currentTime forward + readyState 점검
                    try { v.currentTime = 0.6; } catch (_) {}
                    return {
                        src: v.querySelector('source')?.src || null,
                        readyState: v.readyState,
                        currentTime: v.currentTime,
                        duration: v.duration,
                        paused: v.paused,
                    };
                }""",
                key,
            )
            # readyState 2 이상 대기 (최대 3초)
            for _ in range(15):
                if isinstance(video_status, dict) and video_status.get("readyState", 0) >= 2:
                    break
                page.wait_for_timeout(200)
                video_status = page.evaluate(
                    """(key) => {
                        const card = document.querySelector(`.char-card[data-character='${key}']`);
                        const v = card ? card.querySelector('.char-card-video') : null;
                        if (!v) return {has_video: false, readyState: 0};
                        return {readyState: v.readyState, currentTime: v.currentTime};
                    }""",
                    key,
                )
            # 프레임 그리기 최종 대기
            page.wait_for_timeout(400)

            meta = get_active_card_meta(page)
            screenshot_path = output_dir / f"{i+1:02d}_{key}.png"

            # ★ 좌표 모호함 우회: 활성 카드를 body 직하 fixed position으로 임시 이동
            # → viewport 좌상단 고정 좌표에서 깔끔히 element screenshot 가능
            # 캡처 후 원래 위치 복원
            page.evaluate(
                """(key) => {
                    const card = document.querySelector(`.char-card[data-character='${key}']`);
                    if (!card) return false;
                    // 원본 부모·다음 형제 기억 (복원용)
                    card._origParent = card.parentNode;
                    card._origNext = card.nextSibling;
                    card._origStyle = card.getAttribute('style') || '';
                    // body 직하 fixed 이동
                    document.body.appendChild(card);
                    card.style.cssText = `
                        position: fixed !important;
                        left: 0 !important;
                        top: 0 !important;
                        width: 414px !important;
                        height: 552px !important;
                        z-index: 99999 !important;
                        display: block !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                        transform: none !important;
                    `;
                    return true;
                }""",
                key,
            )
            page.wait_for_timeout(300)
            try:
                target = page.locator(f".char-card[data-character='{key}']").first
                target.screenshot(path=str(screenshot_path))
            except Exception as e:
                print(f"  ⚠ element screenshot 실패: {e}")
                page.screenshot(path=str(screenshot_path))
            # 카드를 원래 위치 복원 (다음 iteration 정상 진행 보장)
            page.evaluate(
                """(key) => {
                    const card = document.querySelector(`.char-card[data-character='${key}']`);
                    if (!card || !card._origParent) return;
                    if (card._origNext) {
                        card._origParent.insertBefore(card, card._origNext);
                    } else {
                        card._origParent.appendChild(card);
                    }
                    card.setAttribute('style', card._origStyle || '');
                }""",
                key,
            )
            page.wait_for_timeout(200)

            match = meta.get("data_character") == key
            status = "✅" if match else "⚠"
            print(
                f"  [{i+1}/7] {status} 기대 {expected_name}({key}) / "
                f"실제 {meta.get('name')}({meta.get('data_character')}) "
                f"[goto={goto_result.get('ok')}]"
            )
            results.append({
                "idx": i,
                "expected_key": key,
                "expected_name": expected_name,
                "actual_key": meta.get("data_character"),
                "actual_name": meta.get("name"),
                "sub": meta.get("sub"),
                "quote": meta.get("quote"),
                "enter_label": meta.get("enter_label"),
                "body_class": meta.get("body_class"),
                "match": match,
                "screenshot": screenshot_path.name,
            })

        # 마지막에서 한 칸 뒤로 — prev() 동등
        goto_card_index(page, 5)  # 옥선 할미로 복귀
        page.wait_for_timeout(700)
        back_meta = get_active_card_meta(page)
        print(f"  [뒤로 1회] 활성: {back_meta.get('name')} ({back_meta.get('data_character')})")
        page.screenshot(path=str(output_dir / "08_after_back.png"), full_page=False)

        summary = {
            "site_url": SITE_URL,
            "timestamp": timestamp,
            "initial": initial_meta,
            "forward_results": results,
            "after_back_left": back_meta,
            "all_match": all(r["match"] for r in results),
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"\n저장: {output_dir}")
        print(f"  스크린샷 8장 + summary.json")
        print(f"  전체 일치: {'✅' if summary['all_match'] else '⚠ 일부 불일치'}")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    swipe_all(headless=args.headless)


if __name__ == "__main__":
    main()
