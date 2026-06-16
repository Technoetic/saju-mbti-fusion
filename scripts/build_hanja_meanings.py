"""assets/hanja/hanja_meanings.json 생성 — char → 짧은 뜻.

소스 (한국어 우선순위):
1. front/js/core/name-engine.js 한자_뜻 (한국어 훈, ~2,100자) — 작명용 자연스러운 한글 훈
2. engine/saju/hanja_data.py HANJA_LIST 의 meaning (한국어 훈, ~412자) — 검증된 인명용
3. assets/unihan/Unihan_Readings.txt kDefinition (영문, 폴백) — 첫 구절만 짧게

한국어 소스(1·2)가 영문(3)보다 항상 우선. 대상: korean_hanja_unihan.json 9,932자.
백엔드 candidates_by_ko()가 후보 한자의 뜻 표시에 사용.

재실행: python scripts/build_hanja_meanings.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_ENGINE = ROOT / "front" / "js" / "core" / "name-engine.js"
HANJA_DATA = ROOT / "engine" / "saju" / "hanja_data.py"
UNIHAN_READINGS = ROOT / "assets" / "unihan" / "Unihan_Readings.txt"
KOREAN_HANJA = ROOT / "assets" / "hanja" / "korean_hanja_unihan.json"
OUT = ROOT / "assets" / "hanja" / "hanja_meanings.json"


def _is_korean(s: str) -> bool:
    return any("가" <= c <= "힣" for c in s)


def korean_meanings() -> dict[str, str]:
    """프론트 한자_뜻 + 백엔드 HANJA_LIST 의 한국어 훈 병합 (프론트 우선)."""
    out: dict[str, str] = {}

    # 2순위 먼저 채우고 1순위로 덮어쓰기 (프론트 우선)
    hd = HANJA_DATA.read_text(encoding="utf-8")
    for ch, mean in re.findall(
        r'"han":\s*"(.)".*?"meaning":\s*"([^"]+)"', hd
    ):
        mean = mean.strip()
        if _is_korean(mean):
            out[ch] = mean

    src = NAME_ENGINE.read_text(encoding="utf-8")
    m = re.search(r"const 한자_뜻\s*=\s*\{(.*?)\n\};", src, re.S)
    if m:
        for ch, mean in re.findall(r"['\"](.)['\"]\s*:\s*['\"]([^'\"]+)['\"]", m.group(1)):
            out[ch] = mean.strip()
    return out


def english_meanings() -> dict[str, str]:
    out: dict[str, str] = {}
    with UNIHAN_READINGS.open(encoding="utf-8") as f:
        for line in f:
            if "\tkDefinition\t" not in line:
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                ch = chr(int(p[0][2:], 16))
                out[ch] = re.split(r"[;,]", p[2])[0].strip()[:24]
    return out


def supplement_meanings() -> dict[str, str]:
    """수동 보강 훈 (표준 자전 통설). 없으면 빈 dict."""
    path = ROOT / "assets" / "hanja" / "hanja_meanings_supplement.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    except Exception:
        return {}


def naver_meanings() -> dict[str, str]:
    """네이버 한자사전 수집 훈음 (한국어 훈+음). 없으면 빈 dict.

    한자의 훈음은 자전 공유 지식(사실)이며 본 수집물은 우리 가공 데이터.
    """
    path = ROOT / "assets" / "hanja" / "hanja_meanings_naver.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    ko = korean_meanings()
    nv = naver_meanings()
    sup = supplement_meanings()
    en = english_meanings()
    db = json.loads(KOREAN_HANJA.read_text(encoding="utf-8"))

    # 한국어 소스 우선순위: 프론트/HANJA_LIST(검증된 작명용) > 네이버 > 수동보강 > 영문
    out: dict[str, str] = {}
    ko_n = nv_n = sup_n = en_n = none_n = 0
    for x in db:
        ch = x["char"]
        if ch in ko:
            out[ch] = ko[ch]; ko_n += 1
        elif ch in nv:
            out[ch] = nv[ch]; nv_n += 1
        elif ch in sup:
            out[ch] = sup[ch]; sup_n += 1
        elif ch in en:
            out[ch] = en[ch]; en_n += 1
        else:
            none_n += 1

    OUT.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(
        f"프론트/리스트 {ko_n} / 네이버 {nv_n} / 보강 {sup_n} / "
        f"영문폴백 {en_n} / 뜻없음 {none_n} → {len(out)}자"
    )
    kor_total = ko_n + nv_n + sup_n
    print(f"한국어 합계 {kor_total} ({100*kor_total/len(out):.1f}%)")
    print(f"저장: {OUT}")


if __name__ == "__main__":
    main()
