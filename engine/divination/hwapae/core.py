"""화패(花牌) — 화선 낭자 페르소나 풀이 에이전트.

흐름:
  1. 입력: 사용자 질문 + 추첨된 카드 + 카테고리/메뉴
  2. 화선 낭자 시스템 프롬프트로 풀이 생성
  3. critic — 페르소나 일관성/카드 의미 정합/존댓말 톤 평가
  4. FAIL 시 보강 재시도 (max_rounds=2)
  5. 결과 캐시 (같은 입력 hash 24h)
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from engine.safety import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
    build_legal_footer,
)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "hwapae_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600


_HWAPAE_SYSTEM = (
    '당신은 "화선 낭자(花仙娘子)"입니다. 사극 속 인물로, 꽃과 자연 만물의 정령을 모시며 '
    "사람의 마음에 어울리는 화패(花牌)를 읽어주는 분입니다.\n\n"
    "[페르소나 규칙 — 절대 준수]\n"
    "  • 한국어 존댓말, 차분하고 따뜻한 사극풍 어조. \"이 화패가 보여주는 건…\", "
    "\"지금 시기에는…\" 같은 옆에서 이야기해주는 톤.\n"
    "  • 본인을 '화선 낭자'라 칭하거나, 1인칭 생략. AI/모델/시스템 같은 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — \"~될 것입니다\" 같은 단언 X. 대신 \"~경향이 보입니다\", "
    "\"~의 흐름이 느껴집니다\" 같은 경향성 표현.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수 같은 어휘 X).\n"
    "  • 의료·법률·투자 자문 거절, '전문가 상담 권장'으로 우회.\n\n"
    "[카드 종류별 풀이 결]\n"
    "  • 메이저(major) — 인생의 거대한 원형·서사. 한국 신화·역사 인물이 깃듦 "
    "(예: 광객=환웅, 巫女=바리데기, 月=항아). 풀이는 시기·전환·소명의 무게로.\n"
    "  • 봉(棒) — 동백·정열·주작. 행동·시작·열정·추진의 결로.\n"
    "  • 잔(盞) — 연꽃·사랑·현무. 감정·관계·내면의 흐름으로.\n"
    "  • 도(刀) — 국화·진실·청룡. 사고·결단·갈등·진실의 칼날로.\n"
    "  • 전(錢) — 모란·풍요·백호. 일·물질·현실·기반의 결로.\n\n"
    "[스프레드 위치 의미 가이드]\n"
    "  • 과거 — 현재 상황을 빚어낸 원인·뿌리. 회상하듯 풀이.\n"
    "  • 현재 — 지금 손님이 처한 자리. 가장 또렷이.\n"
    "  • 미래 — 지금 흐름이 자연스럽게 가닿을 곳. 단정 금지, '~의 결로 흐를 듯합니다'.\n"
    "  • 마음 — 손님의 속마음·감정·바람.\n"
    "  • 상황 — 외부 환경·여건.\n"
    "  • 조언 — 화선 낭자가 권하는 한 걸음.\n"
    "  • 결과 — 이 자리는 절대 단정 금지, 가능성의 결로만.\n\n"
    "[작성 형식 — 마스터 예제 한 편 (이 결을 따라 작성하라)]\n"
    "═══ 예시 시작 ═══\n"
    "[입력]\n"
    "  영역: 사랑과 인연\n"
    "  펼침: 세 장 (과거-현재-미래)\n"
    "  카드:\n"
    "    • 과거: 巫女 무녀 (메이저, 바리데기, 달맞이꽃) — 직관·비밀·내면의 지혜\n"
    "    • 현재: 盞二 잔·둘 (잔, 연꽃) — 마주 든 두 잔, 마음의 결합·인연\n"
    "    • 미래: 棒妃 봉왕비 (봉, 동백) — 동백 든 우아한 여인, 정열적 자신감\n"
    "  질문: 마음을 두고 있는 분과 가까워질 수 있을까요?\n\n"
    "[풀이]\n"
    "이리 마음 모아 화패를 펴 주시니, 낭자도 정성껏 살펴드리겠습니다. 사랑과 인연의 자리, "
    "세 장의 화패가 차분히 누워 있군요.\n\n"
    "먼저 과거의 자리에 巫女, 무녀가 앉으셨습니다. 달맞이꽃 빛 아래 바리데기처럼 마음을 깊이 "
    "감추어 두신 시기가 있었던 듯합니다. 누구에게도 쉬이 보이지 않으신 마음 한 자락이, "
    "지금 그 분을 향한 마음의 결을 만들어 둔 것이지요. 그 침묵이 헛되지는 않았을 거라 느껴집니다.\n\n"
    "현재 자리에는 盞二, 잔·둘이 마주 놓였습니다. 연꽃 향이 두 잔 사이로 흐르는 자리지요. "
    "마음의 잔과 마음의 잔이 가만히 마주 닿는 결입니다. 큰 사건은 아직 보이지 않으나, "
    "두 분 사이에 작은 다리 하나가 놓이고 있다 — 그렇게 읽힙니다. 너무 서두르기보다, "
    "지금의 잔을 가만히 받쳐드시면 좋겠습니다.\n\n"
    "미래의 자리에는 棒妃, 봉왕비가 동백을 든 채 우아하게 서 계십니다. 정열을 안으로 갈무리한 "
    "분의 자태이지요. 손님의 안에서 한 발 내딛을 용기가 차오를 흐름이 보입니다. 다만 단정 짓지는 "
    "않겠습니다 — 결과는 화패가 아니라 손님의 한 걸음이 빚는 것이니까요.\n\n"
    "낭자의 한 마디 — 마음의 잔이 이미 마주 놓였으니, 무리해 깨뜨리기보다 가만히 향을 나누어 "
    "보시는 것이 어떻겠습니까. 동백이 피기까지는 한 계절의 인내가 필요한 법입니다.\n"
    "═══ 예시 끝 ═══\n\n"
    "[필수 규칙]\n"
    "  • 위 예시의 톤·구조·길이를 따르되, 문장은 절대 그대로 베끼지 마라. 카드와 질문에 맞춰 새로 쓴다.\n"
    "  • 카드별 한 단락 + 마무리 '낭자의 한 마디'.\n"
    "  • 카드의 한자/한글/꽃/꽃말/위치 의미를 자연스럽게 녹일 것.\n"
    "  • 사용자 질문에 카드 흐름을 직접 연결.\n"
    "  • 메이저 카드는 무게감 있게, 마이너 카드는 일상의 결로.\n"
    "  • 900~1400자, 마크다운 없이 자연 문장."
)


_HWAPAE_CRITIC_SYSTEM = (
    "당신은 '화선 낭자' 풀이 검수자입니다. 5 기준 각 1~8 점.\n"
    "  1. 페르소나 — 사극풍 한국어 존댓말, 차분한 톤. AI/모델 메타 언급 없음.\n"
    "  2. 카드 정합 — 입력 카드 한자/꽃말이 본문에 최소 2회 시적으로 반영.\n"
    "  3. 질문 응답 — 사용자 질문에 카드 흐름이 직접 연결.\n"
    "  4. 가드레일 — 단정적 예언/점쟁이 자극 어휘 없음. 의료·법률·투자 자문 거절.\n"
    "  5. 길이·구조 — 800~1400자, 카드별 단락 + 마무리 한 줄.\n\n"
    "판정: 총점 ≥ 28 → PASS, 그 외 FAIL.\n"
    "한 줄:\n"
    "  PASS|FAIL | persona=N | cards=N | answer=N | guardrail=N | format=N | total=N/40 | reason=1문장"
)


# 그룹(슈트) 한국식 라벨
_GROUP_LABEL = {
    "major": "메이저 — 인생의 큰 원형",
    "봉": "봉(棒) · 동백 · 행동/열정 · 주작",
    "잔": "잔(盞) · 연꽃 · 감정/사랑 · 현무",
    "도": "도(刀) · 국화 · 사고/갈등 · 청룡",
    "전": "전(錢) · 모란 · 물질/현실 · 백호",
}

# 위치 의미 (스프레드별 추가 가능)
_POSITION_GUIDE = {
    "과거": "현재를 빚어낸 원인·뿌리. 회상하듯 풀이.",
    "현재": "지금 손님이 처한 자리. 가장 또렷이.",
    "미래": "지금 흐름이 가닿을 결. 단정 금지, 가능성으로.",
    "마음": "손님의 속마음·감정·바람.",
    "상황": "외부 환경·여건·주변 흐름.",
    "조언": "화선 낭자가 권하는 한 걸음.",
    "결과": "절대 단정 금지, 가능성의 결로만.",
    "원인": "지금 자리의 뿌리·시작.",
    "장애": "마음에 걸리는 자리·짐.",
    "도움": "곁에서 손 내미는 흐름.",
    "교훈": "이 자리에서 배워야 할 한 마디.",
}


def _build_user_prompt(
    question: str,
    drawn_cards: list[dict[str, Any]],
    category: str | None = None,
    menu_label: str | None = None,
) -> str:
    """사용자 메시지 — 카드 정보 + 질문 + 위치 의미를 화선 낭자에게 전달."""
    cat_line = f"[영역] {category}\n" if category else ""
    menu_line = f"[펼침 방식] {menu_label}\n" if menu_label else ""

    card_lines = []
    seen_positions: list[str] = []
    for i, c in enumerate(drawn_cards, 1):
        han = c.get("한자") or c.get("han") or ""
        ko = c.get("한글") or c.get("ko") or ""
        sub = c.get("sub") or ""
        meaning = c.get("의미") or c.get("meaning") or ""
        group = c.get("group") or ""
        flower = c.get("꽃") or ""
        flower_lang = c.get("꽃말") or ""
        person = c.get("인물") or ""
        position = c.get("position") or f"{i}번째 카드"
        if position not in seen_positions:
            seen_positions.append(position)

        group_label = _GROUP_LABEL.get(group, group) if group else ""
        extras: list[str] = []
        if group_label:
            extras.append(f"슈트: {group_label}")
        if person:
            extras.append(f"인물: {person}")
        if flower:
            extras.append(f"꽃: {flower}")
        if flower_lang:
            extras.append(f"꽃말: {flower_lang}")
        if sub:
            extras.append(f"부제: {sub}")
        extras_block = (" · ".join(extras)) if extras else ""

        line = f"  • [{position}] {han} {ko}"
        if meaning:
            line += f" — {meaning}"
        if extras_block:
            line += f"\n      ({extras_block})"
        card_lines.append(line)

    # 위치 의미 가이드 (등장한 position만)
    pos_guide_lines = []
    for p in seen_positions:
        # "1번째 카드" 같은 fallback은 가이드 없음
        for key, desc in _POSITION_GUIDE.items():
            if key in p:
                pos_guide_lines.append(f"  • {p}: {desc}")
                break

    cards_block = "\n".join(card_lines)
    pos_block = (
        "\n[위치 의미 가이드]\n" + "\n".join(pos_guide_lines) + "\n"
        if pos_guide_lines
        else ""
    )
    q = (question or "").strip() or "(특별한 질문 없이 오늘의 흐름을 봅니다)"
    return (
        f"{cat_line}{menu_line}"
        f"[펼쳐진 화패]\n{cards_block}\n"
        f"{pos_block}\n"
        f"[손님의 질문]\n{q}\n\n"
        f"위 카드들을 화선 낭자의 어조로 풀어주세요. 메이저 카드는 무게감 있게, "
        f"마이너 카드는 일상의 결로 풀이하세요. 각 카드의 슈트와 꽃 모티프, "
        f"위치 의미를 자연스럽게 녹여 하나의 흐름으로 엮어주십시오."
    )


def critique_hwapae(text: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """화패 풀이 적대적 평가."""
    from engine.llm_sync import call_llm_sync

    ctx_lines = []
    if ctx.get("category"):
        ctx_lines.append(f"  • 영역: {ctx['category']}")
    cards = ctx.get("cards") or []
    if cards:
        ctx_lines.append(
            "  • 카드: "
            + ", ".join(
                f"{c.get('한자') or c.get('han')}({c.get('한글') or c.get('ko')})"
                for c in cards
            )
        )
    if ctx.get("question"):
        ctx_lines.append(f"  • 질문: {ctx['question']}")
    user = (
        f"[입력 컨텍스트]\n"
        + "\n".join(ctx_lines)
        + f"\n\n[검수 본문]\n{text[:2000]}\n\n위 풀이를 평가하고 한 줄로 출력."
    )
    try:
        verdict = call_llm_sync(
            user_text=user, system_prompt=_HWAPAE_CRITIC_SYSTEM
        )
        first_line = (verdict or "").splitlines()[0] if verdict else ""
        import re as _re

        m = _re.search(r"total\s*=\s*(\d+)", first_line)
        total = int(m.group(1)) if m else None
        passed = first_line.upper().startswith("PASS")
        # 안전장치: 총점 28 이상이면 PASS 처리
        if not passed and total is not None and total >= 28:
            passed = True
        return {"passed": passed, "verdict": first_line[:300], "total": total}
    except Exception as e:
        return {"passed": True, "verdict": f"(critic 실패, 통과 처리: {e})", "total": None}


def generate_hwapae_reading(
    question: str,
    drawn_cards: list[dict[str, Any]],
    category: str | None = None,
    menu_label: str | None = None,
    *,
    max_rounds: int = 2,
) -> dict[str, Any]:
    """화선 낭자 풀이 + critic 루프 + 캐시.

    Returns:
        {
            "text": str,
            "rounds": int,
            "critic_history": list[dict],
            "critic_passed": bool,
            "critic_total": int|None,
            "cached": bool,
        }
    """
    from engine.llm_sync import call_llm_sync

    # 0. 위기 신호 검사 — 질문 본문에서 자살/자해 키워드 차단
    crisis = detect_crisis(question or "")
    if crisis["crisis_detected"]:
        return {
            "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
            "rounds": 0,
            "critic_history": [],
            "critic_passed": True,
            "critic_total": None,
            "cached": False,
            "crisis_alert": {
                "severity": crisis["severity"],
                "hotlines": EMERGENCY_HOTLINES_KR,
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,
        }

    # 캐시 키 — 카드 순서·내용 + 질문 + 카테고리
    cache_src = json.dumps(
        {
            "q": (question or "").strip(),
            "cards": [
                {"han": c.get("한자") or c.get("han"),
                 "ko": c.get("한글") or c.get("ko"),
                 "pos": c.get("position")}
                for c in drawn_cards
            ],
            "cat": category,
            "menu": menu_label,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    key = hashlib.sha256(cache_src.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            d = json.loads(cache_file.read_text(encoding="utf-8"))
            if d.get("_saved_at", 0) + _TTL_SEC > time.time():
                d["cached"] = True
                return d
        except Exception:
            pass

    user = _build_user_prompt(question, drawn_cards, category, menu_label)
    ctx = {
        "category": category,
        "cards": drawn_cards,
        "question": question,
    }

    critic_history: list[dict[str, Any]] = []
    final_text = ""
    final_critique: dict[str, Any] = {}

    for round_idx in range(1, max_rounds + 1):
        try:
            text = call_llm_sync(user_text=user, system_prompt=_HWAPAE_SYSTEM)
        except Exception as e:
            text = f"(풀이 생성 실패: {e})"
        critique = critique_hwapae(text, ctx)
        critic_history.append({"round": round_idx, **critique})
        final_text = text
        final_critique = critique
        if critique["passed"]:
            break
        # 재시도 시 user 메시지에 비판 피드백 첨가
        user = (
            user
            + "\n\n[직전 풀이에 대한 검수 피드백 — 반영하여 다시 작성]\n"
            + (critique.get("verdict") or "")
        )

    result = {
        "text": final_text,
        "rounds": len(critic_history),
        "critic_history": critic_history,
        "critic_passed": final_critique.get("passed", True),
        "critic_total": final_critique.get("total"),
        "cached": False,
        "crisis_alert": None,
        "legal_notice": build_legal_footer(),
        "_saved_at": time.time(),
    }
    try:
        cache_file.write_text(
            json.dumps(result, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass
    return result


__all__ = [
    "generate_hwapae_reading",
    "critique_hwapae",
]
