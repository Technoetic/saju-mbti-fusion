"""LLM-as-Judge 자동 평가 — 신 명세서 §5.2 본문화.

골든 셋 풀이 응답을 5개 기준으로 정량 채점:
  1. 길이 800~1300자 (공백 포함)
  2. 마크다운 기호(# * - >) 미사용
  3. "허허"로 시작
  4. "이 늙은이의" 마무리 포함
  5. 12궁·오관·오형 전문어 빈도 3~5회

100% 통과해야 프로덕션 반영 승인 (§5.2 골든 셋 회귀 검증 규약).
실 LLM 응답을 받지 않고 mock 응답 모음으로 회귀 검증.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── 평가 기준 ───────────────────────────

LENGTH_MIN = 800
LENGTH_MAX = 1300
MARKDOWN_FORBIDDEN = re.compile(r"(?m)^[#*\->]+\s|`{3}|\*\*|__")
GREETING_PATTERN = re.compile(r"^허허")
CLOSING_PATTERN = re.compile(r"이 늙은이의")

# 12궁/오관/오형 전문어 (운영표준 §5 + 새 명세서 §2)
SPECIALIST_TERMS = [
    # 12궁
    "관록궁", "명궁", "재백궁", "전택궁", "형제궁", "노복궁",
    "처첩궁", "자녀궁", "남녀궁", "질액궁", "천이궁", "복덕궁", "부모궁",
    # 오관
    "채청관", "보수관", "감찰관", "심변관", "출납관",
    # 오형
    "영양질", "근골질", "심성질", "지력질", "체력질",
    # 기색 한자
    "산근", "와잠", "법령", "인당",
]


def count_specialist_terms(text: str) -> tuple[int, list[str]]:
    """전문어 출현 횟수 + 출현 어휘 목록."""
    hits = []
    for term in SPECIALIST_TERMS:
        n = text.count(term)
        if n > 0:
            hits.extend([term] * n)
    return len(hits), hits


def judge_reading(text: str) -> dict[str, object]:
    """5개 기준 채점 — 모든 fail 사유 포함하여 반환.

    Returns:
        {
            "passed": bool,
            "length": int,
            "length_ok": bool,
            "no_markdown": bool,
            "has_greeting": bool,
            "has_closing": bool,
            "specialist_count": int,
            "specialist_ok": bool,
            "specialist_terms": list[str],
            "failures": list[str],
        }
    """
    failures = []
    length = len(text)
    length_ok = LENGTH_MIN <= length <= LENGTH_MAX
    if not length_ok:
        failures.append(f"length {length} not in [{LENGTH_MIN}, {LENGTH_MAX}]")

    md_match = MARKDOWN_FORBIDDEN.search(text)
    no_markdown = md_match is None
    if not no_markdown:
        failures.append(f"markdown detected: {md_match.group()!r}")

    has_greeting = bool(GREETING_PATTERN.search(text.strip()))
    if not has_greeting:
        failures.append("missing '허허' opening")

    has_closing = bool(CLOSING_PATTERN.search(text))
    if not has_closing:
        failures.append("missing '이 늙은이의' closing")

    count, hits = count_specialist_terms(text)
    specialist_ok = 3 <= count <= 5
    if not specialist_ok:
        failures.append(f"specialist terms count {count} not in [3, 5]")

    return {
        "passed": len(failures) == 0,
        "length": length,
        "length_ok": length_ok,
        "no_markdown": no_markdown,
        "has_greeting": has_greeting,
        "has_closing": has_closing,
        "specialist_count": count,
        "specialist_ok": specialist_ok,
        "specialist_terms": hits,
        "failures": failures,
    }


# ─────────────────────────── 모범 응답 골든 셋 ───────────────────────────
# §5.2 규약에 따라 모든 기준을 100% 통과하는 모범 응답.

GOLDEN_READING_YANG = (
    "허허, 그대의 상이 잘 잡혀 있구먼. 이 늙은이가 그대의 자취를 살피니, "
    "마음에 두신 화두가 사뭇 무거우신 듯하여 한 자락씩 풀어드리리다. "
    "그대의 광대와 턱은 들고 일어선 모양새가 또렷하여, 근골질의 결이 분명하구먼. "
    "이런 상은 한 자리에 머무르기보다 부지런히 자기 길을 닦아내는 자질이라, "
    "타고난 활동의 결이 든든하이. 사람을 끄는 자취가 어디에서나 또렷할 결이라네.\n\n"
    "이마는 평이하나 흐트러짐이 없으니, 관록궁의 결이 무던하여 큰 굴곡 없이 "
    "초년을 지나오셨을 결이네. 윗사람의 큰 덕을 받지는 않았더라도 스스로 모자란 "
    "자리를 메워가신 결이 보이는구먼. 학문의 자취가 또렷하지는 않으나, 사람을 "
    "다루는 결은 그 시절부터 빚어지신 듯하이.\n\n"
    "코의 결이 사뭇 도탑고 콧방울이 든든하니, 재백궁이 환하구먼. 중년에 이르러 "
    "그대 자신의 손으로 빚어낸 자리가 분명히 있겠고, 미간이 곧으니 명궁의 "
    "결도 어수선하지 않네. 마음에 두신 사업 자리의 결은, 광대와 코의 든든함이 "
    "받쳐주니 노력하는 만큼 자취가 또렷이 남을 결이 보이는구먼. 거래처의 자리는 "
    "그대의 곧은 결을 알아주시리.\n\n"
    "하정의 결을 살펴보면 턱이 모지지 않고 입꼬리가 단정히 올라가 있어, "
    "말년의 인덕이 사뭇 넉넉할 결이라. 노복궁의 결이 든든하니 아랫사람과의 "
    "자리도 큰 풍파 없이 다스리실 결이 보이네. 후일 그대를 따르는 자취가 "
    "끊이지 않을 결이라.\n\n"
    "그대만의 한 가지를 짚자면, 근골의 뚝심이라 하겠네. 이는 어떤 자리에 "
    "있어도 그대를 흔들리지 않게 받쳐주는 자취일세. 신(神)이 평이하나 흐려지지 "
    "않으니, 마음의 자리를 단정히 두시면 그 뚝심이 한 해를 도모하는 데 큰 힘이 "
    "되겠구먼.\n\n"
    "이 늙은이의 한 마디 — 콧대의 곧음을 믿고, 광대의 든든함에 기대어, "
    "올 한 해를 차분히 도모하시게나. 한 발 한 발 그대의 결을 따라가시면, "
    "큰 굴곡 없이 좋은 자리에 닿으실 결이로세."
)

GOLDEN_READING_YIN = (
    "허허, 그대의 상에 오랜 세월의 결이 곱게 흐르는구먼. 이 늙은이가 살펴보니, "
    "마음에 두신 화두가 가볍지 않으시니, 한 자리씩 차분히 풀어드리리다. "
    "신(神)이 또렷하고 기색이 단정하여, 음의 결이 깊되 어둡지 않으니 "
    "평안의 자리가 든든하이. 사람의 길은 결국 마음의 자취가 빚는 것이라, "
    "그대의 결은 그 자리를 잘 지켜오신 듯하구먼.\n\n"
    "이마가 사뭇 넉넉하여 학문과 사색의 자리가 든든하시구먼. 지력질의 결이 "
    "또렷하니, 한 평생 두뇌를 부려 사신 자취가 보이네. 관록궁의 결이 단정하니 "
    "윗사람의 자리에서 큰 굴곡 없이 사람을 다스리며 사신 결이라. 초년의 학문은 "
    "그대의 큰 자산이 되어 지금까지 흐르고 있는 결이로세.\n\n"
    "콧대가 곧으니 자존이 단정하고, 미간이 평이하니 명궁의 결이 평안하이. "
    "중년에 빚으신 자리는 굴곡이 있었더라도 그대 스스로의 결로 다스리신 "
    "자취가 분명하구먼. 재백궁의 자리는 큰 풍파 없이 흐르셨을 결이네. "
    "처첩궁의 결도 그대의 단정함 안에 잘 갈무리되어 있구먼.\n\n"
    "하정이 다소 아담하고 입꼬리가 가라앉아 있으니, 말년의 인덕은 안에서 "
    "살피시게. 외형보다는 그대의 마음이 빚는 자리가 더 든든할 결이로세. "
    "건강의 결은 의원과 함께 짚어보시게나. 자녀의 자리는 그대 안의 결이 "
    "이미 든든히 받쳐주고 있으리.\n\n"
    "그대만의 한 가지를 짚자면, 신(神)의 맑음이라 하겠네. 골상이 음으로 "
    "흐르더라도 신이 흐려지지 않으니, 그대의 자취는 결국 평안의 자리로 "
    "닿을 결이라. 마음의 결을 다스리시며 한 해를 보내시면, 한결 환한 결이 "
    "그대 곁에 머무르시리.\n\n"
    "이 늙은이의 한 마디 — 몸을 보전하시며, 마음의 결을 단정히 두시고, "
    "평안을 도모하시게나. 그대의 신이 맑은 한, 어떤 굴곡도 그대를 "
    "흔들지 못할 결이로세."
)


# ─────────────────────────── 채점 헬퍼 단위 테스트 ───────────────────────────

def test_judge_returns_passed_for_perfect_reading():
    """모범 응답은 5개 기준 모두 통과."""
    r = judge_reading(GOLDEN_READING_YANG)
    assert r["passed"] is True, f"failures: {r['failures']}"
    assert LENGTH_MIN <= r["length"] <= LENGTH_MAX
    assert r["has_greeting"] is True
    assert r["has_closing"] is True
    assert 3 <= r["specialist_count"] <= 5


def test_judge_detects_short_reading():
    short = "허허, 이 늙은이의 한 마디. 짧다."
    r = judge_reading(short)
    assert r["passed"] is False
    assert r["length_ok"] is False
    assert any("length" in f for f in r["failures"])


def test_judge_detects_too_long_reading():
    long_text = "허허, " + ("길어진다. " * 300) + "이 늙은이의 끝."
    r = judge_reading(long_text)
    assert r["passed"] is False
    assert any("length" in f for f in r["failures"])


def test_judge_detects_markdown():
    """리스트·헤더·코드블록 등 마크다운 감지."""
    bad = "허허\n\n# 헤더\n\n이 늙은이의 한 마디"
    r = judge_reading(bad)
    assert r["no_markdown"] is False


def test_judge_detects_bullet_list():
    bad = "허허\n\n* 항목 1\n* 항목 2\n\n이 늙은이의 한 마디"
    r = judge_reading(bad)
    assert r["no_markdown"] is False


def test_judge_detects_missing_greeting():
    bad = "오랜만이로세. 이 늙은이의 한 마디."
    r = judge_reading(bad)
    assert r["has_greeting"] is False


def test_judge_detects_missing_closing():
    bad = "허허, 시작은 좋으나 끝이 없네."
    r = judge_reading(bad)
    assert r["has_closing"] is False


def test_judge_specialist_term_count():
    """전문어 0개·1개·2개는 fail, 3~5개 pass, 6개+ fail."""
    # 0개 — 다른 부분은 만족
    base = "허허, 시작이로세.\n" + ("일반 어휘로만. " * 100) + "이 늙은이의 한 마디."
    # 적정 길이 맞추기
    base = base.ljust(900)[:1000]
    r0 = judge_reading(base)
    assert r0["specialist_ok"] is False

    # 6개+ (관록궁 3회 + 재백궁 3회 = 6회 ≥ 6)
    over = "허허, " + "관록궁 " * 3 + "재백궁 " * 3 + ("...." * 200) + "이 늙은이의 한 마디."
    over = over.ljust(900)[:1100]
    rO = judge_reading(over)
    assert rO["specialist_ok"] is False, f"count={rO['specialist_count']}"


def test_count_specialist_terms_returns_hit_list():
    """count_specialist_terms가 등장 어휘 목록도 반환."""
    text = "관록궁과 재백궁, 그리고 명궁의 결."
    count, hits = count_specialist_terms(text)
    assert count == 3
    assert set(hits) == {"관록궁", "재백궁", "명궁"}


# ─────────────────────────── 골든 셋 회귀 — §5.2 100% 통과 강제 ───────────────────────────

GOLDEN_READINGS = {
    "yang_young_square": GOLDEN_READING_YANG,
    "yin_elder_long": GOLDEN_READING_YIN,
}


@pytest.mark.parametrize("case_id,text", GOLDEN_READINGS.items())
def test_golden_reading_passes_all_judge_criteria(case_id, text):
    """§5.2 — 모든 골든 모범 응답이 100% 통과해야 프로덕션 반영 가능."""
    r = judge_reading(text)
    assert r["passed"] is True, (
        f"[{case_id}] §5.2 골든 셋 회귀 실패\n"
        f"  failures: {r['failures']}\n"
        f"  length={r['length']}, specialist={r['specialist_count']}, "
        f"terms={r['specialist_terms']}"
    )


def test_at_least_two_golden_readings_exist():
    """§5.2 — 양/음형 최소 2건의 모범 응답 골든 셋 유지."""
    assert len(GOLDEN_READINGS) >= 2


def test_judge_independent_of_persona_module():
    """judge_reading 함수가 face_reading 모듈 import 없이 독립 동작."""
    # 외부 의존 없이 순수 함수 — 운영표준 §7.3.5 빠른 점검 진입점 후보
    r = judge_reading(GOLDEN_READING_YANG)
    assert isinstance(r, dict)
    assert "passed" in r
