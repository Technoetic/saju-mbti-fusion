"""Unihan 데이터 → 한국어 음(kHangul) + 획수(kTotalStrokes) + 부수(kRSUnicode)
가진 한자만 JSON 추출.

대법원 인명용 한자 9,389자 전체 풀을 직접 매핑하려면 별도 PDF 파싱이 필요하나,
Unihan의 kHangul 필드가 있는 한자는 한국어로 음이 정의된 것이므로 인명용
사용 가능 후보로 1차 채택.

추출 결과: data/korean_hanja.json
"""

from __future__ import annotations

import json
from pathlib import Path

_DIR = Path(__file__).resolve().parent

# 부수 → 자원오행 매핑 (Unihan kRSUnicode의 부수 번호 기준)
# 부수 번호는 1~214 (康熙字典 부수)
# 학파별 차이 있으므로 명확한 자연 의미만 매핑, 추상 부수는 ""
_RADICAL_TO_OHAENG: dict[int, str] = {
    # 木 — 나무
    75: "목",   # 木
    111: "목",  # 矢 (화살 — 나무로 만듦)
    118: "목",  # 竹 — 대나무
    149: "목",  # 言 (혀 — 학파에 따라 火 — 미정)
    140: "목",  # 艸 (풀)
    119: "목",  # 米 (쌀 — 식물)
    # 火 — 불
    86: "화",   # 火
    72: "화",   # 日 (해)
    195: "화",  # 魚 — 학파별 (보통 水)
    # 土 — 흙
    32: "토",   # 土
    46: "토",   # 山
    33: "토",   # 士 (선비 — 학파에 따라 金)
    27: "토",   # 厂 (낭떠러지)
    104: "토",  # 疒 (병)
    # 金 — 쇠·옥
    167: "금",  # 金
    96: "금",   # 玉
    112: "금",  # 石
    211: "금",  # 齒 (이)
    177: "금",  # 革 (가죽)
    # 水 — 물
    85: "수",   # 水
    9: "수",    # 人 (학파별 차이 — 보통 木)
    173: "수",  # 雨
    87: "수",   # 爪 (학파에 따라 金)
    195: "수",  # 魚 — 다시 덮어쓰기 (魚는 水 통설 더 강)
}

# 한자 → 자원오행 보정 (부수만으로 결정 안 되는 경우)
# 미세 보정은 인명용 자주 쓰는 한자만 (기존 name_strokes 데이터와 일치)
_MANUAL_OHAENG_OVERRIDE: dict[str, str] = {
    # 木 — name_strokes.py와 일치
    "李": "목", "朴": "목", "林": "목", "權": "목",
    "東": "목", "建": "목", "健": "목",
    # 火
    "明": "화", "炳": "화", "炯": "화", "煥": "화",
    # 土
    "崔": "토", "姜": "토", "尹": "토", "安": "토",
    # 金
    "金": "금", "宋": "목", "白": "금", "申": "금", "西": "금",
    # 水
    "水": "수", "永": "수", "海": "수", "韓": "수",
}


def parse_unihan_field(filepath: Path, fields: set[str]) -> dict[str, dict[str, str]]:
    """Unihan txt 파일에서 지정 필드만 추출.

    Returns:
        {"U+661F": {"kHangul": "성:0E", "kTotalStrokes": "9", ...}, ...}
    """
    result: dict[str, dict[str, str]] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            cp, key, value = parts
            if key not in fields:
                continue
            if cp not in result:
                result[cp] = {}
            result[cp][key] = value
    return result


def cp_to_char(cp: str) -> str:
    """U+661F → 星."""
    return chr(int(cp.replace("U+", ""), 16))


def hangul_to_first_reading(raw: str) -> str:
    """kHangul 값에서 첫 한국어 음 추출.

    예: '성:0E 정:1.0' → '성'
    """
    if not raw:
        return ""
    # 공백으로 분리, 첫 항목의 콜론 앞 추출
    first = raw.split()[0] if raw.split() else ""
    return first.split(":")[0] if ":" in first else first


def radical_from_rs(rs: str) -> int:
    """kRSUnicode '72.5' → 72 (부수 번호)."""
    if not rs:
        return 0
    first = rs.split()[0] if rs.split() else ""
    radical_str = first.split(".")[0].replace("'", "")
    try:
        return int(radical_str)
    except ValueError:
        return 0


def build():
    irg_data = parse_unihan_field(
        _DIR / "Unihan_IRGSources.txt",
        {"kRSUnicode", "kTotalStrokes"},
    )
    readings = parse_unihan_field(
        _DIR / "Unihan_Readings.txt",
        {"kHangul", "kKorean"},
    )

    output: list[dict] = []
    skipped_no_hangul = 0
    skipped_no_strokes = 0

    for cp, reading_data in readings.items():
        hangul_raw = reading_data.get("kHangul", "")
        if not hangul_raw:
            skipped_no_hangul += 1
            continue

        hangul = hangul_to_first_reading(hangul_raw)
        if not hangul:
            continue

        irg = irg_data.get(cp, {})
        total_strokes = irg.get("kTotalStrokes", "")
        rs_unicode = irg.get("kRSUnicode", "")

        if not total_strokes:
            skipped_no_strokes += 1
            continue

        # 첫 번째 값만 사용 (J/T/S source가 다를 수 있음)
        kangxi = int(total_strokes.split()[0])
        radical = radical_from_rs(rs_unicode)

        char = cp_to_char(cp)

        # 자원오행 결정
        if char in _MANUAL_OHAENG_OVERRIDE:
            ohaeng = _MANUAL_OHAENG_OVERRIDE[char]
        else:
            ohaeng = _RADICAL_TO_OHAENG.get(radical, "")

        output.append({
            "char": char,
            "hangul": hangul,
            "kangxi_strokes": kangxi,
            "radical": radical,
            "resource_ohaeng": ohaeng,
        })

    output.sort(key=lambda x: (x["hangul"], x["char"]))

    out_path = _DIR.parent / "korean_hanja_unihan.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")

    # 통계
    total = len(output)
    with_ohaeng = sum(1 for o in output if o["resource_ohaeng"])
    print(f"총 한자: {total}자")
    print(f"  자원오행 자동 매핑: {with_ohaeng}자 ({with_ohaeng*100//total}%)")
    print(f"  자원오행 미정 (수동 필요): {total - with_ohaeng}자")
    print(f"건너뛴 한자:")
    print(f"  kHangul 없음: {skipped_no_hangul}")
    print(f"  kTotalStrokes 없음: {skipped_no_strokes}")
    print(f"출력: {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
