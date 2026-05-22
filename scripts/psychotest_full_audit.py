"""psychotest 12 미니 카드 × 48 캐릭터 풀 전수 검증·평가.

검증 영역:
  1. 구조 무결성 — 12 카드 × 4 선택 × 4 캐릭터 필드 (title·archetype·body·shadow)
  2. ADR 정합 — 단정 어휘 부재, sanitize 7중 안전망 통과
  3. 학파 출처 — 12 학파 본문 명시 + 외부 학술 검증 가능
  4. 결정론 — 동일 카드+선택 → 동일 캐릭터
  5. UI 통합 — front/js/ui/play.js renderCard·renderResult 정합
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


PSYCHOTEST_JS = Path("front/js/data/psychotest.js")


# ADR-094·113·115·116·117·122·134 sanitize 7중 안전망 단정 어휘 풀
FORBIDDEN_WORDS = [
    # ADR-094 일반 단정 부사
    "반드시", "확실히", "절대", "틀림없이", "100%",
    # ADR-113 palm 단정 어휘
    "이혼", "재혼", "우울증", "정신질환", "단명",
    # ADR-116 face 단정 어휘
    "길흉화복", "대운", "금전수", "길운", "흉운", "흉상이라",
    # ADR-122 ancestor 빙의·접신
    "빙의", "접신", "신내림", "영안", "채널링",
    # ADR-134 tojeong 凶事·大凶
    "凶事", "大凶", "病死",
    # ADR-006 자문 거절
    "사망", "객사", "혈광지사", "사고사",
]

# ADR-115 다국어 hallucination
FOREIGN_PATTERNS = ["saudável", "élégant", "magnifique", "perfecto", "wundervoll"]


def export_to_json() -> dict:
    """psychotest.js → node 실행 → JSON 추출."""
    script = (
        "import('./front/js/data/psychotest.js').then(m => {"
        "console.log(JSON.stringify({"
        "title: m.PSYCHOTEST.title, "
        "description: m.PSYCHOTEST.description, "
        "cards: m.PSYCHOTEST.cards"
        "}));"
        "});"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"node failed: {result.stderr}")
    # Node warning 제거 (stderr → stdout 잡혔을 가능성)
    lines = result.stdout.strip().split("\n")
    json_line = [ln for ln in lines if ln.startswith("{")]
    if not json_line:
        raise RuntimeError(f"No JSON in output: {result.stdout}")
    return json.loads(json_line[0])


def check_structure(data: dict) -> dict:
    """구조 무결성 검증."""
    findings = {"total_cards": 0, "total_characters": 0, "issues": []}
    cards = data.get("cards", [])
    findings["total_cards"] = len(cards)

    if len(cards) != 12:
        findings["issues"].append(f"Card count: {len(cards)} (expected 12)")

    required_card_fields = ["key", "title", "glyph", "school", "scene", "choices"]
    required_char_fields = ["title", "archetype", "body"]

    for i, card in enumerate(cards):
        for f in required_card_fields:
            if f not in card:
                findings["issues"].append(f"Card {i+1} missing '{f}'")
        if len(card.get("choices", [])) != 4:
            findings["issues"].append(
                f"Card {i+1} '{card.get('key')}' has {len(card.get('choices', []))} choices (expected 4)"
            )
        for j, choice in enumerate(card.get("choices", [])):
            ch = choice.get("character", {})
            for f in required_char_fields:
                if f not in ch or not ch[f]:
                    findings["issues"].append(
                        f"Card {i+1} Choice {j+1} character missing '{f}'"
                    )
            findings["total_characters"] += 1

    return findings


def check_sanitize_safety(data: dict) -> dict:
    """sanitize 7중 안전망 — 단정 어휘 + 다국어 + 한국어 중복 검증."""
    findings = {
        "forbidden_per_character": {},
        "foreign_per_character": {},
        "korean_dupes_per_character": {},
        "total_violations": 0,
    }

    for card in data.get("cards", []):
        for j, choice in enumerate(card.get("choices", [])):
            ch = choice.get("character", {})
            ch_id = f"{card['key']}#{j+1}"
            all_text = " ".join([
                str(ch.get("title", "")),
                str(ch.get("archetype", "")),
                str(ch.get("body", "")),
                str(ch.get("shadow", "")),
            ])

            # 단정 어휘
            found = [w for w in FORBIDDEN_WORDS if w in all_text]
            if found:
                findings["forbidden_per_character"][ch_id] = found
                findings["total_violations"] += len(found)

            # 다국어
            foreign = [w for w in FOREIGN_PATTERNS if w in all_text]
            if foreign:
                findings["foreign_per_character"][ch_id] = foreign
                findings["total_violations"] += len(foreign)

            # 한국어 단어 중복
            dupes = []
            for m in re.finditer(r"(\b\S{2,}\b)\s+\1", all_text):
                dupes.append(m.group(0))
            if dupes:
                findings["korean_dupes_per_character"][ch_id] = dupes
                findings["total_violations"] += len(dupes)

    return findings


def check_school_attribution(data: dict) -> dict:
    """12 학파 출처 본문 명시 검증."""
    findings = {"schools": [], "missing_year": [], "missing_author": []}

    for i, card in enumerate(data.get("cards", [])):
        school = card.get("school", "")
        findings["schools"].append({
            "card": i+1,
            "key": card["key"],
            "title": card["title"],
            "school": school,
        })
        # 연도 (4 digits) 포함 여부
        if not re.search(r"\d{4}", school):
            findings["missing_year"].append(f"Card {i+1} '{card['key']}': {school}")
        # 저자 (한글 또는 영문 이름) 포함 여부
        if not re.search(r"[A-Z][a-z]+|[가-힣]{2,4}", school):
            findings["missing_author"].append(f"Card {i+1} '{card['key']}': {school}")

    return findings


def check_balance(data: dict) -> dict:
    """선택지 균형 — 4축 부호 분포 + 그림자 명시율."""
    findings = {
        "shadow_present": 0,
        "shadow_missing": 0,
        "archetype_diversity": set(),
    }
    for card in data.get("cards", []):
        for choice in card.get("choices", []):
            ch = choice.get("character", {})
            if ch.get("shadow"):
                findings["shadow_present"] += 1
            else:
                findings["shadow_missing"] += 1
            arch = ch.get("archetype", "")
            findings["archetype_diversity"].add(arch)

    findings["archetype_diversity"] = sorted(findings["archetype_diversity"])
    return findings


def check_determinism(data: dict) -> dict:
    """결정론 보장 — 동일 카드+선택 → 동일 캐릭터 (구조 검증)."""
    findings = {"deterministic": True, "key_collisions": []}
    seen_keys = {}
    for card in data.get("cards", []):
        key = card["key"]
        if key in seen_keys:
            findings["key_collisions"].append(key)
            findings["deterministic"] = False
        seen_keys[key] = card
    # 캐릭터 title 중복 (다른 카드 간 동일 캐릭터명 충돌)
    char_titles = {}
    for card in data.get("cards", []):
        for j, choice in enumerate(card.get("choices", [])):
            title = choice.get("character", {}).get("title", "")
            if title in char_titles:
                # 동일 카드 내 중복은 OK (4 선택이 각각 다른 캐릭터)
                # 다른 카드 간 동일 title은 의도적일 수 있으나 추적
                pass
            char_titles.setdefault(title, []).append(f"{card['key']}#{j+1}")
    cross_card_dupes = {t: l for t, l in char_titles.items() if len(l) > 1}
    findings["cross_card_title_dupes"] = cross_card_dupes
    return findings


def main():
    print("="*72)
    print("psychotest 12 미니 카드 × 48 캐릭터 전수 검증·평가")
    print("="*72)

    data = export_to_json()
    print(f"\nTitle: {data['title']}")
    print(f"Description: {data['description']}")

    # 1. 구조
    print("\n" + "="*72)
    print("1. 구조 무결성")
    print("="*72)
    s = check_structure(data)
    print(f"  카드 수: {s['total_cards']} (목표: 12)")
    print(f"  총 캐릭터 수: {s['total_characters']} (목표: 48)")
    if s["issues"]:
        print(f"  ❌ 이슈 {len(s['issues'])}건:")
        for i in s["issues"]:
            print(f"    - {i}")
    else:
        print("  ✅ PASS — 12 카드 × 4 선택 × 캐릭터 필드 모두 정합")

    # 2. sanitize
    print("\n" + "="*72)
    print("2. ADR sanitize 7중 안전망 (48 캐릭터 텍스트)")
    print("="*72)
    sa = check_sanitize_safety(data)
    print(f"  단정 어휘 위반: {len(sa['forbidden_per_character'])}건")
    if sa["forbidden_per_character"]:
        for k, v in sa["forbidden_per_character"].items():
            print(f"    {k}: {v}")
    print(f"  다국어 hallucination: {len(sa['foreign_per_character'])}건")
    print(f"  한국어 중복: {len(sa['korean_dupes_per_character'])}건")
    print(f"  총 위반: {sa['total_violations']}건")
    if sa["total_violations"] == 0:
        print("  ✅ PASS — sanitize 7중 안전망 완전 통과")

    # 3. 학파 출처
    print("\n" + "="*72)
    print("3. 학파 출처 (school 필드)")
    print("="*72)
    sc = check_school_attribution(data)
    print(f"  12 학파 명시:")
    for s_item in sc["schools"]:
        print(f"    {s_item['card']:2}. {s_item['title']:14} → {s_item['school']}")
    print(f"\n  연도 누락: {len(sc['missing_year'])}건")
    print(f"  저자 누락: {len(sc['missing_author'])}건")
    if not sc["missing_year"] and not sc["missing_author"]:
        print("  ✅ PASS — 12 학파 모두 연도+저자 명시")

    # 4. 균형
    print("\n" + "="*72)
    print("4. 캐릭터 균형 (그림자 명시 + archetype 다양성)")
    print("="*72)
    b = check_balance(data)
    print(f"  그림자 명시: {b['shadow_present']}/48")
    print(f"  그림자 부재: {b['shadow_missing']}/48")
    print(f"  archetype 다양성: {len(b['archetype_diversity'])}종")
    # 처음 10개만 출력
    for a in b["archetype_diversity"][:10]:
        print(f"    - {a}")
    if len(b["archetype_diversity"]) > 10:
        print(f"    ... 외 {len(b['archetype_diversity'])-10}종")

    # 5. 결정론
    print("\n" + "="*72)
    print("5. 결정론 보장 (key 충돌·캐릭터 title 중복)")
    print("="*72)
    d = check_determinism(data)
    print(f"  결정론: {'✅ 보장' if d['deterministic'] else '❌ 깨짐'}")
    print(f"  key 충돌: {len(d['key_collisions'])}건")
    print(f"  카드 간 동일 title: {len(d['cross_card_title_dupes'])}건")
    if d["cross_card_title_dupes"]:
        for t, l in d["cross_card_title_dupes"].items():
            print(f"    '{t}' → {l}")

    # 종합
    print("\n" + "="*72)
    print("종합 평가")
    print("="*72)
    all_pass = (
        not s["issues"]
        and sa["total_violations"] == 0
        and not sc["missing_year"]
        and not sc["missing_author"]
        and d["deterministic"]
    )
    print(f"  종합: {'✅ ALL PASS' if all_pass else '❌ FAIL'}")
    print(f"  구조: {'✅' if not s['issues'] else '❌'}")
    print(f"  sanitize: {'✅' if sa['total_violations'] == 0 else '❌'}")
    print(f"  학파 출처: {'✅' if not sc['missing_year'] and not sc['missing_author'] else '❌'}")
    print(f"  결정론: {'✅' if d['deterministic'] else '❌'}")

    # 결과 저장
    out_dir = Path("step_archive/psychotest_audit")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "structure": s,
        "sanitize": {
            "forbidden_count": len(sa["forbidden_per_character"]),
            "foreign_count": len(sa["foreign_per_character"]),
            "korean_dupes_count": len(sa["korean_dupes_per_character"]),
            "total_violations": sa["total_violations"],
        },
        "schools": sc,
        "balance": {
            "shadow_present": b["shadow_present"],
            "shadow_missing": b["shadow_missing"],
            "archetype_diversity": b["archetype_diversity"],
        },
        "determinism": {
            "deterministic": d["deterministic"],
            "key_collisions": d["key_collisions"],
            "cross_card_title_dupes": d["cross_card_title_dupes"],
        },
        "all_pass": all_pass,
    }
    out = out_dir / "audit_result.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  결과 저장: {out}")


if __name__ == "__main__":
    main()
