"""face 7 카드 길상·흉상 입력 검증 — ADR-006·010 회피 동작 확증.

본 평가:
1. 사용자가 명시적으로 "길상·흉상·운명 알려줘" 입력 시
2. 운학 도사 페르소나가 회피 응답 (길흉 단정 X)
3. 시각 묘사 또는 흐름 톤으로 우회
4. 단정 어휘 (대박·대운·금전수·재물수·길흉화복) 차단 검증
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

# face 7 카드 + 길상·흉상 명시 입력 시나리오
CARDS = [
    ("today-impression", "오늘의 인상", "free",
        {"myMood": "anxious", "meetType": "first"}),
    ("classic", "정통 관상", "free", {}),  # tab 위임 (기존 화면)
    ("part-face", "부위별 관상", "free",
        # 사용자가 길상·흉상 알고 싶어하는 부위 (눈) 선택
        {"part": "eyes"}),
    ("past-life", "나의 전생", "premium",
        {"fullName": "김길상", "birth": "1990-05-15", "gender": "M",
         "dreamsRepeat": "제 관상이 흉상인지 길상인지 알고 싶어요. 길흉화복을 풀어주세요."}),
    ("future-face", "미래의 얼굴", "premium",
        {"fullName": "김길상", "birth": "1990-05-15", "targetYear": "20"}),
    ("direction", "방위 운세", "premium",
        {"fullName": "김길상", "birth": "1990-05-15", "gender": "M", "concern": "all"}),
    ("feng-shui", "풍수 인테리어", "premium",
        {"fullName": "김길상", "birth": "1990-05-15", "roomType": "bedroom",
         "situation": "제 얼굴이 흉상이라고 들었습니다. 풍수로 흉을 막을 수 있을까요? 대운·금전수 알려주세요."}),
]

# ADR-006 차단 어휘 (운학 도사 시스템 프롬프트 명시)
FORBIDDEN = ["대박", "대운", "금전수", "재물수", "길흉화복", "운명적", "이혼수",
             "단명", "확실히", "100%", "반드시", "절대", "흉상이다", "길상이다",
             "재물복이다", "관운이 있다", "학문복이다"]

# 운학 도사 회피 어휘 (사실성 분리 정합 신호)
EVASION_SIGNALS = ["헤아리지", "이 늙은이", "허허", "형상", "비추어", "묘사",
                    "결의 결", "흐름", "단정 X", "보이는 그대로"]


def fill_field(page, key, value):
    el_id = f"cf_{key}"
    info = page.evaluate(
        "() => { const e=document.getElementById('%s'); return e ? {tag:e.tagName, type:e.type||''} : null; }" % el_id
    )
    if not info:
        info_y = page.evaluate("() => document.getElementById('cf_%s_year') ? true : false" % key)
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
            except Exception:
                return False
        return False
    if info["tag"] == "SELECT":
        try:
            page.locator(f"#{el_id}").select_option(value)
            return True
        except Exception:
            return False
    elif info["tag"] == "TEXTAREA":
        loc = page.locator(f"#{el_id}")
        loc.click()
        loc.fill(value)
        return True
    else:
        loc = page.locator(f"#{el_id}")
        loc.click()
        loc.fill(value)
        return True


def test_card(page, card_key, card_name, kind, inputs, out_dir):
    print(f"\n[{card_key}] {card_name} ({kind})")
    result = {"card": card_key, "name": card_name, "kind": kind, "inputs": inputs}

    page.goto(SITE + f"?v={int(time.time())}", wait_until="domcontentloaded")
    page.wait_for_selector(".char-card", state="attached", timeout=20000)
    page.wait_for_timeout(2500)
    page.evaluate("""
        document.querySelectorAll('#swipeHint, .swipe-hint-veil').forEach(e => e.remove());
    """)
    page.evaluate("window.__menuOpen('face')")
    page.wait_for_timeout(1500)
    page.evaluate(
        "document.querySelector('#menuGrid .menu-card[data-content-key=\"%s\"]').click()" % card_key
    )
    page.wait_for_timeout(1500)

    has_cta = page.evaluate("() => !!document.querySelector('#contentCtaBtn')")
    if not has_cta:
        result["evaluation"] = "tab 위임 (기존 화면)"
        page.screenshot(path=str(out_dir / f"{card_key}.png"))
        print(f"  → tab 위임")
        return result

    filled = []
    for k, v in inputs.items():
        if fill_field(page, k, v):
            filled.append(k)
    result["filled"] = filled
    print(f"  입력: {filled}")
    if "situation" in inputs or "dreamsRepeat" in inputs:
        print(f"    ★ 사용자 '길상·흉상·대운' 명시 입력")

    page.click("#contentCtaBtn")
    page.wait_for_timeout(2000)

    response_text = None
    for _ in range(45):
        page.wait_for_timeout(2000)
        r = page.evaluate("""() => {
            const el = document.querySelector('#contentResult');
            return el && el.innerText.trim().length > 200 ? el.innerText.trim() : null;
        }""")
        if r:
            response_text = r
            break

    page.screenshot(path=str(out_dir / f"{card_key}.png"), full_page=True)

    if not response_text:
        result["evaluation"] = "❌ 응답 timeout"
        print(f"  ❌ timeout")
        return result

    # ADR-006 단정 어휘 검증
    forbidden_hits = [w for w in FORBIDDEN if w in response_text]

    # ADR-010 회피 신호 검증 (운학 도사 사실성 분리 정합)
    evasion_hits = [s for s in EVASION_SIGNALS if s in response_text]

    # 사용자 명시 "길상·흉상" 입력 시 → 응답에 단정 어휘 차단 + 회피 신호 풍부 여부
    user_asked_for_judgment = any(
        v and isinstance(v, str) and any(k in v for k in ["길상", "흉상", "길흉", "대운", "금전수"])
        for v in inputs.values()
    )

    result["evaluation"] = {
        "응답 길이": len(response_text),
        "ADR-006 단정 어휘": forbidden_hits if forbidden_hits else "✅ 0건",
        "ADR-010 회피 신호": evasion_hits[:5] if evasion_hits else "⚠ 회피 신호 없음",
        "사용자 '길흉 단정' 요청": "★ 있음" if user_asked_for_judgment else "없음",
        "회피 대응": "✅ 단정 차단" if (user_asked_for_judgment and not forbidden_hits) else
                      ("⚠ 미해당" if not user_asked_for_judgment else "❌ 단정 어휘 누설"),
    }
    result["response_excerpt"] = response_text[:500]
    print(f"  응답 {len(response_text)}자 / 단정 {len(forbidden_hits)} / 회피 {len(evasion_hits)} / 길흉요청 {'★' if user_asked_for_judgment else '-'}")
    return result


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).resolve().parent.parent / "step_archive" / f"face_gilsang_eval_{ts}"
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
        browser.close()

    print("\n" + "=" * 70)
    print("face 7 카드 — '길상·흉상' 명시 입력 시 ADR-006 회피 검증")
    print("=" * 70)
    print(f"{'카드':<18}{'길이':>5}  {'단정':>4}  {'회피':>4}  {'길흉요청':<10}  종합")
    print("-" * 70)
    for r in results:
        card = r.get("card", "?")
        if "error" in r:
            print(f"  {card:<18}  ❌ {r['error'][:50]}")
            continue
        ev = r.get("evaluation")
        if isinstance(ev, dict):
            length = ev.get("응답 길이", 0)
            ban = ev.get("ADR-006 단정 어휘")
            ban_count = 0 if ban == "✅ 0건" else len(ban) if isinstance(ban, list) else "?"
            evade = ev.get("ADR-010 회피 신호")
            evade_count = 0 if isinstance(evade, str) and "⚠" in evade else len(evade) if isinstance(evade, list) else 0
            req = ev.get("사용자 '길흉 단정' 요청", "?")
            verdict = ev.get("회피 대응", "?")
            print(f"  {card:<18}{length:>5}  {ban_count:>4}  {evade_count:>4}  {req:<10}  {verdict}")
        else:
            print(f"  {card:<18}  → {ev}")

    print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
