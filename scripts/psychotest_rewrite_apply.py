"""4 청크 JSON → psychotest.js 본문 교체 + glyph·school 유지.

전제:
  · chunks/chunk_01~04.json — 100 카드 신규 본문 (title·archetype·body·shadow + key)
  · 기존 psychotest.js — glyph·school·scene 유지 (이미 100/100 유니크 + ADR 정합)

처리:
  · 4 청크 합쳐 100 카드 JSON 생성
  · 기존 psychotest.js의 카드별로 character.{title,archetype,body,shadow} 교체
  · scene 도 새 청크 값 우선 (장면 묘사 강화된 경우 반영)
  · glyph·school·choice.text 는 기존 유지
"""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

CHUNKS_DIR = Path("step_archive/psychotest_rewrite/chunks")
PSYCHOTEST_JS = Path("front/js/data/psychotest.js")


def load_chunks() -> list[dict]:
    """4 청크 → 100 카드 리스트."""
    all_cards = []
    for n in [1, 2, 3, 4]:
        with open(CHUNKS_DIR / f"chunk_0{n}.json", encoding="utf-8") as f:
            all_cards.extend(json.load(f))
    if len(all_cards) != 100:
        raise SystemExit(f"❌ 카드 수 {len(all_cards)} (목표: 100)")
    return all_cards


def load_existing() -> dict:
    """기존 psychotest.js → JSON (Node export)."""
    script = (
        "import('./front/js/data/psychotest.js').then(m => "
        "console.log(JSON.stringify({title: m.PSYCHOTEST.title, "
        "subtitle: m.PSYCHOTEST.subtitle, description: m.PSYCHOTEST.description, "
        "cards: m.PSYCHOTEST.cards})));"
    )
    r = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        raise SystemExit(f"❌ node 실패: {r.stderr}")
    lines = [ln for ln in r.stdout.strip().split("\n") if ln.startswith("{")]
    if not lines:
        raise SystemExit(f"❌ JSON 못 찾음: {r.stdout}")
    return json.loads(lines[0])


def merge_cards(existing: dict, new_chunks: list[dict]) -> dict:
    """기존 카드 (glyph·school·choice.text 유지) + 신규 본문 (title·archetype·body·shadow·scene)."""
    new_by_key = {c["key"]: c for c in new_chunks}
    merged_cards = []
    missing = []

    for old_card in existing["cards"]:
        key = old_card["key"]
        if key not in new_by_key:
            missing.append(key)
            merged_cards.append(old_card)
            continue
        new_card = new_by_key[key]
        # 합쳐진 카드 구조
        merged = {
            "key": key,
            "title": old_card["title"],  # 카드 타이틀 (질문 문구)은 기존 유지
            "glyph": old_card["glyph"],  # 글리프 유지 (100/100 유니크)
            "school": old_card["school"],  # 학파 출처 유지 (ADR 정합)
            "scene": new_card.get("scene", old_card["scene"]),  # 장면 묘사 신규 우선
            "choices": [],
        }
        # 선택지 합치기 — text는 기존, character는 신규
        for i, old_ch in enumerate(old_card["choices"]):
            new_ch = new_card["choices"][i] if i < len(new_card["choices"]) else None
            if new_ch is None:
                merged["choices"].append(old_ch)
                continue
            merged["choices"].append({
                "text": old_ch["text"],  # 선택지 라벨 기존 유지
                "character": new_ch["character"],  # 캐릭터 본문 신규
            })
        merged_cards.append(merged)

    if missing:
        print(f"⚠️ 신규 청크에 누락된 key {len(missing)}건: {missing[:5]}...")

    return {
        "title": existing["title"],
        "subtitle": existing["subtitle"],
        "description": existing["description"],
        "cards": merged_cards,
    }


