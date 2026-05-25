"""라이브 손금 페이지 Playwright 직접 테스트."""
from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # 콘솔 + 네트워크 로깅
        console_logs = []
        network_errors = []

        def on_console(msg):
            text = f"[{msg.type}] {msg.text}"
            console_logs.append(text)
            if msg.type in ("error", "warning"):
                print(f"  CONSOLE {text[:200]}")

        def on_response(resp):
            if resp.status >= 400 and "/api/" in resp.url:
                network_errors.append(f"{resp.status} {resp.url}")
                print(f"  NETWORK ERROR {resp.status} {resp.url}")

        page.on("console", on_console)
        page.on("response", on_response)

        # 1. 사이트 접속
        print("[1] saju-mbti-fusion.fly.dev 접속")
        page.goto("https://saju-mbti-fusion.fly.dev/", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # 2. 페이지 스크린샷
        page.screenshot(path="step_archive/palm_test_01_landing.png", full_page=True)
        print(f"  스크린샷: step_archive/palm_test_01_landing.png")

        # 3. 손금 캐릭터(옥선 할미) 찾기 + 클릭
        print("[2] 손금 도메인 (옥선 할미) 클릭 시도")
        try:
            page.click("text=옥선 할미", timeout=10000)
        except Exception:
            # 다른 셀렉터 시도
            try:
                page.click("[data-character='palm']", timeout=5000)
            except Exception:
                # 손금 텍스트로 시도
                try:
                    page.click("text=손금", timeout=5000)
                except Exception as e:
                    print(f"  손금 캐릭터 클릭 실패: {e}")
                    # 페이지 소스 일부 출력
                    print("  body text sample:", page.inner_text("body")[:300])

        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)
        page.screenshot(path="step_archive/palm_test_02_character.png", full_page=True)

        # 4. 손바닥 이미지 업로드 input 찾기
        print("[3] 이미지 업로드 input 찾기")
        file_inputs = page.locator("input[type='file']").all()
        print(f"  file inputs found: {len(file_inputs)}")

        if file_inputs:
            test_img = r"D:\palm_dataset\eval_holdout\Hand_0000068.jpg"
            file_inputs[0].set_input_files(test_img)
            print(f"  업로드: {test_img}")
            time.sleep(3)
            page.screenshot(path="step_archive/palm_test_03_uploaded.png", full_page=True)

            # 5. 제출 버튼 찾기 + 클릭
            print("[4] 제출 버튼 클릭")
            try:
                page.click("button:has-text('풀이')", timeout=5000)
            except Exception:
                try:
                    page.click("button:has-text('보기')", timeout=5000)
                except Exception:
                    try:
                        page.click("button:has-text('시작')", timeout=5000)
                    except Exception as e:
                        print(f"  제출 버튼 클릭 실패: {e}")

            print("  결과 대기 (최대 60초)...")
            time.sleep(60)
            page.screenshot(path="step_archive/palm_test_04_result.png", full_page=True)

            # 6. 결과 영역 추출
            print("[5] 결과 텍스트 추출")
            try:
                result_text = page.inner_text("#palmResultBoard, .face-result-card, [class*='result']")
                print("  결과:", result_text[:1500])
            except Exception as e:
                print(f"  결과 추출 실패: {e}")

        # 7. 콘솔/네트워크 요약
        print()
        print("=" * 60)
        print(f"[콘솔 로그 총 {len(console_logs)}건]")
        for log in console_logs[-10:]:
            print(f"  {log[:200]}")
        print()
        print(f"[네트워크 오류 총 {len(network_errors)}건]")
        for err in network_errors:
            print(f"  {err}")

        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
