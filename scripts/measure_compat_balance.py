"""ADR-093 라이브 측정 — 궁합 3 mode 각 10회 호출 평균 균형도.

본 스크립트는 본 시스템 라이브 (https://saju-mbti-fusion.fly.dev) 호출 후
ADR-092 (긍정·부정 1:1 지시) 라이브 효과 객관 측정.

용도: ADR-092·093 라이브 검증 + 향후 회귀 데이터 누적.
"""

from __future__ import annotations

import json
import time

import httpx

from engine.saju.balance_meter import measure_batch


_API_URL = "https://saju-mbti-fusion.fly.dev/api/saju/compat"

_TEST_PAYLOAD = {
    "a": {"dt_local": "1988-08-15T12:00:00", "gender": "M", "name_ko": "김행복", "mbti": "INTJ"},
    "b": {"dt_local": "1975-04-22T12:00:00", "gender": "F", "name_ko": "이고난", "mbti": "ENFP"},
    "interpret": True,
    "lang": "ko",
}


def call_once(mode: str, client: httpx.Client) -> str | None:
    """단일 호출 → interpretation 본문 반환."""
    payload = dict(_TEST_PAYLOAD)
    payload["relation_mode"] = mode
    try:
        resp = client.post(_API_URL, json=payload, timeout=60.0)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("interpretation", "") or ""
    except Exception as e:
        print(f"  ⚠ 호출 실패: {e}")
        return None


def measure_mode(mode: str, n: int = 10) -> dict:
    """N회 호출 → 균형도 평균."""
    texts: list[str] = []
    with httpx.Client() as client:
        for i in range(n):
            t = call_once(mode, client)
            if t:
                texts.append(t)
                print(f"  [{i+1}/{n}] {len(t)}자 수집")
            else:
                print(f"  [{i+1}/{n}] 실패")
            time.sleep(0.5)  # rate limit
    batch = measure_batch(texts)
    batch["mode"] = mode
    return batch


def main() -> None:
    modes = ["romantic", "friend", "work"]
    print("=" * 70)
    print("ADR-093 라이브 균형도 측정 — 각 mode 10회 호출")
    print("=" * 70)
    results = []
    for mode in modes:
        print(f"\n### {mode}")
        result = measure_mode(mode, n=10)
        results.append(result)
        print(
            f"  결과: avg={result['avg_balance_pct']}% "
            f"min={result['min_balance_pct']}% max={result['max_balance_pct']}% "
            f"verdict={result['verdict']} (n={result['count']})"
        )

    print()
    print("=" * 70)
    print("종합")
    print("=" * 70)
    for r in results:
        print(
            f"{r['mode']:12} avg={r['avg_balance_pct']:5.1f}% "
            f"[min {r['min_balance_pct']:.1f}, max {r['max_balance_pct']:.1f}] "
            f"→ {r['verdict']}"
        )

    # 파일 저장
    out_path = "C:/tmp/adr_093_balance_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            [{k: v for k, v in r.items() if k != "samples"} for r in results],
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main()
