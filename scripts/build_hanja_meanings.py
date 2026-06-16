"""data/hanja/hanja_meanings.json 생성 — char → 짧은 뜻.

소스 (우선순위):
1. front/js/core/name-engine.js 한자_뜻 (한국어 훈, ~2,100자) — 작명용 자연스러운 한글 훈
2. data/unihan/Unihan_Readings.txt kDefinition (영문, 폴백) — 첫 구절만 짧게

대상: data/hanja/korean_hanja_unihan.json 의 9,932자.
백엔드 candidates_by_ko()가 후보 한자의 뜻 표시에 사용.

재실행: python scripts/build_hanja_meanings.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_ENGINE = ROOT / "front" / "js" / "core" / "name-engine.js"
UNIHAN_READINGS = ROOT / "assets" / "unihan" / "Unihan_Readings.txt"
KOREAN_HANJA = ROOT / "assets" / "hanja" / "korean_hanja_unihan.json"
OUT = ROOT / "assets" / "hanja" / "hanja_meanings.json"


def korean_meanings() -> dict[str, str]:
    src = NAME_ENGINE.read_text(encoding="utf-8")
    m = re.search(r"const 한자_뜻\s*=\s*\{(.*?)\n\};", src, re.S)
    out: dict[str, str] = {}
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


def main() -> None:
    ko = korean_meanings()
    en = english_meanings()
    db = json.loads(KOREAN_HANJA.read_text(encoding="utf-8"))

    out: dict[str, str] = {}
    ko_n = en_n = none_n = 0
    for x in db:
        ch = x["char"]
        if ch in ko:
            out[ch] = ko[ch]; ko_n += 1
        elif ch in en:
            out[ch] = en[ch]; en_n += 1
        else:
            none_n += 1

    OUT.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"한국어 {ko_n} / 영문폴백 {en_n} / 뜻없음 {none_n} → {len(out)}자")
    print(f"저장: {OUT}")


if __name__ == "__main__":
    main()
