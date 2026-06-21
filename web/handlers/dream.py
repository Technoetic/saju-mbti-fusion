"""웹 API 핸들러 — dream 도메인 (구조 리팩터링 2026-06-21).

PersonalityAPIServer 가 본 Mixin 을 상속. self.engine·self.saju_cli·self._analytics 등
공유 상태는 최종 클래스에서 제공되므로 본 파일에서 정의하지 않는다.
원본 web/server.py 에서 메서드 블록을 물리적으로 분리 (동작 불변).
"""
from __future__ import annotations

import asyncio  # noqa: F401
import os  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Any  # noqa: F401

from fastapi import HTTPException, Request  # noqa: F401
from fastapi.responses import StreamingResponse  # noqa: F401

import web.schemas as _schemas
from web.schemas import *  # noqa: F401,F403


class DreamHandlersMixin:
    """dream 도메인 핸들러 묶음 (Mixin)."""

    async def post_dream_interpret(
        self, req: DreamInterpretRequest
    ) -> dict[str, Any]:
        """해몽 v1 호환 — 내부적으로 v2 오케스트레이션 호출.

        기존 응답 키(text/rounds/critic_*/cached/analysis_summary/crisis_alert/legal_notice)
        를 그대로 유지하면서, v2 신규 키(agent_meta·rag_gate)를 추가.

        구버전 클라이언트는 기존 키만 읽고, 신버전 클라이언트는 agent_meta 활용 가능.
        """
        try:
            from engine.agents import interpret_dream_v2

            # v1 flat profile → v2 nested profile
            payload = req.model_dump()
            dream_text = payload.pop("dream_text", "") or ""
            # locale·religion·user_target_domain은 v1에 없으므로 기본값
            profile = payload  # 나머지 전부 = PersonalContext 필드

            v2_result = await interpret_dream_v2(
                dream_text,
                user_id=None,  # v1은 익명 (DB 비활성)
                profile=profile,
                locale="ko",
                religion=None,
                user_target_domain=None,
                enable_llm_agents=True,
            )

            # v1 호환 응답 형식
            return {
                "text": v2_result.get("text"),
                "rounds": v2_result.get("rounds"),
                "critic_passed": v2_result.get("critic_passed"),
                "critic_total": v2_result.get("critic_total"),
                "cached": False,  # v2는 캐시 비사용 (오케스트레이션이 더 정밀)
                "analysis_summary": v2_result.get("domain_analysis_summary"),
                "crisis_alert": v2_result.get("crisis_alert"),
                "legal_notice": v2_result.get("legal_notice"),
                # ─── v2 추가 키 (구버전 클라이언트는 무시) ───
                "agent_meta": v2_result.get("agent_meta"),
                "rag_gate": v2_result.get("rag_gate"),
                "elapsed_ms": v2_result.get("elapsed_ms"),
                "_engine_version": "v2",
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_irt_rescript(self, req: IRTRescriptRequest) -> dict[str, Any]:
        """IRT Step 4 — 표적 악몽의 재각본 3안 생성."""
        try:
            self._analytics["irt_rescript_calls"] += 1
            from engine.clinical.irt import generate_rescripted_endings
            result = await asyncio.to_thread(
                generate_rescripted_endings, req.nightmare_text
            )
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_incubation_session(
        self, req: IncubationRequest
    ) -> dict[str, Any]:
        """꿈 부화 안내 — 취침 전 5단계 + 회상 가이드."""
        try:
            from engine.divination.dream_lex.incubation import (
                build_incubation_session,
                recommend_incubation,
            )
            from engine.safety import build_legal_footer

            session = await asyncio.to_thread(build_incubation_session, req.question)
            recommendation = await asyncio.to_thread(
                recommend_incubation,
                low_recall=req.low_recall,
                upcoming_decision=req.upcoming_decision,
                high_stress=req.high_stress,
                lucid_dream_practice=req.lucid_dream_practice,
            )
            return {
                "session": session,
                "recommendation": recommendation,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dream_hvdc_llm(
        self, req: HVdCLLMRequest
    ) -> dict[str, Any]:
        """LLM HVdC 자동 코딩 (Bertolini 2024). 결정론 코더와 union 병합 옵션."""
        try:
            from engine.divination.dream_lex.hvdc_llm import (
                code_dream_with_llm,
                merge_deterministic_and_llm,
            )
            from engine.divination.dream_lex.hallvandecastle import code_dream as det_code, compute_indices
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "coding": None,
                }

            llm_result = await asyncio.to_thread(code_dream_with_llm, req.dream_text)
            coding = llm_result["coding"]
            if req.merge_with_deterministic:
                det = await asyncio.to_thread(det_code, req.dream_text)
                coding = await asyncio.to_thread(merge_deterministic_and_llm, det, coding)

            # 정서 dict의 list/int 혼합 정규화 후 indices 계산
            try:
                indices = compute_indices(coding)
            except Exception:
                indices = None

            return {
                "coding": coding,
                "indices": indices,
                "method": llm_result["method"],
                "parse_success": llm_result["parse_success"],
                "merged_with_deterministic": req.merge_with_deterministic,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_lucid_program(self) -> dict[str, Any]:
        """7일 자각몽 입문 프로그램."""
        try:
            from engine.divination.dream_lex.lucid import (
                build_7day_lucid_program,
                REALITY_CHECKS_KO,
            )
            from engine.safety import build_legal_footer
            program = build_7day_lucid_program()
            return {
                "program": program,
                "all_reality_checks": REALITY_CHECKS_KO,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_mood_curve(
        self, req: MoodCurveRequest
    ) -> dict[str, Any]:
        """Cartwright 7일+ mood-dream 곡선 분석.

        daily_entries가 비었고 user_id가 있으면 DB에서 자동 로드.
        """
        try:
            from engine.divination.dream_lex.cartwright import analyze_mood_dream_curve
            from engine.safety import build_legal_footer

            entries = req.daily_entries or []
            if not entries and req.user_id:
                from engine.storage import DreamDiaryRepo
                diaries = await asyncio.to_thread(
                    DreamDiaryRepo.list_recent, req.user_id, req.days, 60
                )
                entries = [
                    {
                        "date_iso": d["created_at_iso"],
                        "valence": d["valence"],
                        "vividness": d["vividness"],
                        "recall_quality": d["recall_quality"],
                        "narrative_text": d["narrative_text"],
                    }
                    for d in diaries
                ]
            result = await asyncio.to_thread(analyze_mood_dream_curve, entries)
            return {
                **result,
                "source": "db" if (req.user_id and not req.daily_entries) else "client",
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_myoe_long_term(
        self, req: MyoeLongTermRequest
    ) -> dict[str, Any]:
        """묘에 몽기 — 장기 일기(14일+) 반복 모티프·정서 곡선 분석.

        entries 빈 경우 user_id로 DB 자동 로드.
        """
        try:
            from engine.divination.dream_lex.myoe import analyze_long_term_diary
            from engine.safety import build_legal_footer

            entries = req.entries or []
            if not entries and req.user_id:
                from engine.storage import MyoeDiaryRepo
                entries = await asyncio.to_thread(
                    MyoeDiaryRepo.list_for_analysis, req.user_id, req.days, 60
                )
            result = await asyncio.to_thread(
                analyze_long_term_diary, entries, req.min_entries
            )
            return {
                **result,
                "source": "db" if (req.user_id and not req.entries) else "client",
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_myoe_diary_template(self) -> dict[str, Any]:
        """묘에 스타일 자기관찰 일지 템플릿."""
        try:
            from engine.divination.dream_lex.myoe import (
                MYOE_DIARY_FIELDS_KO, TRADITIONAL_MOTIFS, MYOE_LABEL,
            )
            return {
                "label": MYOE_LABEL,
                "diary_fields": MYOE_DIARY_FIELDS_KO,
                "traditional_motifs": list(TRADITIONAL_MOTIFS.keys()),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dormio_session(
        self, req: DormioSessionRequest
    ) -> dict[str, Any]:
        """Dormio TDI 세션 — N1 표적 부화 안내 + 음성 큐 + 보고 양식."""
        try:
            from engine.divination.dream_lex.dormio import build_dormio_session
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(
                build_dormio_session, req.target_topic, req.category, req.cycles
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_dormio_synthesize(
        self, req: DormioSynthesizeRequest
    ) -> dict[str, Any]:
        """Dormio N회 미세꿈 보고들 종합 — 반복 이미지·정서 분포·예상 밖 요소."""
        try:
            from engine.divination.dream_lex.dormio import synthesize_microdream_insights
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(
                synthesize_microdream_insights, req.reports, req.target_topic
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_ullman_group(
        self, req: UllmanGroupRequest
    ) -> dict[str, Any]:
        """Ullman 그룹 꿈 분석 — N개 페르소나 LLM 동시 호출 + 투사 집계."""
        try:
            from engine.divination.dream_lex.ullman import (
                build_ullman_session, aggregate_persona_projections, ULLMAN_SYSTEM_KO,
            )
            from engine.llm_sync import call_llm_sync
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            # 위기 검사
            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "projections": [],
                }

            session = await asyncio.to_thread(
                build_ullman_session, req.dream_text, req.personas
            )
            if not session.get("ready"):
                raise HTTPException(400, session.get("error", "세션 빌드 실패"))

            # 각 페르소나에 LLM 호출 (병렬)
            async def _gen(p: dict[str, str]) -> dict[str, str]:
                try:
                    text = await asyncio.to_thread(
                        call_llm_sync,
                        user_text=p["user_message"],
                        system_prompt=ULLMAN_SYSTEM_KO,
                    )
                except Exception as e:
                    text = f"(생성 실패: {e})"
                return {
                    "persona_key": p["persona_key"],
                    "persona_name": p["persona_name"],
                    "text": text or "",
                }

            projections = await asyncio.gather(
                *(_gen(p) for p in session["persona_prompts"])
            )
            aggregate = await asyncio.to_thread(
                aggregate_persona_projections, list(projections)
            )

            return {
                "projections": list(projections),
                "aggregate": aggregate,
                "guidance": session.get("guidance"),
                "ullman_principle": session.get("ullman_principle"),
                "legal_notice": build_legal_footer(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 익명 사용자 ───────────────────────────
    async def post_dream_interpret_v2(
        self, req: InterpretV2Request
    ) -> dict[str, Any]:
        """v2 통합 해석 — 14 에이전트 + 30 도메인 (PRE→ANALYZE→CORE→SYNTH→POST).

        - 사용자별 일일 비용 가드 (기본 20회/24h)
        - 위기 신호 시 익명 통계 자동 누적
        - 캐시 hit 시 비용 0
        """
        try:
            from engine.agents import interpret_dream_v2
            from engine.storage import RateLimitRepo, CrisisStatsRepo, ErrorLogRepo

            # ─── 비용 가드: 사용자별 일일 한도 ───
            daily_limit = int(os.environ.get("V2_DAILY_LIMIT_PER_USER", "20"))
            if req.user_id and req.enable_llm_agents:
                gate = await asyncio.to_thread(
                    RateLimitRepo.check_and_record,
                    req.user_id, "dream_v2",
                    daily_limit=daily_limit, window_sec=86400,
                )
                if not gate["allowed"]:
                    raise HTTPException(
                        429,
                        f"{gate['reason']}. 내일 다시 시도해주세요.",
                    )

            result = await interpret_dream_v2(
                req.dream_text,
                user_id=req.user_id,
                profile=req.profile,
                locale=req.locale,
                religion=req.religion,
                user_target_domain=req.user_target_domain,
                enable_llm_agents=req.enable_llm_agents,
            )

            # ─── 모니터링 + 위기 익명 통계 ───
            try:
                self._analytics["dream_v2_calls"] += 1
                if result.get("crisis_alert"):
                    self._analytics["dream_v2_crisis_blocked"] += 1
                    # 위기 익명 통계 누적 (사용자 ID·텍스트 X)
                    ca = result["crisis_alert"]
                    await asyncio.to_thread(
                        CrisisStatsRepo.add,
                        ca.get("severity", "unknown"),
                        ca.get("matched_count", 0),
                        "dream_v2",
                    )
                if result.get("elapsed_ms"):
                    samples = self._analytics["dream_v2_elapsed_ms_samples"]
                    samples.append(result["elapsed_ms"])
                    self._analytics["dream_v2_elapsed_ms_samples"] = samples[-50:]
                am = result.get("agent_meta") or {}
                persona_key = (am.get("persona") or {}).get("primary")
                if persona_key:
                    self._analytics["dream_v2_persona_counts"][persona_key] = (
                        self._analytics["dream_v2_persona_counts"].get(persona_key, 0) + 1
                    )
                if am.get("is_cathartic"):
                    self._analytics["dream_v2_cathartic_counts"] += 1
            except Exception:
                pass
            return result
        except HTTPException:
            raise
        except Exception as e:
            try:
                from engine.storage import ErrorLogRepo
                await asyncio.to_thread(
                    ErrorLogRepo.add, str(e)[:500], "server",
                    user_id=req.user_id, severity="error",
                )
            except Exception:
                pass
            raise HTTPException(500, str(e))

    async def post_bivalent_feedback(
        self, req: BivalentFeedbackRequest
    ) -> dict[str, Any]:
        """B4 양가 카드 사용자 선택 피드백."""
        try:
            from engine.agents import record_feedback, get_user_feedback_summary
            result = await asyncio.to_thread(
                record_feedback, req.user_id, req.chosen_source, req.polarity, req.keyword
            )
            summary = await asyncio.to_thread(get_user_feedback_summary, req.user_id)
            return {"feedback": result, "summary": summary}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 운영 엔드포인트 ───────────────────────────
    async def post_freud_map(self, req: dict[str, Any]) -> dict[str, Any]:
        """A8 Freud 명시몽→잠재몽 LLM 매핑."""
        try:
            from engine.agents import map_latent_dream
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer
            dream_text = req.get("dream_text", "")
            crisis = detect_crisis(dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {"severity": crisis["severity"]},
                    "mapping": None,
                }
            result = await asyncio.to_thread(
                map_latent_dream, dream_text, req.get("recent_emotions"),
            )
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_social_unconscious(self, days: int = 7) -> dict[str, Any]:
        """A13 소셜 무의식 — 최근 N일 전체 사용자 일기 토픽 클러스터."""
        try:
            from engine.agents import aggregate_social_unconscious
            return await asyncio.to_thread(
                aggregate_social_unconscious,
                days=days, min_users=30, min_entries=100,
            )
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_hill_step(
        self, req: HillStepRequest
    ) -> dict[str, Any]:
        """Clara Hill 3단계 — 한 단계 실행 (LLM 호출 포함)."""
        try:
            from engine.divination.dream_lex.clara_hill import (
                build_step_prompt, ACTION_CATEGORIES_KO,
            )
            from engine.llm_sync import call_llm_sync
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            crisis = detect_crisis(req.dream_text)
            if crisis["crisis_detected"]:
                return {
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "step": req.step,
                }

            session_data = {
                "dream_text": req.dream_text,
                "exploration_responses": req.exploration_responses,
                "insight_text": req.insight_text,
            }
            prompt_info = await asyncio.to_thread(
                build_step_prompt, req.step, session_data
            )
            try:
                text = await asyncio.to_thread(
                    call_llm_sync,
                    user_text=prompt_info["user_message"],
                    system_prompt=prompt_info["system"],
                )
            except Exception as e:
                text = f"(생성 실패: {e})"

            response: dict[str, Any] = {
                "step": req.step,
                "step_name": prompt_info["step_name"],
                "text": (text or "").strip(),
                "legal_notice": build_legal_footer(),
            }
            # Step 1: 추천 프롬프트도 함께
            if req.step == 1 and "suggested_prompts" in prompt_info:
                response["suggested_prompts"] = prompt_info["suggested_prompts"]
            # Step 3: 행동 카테고리
            if req.step == 3:
                response["action_categories"] = ACTION_CATEGORIES_KO
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))
