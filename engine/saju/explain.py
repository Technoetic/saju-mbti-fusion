"""사주 LLM 해석 — call_llm_sync 사용.

Bizrouter (Gemini 2.5 Flash Lite) 우선, Anthropic fallback.
실패 시 결정론적 fallback 문자열 반환.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from engine.llm_sync import call_llm_sync


# explain 결과 캐시 — 같은 입력 hash 24h 보관
_EXPLAIN_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "explain_cache"
_EXPLAIN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_EXPLAIN_TTL_SEC = 24 * 3600


def _cache_key(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _cache_get(key: str) -> dict[str, Any] | None:
    f = _EXPLAIN_CACHE_DIR / f"{key}.json"
    if not f.exists():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("_saved_at", 0) + _EXPLAIN_TTL_SEC > time.time():
            return d.get("payload")
    except Exception:
        pass
    return None


def _cache_set(key: str, payload: dict[str, Any]) -> None:
    f = _EXPLAIN_CACHE_DIR / f"{key}.json"
    try:
        f.write_text(
            json.dumps({"_saved_at": time.time(), "payload": payload}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

_SYSTEM_PROMPT = (
    "당신은 한국 사주 명리학 전문가입니다. "
    "결정론적 알고리즘 결과를 바탕으로 한국어 해석을 제공하세요. "
    "단정적 예언이 아닌 경향성·성격 해석에 집중하세요. "
    "본문에 반드시 '사주', '명리', '오행', '일간' 단어를 모두 자연스럽게 포함시키세요. "
    "마지막에 '경향성·자기이해' 관점의 해석임을 명시하세요."
)


def _format_user_prompt(saju: dict[str, Any]) -> str:
    """saju_data dict → 사용자 프롬프트 (요약된 핵심만)."""
    pillars_line = (
        f"年{saju.get('year')} / 月{saju.get('month')} / "
        f"日{saju.get('day')} / 時{saju.get('hour')}"
    )
    wx = saju.get("wuxing_dist", {})
    wx_line = ", ".join(f"{k} {v}" for k, v in wx.items())
    tg = saju.get("ten_gods", {})
    tg_line = ", ".join(f"{k}={v}" for k, v in tg.items() if v)
    shensha = saju.get("shensha", {})
    shensha_line = ", ".join(f"{k}={v}" for k, v in shensha.items() if v)

    return (
        f"사주 4기둥: {pillars_line}\n"
        f"日主(일간): {saju.get('day_master')}\n"
        f"오행 분포: {wx_line}\n"
        f"10신: {tg_line}\n"
        f"신살: {shensha_line}\n\n"
        f"위 정보를 바탕으로:\n"
        f"1) 한 줄 코멘트 (성격 핵심)\n"
        f"2) 3~5문장 해석 (강점·약점·균형 제언)"
    )


def _fallback(saju: dict[str, Any]) -> str:
    """LLM 호출 실패 시 결정론적 요약."""
    dm = saju.get("day_master", "?")
    wx = saju.get("wuxing_dist", {})
    strongest = max(wx, key=wx.get) if wx else "?"
    weakest = min(wx, key=wx.get) if wx else "?"
    return (
        f"日主 {dm}. 오행에서 {strongest} 가 가장 왕성하고 {weakest} 가 부족합니다. "
        f"균형을 위해 {weakest} 의 보강을 권합니다. (LLM 미호출 fallback)"
    )


def explain_saju(saju_data: dict[str, Any], model_label: str | None = None) -> str:
    """사주 결과 dict → LLM 한국어 해석.

    Args:
        saju_data: SajuCLI.assess() 반환 dict
        model_label: LLM 모델명 (None 이면 라우터 기본값)

    Returns:
        해석 텍스트 (실패 시 fallback 문자열).
    """
    user_text = _format_user_prompt(saju_data)
    try:
        return call_llm_sync(
            user_text=user_text,
            system_prompt=_SYSTEM_PROMPT,
            model=model_label,
        )
    except Exception:
        return _fallback(saju_data)


_SECTION_PROMPTS: dict[str, str] = {
    "pillar": (
        "사주 4기둥(연/월/일/시 의 천간·지지 8글자)만을 보고, "
        "일간을 중심으로 한 글자 한 글자의 의미와 조합의 특징을 한국어로 4~6문장 설명하세요. "
        "오행 분포·십신·대운·신살 같은 다른 정보는 일절 언급하지 마세요."
    ),
    "wuxing": (
        "오행 분포(목·화·토·금·수의 가중치)만을 보고, 가장 강한 오행과 약한 오행이 "
        "성격·기질·행동 양식에 어떤 영향을 줄지 한국어로 3~5문장 설명하세요. "
        "사주 8글자나 십신은 언급하지 마세요."
    ),
    "tengods": (
        "십신(연간/연지/월간/월지/일간/일지/시간/시지의 10신)만을 보고, "
        "일간을 기준으로 한 사회·재물·관계 측면의 경향을 한국어로 4~6문장 설명하세요. "
        "다른 정보는 언급하지 마세요."
    ),
    "luck": (
        "대운 흐름(10년 단위 8개)만을 보고, 큰 흐름(상승/전환/도전 구간)을 한국어로 4~6문장 짚어 주세요. "
        "각 구간의 천간·지지 의미를 간단히 곁들이되, 단정적 예언은 피하세요."
    ),
    "shensha": (
        "신살(천을귀인·문창귀인·역마·도화·공망 등)만을 보고, "
        "포함된 신살이 성격과 인생에 부여하는 색채를 한국어로 3~5문장 설명하세요. "
        "신살이 비어있으면 '특별한 신살 작용은 약합니다' 라고 한 문장으로만 답하세요."
    ),
}

_SECTION_ALIAS = {"ten_gods": "tengods"}


def _format_section_user_prompt(section: str, saju: dict[str, Any]) -> str:
    if section == "pillar":
        return (
            f"日主(일간): {saju.get('day_master')}\n"
            f"4기둥: 연{saju.get('year')} 월{saju.get('month')} "
            f"일{saju.get('day')} 시{saju.get('hour')}"
        )
    if section == "wuxing":
        wx = saju.get("wuxing_dist", {})
        return "오행 분포: " + ", ".join(f"{k}={v}" for k, v in wx.items())
    if section == "tengods":
        tg = saju.get("ten_gods", {})
        return (
            f"日主: {saju.get('day_master')}\n"
            f"십신: " + ", ".join(f"{k}={v}" for k, v in tg.items() if v)
        )
    if section == "luck":
        lc = saju.get("luck_cycle", [])
        line = ", ".join(
            f"{p.get('start_age')}세 {p.get('ganzhi')}" for p in lc[:8]
        )
        return f"日主: {saju.get('day_master')}\n대운: {line}"
    if section == "shensha":
        ss = saju.get("shensha", {})
        active = {k: v for k, v in ss.items() if v}
        if not active:
            return "신살: (없음)"
        return "신살: " + ", ".join(f"{k}={v}" for k, v in active.items())
    raise ValueError(f"unknown section: {section}")


def explain_section(
    section: str,
    saju_data: dict[str, Any],
    model_label: str | None = None,
    context: str | None = None,
) -> str:
    """카드별 부분 해설.

    Args:
        section: 'pillar' | 'wuxing' | 'tengods' | 'luck' | 'shensha'
            (구버전 'ten_gods' 도 alias 로 허용)
        saju_data: SajuCLI.assess() 반환 dict
        context: 사용자 현재 상황 메모 (선택). 있으면 prompt 에 첨부되어
            해설이 현재 상황과 연결되도록 유도.
    """
    section = _SECTION_ALIAS.get(section, section)
    if section not in _SECTION_PROMPTS:
        raise ValueError(f"unknown section: {section}")
    sys = _SECTION_PROMPTS[section]
    user = _format_section_user_prompt(section, saju_data)

    has_mbti = bool(context and ("MBTI" in context or "mbti" in context))
    if context and context.strip():
        if has_mbti:
            # 융합 캐릭터 모드 — 매핑 표 + 인지기능 스택을 강제 주입
            sys = (
                sys
                + " 이 사용자는 사주와 MBTI 를 결합한 '융합 캐릭터' 관점에서 해석을 원합니다. "
                "다음 십성↔MBTI 매핑을 반드시 적용해 해설을 작성하세요:\n"
                "  • 인성 ↔ 직관 N, 재성 ↔ 감각 S, 관살 ↔ 사고 T, 식상 ↔ 감정 F, 비겁 ↔ 자아축\n"
                "사주 요소를 해석할 때마다 'MBTI 의 어떤 인지 기능(주/부/3차/열등) 이 이 부분을 어떻게 "
                "증폭·완화·굴절시키는가' 를 본문 안에서 자연스럽게 엮으세요. 별도 단락으로 분리하지 말고 문장 단위로 융합. "
                "16유형 팝 심리학식 요약·이분법적 동질/이질 비교·단정적 예언 모두 금지."
            )
        else:
            sys = (
                sys
                + " 사용자가 현재 상황 메모를 제공했다면, 사주 분석 후 그 상황과 어떻게 연결되는지 "
                "1~2문장 추가로 짚어 주세요. 단정적 예언은 금지, 경향성·자기이해 조언만 제시하세요."
            )
        user = user + f"\n\n[사용자 컨텍스트]\n{context.strip()[:800]}"
    try:
        return call_llm_sync(user_text=user, system_prompt=sys, model=model_label)
    except Exception as e:
        return f"(해설 생성 실패: {e})"


_FUSION_SYSTEM = (
    "당신은 동양 사주 명리학(일주론 + 십성)과 서양 MBTI 인지 기능 스택(융의 8 기능) 을 "
    "통합 해석하는 융합 캐릭터 분석 전문가입니다. "
    "다음 정밀 매핑 원칙을 반드시 따르세요 (설계도 §3.2 표준):\n"
    "  • 정인 ↔ Ni (내향 직관, 깊은 수용·이상)\n"
    "  • 편인 ↔ Ne (외향 직관, 비주류 통찰·탐험)\n"
    "  • 정재 ↔ Si (내향 감각, 꼼꼼·과거 기록)\n"
    "  • 편재 ↔ Se (외향 감각, 개방·즉시 반응·기회)\n"
    "  • 정관 ↔ Te (외향 사고, 체계·시스템 순응)\n"
    "  • 편관 ↔ Ti (내향 사고, 독립·강박적 원칙)\n"
    "  • 식신 ↔ Fe (외향 감정, 조화·완만 표현)\n"
    "  • 상관 ↔ Ne+Fe (창의 표현·거침없는 발산)\n"
    "오행 발산/수렴 ↔ E/I 매핑 (설계도 §3.1):\n"
    "  • 목·화 우세 → E (외향 발산), 금·수 우세 → I (내향 수렴)\n"
    "  • 선천(사주) ↔ 후천(MBTI) 모순 시 '환경 적응 페르소나' 로 해석\n"
    "두 체계가 정렬되는 영역은 강점 시너지로, 충돌하는 영역은 '내적 딜레마' 로 입체적으로 해석하세요. "
    "이분법적 동질/이질 비교, 단정적 예언, 16유형 팝 심리학식 요약은 금지."
)

_MBTI_DESC = {
    "INTJ": "전략가 — 장기적·체계적·독립적",
    "INTP": "논리학자 — 분석적·호기심·유연한 사고",
    "ENTJ": "통솔자 — 결단력·조직력·목표 지향",
    "ENTP": "변론가 — 창의적·논쟁적·도전적",
    "INFJ": "옹호자 — 통찰력·이상주의·신중",
    "INFP": "중재자 — 가치 지향·공감·창의",
    "ENFJ": "선도자 — 카리스마·이타·영감",
    "ENFP": "활동가 — 열정·자발성·창의",
    "ISTJ": "현실주의자 — 책임감·성실·전통",
    "ISFJ": "수호자 — 헌신·세심·온화",
    "ESTJ": "경영자 — 실용·관리·규율",
    "ESFJ": "집정관 — 사교·돌봄·협력",
    "ISTP": "장인 — 실용·기술·유연",
    "ISFP": "모험가 — 감각·온화·예술",
    "ESTP": "사업가 — 행동·즉흥·현실",
    "ESFP": "연예인 — 활달·즐거움·즉각",
}


def explain_fusion(
    saju_data: dict[str, Any],
    mbti: str,
    model_label: str | None = None,
    myeong: dict[str, Any] | None = None,
    lang: str = "ko",
) -> str:
    """사주 + MBTI 융합 해설. myeong 이 있으면 5번째 'Naming Resonance' 섹션 추가.

    같은 입력은 24h 캐시.
    """
    from .mbti_functions import function_stack_lines
    from .ten_gods import (
        cluster_mbti_hints,
        sipsung_clusters,
        tengod_function_hints,
        wuxing_ei_signal,
    )

    mbti = (mbti or "").upper().strip()
    if mbti not in _MBTI_DESC:
        raise ValueError(f"unknown MBTI: {mbti}")

    # 캐시 조회 (lang별로 분리)
    fkey = _cache_key(
        "fusion_explain",
        saju_data.get("day_master"),
        saju_data.get("year"),
        saju_data.get("month"),
        saju_data.get("day"),
        saju_data.get("hour"),
        (saju_data.get("wuxing_dist") or {}),
        mbti,
        (myeong or {}).get("name_ko"),
        (myeong or {}).get("name_han"),
        lang,
    )
    fcached = _cache_get(fkey)
    if fcached and isinstance(fcached, dict) and fcached.get("text"):
        return fcached["text"]

    pillars_line = (
        f"{saju_data.get('year')} / {saju_data.get('month')} / "
        f"{saju_data.get('day')} / {saju_data.get('hour')}"
    )
    wx = saju_data.get("wuxing_dist", {})
    wx_line = ", ".join(f"{k}={v}" for k, v in wx.items())

    # E/I 신호 (목·화 vs 금·수)
    ei = wuxing_ei_signal(wx)
    ei_match = ""
    if ei["signal"] == "E" and mbti[0] == "E":
        ei_match = "선천(E) ↔ 후천(E) 일치 — 일관된 외향 발산형"
    elif ei["signal"] == "I" and mbti[0] == "I":
        ei_match = "선천(I) ↔ 후천(I) 일치 — 일관된 내향 수렴형"
    elif ei["signal"] == "E" and mbti[0] == "I":
        ei_match = "선천 외향(E) ↔ 후천 내향(I) **모순** — 외향 기질을 의식적으로 통제하는 페르소나"
    elif ei["signal"] == "I" and mbti[0] == "E":
        ei_match = "선천 내향(I) ↔ 후천 외향(E) **모순** — 내면 수렴 기질을 후천적 사회화로 발산하는 페르소나"
    else:
        ei_match = f"오행 균형 ({ei['signal']}, score={ei['score']}) — MBTI 첫 글자({mbti[0]}) 와 자유롭게 결합"

    # 십성 4세력 집계
    tg = saju_data.get("ten_gods", {})
    clusters = sipsung_clusters(tg)
    cluster_line = ", ".join(f"{k}={v}" for k, v in clusters.items() if v)
    hints = cluster_mbti_hints(clusters)
    hint_lines = [
        f"  • {h['cluster']}({h['count']}) ↔ {h['mbti_axis']}" for h in hints[:3]
    ]
    cluster_hint_block = "\n".join(hint_lines) if hint_lines else "  • (세력 데이터 없음)"

    # 10 십성 개별 정밀 매핑
    fn_hints = tengod_function_hints(tg)
    fn_lines = [
        f"  • {h['slot']} = {h['tengod']} → {h['function']}"
        for h in fn_hints[:8]
    ]
    fn_block = "\n".join(fn_lines) if fn_lines else "  • (십성 데이터 없음)"

    # MBTI 인지 기능 스택
    stack_lines = function_stack_lines(mbti)

    # 이름 데이터 (선택)
    name_block = ""
    sections_5 = ""
    if myeong:
        name_ko = myeong.get("name_ko", "")
        name_wx = myeong.get("wuxing_dist", {})
        comp = myeong.get("complement", {}) or {}
        grids = myeong.get("grids", {})
        grids_brief = ", ".join(
            f"{k}={v.get('number',0)}({v.get('label','?')})"
            for k, v in grids.items()
        )
        name_wx_line = ", ".join(f"{k}={v}" for k, v in name_wx.items() if v)
        name_block = (
            f"\n[이름 데이터]\n"
            f"이름: {name_ko}\n"
            f"음령오행 분포: {name_wx_line}\n"
            f"수리오격 81운수: {grids_brief}\n"
            f"사주 보완도: {comp.get('score','?')} ({comp.get('grade','?')})\n"
            f"보완 사유: {comp.get('reason','')[:200]}\n"
        )
        sections_5 = (
            "\n### 5. Naming Resonance (이름의 공명) — 이름이 사주의 약한 기운을 어떻게 보강하거나 "
            "강한 기운을 어떻게 증폭하는지, 그리고 그 결과가 MBTI 의 어떤 인지 기능과 만나 "
            "어떤 사회적 정체성으로 발현되는지 (3~4문장)"
        )

    user = (
        f"[사주 데이터]\n"
        f"4기둥: {pillars_line}\n"
        f"日主(일간): {saju_data.get('day_master')}\n"
        f"오행 분포: {wx_line}\n"
        f"오행 발산/수렴 ↔ E/I 신호: {ei_match}\n"
        f"십성 4세력 집계: {cluster_line}\n"
        f"십성↔MBTI 친화축 (강한 순):\n{cluster_hint_block}\n"
        f"10 십성 개별 정밀 매핑:\n{fn_block}\n\n"
        f"[MBTI 데이터]\n"
        f"유형: {mbti} ({_MBTI_DESC[mbti]})\n"
        f"인지 기능 스택:\n" + "\n".join(stack_lines) + "\n"
        + name_block + "\n"
        f"[작성 형식] — 아래 섹션을 반드시 모두 작성:\n"
        f"### 1. Core Identity (본질) — 사주 일주의 태생적 기질이 MBTI 주기능과 어떻게 결합되는가 (3~4문장)\n"
        f"### 2. Social Dynamics (사회적 페르소나) — 십성 지배 세력이 부기능과 만나 대인 관계에서 어떻게 발현되는가 (3~4문장)\n"
        f"### 3. Crisis Breakdown (위기 패턴) — 사주의 약한 오행 + MBTI 열등 기능이 스트레스 시 어떻게 폭발하는가 (3~4문장)\n"
        f"### 4. Growth Outlook (성장 통찰) — 두 체계가 충돌하는 지점을 강점으로 전환하는 방법 (3~4문장)"
        + sections_5
    )
    lang_directive = {
        "en": "\n\n[Output language] Write the FINAL answer in natural English. Keep the section "
              "titles in English (e.g., '### 1. Core Identity'). Keep Hanja for Saju terms in parentheses.",
        "ja": "\n\n[出力言語] 最終的な解説は自然な日本語で書いてください。セクションタイトルは "
              "日本語化（例：'### 1. 本質'）。四柱の漢字（甲乙など）は括弧書きで残してください。",
    }.get(lang, "")
    user = user + lang_directive
    try:
        text = call_llm_sync(user_text=user, system_prompt=_FUSION_SYSTEM, model=model_label)
        _cache_set(fkey, {"text": text})
        return text
    except Exception as e:
        return f"(융합 해설 생성 실패: {e})"


_CRITIC_SYSTEM = (
    "당신은 사주 + MBTI 융합 해설 검수자입니다. 다음 3개 기준 중 "
    "최소 2개 이상 충족하면 PASS, 그렇지 않으면 FAIL.\n\n"
    "[검수 기준]\n"
    "  1. 사주 일주(日柱) 또는 십성 세력(인성/재성/관살/식상 중 1개 이상)이 본문에 언급됐는가\n"
    "  2. MBTI 8 인지 기능 중 최소 2개(주기능·부기능 등)가 구체 명칭으로 언급됐는가\n"
    "  3. 두 체계의 시너지 또는 충돌이 입체적으로 해석됐는가 (이분법 단순 비교 X)\n\n"
    "[출력 형식] — 첫 줄에 'PASS' 또는 'FAIL' 만 출력. FAIL 시 둘째 줄부터 미달 기준만 1~3문장으로 지적. "
    "완벽함을 요구하지 말고 합리적인 수준에서 판정하세요."
)


def critique_fusion(
    saju_data: dict[str, Any],
    mbti: str,
    fusion_text: str,
    model_label: str | None = None,
) -> tuple[bool, str]:
    """융합 해설 적대적 비판.

    Returns:
        (passed, feedback) — passed=True 면 통과, False 면 feedback 에 결함 지적.
    """
    user = (
        f"[입력 데이터]\n"
        f"日主: {saju_data.get('day_master')}\n"
        f"MBTI: {mbti}\n\n"
        f"[검수 대상 해설]\n{fusion_text[:3000]}"
    )
    try:
        verdict = call_llm_sync(
            user_text=user, system_prompt=_CRITIC_SYSTEM, model=model_label
        )
    except Exception as e:
        return True, f"(critic 호출 실패, 통과 처리: {e})"
    first_line = (verdict.strip().splitlines() or [""])[0].strip().upper()
    passed = first_line.startswith("PASS")
    return passed, verdict


def explain_fusion_with_critic(
    saju_data: dict[str, Any],
    mbti: str,
    model_label: str | None = None,
    max_rounds: int = 2,
    myeong: dict[str, Any] | None = None,
    lang: str = "ko",
) -> dict[str, Any]:
    """1차 생성 → critic → FAIL 시 보강 재생성. myeong 있으면 5섹션 모드.

    같은 입력은 24h 캐시 — 비용 절감.
    """
    cache_key = _cache_key(
        "fusion_with_critic",
        saju_data.get("day_master"),
        saju_data.get("year"),
        saju_data.get("month"),
        saju_data.get("day"),
        saju_data.get("hour"),
        (saju_data.get("wuxing_dist") or {}),
        (mbti or "").upper(),
        max_rounds,
        (myeong or {}).get("name_ko"),
        (myeong or {}).get("name_han"),
        lang,
    )
    cached = _cache_get(cache_key)
    if cached:
        cached = dict(cached)
        cached["cached"] = True
        return cached

    history: list[dict[str, Any]] = []
    text = explain_fusion(saju_data, mbti, model_label=model_label, myeong=myeong, lang=lang)
    for round_idx in range(1, max_rounds + 1):
        passed, feedback = critique_fusion(saju_data, mbti, text, model_label)
        history.append({"round": round_idx, "passed": passed, "feedback": feedback})
        if passed:
            break
        text = _refine_fusion(saju_data, mbti, text, feedback, model_label)
    result = {
        "text": text,
        "rounds": len(history),
        "critic_history": history,
        "cached": False,
    }
    _cache_set(cache_key, result)
    return result


def _refine_fusion(
    saju_data: dict[str, Any],
    mbti: str,
    prev_text: str,
    critic_feedback: str,
    model_label: str | None = None,
) -> str:
    """critic 피드백 반영 재생성."""
    from .mbti_functions import function_stack_lines
    from .ten_gods import cluster_mbti_hints, sipsung_clusters

    tg = saju_data.get("ten_gods", {})
    clusters = sipsung_clusters(tg)
    cluster_line = ", ".join(f"{k}={v}" for k, v in clusters.items() if v)
    hints = cluster_mbti_hints(clusters)
    hint_lines = [
        f"  • {h['cluster']}({h['count']}) ↔ {h['mbti_axis']}" for h in hints[:3]
    ]
    cluster_hint_block = "\n".join(hint_lines) if hint_lines else "  • (없음)"
    stack_lines = function_stack_lines(mbti)

    user = (
        f"[사주]\n日主: {saju_data.get('day_master')}\n"
        f"십성 4세력: {cluster_line}\n"
        f"매핑 힌트:\n{cluster_hint_block}\n\n"
        f"[MBTI {mbti}] 인지 기능 스택:\n" + "\n".join(stack_lines) + "\n\n"
        f"[이전 해설]\n{prev_text[:2000]}\n\n"
        f"[비판 에이전트 피드백]\n{critic_feedback[:600]}\n\n"
        f"위 피드백을 반영해 4 섹션(Core Identity / Social Dynamics / Crisis Breakdown / Growth Outlook) "
        f"구조를 유지하면서 해설을 보강하세요. 비판이 지적한 누락 항목을 반드시 본문에 포함시키세요."
    )
    try:
        return call_llm_sync(
            user_text=user, system_prompt=_FUSION_SYSTEM, model=model_label
        )
    except Exception:
        return prev_text


_COMPAT_SYSTEM = (
    "당신은 두 사람의 사주 + MBTI + 이름을 통합 해석하는 궁합 전문가입니다. "
    "결정론적으로 계산된 천간/지지 관계, 오행 흐름, MBTI 호환 점수를 바탕으로 "
    "한국어 4섹션 해설을 작성하세요. "
    "단정적 예언 금지, 경향성·자기이해 조언만."
)


MAX_CHAT_TURNS = 10

_RELATION_MODE_HINT = {
    "romantic": "두 사람을 연인 또는 배우자 관계로 해석한다. 끌림·친밀감·갈등·일상 등을 다룬다.",
    "family": "두 사람을 가족(부모·자녀·형제) 관계로 해석한다. 세대 차이·돌봄·기대·자율의 충돌·관계 회복을 다룬다. 연인 관점 어휘(설렘·사랑·이별) 금지.",
    "work": "두 사람을 직장(상사·부하·동료) 관계로 해석한다. 협업 스타일·의사결정·갈등 해결·서로의 업무 강점을 다룬다. 연인 관점 어휘 금지.",
    "friend": "두 사람을 친구 관계로 해석한다. 우정·신뢰·취향 차이·서로에게 주는 영향을 다룬다. 연인 관점 어휘 금지.",
}


def explain_compat(
    compat: dict[str, Any],
    model_label: str | None = None,
    relation_mode: str = "romantic",
    lang: str = "ko",
) -> str:
    """궁합 결정론 데이터 → LLM 4섹션 해설.

    relation_mode 가 'family'/'work'/'friend' 면 톤과 어휘를 그에 맞게 변경.
    """
    stem = compat.get("stem", {})
    branch = compat.get("branch", {})
    wx = compat.get("wuxing_flow", {})
    mbti = compat.get("mbti") or {}
    name = compat.get("name_flow") or {}

    stem_rel = ", ".join(r["label"] for r in stem.get("relations", []))
    branch_rel = ", ".join(branch.get("relations", []))
    wx_pos = "; ".join(wx.get("positive", []))
    wx_neg = "; ".join(wx.get("negative", []))
    name_block = ""
    if name:
        name_block = (
            f"\n[이름 오행 흐름]\n"
            f"  상생: {'; '.join(name.get('positive', [])) or '없음'}\n"
            f"  상극: {'; '.join(name.get('negative', [])) or '없음'}"
        )
    mbti_block = ""
    if mbti.get("a") and mbti.get("b"):
        mbti_block = (
            f"\n[MBTI 호환]\n"
            f"  A {mbti['a']} × B {mbti['b']} → 점수 {mbti.get('score', '?')}/9"
        )

    rel_hint = _RELATION_MODE_HINT.get(relation_mode, _RELATION_MODE_HINT["romantic"])
    user = (
        f"[관계 유형] {relation_mode} — {rel_hint}\n\n"
        f"[결정론 궁합 데이터]\n"
        f"종합 점수: {compat.get('score', '?')}/100 ({compat.get('grade', '?')})\n\n"
        f"[일주 관계]\n"
        f"  A 일주: {stem.get('a','?')}{branch.get('a','?')}\n"
        f"  B 일주: {stem.get('b','?')}{branch.get('b','?')}\n"
        f"  천간 관계: {stem_rel or '특별 관계 없음'}\n"
        f"  지지 관계: {branch_rel or '특별 관계 없음'}\n\n"
        f"[오행 흐름]\n"
        f"  상생: {wx_pos or '없음'}\n"
        f"  상극: {wx_neg or '없음'}"
        f"{mbti_block}{name_block}\n\n"
        f"[작성 형식] — 4 섹션 모두 작성, 관계 유형의 어휘를 유지:\n"
        f"### 1. Core Resonance (핵심 공명) — 일주 합/충이 만들어내는 두 사람의 본질적 끌림과 거리감 (3~4문장)\n"
        f"### 2. Daily Rhythm (일상 리듬) — MBTI 인지 기능 + 오행 흐름이 만드는 평소 상호작용 (3~4문장)\n"
        f"### 3. Friction Points (갈등 지점) — 충/형/파/해/상극이 드러나는 위기 패턴과 회복법 (3~4문장)\n"
        f"### 4. Growth Together (함께 성장) — 서로의 부족한 기운/기능을 어떻게 보완하는가 (3~4문장)"
    )
    lang_directive = {
        "en": "\n\n[Output language] Write the FINAL answer in natural English. "
              "Keep section titles in English. Keep Hanja day-stem in parentheses.",
        "ja": "\n\n[出力言語] 最終解説は日本語で書く。セクション見出しは日本語化、"
              "四柱の漢字（甲乙など）は括弧書きで残す。",
    }.get(lang, "")
    user = user + lang_directive
    try:
        return call_llm_sync(
            user_text=user, system_prompt=_COMPAT_SYSTEM, model=model_label
        )
    except Exception as e:
        return f"(궁합 해설 생성 실패: {e})"


__all__ = [
    "explain_saju",
    "explain_section",
    "explain_fusion",
    "critique_fusion",
    "explain_fusion_with_critic",
    "explain_compat",
]
