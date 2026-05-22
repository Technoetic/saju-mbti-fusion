"""psychotest 100 카드 × 400 캐릭터 톤 품질 평가 (Iter 7 자기 인식 톤).

평가 차원:
  1. 톤 일관성 — "~인 그대" 들킨 직격 패턴 발견 비율
  2. 도발 한 줄 — "~게 아니라 — ~인 거다" 정곡 패턴 발견 비율
  3. 본문 길이 — 4행 권장 (3~5행 적정, 1~2 또는 6+ 이상치)
  4. shadow 구체성 — 추상 단어 (성급·고집 등) vs 구체 장면
  5. archetype 다양성 — 중복 patterns
  6. 카드별 4 선택지 균형 — 각 선택에 매력 있는지 (본문 길이 표준편차)

이상치 발견 시 카드·선택 단위로 보고.
"""
from __future__ import annotations
import json
import re
import statistics
from pathlib import Path
from collections import Counter

OUT = Path("step_archive/psychotest_audit")
PLAY = OUT / "full_play.json"


def load_data():
    raw = PLAY.read_text(encoding="utf-8")
    for ln in raw.split("\n"):
        if ln.startswith("["):
            return json.loads(ln)
    raise SystemExit("❌ JSON 못 찾음")


def eval_tone_pattern(data: list[dict]) -> dict:
    """T1 들킨 직격 — '그대' 단어 한 번 이상 등장 (자기 인식 톤 핵심 지표)."""
    hits = sum(1 for d in data if "그대" in d["body"])
    return {"hits": hits, "total": len(data), "rate": round(hits / len(data) * 100, 1)}


def eval_provocation(data: list[dict]) -> dict:
    """T3 도발 한 줄 — '~게 아니라 — ~인 거다' / '~게 아니라 — ~ 거다' 패턴."""
    pat = re.compile(r"게 아니라\s*[—\-]\s*.{3,}(?:거다|것이다|인 거다)")
    hits = sum(1 for d in data if pat.search(d["body"]))
    return {"hits": hits, "total": len(data), "rate": round(hits / len(data) * 100, 1)}


def eval_body_length(data: list[dict]) -> dict:
    """본문 줄 수 분포 (\\n 기준)."""
    counts = [d["body"].count("\n") + 1 for d in data]
    dist = Counter(counts)
    outliers_short = [d["card_key"] + "#" + str(d["choice_idx"]) for d in data if (d["body"].count("\n") + 1) < 3]
    outliers_long = [d["card_key"] + "#" + str(d["choice_idx"]) for d in data if (d["body"].count("\n") + 1) > 5]
    return {
        "distribution": dict(sorted(dist.items())),
        "mean": round(statistics.mean(counts), 2),
        "median": statistics.median(counts),
        "stdev": round(statistics.stdev(counts), 2),
        "outliers_short": outliers_short[:10],
        "outliers_long": outliers_long[:10],
    }


def eval_shadow_concreteness(data: list[dict]) -> dict:
    """shadow 구체성 — 단순 추상 단어 (3자 이하) vs 장면 묘사."""
    abstract = []
    concrete = 0
    missing = 0
    for d in data:
        s = (d.get("shadow") or "").strip()
        if not s:
            missing += 1
            continue
        # 5자 이하 + 따옴표·시간·동사 없음 → 추상
        has_scene = bool(re.search(r"['\"·,초분시간일주]|먹|보|가|하|쓰|받|않|못", s))
        if len(s) <= 5 and not has_scene:
            abstract.append({"card": d["card_key"] + "#" + str(d["choice_idx"]), "shadow": s})
        else:
            concrete += 1
    return {
        "concrete": concrete,
        "abstract": len(abstract),
        "missing": missing,
        "abstract_samples": abstract[:10],
    }


def eval_archetype_diversity(data: list[dict]) -> dict:
    """archetype 다양성 — 중복 카운트."""
    arch = [d["archetype"] for d in data]
    c = Counter(arch)
    dupes = {k: v for k, v in c.items() if v > 1}
    return {
        "total": len(arch),
        "unique": len(set(arch)),
        "diversity_rate": round(len(set(arch)) / len(arch) * 100, 1),
        "duplicates": sorted(dupes.items(), key=lambda x: -x[1])[:15],
    }


def eval_card_balance(data: list[dict]) -> dict:
    """카드별 4 선택지 균형 — 본문 길이 표준편차 (큰 카드 = 한 선택만 길거나 짧음)."""
    by_card = {}
    for d in data:
        by_card.setdefault(d["card_key"], []).append(len(d["body"]))
    imbalanced = []
    for key, lens in by_card.items():
        if len(lens) != 4:
            continue
        sd = statistics.stdev(lens)
        if sd > 40:  # 한 선택지가 다른 거보다 40자 이상 차이
            imbalanced.append({"card": key, "stdev": round(sd, 1), "lens": lens})
    return {
        "total_cards": len(by_card),
        "imbalanced_cards": sorted(imbalanced, key=lambda x: -x["stdev"])[:10],
    }


