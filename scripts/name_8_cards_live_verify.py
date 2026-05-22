"""name 도메인 8 카드 라이브 검증 + 평가.

palm 도메인 검증 방식 정합. sanitize 7중 안전망 + 결정론 인용 자동 검증.

8 카드 (front/js/data/contents.js name 풀):
  1. today-hanja (오늘의 한자) — fields: fullName
  2. classic (정통 이름 풀이) — tab='name' (기존 묵향 화면)
  3. fate-hanja (운명의 한자) — fields: fullName, hanja
  4. newborn (신생아 작명) — fields: surname, babyBirth, babyHour, babyGender, parentWish
  5. rename (개명 추천) — fields: currentName, birth, hourBranch, gender, reason
  6. biz (상호 작명) — fields: ownerName, ownerBirth, bizType, concept
  7. pen (예명 작명) — fields: realName, birth, field, imageWant
  8. saju-name (사주+이름 종합) — fields: fullName, hanja, birth, hourBranch, gender
"""
import base64
import json
import time
from pathlib import Path

import requests

BASE_URL = "https://saju-mbti-fusion.fly.dev"
API = f"{BASE_URL}/api/content/reading"

# 8 카드 라이브 테스트 케이스
TEST_CASES = [
    {
        "label": "1. today-hanja (오늘의 한자)",
        "char_key": "name",
        "content_key": "today-hanja",
        "fields": {"fullName": "김민준"},
    },
    {
        "label": "2. classic (정통 이름 풀이)",
        "char_key": "name",
        "content_key": "classic",
        "fields": {"fullName": "김민준", "hanja": "金敏俊"},
    },
    {
        "label": "3. fate-hanja (운명의 한자)",
        "char_key": "name",
        "content_key": "fate-hanja",
        "fields": {"fullName": "김민준", "hanja": "金敏俊"},
    },
    {
        "label": "4. newborn (신생아 작명)",
        "char_key": "name",
        "content_key": "newborn",
        "fields": {
            "surname": "김",
            "babyBirth": "2026-05-22",
            "babyHour": "午",
            "babyGender": "M",
            "parentWish": "건강하고 지혜로운 아이로",
        },
    },
    {
        "label": "5. rename (개명 추천)",
        "char_key": "name",
        "content_key": "rename",
        "fields": {
            "currentName": "김철수",
            "birth": "1990-05-15",
            "hourBranch": "午",
            "gender": "M",
            "reason": "일이 잘 풀리지 않아서",
        },
    },
    {
        "label": "6. biz (상호 작명)",
        "char_key": "name",
        "content_key": "biz",
        "fields": {
            "ownerName": "박형민",
            "ownerBirth": "1985-03-22",
            "bizType": "카페",
            "concept": "따뜻한 분위기",
        },
    },
    {
        "label": "7. pen (예명 작명)",
        "char_key": "name",
        "content_key": "pen",
        "fields": {
            "realName": "이수영",
            "birth": "1995-08-10",
            "field": "writer",
            "imageWant": "신비롭고 부드러운",
        },
    },
    {
        "label": "8. saju-name (사주+이름 종합)",
        "char_key": "name",
        "content_key": "saju-name",
        "fields": {
            "fullName": "김민준",
            "hanja": "金敏俊",
            "birth": "1990-05-15",
            "hourBranch": "午",
            "gender": "M",
        },
    },
]

# 단정 어휘 차단 검증 (ADR-094·113·115·116·117·122·134)
FORBIDDEN_WORDS = [
    # ADR-094 일반 단정 부사
    "반드시", "확실히", "절대", "틀림없이", "100%",
    # ADR-113 palm 단정 (이름 도메인에서도 인용 위험)
    "이혼", "재혼", "우울증", "정신질환", "단명",
    # ADR-116 face 단정 (이름 도메인에서도)
    "길흉화복", "대운", "금전수", "흉상이라",
    # ADR-006 자문 거절 정신
    "사망", "객사", "단명", "혈광지사",
]

# 다국어 hallucination (ADR-115)
FOREIGN_PATTERNS = ["saudável", "élégant", "magnifique", "perfecto", "wundervoll"]


