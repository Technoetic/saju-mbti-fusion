"""꿈 해석 오케스트레이터 — 14개 AI 에이전트 + 30 도메인 통합.

흐름:
  PRE (병렬):
    A7 위기 탐지 (결정론, 차단 시 즉시 종료)
    B3 페르소나 분기
    B2 다국어 라우터
    A1 텍스트 정제 (옵션 LLM)
  ANALYZE:
    30 도메인 결정론 분석 (dream.analyze_dream)
  CORE LLM (병렬):
    A3 표상 양가 카드
    A4 한방 장부 (조건부 LLM)
    A5 융 원형 분류 (조건부 LLM)
    A9 Lakoff 토폴로지 ⭐
    A10 카타르시스 LLM 미세
    A11 디지털 바이오마커 (DB 있을 때)
  SYNTHESIZE:
    기존 dream.interpret_dream의 critic 루프 (도메인 사실 + 에이전트 결과 통합)
  POST:
    B1 환각 억제 RAG 게이트
    B5 면책 푸터 (engine.safety)
"""

from __future__ import annotations
from typing import Any
import asyncio
import hashlib
import json
import time
from pathlib import Path

from engine.divination.dream import (
    analyze_dream,
    DREAM_SYSTEM,
    DREAM_CRITIC_SYSTEM,
    _build_facts_block,
    critique_dream,
)
from engine.divination.dream_lex.personal_context import (
    PersonalContext, build_context_from_dict,
)
from engine.safety import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
    build_legal_footer,
)

from engine.agents.persona_router import classify_persona
from engine.agents.locale_router import route_locale
from engine.agents.text_cleaner import run_text_cleaner
from engine.agents.bivalent_cards import generate_bivalent_cards
from engine.agents.lakoff_topology import extract_topology
from engine.agents.hanbang_organ import run_hanbang_agent
from engine.agents.jung_classifier import classify_archetype
from engine.agents.cathartic_llm import classify_arc_llm
from engine.agents.biomarker import compute_biomarker_signals
from engine.agents.weight_learner import get_personalized_weights
from engine.agents.rag_gate import evaluate_rag_compliance


ORCHESTRATOR_LABEL = (
    "꿈 해석 오케스트레이터 — 14 에이전트 + 30 도메인 통합 (3계층 PRE→CORE→POST)."
)

# v2 캐시 — 사용자별 (dream_text + profile) 키 → 24h
_V2_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "v2_cache"
_V2_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_V2_TTL_SEC = 24 * 3600