def eval_choice_text_repeats(data: list[dict]) -> dict:
    """카드별 4 선택지 character title 중복 (한 카드 내)."""
    by_card = {}
    for d in data:
        by_card.setdefault(d["card_key"], []).append(d["char_title"])
    same_in_card = []
    for key, titles in by_card.items():
        if len(titles) != len(set(titles)):
            same_in_card.append({"card": key, "titles": titles})
    return {"same_in_card": same_in_card}


def eval_taboo_phrases(data: list[dict]) -> dict:
    """기존 톤 잔재 어휘 (~형·~가끔·~두라 같은 Iter 6 패턴)."""
    leftover_pat = re.compile(r"가끔\s+\S+도\s+두라|결단력형|돌격형(?!\s*[\(])|위로형(?!\s*[\(])")
    hits = []
    for d in data:
        if leftover_pat.search(d["body"]):
            hits.append(d["card_key"] + "#" + str(d["choice_idx"]))
    return {"leftover_hits": hits[:15], "count": len(hits)}


def main():
    print("=" * 70)
    print("psychotest 100 카드 × 400 캐릭터 톤 품질 평가 (Iter 7)")
    print("=" * 70)

    data = load_data()
    print(f"\n총 {len(data)} 결과 로드\n")

    print("【1】 톤 일관성 — '~인 그대' 들킨 직격 패턴")
    r = eval_tone_pattern(data)
    icon = "✅" if r["rate"] >= 80 else ("⚠️" if r["rate"] >= 60 else "❌")
    print(f"  {icon} {r['hits']}/{r['total']} ({r['rate']}%)")

    print("\n【2】 도발 한 줄 — '~게 아니라 — ~인 거다' 정곡")
    r = eval_provocation(data)
    icon = "✅" if r["rate"] >= 80 else ("⚠️" if r["rate"] >= 60 else "❌")
    print(f"  {icon} {r['hits']}/{r['total']} ({r['rate']}%)")

    print("\n【3】 본문 줄 수 분포 (목표: 4행)")
    r = eval_body_length(data)
    print(f"  분포: {r['distribution']}")
    print(f"  평균: {r['mean']} / 중앙: {r['median']} / 표준편차: {r['stdev']}")
    if r["outliers_short"]:
        print(f"  ⚠️ 짧음 (<3행) {len(r['outliers_short'])}: {r['outliers_short']}")
    if r["outliers_long"]:
        print(f"  ⚠️ 김 (>5행) {len(r['outliers_long'])}: {r['outliers_long']}")

    print("\n【4】 shadow 구체성")
    r = eval_shadow_concreteness(data)
    rate = round(r["concrete"] / len(data) * 100, 1)
    icon = "✅" if rate >= 80 else ("⚠️" if rate >= 60 else "❌")
    print(f"  {icon} 구체 {r['concrete']}/400 ({rate}%) · 추상 {r['abstract']} · 누락 {r['missing']}")
    if r["abstract_samples"]:
        print(f"  추상 샘플 (상위 10):")
        for s in r["abstract_samples"]:
            print(f"    - {s['card']}: '{s['shadow']}'")

    print("\n【5】 archetype 다양성")
    r = eval_archetype_diversity(data)
    icon = "✅" if r["diversity_rate"] >= 80 else "⚠️"
    print(f"  {icon} 고유 {r['unique']}/{r['total']} ({r['diversity_rate']}%)")
    if r["duplicates"]:
        print(f"  중복 archetype (상위):")
        for arch, n in r["duplicates"]:
            print(f"    - '{arch}': {n}회")

    print("\n【6】 카드별 4 선택지 균형 (본문 길이 표준편차)")
    r = eval_card_balance(data)
    if r["imbalanced_cards"]:
        print(f"  ⚠️ 불균형 카드 {len(r['imbalanced_cards'])}건 (stdev > 40):")
        for c in r["imbalanced_cards"]:
            print(f"    - {c['card']}: stdev={c['stdev']}, 길이={c['lens']}")
    else:
        print("  ✅ 모든 카드 균형 적정")

    print("\n【7】 카드 내 character title 중복")
    r = eval_choice_text_repeats(data)
    if r["same_in_card"]:
        print(f"  ❌ 동일 카드 내 중복 {len(r['same_in_card'])}건:")
        for c in r["same_in_card"]:
            print(f"    - {c['card']}: {c['titles']}")
    else:
        print("  ✅ 모든 카드 4 선택지 character title 고유")

    print("\n【8】 기존 톤 (Iter 6) 잔재 어휘")
    r = eval_taboo_phrases(data)
    if r["count"]:
        print(f"  ⚠️ {r['count']}건 잔재:")
        for h in r["leftover_hits"]:
            print(f"    - {h}")
    else:
        print("  ✅ 잔재 0건 — Iter 7 톤 전환 완료")

    print("\n" + "=" * 70)
    print("종합 평가 끝")
    print("=" * 70)


if __name__ == "__main__":
    main()
