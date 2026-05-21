"""star(성하 공자) 전체 메뉴 카드 8장 라이브 검증 + 자동 평가.

본 시스템 star 도메인 (ADR-068·106·107·114):
- ADR-068: 12 황도대 + 7 일일 톤 결정론
- ADR-106: 144 별자리 궁합 매트릭스
- ADR-107: 한국 천상열차분야지도 28수
- ADR-114: Skyfield + JPL DE440s 빅3·하우스·트랜짓·시너스트리

검증:
1. 무료 (today-zodiac, big3): LLM 응답 + 단정 어휘 검사
2. 프리미엄 (classic·love-stars·compatibility·east28·transit·saju-star): 결제 모달 표시 검증
3. star + 사주 융합 (saju-star, big3 with birth): wants_saju 분기 본문화 검증
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.stderr.write("playwright 미설치\n"); sys.exit(1)


SITE = "https://saju-mbti-fusion.fly.dev/"

# star 메뉴 카드 8장 + 입력 시나리오 (★ birth + hourBranch 명시 입력)
CARDS = [
    # (key, name, kind, inputs)
    ("today-zodiac", "오늘의 별자리 운세", "free",
        {"sign": "leo"}),
    ("big3", "빅3 분석", "free",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未", "birthplace": "서울"}),
    ("classic", "정통 별빛 풀이", "premium",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未", "birthplace": "서울"}),
    ("love-stars", "별의 연서", "premium",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未", "birthplace": "서울", "status": "single"}),
    ("compatibility", "별자리 궁합", "premium",
        {"mySign": "taurus", "partnerSign": "cancer", "relation": "romance"}),
    ("east28", "동양 28수 풀이", "premium",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未"}),
    ("transit", "행운의 시기", "premium",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未", "concern": "이직 시기를 알고 싶어요"}),
    ("saju-star", "사주 + 별빛 통합 분석", "premium",
        {"fullName": "김준수", "birth": "1990-05-15", "hourBranch": "未", "birthplace": "서울", "gender": "M"}),
]

FORBIDDEN = ["반드시", "확실히", "100%", "단명", "이혼수", "파산 확정", "배우자 사망",
             "결혼 실패", "재물운이 막힐", "운명적 결정"]


def fill_field(page, key, value):
    """필드 ID 기반 입력 (cf_{key} + ymd 분기).

    본 시스템 구조 (content-system.js):
    - 일반 필드: <select id="cf_{key}"> 또는 <input id="cf_{key}">
    - ymd: <select id="cf_{key}_year/_month/_day"> 3개 (ID 통일 후)
    - hour-branch: <select id="cf_{key}"> (단순 select, 본 fn SELECT 분기)
    - gender: <select id="cf_{key}"> (단순 select)
    """
    el_id = f"cf_{key}"
    info = page.evaluate(f"() => {{const e=document.getElementById('{el_id}'); return e ? {{tag:e.tagName, type:e.type||''}} : null;}}")

    if not info:
        # ymd 3-select 처리 (id 통일 후 _year/_month/_day)
        info_y = page.evaluate(f"() => document.getElementById('cf_{key}_year') ? true : false")
        if info_y:
            if value and isinstance(value, str) and "-" in value:
                parts = value.split("-")
                y, m, d = parts[0], str(int(parts[1])), str(int(parts[2]))
            else:
                y, m, d = "1990", "5", "15"
            try:
                page.locator(f"#cf_{key}_year").select_option(y)
                page.locator(f"#cf_{key}_month").select_option(m)
                page.locator(f"#cf_{key}_day").select_option(d)
                return True
            except Exception as e:
                print(f"    ymd 입력 실패 ({key}): {e}")
                return False
        return False

    if info["tag"] == "SELECT":
        try:
            page.locator(f"#{el_id}").select_option(value)
            return True
        except Exception as e:
            print(f"    select 실패 ({key}={value}): {e}")
            return False
    else:
        loc = page.locator(f"#{el_id}")
        loc.click()
        loc.fill(value)
    return True


def test_card(page, card_key, card_name, kind, inputs, out_dir):
    print(f"\n[{card_key}] {card_name} ({kind})")
    result = {"card": card_key, "name": card_name, "kind": kind}

    page.goto(SITE + f"?v={int(time.time())}", wait_until="domcontentloaded")
    page.wait_for_selector(".char-card", state="attached", timeout=20000)
    page.wait_for_timeout(2500)
    page.evaluate("""
        const sh = document.querySelector('#swipeHint'); if (sh) sh.remove();
        const v = document.querySelector('.swipe-hint-veil'); if (v) v.remove();
    """)
    page.evaluate("window.__menuOpen('star')")
    page.wait_for_timeout(1200)
    page.evaluate(f"document.querySelector(\"#menuGrid .menu-card[data-content-key='{card_key}']\").click()")
    page.wait_for_timeout(1500)

    has_cta = page.evaluate("() => !!document.querySelector('#contentCtaBtn')")
    if not has_cta:
        state = page.evaluate("""() => ({
            body_class: document.body.className,
        })""")
        result["state"] = state
        result["evaluation"] = f"tab 위임 (CTA 미렌더, body_class={state['body_class']})"
        page.screenshot(path=str(out_dir / f"{card_key}.png"))
        result["screenshot"] = f"{card_key}.png"
        print(f"  → tab 위임 라우팅")
        return result

    # 입력
    filled = []
    for k, v in inputs.items():
        if fill_field(page, k, v):
            filled.append(k)
    result["filled"] = filled
    print(f"  입력: {filled}")

    cta_info = page.evaluate("""() => {
        const b = document.querySelector('#contentCtaBtn');
        return b ? {tier: b.dataset.tier, label: b.textContent.trim()} : null;
    }""")
    result["cta"] = cta_info
    page.click("#contentCtaBtn")
    page.wait_for_timeout(1500)

    if kind == "free":
        print("  LLM 응답 대기...")
        response_text = None
        for _ in range(35):
            page.wait_for_timeout(2000)
            r = page.evaluate("""() => {
                const el = document.querySelector('#contentResult');
                return el && el.innerText.trim().length > 200 ? el.innerText.trim() : null;
            }""")
            if r:
                response_text = r
                break
        page.screenshot(path=str(out_dir / f"{card_key}.png"), full_page=True)
        result["screenshot"] = f"{card_key}.png"
        if response_text:
            forbidden_hits = [w for w in FORBIDDEN if w in response_text]
            input_str = " ".join(str(v) for v in inputs.values() if v)
            input_terms = [w for w in input_str.split() if len(w) >= 2 and w in response_text]
            # star 도메인 결정론 키워드 점검 (별자리 명·점성술 어휘)
            star_terms = ["별자리", "황도", "별", "태양", "달", "행성", "하우스"]
            star_term_hits = [t for t in star_terms if t in response_text]
            result["evaluation"] = {
                "단정 어휘": forbidden_hits if forbidden_hits else "없음 ✅",
                "입력 반영 키워드 개수": len(input_terms),
                "star 도메인 어휘 개수": len(star_term_hits),
                "응답 길이": len(response_text),
            }
            result["response_excerpt"] = response_text[:400]
            print(f"  응답 {len(response_text)}자, 단정={result['evaluation']['단정 어휘']}, star어휘={len(star_term_hits)}")
        else:
            result["evaluation"] = "❌ 응답 timeout"
            print(f"  ❌ 응답 timeout")

    elif kind == "premium":
        page.wait_for_timeout(1000)
        modal = page.evaluate("""() => {
            const m = document.querySelector('.premium-prompt-modal');
            if (!m) return null;
            return {
                title: m.querySelector('.premium-prompt-title')?.textContent?.trim(),
                has_close: !!m.querySelector('[data-action=close]'),
                has_info: !!m.querySelector('[data-action=info]'),
                has_disclaimer: !!m.querySelector('.premium-prompt-disclaimer'),
            };
        }""")
        page.screenshot(path=str(out_dir / f"{card_key}.png"))
        result["screenshot"] = f"{card_key}.png"
        result["modal"] = modal
        if modal:
            ok = all([modal["title"], modal["has_close"], modal["has_info"], modal["has_disclaimer"]])
            result["evaluation"] = f"✅ 모달 표시 (전부 OK)" if ok else f"⚠ 부분: {modal}"
            print(f"  {result['evaluation']}")
            page.click("[data-action=close]")
            page.wait_for_timeout(400)
        else:
            # 베타 모드(window.WHM_BETA_MODE)에서는 모달 X, LLM 응답 직접 출력
            print("  모달 미표시 — 베타 모드 LLM 응답 대기...")
            response_text = None
            for _ in range(35):
                page.wait_for_timeout(2000)
                r = page.evaluate("""() => {
                    const el = document.querySelector('#contentResult');
                    return el && el.innerText.trim().length > 200 ? el.innerText.trim() : null;
                }""")
                if r:
                    response_text = r
                    break
            page.screenshot(path=str(out_dir / f"{card_key}.png"), full_page=True)
            if response_text:
                forbidden_hits = [w for w in FORBIDDEN if w in response_text]
                input_str = " ".join(str(v) for v in inputs.values() if v)
                input_terms = [w for w in input_str.split() if len(w) >= 2 and w in response_text]
                star_terms = ["별자리", "황도", "태양", "달", "상승", "행성", "하우스", "28수", "트랜짓", "ADR-114", "황소자리", "사자자리", "물병자리", "처녀자리", "전갈자리", "물고기자리", "양자리"]
                star_term_hits = [t for t in star_terms if t in response_text]
                result["evaluation"] = {
                    "베타 무료 응답 ✅": True,
                    "단정 어휘": forbidden_hits if forbidden_hits else "없음 ✅",
                    "입력 반영 키워드 개수": len(input_terms),
                    "star 도메인 어휘 개수": len(star_term_hits),
                    "응답 길이": len(response_text),
                }
                result["response_excerpt"] = response_text[:400]
                print(f"  응답 {len(response_text)}자, 단정={result['evaluation']['단정 어휘']}, star어휘={len(star_term_hits)}")
            else:
                result["evaluation"] = "❌ 응답 timeout (베타 모드)"
                print(f"  ❌ 응답 timeout")

    return result


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).resolve().parent.parent / "step_archive" / f"star_full_eval_{ts}"
    out.mkdir(parents=True, exist_ok=True)

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        ctx = browser.new_context(viewport={"width":414,"height":896}, device_scale_factor=2, is_mobile=True, locale="ko-KR")
        page = ctx.new_page()
        for k, n, kd, ins in CARDS:
            try:
                r = test_card(page, k, n, kd, ins, out)
                results.append(r)
            except Exception as e:
                print(f"  ❌ {k} 예외: {e}")
                results.append({"card": k, "error": str(e)})
        (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n저장: {out}")
        browser.close()

    # 종합 요약
    print("\n" + "=" * 60)
    print("star 8 카드 종합 평가")
    print("=" * 60)
    for r in results:
        line = f"  {r.get('card','?'):<16}"
        if "error" in r:
            line += f"  ❌ {r['error'][:50]}"
        elif isinstance(r.get("evaluation"), dict):
            ev = r["evaluation"]
            line += f"  ✅ {ev.get('단정 어휘')} / star={ev.get('star 도메인 어휘 개수','?')} / len={ev.get('응답 길이','?')}"
        else:
            line += f"  → {r.get('evaluation','?')}"
        print(line)


if __name__ == "__main__":
    main()
