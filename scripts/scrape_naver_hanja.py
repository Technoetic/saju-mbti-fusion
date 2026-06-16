"""네이버 한자사전에서 한국어 훈음(訓音) 수집 → assets/hanja/hanja_meanings_naver.json.

대상: hanja_meanings.json 에서 영문/공란으로 폴백된 한자.
응답 필드: searchResultMap.searchResultListMap.LETTER.items[0].expKoreanPron
  예: 攸 → "바 유". <strong> 태그 제거.

출처: 네이버 한자사전 (데이터 ㈜오픈마인드인포테인먼트 e-hanja.kr).
개별 훈음은 사실·상식이나, 본 수집은 사용자 명시 지시 하에 진행.

사용:
  python scripts/scrape_naver_hanja.py --limit 20      # 검증
  python scripts/scrape_naver_hanja.py                  # 전체
"""
from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
MEANINGS = ROOT / "assets" / "hanja" / "hanja_meanings.json"
DB = ROOT / "assets" / "hanja" / "korean_hanja_unihan.json"
OUT = ROOT / "assets" / "hanja" / "hanja_meanings_naver.json"

API = "https://hanja.dict.naver.com/api3/ccko/search?query={q}&m=pc&range=letter"
_TAG = re.compile(r"<[^>]+>")


def _is_korean(s: str) -> bool:
    return bool(s) and any("가" <= c <= "힣" for c in s)


def targets() -> list[str]:
    mn = json.loads(MEANINGS.read_text(encoding="utf-8"))
    db = json.loads(DB.read_text(encoding="utf-8"))
    return [x["char"] for x in db if not _is_korean(mn.get(x["char"], ""))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0=전체")
    ap.add_argument("--sleep", type=float, default=0.25, help="요청 간 대기(초)")
    args = ap.parse_args()

    chars = targets()
    if args.limit:
        chars = chars[: args.limit]
    print(f"수집 대상: {len(chars)}자")

    # 이어받기: 기존 결과 로드
    result: dict[str, str] = {}
    if OUT.exists():
        result = json.loads(OUT.read_text(encoding="utf-8"))
        chars = [c for c in chars if c not in result]
        print(f"이어받기: 기존 {len(result)}자, 남은 {len(chars)}자")

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        # 한 번 페이지를 열어 쿠키·세션 확보
        pg.goto("https://hanja.dict.naver.com/#/main", wait_until="domcontentloaded", timeout=40000)
        pg.wait_for_timeout(1500)

        ok = fail = 0
        for i, ch in enumerate(chars):
            try:
                # 페이지 컨텍스트에서 fetch (Referer 검증 통과)
                data = pg.evaluate(
                    """async (url) => {
                        const r = await fetch(url, {headers: {'Accept':'application/json'}});
                        if (!r.ok) return null;
                        return await r.json();
                    }""",
                    API.format(q=ch),
                )
                pron = None
                try:
                    items = data["searchResultMap"]["searchResultListMap"]["LETTER"]["items"]
                    for it in items:
                        # 정확 매칭 한자만
                        ent = _TAG.sub("", it.get("expEntry", "") or it.get("handleEntry", ""))
                        if ent == ch:
                            pron = _TAG.sub("", it.get("expKoreanPron", "")).strip()
                            break
                except Exception:
                    pron = None
                if pron and _is_korean(pron):
                    result[ch] = pron
                    ok += 1
                else:
                    fail += 1
            except Exception:
                fail += 1
            if (i + 1) % 50 == 0:
                OUT.write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding="utf-8")
                print(f"  [{i + 1}/{len(chars)}] 성공 {ok} / 실패 {fail}")
            time.sleep(args.sleep)

        b.close()

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"완료: 총 {len(result)}자 수집 (이번 성공 {ok} / 실패 {fail})")
    print(f"저장: {OUT}")


if __name__ == "__main__":
    main()
