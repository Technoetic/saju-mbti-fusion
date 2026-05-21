"""ADR-098 A/B 테스트 — dream Flash Lite vs Flash 효과 측정.

본 시스템 라이브 (https://saju-mbti-fusion.fly.dev) 호출 시 DREAM_MODEL Secret
설정 필요 (Fly.io 환경변수). 본 PC fly auth 무 → 사용자 결단 영역.

대안: 본 PC에서 BIZROUTER_API_KEY 등록 후 직접 호출 (각 모델 N회 × 7 콘텐츠).
"""

from __future__ import annotations

import json
import os
import time

import httpx

from engine.saju.balance_meter import measure_balance


_API_URL = "https://saju-mbti-fusion.fly.dev/api/content/reading"

_TEST_PAYLOAD = {
    "char_key": "dream",
    "fields": {
        "dreamText": "하늘을 나는 꿈을 꾸었어. 큰 용이 나타나 나를 등에 태우고 구름 위로 올라갔어.",
        "birth": "1990-05-15",
        "gender": "F",
        "isPregnant": "true",
        "mbti": "INFP",
    },
}

_CONTENTS = ["today", "dict", "classic", "recurring", "baby", "nightmare", "lucid"]
_REPEAT = 5  # 콘텐츠당 5회 (총 35회 × 2 모델 = 70 호출)


def call_once(content_key: str, client: httpx.Client) -> str | None:
    payload = dict(_TEST_PAYLOAD)
    payload["content_key"] = content_key
    try:
        resp = client.post(_API_URL, json=payload, timeout=60.0)
        if resp.status_code != 200:
            print(f"    [{content_key}] HTTP {resp.status_code}")
            return None
        return resp.json().get("text", "") or ""
    except Exception as e:
        print(f"    [{content_key}] Exception: {e}")
        return None


def measure_content(content_key: str) -> dict:
    """7 콘텐츠 중 1 콘텐츠 N회 호출 + 측정."""
    texts = []
    with httpx.Client() as c:
        for i in range(_REPEAT):
            t = call_once(content_key, c)
            if t:
                texts.append(t)
            time.sleep(0.5)

    if not texts:
        return {"content": content_key, "n": 0, "verdict": "EMPTY"}

    # 측정
    gilmong = sum(1 for t in texts if "길몽" in t)
    schools_counts = []
    school_terms = ["Freud", "프로이트", "Jung", "융", "Hobson", "홉슨",
                    "Artemidorus", "아르테미", "민속", "민간", "한방",
                    "동의보감", "주역", "Ibn Sirin", "이븐", "LaBerge",
                    "Dormio", "Hartmann", "IRT", "Revonsuo", "TST"]
    for t in texts:
        schools_counts.append(sum(1 for s in school_terms if s in t))

    balances = [measure_balance(t).balance_pct for t in texts]

    return {
        "content": content_key,
        "n": len(texts),
        "gilmong_rate_pct": round(100 * gilmong / len(texts), 1),
        "schools_avg": round(sum(schools_counts) / len(schools_counts), 1),
        "balance_avg_pct": round(sum(balances) / len(balances), 1),
        "balance_min_pct": round(min(balances), 1),
        "balance_max_pct": round(max(balances), 1),
    }


def main() -> None:
    """A/B 측정 진입점.

    Note: 본 스크립트는 Fly.io 라이브 환경의 모델 설정을 직접 변경 불가.
    사용자가 Fly.io Secret DREAM_MODEL을 변경 후 (또는 변경 전후) 본 스크립트 실행.
    """
    current_model = os.environ.get("DREAM_MODEL", "(Fly Secret 의존)")
    print(f"=== ADR-098 A/B 측정 — DREAM_MODEL = {current_model} ===")
    print(f"콘텐츠 {len(_CONTENTS)}개 × 반복 {_REPEAT}회 = 총 {len(_CONTENTS) * _REPEAT}회 호출")
    print()

    results = []
    for content in _CONTENTS:
        print(f"  측정 중: {content}...")
        r = measure_content(content)
        results.append(r)
        print(
            f"    [{content}] n={r['n']} 길몽={r.get('gilmong_rate_pct', 0)}% "
            f"학파평균={r.get('schools_avg', 0)} 균형도={r.get('balance_avg_pct', 0)}%"
        )

    print()
    print("=" * 70)
    print("종합")
    print("=" * 70)
    for r in results:
        print(
            f"{r['content']:12} n={r['n']:2} 길몽={r.get('gilmong_rate_pct', '?'):>5}% "
            f"학파={r.get('schools_avg', '?'):>4} 균형도={r.get('balance_avg_pct', '?'):>5}%"
        )

    # JSON 저장
    out_path = f"C:/tmp/adr_098_ab_test_{current_model.replace('/', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"model": current_model, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main()