def call_api(case: dict) -> dict:
    """라이브 호출."""
    print(f"\n{'='*70}")
    print(f"  {case['label']}")
    print(f"{'='*70}")
    print(f"  char_key: {case['char_key']} | content_key: {case['content_key']}")
    print(f"  fields: {json.dumps(case['fields'], ensure_ascii=False)[:80]}")
    payload = {
        "char_key": case["char_key"],
        "content_key": case["content_key"],
        "fields": case["fields"],
    }
    t0 = time.time()
    try:
        r = requests.post(API, json=payload, timeout=180)
    except Exception as e:
        print(f"  ❌ 호출 실패: {e}")
        return {}
    elapsed = time.time() - t0
    print(f"  status: {r.status_code} | elapsed: {elapsed:.1f}s")
    if r.status_code != 200:
        print(f"  body: {r.text[:300]}")
        return {}
    return r.json()


def verify(case: dict, resp: dict) -> dict:
    """응답 sanitize 검증."""
    text = resp.get("text", "")
    print(f"\n  응답 길이: {len(text)} chars")
    if len(text) > 0:
        print(f"  응답 미리보기: {text[:300]}{'...' if len(text) > 300 else ''}")
    print()

    findings = {
        "label": case["label"],
        "content_key": case["content_key"],
        "text_len": len(text),
        "forbidden_found": [],
        "foreign_found": [],
        "korean_dupes": [],
        "deterministic_used": resp.get("deterministic_used", False),
        "model": resp.get("ai_generation", {}).get("model_label", "?"),
        "status": "PASS",
    }

    for word in FORBIDDEN_WORDS:
        if word in text:
            findings["forbidden_found"].append(word)

    for word in FOREIGN_PATTERNS:
        if word in text:
            findings["foreign_found"].append(word)

    # 단어 중복 패턴 (ADR-117)
    import re
    for m in re.finditer(r"(\b\S{2,}\b)\s+\1", text):
        findings["korean_dupes"].append(m.group(0))

    if findings["forbidden_found"] or findings["foreign_found"]:
        findings["status"] = "FAIL"

    print(f"  단정 어휘 부재: {'❌ FAIL' if findings['forbidden_found'] else '✅ PASS'}")
    if findings["forbidden_found"]:
        print(f"    발견: {findings['forbidden_found']}")
    print(f"  다국어 hallucination 부재: {'❌ FAIL' if findings['foreign_found'] else '✅ PASS'}")
    if findings["foreign_found"]:
        print(f"    발견: {findings['foreign_found']}")
    print(f"  한국어 중복 부재: {'❌ FAIL' if findings['korean_dupes'] else '✅ PASS'}")
    if findings["korean_dupes"]:
        print(f"    발견: {findings['korean_dupes'][:3]}")
    print(f"  결정론 인용: {'✅' if findings['deterministic_used'] else '⚠ X'}")
    print(f"  모델: {findings['model']}")
    return findings


def main():
    print("="*70)
    print("name 도메인 8 카드 라이브 검증 + 평가")
    print("="*70)

    all_findings = []
    out_dir = Path("step_archive/name_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, case in enumerate(TEST_CASES, 1):
        resp = call_api(case)
        if resp:
            findings = verify(case, resp)
            all_findings.append(findings)
            # 응답 영속화
            safe_key = case["content_key"].replace("-", "_")
            (out_dir / f"response_{i:02d}_{safe_key}.txt").write_text(
                resp.get("text", ""), encoding="utf-8"
            )
        else:
            all_findings.append({
                "label": case["label"],
                "content_key": case["content_key"],
                "status": "API_FAIL",
            })

    print(f"\n{'='*70}")
    print("종합 평가")
    print(f"{'='*70}")
    passed = sum(1 for f in all_findings if f.get("status") == "PASS")
    failed = sum(1 for f in all_findings if f.get("status") == "FAIL")
    api_fail = sum(1 for f in all_findings if f.get("status") == "API_FAIL")
    deterministic = sum(1 for f in all_findings if f.get("deterministic_used"))

    print(f"  총 카드: {len(TEST_CASES)}")
    print(f"  ✅ PASS: {passed} / ❌ FAIL: {failed} / ⚠ API_FAIL: {api_fail}")
    print(f"  결정론 인용: {deterministic}/{len(all_findings)}")
    print(f"  총 단정 어휘: {sum(len(f.get('forbidden_found',[])) for f in all_findings)}건")
    print(f"  총 다국어: {sum(len(f.get('foreign_found',[])) for f in all_findings)}건")
    print(f"  총 한국어 중복: {sum(len(f.get('korean_dupes',[])) for f in all_findings)}건")

    overall = "✅ PASS" if (failed == 0 and api_fail == 0) else "❌ FAIL"
    print(f"\n  종합: {overall}")

    out = out_dir / "verify_result.json"
    out.write_text(json.dumps(all_findings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  결과 저장: {out}")


if __name__ == "__main__":
    main()
