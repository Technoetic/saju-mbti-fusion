"""ADR-125 본문화 — 작명학 한자 자원오행 보고서 §6 9 한자 KCI 매핑 추가.

학술 근거: 이재승·김만태 KCI 학설.
- 이재승·김만태 (2018) 한국 성씨한자의 자원오행 고찰 (DOI 10.33645/cnc.2018.06.40.3.339)
- 이재승 (2024) 인명 한자 214 부수의 자원에 의한 성명학적 오행 배속 (KCI DSpace 2187321)
- 김기승 (2022) 자원오행 성명학 제5판 (ISBN 9791160782363)

본 스크립트는 1회 실행만. 멱등성 보장 — 이미 본문화된 한자는 update 안 함.
"""
from __future__ import annotations

import json
from pathlib import Path


# 보고서 §6 라인 172~213 YAML 9 한자 KCI 매핑 (本 시스템 새로 본문화)
# 光은 이미 영속화됨 — 추가 변경 없음
KCI_9_HANJA_DATA = {
    "田": {
        "resource_ohaeng_kci": "토",
        "kci_reason": "밭은 곡식을 가꾸는 삶의 터전 — 흙(土)의 본성을 가장 강하게 가짐. 부수 田 자체이나 자의(字意)는 흙·대지 본성.",
        "kci_school_source": "이재승(2024), 정통 작명학 김기승(2022)",
        "kci_confidence": "MEDIUM",
    },
    "澈": {
        "resource_ohaeng_kci": "수",
        "kci_reason": "맑은 물 — 부수 水(氵)와 자의 모두 수(水). 상생합치.",
        "kci_school_source": "이재승(2024), 김기승(2022)",
        "kci_confidence": "HIGH",
    },
    "鐵": {
        "resource_ohaeng_kci": "금",
        "kci_reason": "쇠 — 부수 金과 자의 모두 금(金). 상생합치.",
        "kci_school_source": "이재승(2024), 한국학중앙연구원, 김기승(2022)",
        "kci_confidence": "HIGH",
    },
    "綴": {
        "resource_ohaeng_kci": "목",
        "kci_reason": "엮을 철 — 부수 糸(실 사)는 옷감·식물성 섬유에서 파생, 木 오행. 정통 학파 일부는 금속(철) 발음 연관성으로 혼용.",
        "kci_school_source": "정통 작명학 김기승(2022)",
        "kci_confidence": "LOW",
    },
    "標": {
        "resource_ohaeng_kci": "목",
        "kci_reason": "표할 표 — 부수 木(나무)과 자의(나무의 끝·가지) 모두 木. 모든 학파 합의.",
        "kci_school_source": "이재승(2024), 김기승(2022)",
        "kci_confidence": "HIGH",
    },
    "飄": {
        "resource_ohaeng_kci": "목",
        "kci_reason": "나부낄 표 — 부수 風(바람). 명리학 십이지지 巽(손)·기상현상으로 木 취급. 정통은 실용적 木 배속, KCI 학파는 신중.",
        "kci_school_source": "정통 작명학 김기승(2022)",
        "kci_confidence": "LOW",
    },
    "詠": {
        "resource_ohaeng_kci": "화",
        "kci_reason": "읊을 영 — 부수 言(말씀)·口(입)의 발성/감정 발산. 정통은 火, KCI 학파는 水 의견, 사주명리는 土 의견 분기.",
        "kci_school_source": "정통 작명학 김기승(2022)",
        "kci_confidence": "LOW",
    },
    "心": {
        "resource_ohaeng_kci": "화",
        "kci_reason": "마음 심 — 감정의 폭발·발산 에너지. 정통은 火, AKS는 火 합의하나 이재승 KCI는 '불명확(사용 주의)' 의견.",
        "kci_school_source": "정통 작명학 김기승(2022), 한국학중앙연구원",
        "kci_confidence": "LOW",
    },
    # 光은 이미 본문화됨 — kci_confidence 단계만 추가
    "光": {
        "kci_confidence": "HIGH",
    },
}


def main() -> int:
    """본 시스템 unihan DB에 KCI 9 한자 매핑 본문화."""
    db_path = Path(__file__).resolve().parent.parent / "data" / "hanja" / "korean_hanja_unihan.json"
    if not db_path.exists():
        print(f"ERR: {db_path} not found.")
        return 1

    raw = db_path.read_text(encoding="utf-8")
    db = json.loads(raw)
    if not isinstance(db, list):
        print("ERR: DB is not list.")
        return 1

    updated = 0
    for entry in db:
        if not isinstance(entry, dict):
            continue
        char = entry.get("char")
        if char in KCI_9_HANJA_DATA:
            new_data = KCI_9_HANJA_DATA[char]
            changed = False
            for key, val in new_data.items():
                if entry.get(key) != val:
                    entry[key] = val
                    changed = True
            if changed:
                updated += 1
                print(f"UPDATED {char}: {new_data}")
            else:
                print(f"SKIP {char} (already up-to-date)")

    if updated > 0:
        # 멱등성 — sort_keys 사용 X (entry 순서 보존)
        db_path.write_text(
            json.dumps(db, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n총 {updated}건 본문화 완료. DB 저장.")
    else:
        print("\n변경 없음.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
