"""라이브 손금 페이지 Playwright 직접 테스트 v2 — desktop viewport + 정확 셀렉터."""
from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        # 데스크톱 뷰포트
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        network_errors = []
        api_palm_responses = []

        def on_response(resp):
            if "/api/palm/reading" in resp.url:
                api_palm_responses.append((resp.status, resp.url))
                print(f"  >>> /api/palm/reading 응답: HTTP {resp.status}")
                try:
                    body = resp.json()
                    print(f"      text: {body.get('text', '(없음)')[:400]}")
                    print(f"      cached: {body.get('cached')}")
                    print(f"      llm_fallback: {body.get('llm_fallback')}")
                    print(f"      safety_verdict: {body.get('safety_verdict')}")
                    print(f"      safety_failures: {body.get('safety_failures')}")
                    print(f"      safety_fallback_used: {body.get('safety_fallback_used')}")
                except Exception:
                    pass
            if resp.status >= 400 and "/api/" in resp.url:
                network_errors.append(f"{resp.status} {resp.url}")
                print(f"  NETWORK ERROR {resp.status} {resp.url}")

        page.on("response", on_response)

        # 1. 사이트 접속
        print("[1] 데스크톱 뷰포트로 saju-mbti-fusion.fly.dev 접속")
        page.goto("https://saju-mbti-fusion.fly.dev/", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)
        page.screenshot(path="step_archive/palm2_01_landing.png", full_page=True)

        # 2. 모달 있으면 닫기 (성인 인증 등)
        print("[2] 모달 닫기 시도")
        for sel in ["text=돌아가기", "[aria-label='close']", ".modal-close", "button.close"]:
            try:
                page.click(sel, timeout=2000)
                print(f"  닫음: {sel}")
                break
            except Exception:
                continue
        time.sleep(1)

        # 3. 옥선 할미(palm) 카드 클릭
        print("[3] data-go='palm' 클릭")
        try:
            # 카드를 화면 안으로 스크롤
            page.locator("[data-go='palm']").first.scroll_into_view_if_needed(timeout=10000)
            time.sleep(1)
            page.locator("[data-go='palm']").first.click(timeout=10000)
            print("  팜 카드 클릭 OK")
        except Exception as e:
            print(f"  실패: {e}")
            # 탭 버튼 시도
            try:
                page.click("[data-tab='palm']", timeout=5000)
                print("  탭 버튼 클릭 OK")
            except Exception as e2:
                print(f"  탭도 실패: {e2}")

        time.sleep(3)
        page.screenshot(path="step_archive/palm2_02_palm_tab.png", full_page=True)

        # 4. 손바닥 이미지 업로드
        print("[4] 손바닥 이미지 업로드")
        test_img = r"D:\palm_dataset\eval_holdout\Hand_0000068.jpg"
        file_inputs = page.locator("input[type='file']").all()
        print(f"  file inputs found: {len(file_inputs)}")

        # palm-관련 input 찾기
        for inp in file_inputs:
            try:
                accept = inp.get_attribute("accept") or ""
                input_id = inp.get_attribute("id") or ""
                name = inp.get_attribute("name") or ""
                print(f"  input: id={input_id} name={name} accept={accept[:30]}")
                if "image" in accept or "palm" in input_id.lower() + name.lower():
                    inp.set_input_files(test_img)
                    print(f"    업로드: {test_img}")
                    break
            except Exception as e:
                print(f"    skip: {e}")
        time.sleep(3)
        page.screenshot(path="step_archive/palm2_03_uploaded.png", full_page=True)

        # 5. 제출 버튼 찾기 (palm-reader.js의 흐름)
        print("[5] 제출 버튼 찾기")
        candidates = [
            "#palmSubmitBtn", "[data-action='palm-submit']",
            "button:has-text('손금 보기')", "button:has-text('풀이 시작')",
            "button:has-text('풀이')", "button:has-text('보기')",
            "button:has-text('시작')", "button[type='submit']",
        ]
        clicked = False
        for sel in candidates:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1000):
                    btn.click(timeout=3000)
                    print(f"  클릭 OK: {sel}")
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            # 모든 button 후보 출력
            btns = page.locator("button").all()
            print(f"  모든 button: {len(btns)}건")
            for i, b in enumerate(btns[:15]):
                try:
                    txt = b.inner_text(timeout=500).strip()
                    if txt:
                        print(f"    [{i}] {txt[:50]}")
                except Exception:
                    pass

        # 6. /api/palm/reading 응답 대기 (최대 90초)
        print("[6] /api/palm/reading 응답 대기 (90초)")
        deadline = time.time() + 90
        while time.time() < deadline and not api_palm_responses:
            time.sleep(2)

        time.sleep(5)
        page.screenshot(path="step_archive/palm2_04_result.png", full_page=True)

        # 7. 결과 영역
        print("[7] 결과 텍스트")
        try:
            result = page.inner_text("#palmResultBoard, .face-result-card")
            print(f"  화면 결과:\n{result[:1500]}")
        except Exception:
            print("  결과 영역 추출 실패")

        print("\n" + "=" * 60)
        print(f"[/api/palm/reading 호출 {len(api_palm_responses)}건]")
        for code, url in api_palm_responses:
            print(f"  HTTP {code}: {url}")
        print(f"[네트워크 오류 {len(network_errors)}건]")

        time.sleep(8)
        browser.close()


if __name__ == "__main__":
    main()