def render_js(data: dict) -> str:
    """JSON → ES module JS 형식."""
    lines = [
        "// 심리 테스트 — 미니 캐릭터 진단 100 카드 (Iter 7 — 자기 인식 톤 개편)",
        "// 1 카드 = 1 일상 장면 × 4 선택지 × 4 캐릭터 (즉시 결과 + SNS 바이럴식)",
        "//",
        "// 본 시스템 ADR-006·010·014 정합:",
        "//   · 일상 심리 카테고리 — 학파 무게 X, 가벼운 호기심 패턴",
        "//   · 1 선택 = 1 캐릭터 즉시 진단",
        "//   · MBTI 16유형 단정 회피 (ADR-014) — 가벼운 캐릭터 톤",
        "//   · 단정 어휘 차단 — '~인 그대' 자기 인식 톤",
        "//   · 모든 카드 한국 일상 친숙한 장면 (음식·습관·여행·선택 등)",
        "//",
        "// Iter 7 톤 전환 (2026-05):",
        "//   · 설명문 → 들킨 직격 (\"~인 그대\")",
        "//   · 분류 라벨 → 밈 형용사 (\"참을성 0 직진러\")",
        "//   · 일반 단점 → 구체 장면 shadow (\"결제 0.5초 뒤 후회\")",
        "//   · 권유 결구 → 정곡 단정 (\"급한 게 아니라 — 그냥 못 참는 거다\")",
        "",
        "export const PSYCHOTEST = {",
        f"  title: {json.dumps(data['title'], ensure_ascii=False)},",
        f"  subtitle: {json.dumps(data['subtitle'], ensure_ascii=False)},",
        f"  description: {json.dumps(data['description'], ensure_ascii=False)},",
        "",
        "  cards: [",
    ]

    for card in data["cards"]:
        lines.append("    {")
        lines.append(f"      key: {json.dumps(card['key'], ensure_ascii=False)},")
        lines.append(f"      title: {json.dumps(card['title'], ensure_ascii=False)},")
        lines.append(f"      glyph: {json.dumps(card['glyph'], ensure_ascii=False)},")
        lines.append(f"      school: {json.dumps(card['school'], ensure_ascii=False)},")
        lines.append(f"      scene: {json.dumps(card['scene'], ensure_ascii=False)},")
        lines.append("      choices: [")
        for ch in card["choices"]:
            lines.append("        {")
            lines.append(f"          text: {json.dumps(ch['text'], ensure_ascii=False)},")
            char = ch["character"]
            lines.append("          character: {")
            lines.append(f"            title: {json.dumps(char['title'], ensure_ascii=False)},")
            lines.append(f"            archetype: {json.dumps(char['archetype'], ensure_ascii=False)},")
            lines.append(f"            body: {json.dumps(char['body'], ensure_ascii=False)},")
            if char.get("shadow"):
                lines.append(f"            shadow: {json.dumps(char['shadow'], ensure_ascii=False)},")
            lines.append("          },")
            lines.append("        },")
        lines.append("      ],")
        lines.append("    },")

    lines.append("  ],")
    lines.append("};")
    lines.append("")
    lines.append("export function getPsychoCard(key) {")
    lines.append("  return PSYCHOTEST.cards.find(c => c.key === key) || null;")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("psychotest 100 카드 본문 교체 (Iter 7 자기 인식 톤)")
    print("=" * 60)
    print()
    print("1) 청크 로드...")
    new_chunks = load_chunks()
    print(f"   ✅ {len(new_chunks)} 카드")
    print()
    print("2) 기존 psychotest.js 로드...")
    existing = load_existing()
    print(f"   ✅ {len(existing['cards'])} 카드 (glyph·school·choice.text 보존 대상)")
    print()
    print("3) 합치기...")
    merged = merge_cards(existing, new_chunks)
    print(f"   ✅ {len(merged['cards'])} 카드 합쳐짐")
    print()
    print("4) JS 렌더링...")
    js = render_js(merged)
    print(f"   ✅ {len(js):,} 바이트")
    print()
    print("5) 저장...")
    PSYCHOTEST_JS.write_text(js, encoding="utf-8")
    print(f"   ✅ {PSYCHOTEST_JS}")
    print()
    print("완료. 다음 단계: scripts/psychotest_full_audit.py")


if __name__ == "__main__":
    main()