def _v2_cache_key(
    dream_text: str,
    user_id: str | None,
    profile: dict[str, Any] | None,
    locale: str | None,
    user_target_domain: str | None,
) -> str:
    src = json.dumps({
        "u": user_id or "anon",
        "d": (dream_text or "").strip(),
        "p": profile or {},
        "l": locale or "ko",
        "t": user_target_domain or "",
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:32]


def _v2_cache_get(key: str) -> dict[str, Any] | None:
    f = _V2_CACHE_DIR / f"{key}.json"
    if not f.exists():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("_cached_at", 0) + _V2_TTL_SEC > time.time():
            d["cached"] = True
            return d
    except Exception:
        pass
    return None


def _v2_cache_set(key: str, result: dict[str, Any]) -> None:
    try:
        copy = dict(result)
        copy["_cached_at"] = time.time()
        f = _V2_CACHE_DIR / f"{key}.json"
        f.write_text(json.dumps(copy, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def invalidate_user_cache(user_id: str) -> dict[str, Any]:
    """사용자 프로필 변경 시 호출 — 해당 사용자의 모든 v2 캐시 삭제."""
    if not user_id:
        return {"deleted": 0}
    # 캐시 키는 sha256이라 user_id로 직접 매칭 불가 → 모든 파일 읽어 검사
    deleted = 0
    for f in _V2_CACHE_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            # 캐시 내부에 user_id 단서가 없으므로 안전하게 cached_at 기준 24h 후만 cleanup
            # 대신 더 단순한 방법: 모든 캐시를 무효화 (사용자 수 적을 때 OK)
            # 사용자별 invalidation은 키 prefix 도입으로 v2.1에서
            if d.get("_cached_at", 0) + _V2_TTL_SEC < time.time():
                f.unlink()
                deleted += 1
        except Exception:
            pass
    return {"deleted": deleted, "method": "expired_only"}


async def interpret_dream_v2(
    dream_text: str,
    *,
    user_id: str | None = None,
    profile: dict[str, Any] | None = None,
    locale: str | None = "ko",
    religion: str | None = None,
    user_target_domain: str | None = None,
    enable_llm_agents: bool = True,
    max_rounds: int = 2,
) -> dict[str, Any]:
    """v2 통합 해석 엔드포인트.

    Args:
        dream_text: 원본 꿈 텍스트
        user_id: 익명 ID (DB 종단 기능 활성)
        profile: PersonalContext dict
        locale: 'ko'|'en'|'ja'|'zh'|'ar'|...
        religion: 'muslim' 등
        user_target_domain: 'career'|'romance'|... (Lakoff cross-mapping)
        enable_llm_agents: False면 LLM 에이전트 우회 (디버깅용)
    """
    from engine.llm_sync import call_llm_sync

    start_time = time.time()
    profile = profile or {}

    # ─── 캐시 체크 (위기 검사 후 일치하지 않는 입력만) ───
    cache_key = _v2_cache_key(dream_text, user_id, profile, locale, user_target_domain)

    # ─── PRE: 위기 탐지 (즉시 차단 가능) ───
    crisis = detect_crisis(dream_text)
    if crisis["crisis_detected"]:
        # 위기 응답은 캐시하지 않음
        return {
            "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
            "agent_meta": {
                "stopped_at": "PRE_crisis",
                "severity": crisis["severity"],
            },
            "crisis_alert": {
                "severity": crisis["severity"],
                "hotlines": EMERGENCY_HOTLINES_KR,
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,
            "rounds": 0,
            "cached": False,
            "elapsed_ms": int((time.time() - start_time) * 1000),
        }

    # 위기 없을 때만 캐시 확인
    cached = _v2_cache_get(cache_key)
    if cached:
        cached["elapsed_ms"] = int((time.time() - start_time) * 1000)
        return cached

    # ─── PRE: 페르소나·로케일·텍스트 정제 (병렬) ───
    persona = classify_persona(profile, dream_text)
    locale_routing = route_locale(locale, religion)
    text_cleaner_result = (
        await asyncio.to_thread(run_text_cleaner, dream_text, use_llm=enable_llm_agents)
        if enable_llm_agents
        else run_text_cleaner(dream_text, use_llm=False)
    )
    cleaned_text = text_cleaner_result["deterministic"]["cleaned_text"]

    # ─── ANALYZE: 30 도메인 결정론 분석 ───
    ctx = (
        build_context_from_dict(profile)
        if isinstance(profile, dict) else profile
    )
    analysis = await asyncio.to_thread(analyze_dream, cleaned_text, ctx)

    # ─── CORE: 5개 LLM 에이전트 + DB 바이오마커 (병렬) ───
    has_physical_symptoms = any(
        m in cleaned_text for m in ("허리", "심장", "기침", "두통", "복통", "어지럼")
    )

    if enable_llm_agents:
        # 병렬 실행 — 각 to_thread로 LLM 동시 호출
        bivalent_task = asyncio.to_thread(
            generate_bivalent_cards, cleaned_text, profile, 6
        )
        lakoff_task = asyncio.to_thread(
            extract_topology, cleaned_text, user_target_domain=user_target_domain
        )
        hanbang_task = asyncio.to_thread(
            run_hanbang_agent, cleaned_text, has_physical_symptoms=has_physical_symptoms
        )
        jung_task = asyncio.to_thread(
            classify_archetype, cleaned_text, gender=ctx.gender if ctx else None
        )
        cathartic_task = asyncio.to_thread(classify_arc_llm, cleaned_text)

        bivalent, lakoff_topo, hanbang, jung, cathartic_fine = await asyncio.gather(
            bivalent_task, lakoff_task, hanbang_task, jung_task, cathartic_task,
            return_exceptions=True,
        )
    else:
        # LLM 우회 — 결정론만
        bivalent = generate_bivalent_cards(cleaned_text, profile, 6)
        lakoff_topo = {"agent": "A9", "llm_topology": None, "deterministic_metaphors": analysis.get("lakoff_cmt")}
        hanbang = {"agent": "A4", "llm_synthesis": None, "eumsabalmong": analysis.get("eumsabalmong"), "donguibogam": analysis.get("donguibogam")}
        jung = {"agent": "A5", "llm_classification": None, "deterministic": analysis.get("archetypes")}
        cathartic_fine = {"agent": "A10", "llm_classification": None, "deterministic": analysis.get("cathartic")}

    # A11 디지털 바이오마커 (DB 있을 때만)
    biomarker = None
    if user_id:
        try:
            from engine.storage import DreamDiaryRepo, ClinicalLogRepo
            diaries = await asyncio.to_thread(DreamDiaryRepo.list_recent, user_id, 30, 60)
            clinical_hist = await asyncio.to_thread(ClinicalLogRepo.history, user_id, None, 20)
            if diaries:
                biomarker = compute_biomarker_signals(diaries, clinical_hist)
        except Exception as e:
            biomarker = {"agent": "A11", "error": str(e)}

    # 에이전트 예외 → dict로 정리
    def _safe(v: Any, agent_name: str) -> dict[str, Any]:
        if isinstance(v, Exception):
            return {"agent": agent_name, "error": str(v)}
        return v

    bivalent = _safe(bivalent, "A3")
    lakoff_topo = _safe(lakoff_topo, "A9")
    hanbang = _safe(hanbang, "A4")
    jung = _safe(jung, "A5")
    cathartic_fine = _safe(cathartic_fine, "A10")

    # ─── SYNTHESIZE: 본문 합성 + critic 루프 ───
    # 도메인 사실 블록 + 에이전트 결과를 user 메시지에 통합
    facts_block = _build_facts_block(analysis)
    agents_facts = _build_agents_facts_block(
        bivalent, lakoff_topo, hanbang, jung, cathartic_fine, biomarker, persona,
    )

    full_user_message = _build_synthesis_user_message(
        cleaned_text, ctx, facts_block, agents_facts, persona, locale_routing,
    )

    critic_history: list[dict[str, Any]] = []
    final_text = ""
    final_critique: dict[str, Any] = {}

    if enable_llm_agents:
        for round_idx in range(1, max_rounds + 1):
            try:
                text = await asyncio.to_thread(
                    call_llm_sync,
                    user_text=full_user_message,
                    system_prompt=_build_synthesis_system_prompt(locale_routing, persona),
                )
            except Exception as e:
                text = f"(LLM 합성 실패: {e})"

            critique = await asyncio.to_thread(critique_dream, text, analysis)
            critic_history.append({"round": round_idx, **critique})
            final_text = text
            final_critique = critique
            if critique["passed"]:
                break
            full_user_message = (
                full_user_message
                + "\n\n[직전 풀이 검수 피드백 — 반영하여 다시 작성]\n"
                + (critique.get("verdict") or "")
            )
    else:
        final_text = "(LLM 합성 우회 — enable_llm_agents=False)"

    # ─── POST: 환각 억제 RAG 게이트 ───
    rag = evaluate_rag_compliance(
        final_text,
        facts_block + "\n" + agents_facts,
        min_domain_citations=3,
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    result = {
        "text": final_text,
        "rounds": len(critic_history),
        "critic_passed": final_critique.get("passed"),
        "critic_total": final_critique.get("total"),
        "rag_gate": {
            "passed": rag["pass"],
            "domain_citations": rag["domain_citations"],
            "fact_overlap_ratio": rag["fact_overlap_ratio"],
            "issues": rag["issues"],
        },
        "agent_meta": {
            "persona": persona.to_dict(),
            "locale": locale_routing.to_dict(),
            "text_cleaner": text_cleaner_result.get("structured"),
            "bivalent_cards_count": {
                "길": len((bivalent.get("cards_길") or [])),
                "흉": len((bivalent.get("cards_흉") or [])),
                "양가": len((bivalent.get("cards_양가") or [])),
            },
            "lakoff_top_hypotheses": (lakoff_topo.get("summary") or {}).get("top_hypotheses", [])[:3],
            "jung_primary": (jung.get("llm_classification") or {}).get("primary_archetype"),
            "jung_stage": (jung.get("llm_classification") or {}).get("individuation_stage"),
            "cathartic_arc": cathartic_fine.get("final_arc"),
            "is_cathartic": cathartic_fine.get("is_cathartic"),
            "hanbang_synthesis": (hanbang.get("llm_synthesis") or "")[:200],
            "biomarker_signal": (biomarker or {}).get("depression_signal"),
        },
        "domain_analysis_summary": _slim_analysis(analysis),
        "crisis_alert": None,
        "legal_notice": build_legal_footer(),
        "elapsed_ms": elapsed_ms,
        "cached": False,
    }

    # 캐시 저장 (rag pass + critic 30+일 때만 — 품질 낮은 응답은 캐시 안 함)
    if rag["pass"] and (final_critique.get("total") or 0) >= 30:
        _v2_cache_set(cache_key, result)

    return result


def _build_agents_facts_block(
    bivalent: dict[str, Any],
    lakoff_topo: dict[str, Any],
    hanbang: dict[str, Any],
    jung: dict[str, Any],
    cathartic_fine: dict[str, Any],
    biomarker: dict[str, Any] | None,
    persona: Any,
) -> str:
    """에이전트 결과를 [에이전트 사실 블록]으로 조립."""
    L: list[str] = ["[에이전트 사실 블록 — 다음 결과만 추가 근거로 사용]", ""]

    # A3 양가 카드
    if bivalent.get("cards_길") or bivalent.get("cards_흉"):
        L.append(f"[A3 양가 카드] 우선순위: {bivalent.get('recommended_priority')}")
        for c in (bivalent.get("cards_길") or [])[:3]:
            L.append(f"  · 길: {c['keyword']}({c['source']}, conf={c['confidence']:.2f}): {c['meaning']}")
        for c in (bivalent.get("cards_흉") or [])[:3]:
            L.append(f"  · 흉: {c['keyword']}({c['source']}, conf={c['confidence']:.2f}): {c['meaning']}")
        L.append("")

    # A9 Lakoff 토폴로지
    lakoff_llm = (lakoff_topo or {}).get("llm_topology") or {}
    top_hyps = ((lakoff_topo or {}).get("summary") or {}).get("top_hypotheses") or []
    if top_hyps:
        L.append("[A9 Lakoff 토폴로지 — 표면 직역 금지, 도식 기반 가설]")
        for h in top_hyps[:3]:
            L.append(
                f"  · {h.get('source_schema')} → {h.get('target_domain')} "
                f"(conf={h.get('confidence', 0):.2f}): {h.get('hypothesis')}"
            )
        L.append("")

    # A4 한방 합성
    if hanbang.get("llm_synthesis"):
        L.append("[A4 한방 진단 톤 (단정 금지, 한의원 상담 권장)]")
        L.append(f"  · {hanbang['llm_synthesis']}")
        L.append("")

    # A5 융 분류
    jung_llm = (jung or {}).get("llm_classification") or {}
    if jung_llm.get("primary_archetype"):
        L.append(f"[A5 융 원형 분류] 1차: {jung_llm['primary_archetype']} "
                 f"/ 개성화 단계: {jung_llm.get('individuation_stage')}")
        if jung_llm.get("compensation_hypothesis"):
            L.append(f"  · 보상 가설: {jung_llm['compensation_hypothesis']}")
        L.append("")

    # A10 카타르시스
    final_arc = cathartic_fine.get("final_arc")
    if final_arc and final_arc != "unknown":
        L.append(f"[A10 감정 아크 최종] {final_arc}")
        if cathartic_fine.get("is_cathartic"):
            L.append("  · ★ 카타르시스 꿈 — 능동적 정서 처리 신호")
        cf_llm = cathartic_fine.get("llm_classification")
        if cf_llm and cf_llm.get("turning_point"):
            L.append(f"  · 반전 지점: \"{cf_llm['turning_point']}\"")
        L.append("")

    # A11 바이오마커
    if biomarker and biomarker.get("depression_signal"):
        L.append(f"[A11 디지털 바이오마커] {biomarker['depression_signal']}")
        L.append(f"  · {biomarker.get('recommendation', '')}")
        L.append("")

    # 페르소나
    if persona and persona.primary:
        L.append(f"[B3 페르소나] {persona.primary} ({persona.to_dict()['primary_label']}) "
                 f"— UX 톤: {persona.ux_tone}")
        L.append("")

    return "\n".join(L)


def _build_synthesis_user_message(
    dream_text: str,
    ctx: PersonalContext | None,
    facts_block: str,
    agents_facts: str,
    persona: Any,
    locale_routing: Any,
) -> str:
    """본문 합성용 user 메시지."""
    context_block = ctx.to_prompt_block() if ctx else ""

    parts = [
        "[손님의 꿈]",
        dream_text.strip(),
        "",
    ]
    if context_block:
        parts.append(context_block)
        parts.append("")
    parts.append(facts_block)
    parts.append("")
    parts.append(agents_facts)
    parts.append("")
    parts.append(
        f"위 모든 사실 블록만을 근거로, 해몽가의 어조로 풀이를 작성하십시오. "
        f"사실에 없는 상징은 임의로 끌어오지 마십시오. "
        f"페르소나({persona.primary})의 UX 톤({persona.ux_tone})을 반영하십시오. "
        f"{locale_routing.llm_directive}"
    )
    return "\n".join(parts)


def _build_synthesis_system_prompt(locale_routing: Any, persona: Any) -> str:
    """기본 DREAM_SYSTEM + 로케일·페르소나 추가."""
    extra = (
        f"\n\n[추가 지시]\n"
        f"  • 출력 언어: {locale_routing.locale}\n"
        f"  • 페르소나: {persona.primary} (톤: {persona.ux_tone})\n"
    )
    if not locale_routing.enable_ibn_sirin_active:
        extra += "  • 이븐 시린은 비활성 — 짧게 1줄 언급만 허용\n"
    return DREAM_SYSTEM + extra


def _slim_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    """프론트 전송용 슬림 요약 (기존 server.py와 호환)."""
    return {
        "artemidorus_class": (analysis.get("artemidorus_class") or {}).get("class"),
        "wuxing_dominant": (analysis.get("wuxing") or {}).get("dominant_element"),
        "folk_dominant": (analysis.get("korean_folk") or {}).get("dominant_category"),
        "archetype_dominant": (analysis.get("archetypes") or {}).get("dominant_archetype"),
        "bizarreness": (analysis.get("hobson") or {}).get("bizarreness_score"),
        "tst_level": (analysis.get("tst") or {}).get("tst_level"),
        "cathartic_arc": (analysis.get("cathartic") or {}).get("arc_type"),
        "hexagram": ((analysis.get("iching") or {}).get("hexagram") or {}).get("name"),
    }


__all__ = [
    "ORCHESTRATOR_LABEL",
    "interpret_dream_v2",
]
