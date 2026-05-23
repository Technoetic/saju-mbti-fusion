"""ADR-159 Phase 1.5 — MediaPipe 프론트 통합 정적 검증.

검증 항목:
1. face-metrics.js 로드 → window.FaceMetrics 노출 확인
2. MediaPipe SDK CDN 동적 import 성공 확인
3. 빈 canvas로 computeMetrics 호출 → graceful null 반환 (폴백 정상)
4. 실제 얼굴 데이터는 사용자 직접 검증 영역 (브라우저 카메라 권한 필요)

본 검증은 로컬 서버 (http://127.0.0.1:8000) 대상.
"""
from __future__ import annotations
import sys
import time
from playwright.sync_api import sync_playwright

SITE = "http://127.0.0.1:8000/"

def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 414, "height": 896}, is_mobile=True, locale="ko-KR")
        page = ctx.new_page()

        console_msgs: list[str] = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))

        page.goto(SITE + f"?v={int(time.time())}", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 1. window.FaceMetrics 노출
        face_metrics_exists = page.evaluate("() => typeof window.FaceMetrics === 'object' && typeof window.FaceMetrics.computeMetrics === 'function'")
        if not face_metrics_exists:
            failures.append("window.FaceMetrics 미노출")
        else:
            print("PASS 1: window.FaceMetrics.computeMetrics 노출 OK")

        # 2. MediaPipe SDK 동적 import (빈 캔버스로 호출 — 모델 로드만 트리거)
        sdk_load = page.evaluate("""
            async () => {
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = 256; canvas.height = 256;
                    const ctx2d = canvas.getContext('2d');
                    ctx2d.fillStyle = '#000';
                    ctx2d.fillRect(0, 0, 256, 256);
                    const t0 = performance.now();
                    const result = await window.FaceMetrics.computeMetrics(canvas);
                    const elapsed = performance.now() - t0;
                    return { ok: true, elapsed_ms: Math.round(elapsed), result_is_null: result === null };
                } catch (e) {
                    return { ok: false, error: String(e) };
                }
            }
        """)
        if not sdk_load.get("ok"):
            failures.append(f"MediaPipe SDK 로드/호출 실패: {sdk_load.get('error')}")
        else:
            print(f"PASS 2: MediaPipe SDK 로드 + 호출 OK ({sdk_load['elapsed_ms']}ms)")
            # 3. 빈 캔버스(얼굴 없음) → null 폴백
            if sdk_load.get("result_is_null"):
                print("PASS 3: 얼굴 미검출 시 null 폴백 정상")
            else:
                failures.append("얼굴 미검출인데 null이 아님 — 폴백 위반")

        # 콘솔 경고 출력 (디버깅용)
        if console_msgs:
            print("\n--- 브라우저 콘솔 ---")
            for m in console_msgs[-20:]:
                print(m)

        b.close()

    print("\n=" * 1, "=" * 40)
    if failures:
        print(f"FAIL ({len(failures)}건)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS — ADR-159 정적 검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
