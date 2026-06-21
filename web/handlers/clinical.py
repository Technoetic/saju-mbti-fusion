"""웹 API 핸들러 — clinical 도메인 (구조 리팩터링 2026-06-21).

PersonalityAPIServer 가 본 Mixin 을 상속. self.engine·self.saju_cli·self._analytics 등
공유 상태는 최종 클래스에서 제공되므로 본 파일에서 정의하지 않는다.
원본 web/server.py 에서 메서드 블록을 물리적으로 분리 (동작 불변).
"""
from __future__ import annotations

import asyncio  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Any  # noqa: F401

from fastapi import HTTPException, Request  # noqa: F401
from fastapi.responses import StreamingResponse  # noqa: F401

import web.schemas as _schemas
from web.schemas import *  # noqa: F401,F403


class ClinicalHandlersMixin:
    """clinical 도메인 핸들러 묶음 (Mixin)."""

    async def post_clinical_screening(
        self, req: ClinicalScreeningRequest
    ) -> dict[str, Any]:
        """임상 척도 자가검사 — CES-D / BDI-K / STAI-K / PSQI / ISI 통합 채점.

        주어진 응답만 채점하고, 모든 결과를 risk_router로 위험도 산출.
        고위험·임상 위기 시 1393 안내 포함.
        """
        try:
            from engine.clinical import (
                score_ces_d, score_bdi_k, score_stai_k_state, score_psqi, score_isi,
                assess_clinical_risk,
            )
            from engine.clinical.irt import should_trigger_irt
            from engine.safety import build_legal_footer

            results: dict[str, Any] = {}
            if req.ces_d_responses is not None:
                results["ces_d"] = await asyncio.to_thread(
                    score_ces_d, req.ces_d_responses, req.age
                )
            if req.bdi_k_responses is not None:
                results["bdi_k"] = await asyncio.to_thread(score_bdi_k, req.bdi_k_responses)
            if req.stai_k_state_responses is not None:
                results["stai_k_state"] = await asyncio.to_thread(
                    score_stai_k_state, req.stai_k_state_responses
                )
            if req.psqi_component_scores is not None:
                results["psqi"] = await asyncio.to_thread(
                    score_psqi, req.psqi_component_scores
                )
            if req.isi_responses is not None:
                results["isi"] = await asyncio.to_thread(score_isi, req.isi_responses)

            risk = await asyncio.to_thread(
                assess_clinical_risk,
                ces_d_result=results.get("ces_d"),
                bdi_k_result=results.get("bdi_k"),
                stai_k_result=results.get("stai_k_state"),
                psqi_result=results.get("psqi"),
                isi_result=results.get("isi"),
                chronic_nightmare_weeks=req.chronic_nightmare_weeks,
                nightmare_freq_per_week=req.nightmare_freq_per_week,
            )
            irt_trigger = await asyncio.to_thread(
                should_trigger_irt,
                req.nightmare_freq_per_week,
                req.chronic_nightmare_weeks,
            )

            return {
                "scores": results,
                "risk_assessment": risk,
                "irt_trigger": irt_trigger,
                "legal_notice": build_legal_footer(
                    is_crisis=(risk["risk_level"] == "임상 위기")
                ),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_clinical_instruments(self) -> dict[str, Any]:
        """임상 척도 문항 목록 — 프론트가 자가검사 폼을 렌더링할 때 사용."""
        try:
            from engine.clinical.ces_d import (
                CES_D_ITEMS_KO, CES_D_RESPONSE_OPTIONS,
                CES_D_CUTOFF_ADULT, CES_D_CUTOFF_SENIOR,
            )
            from engine.clinical.bdi_k import BDI_K_ITEMS_KO, BDI_K_CUTOFF
            from engine.clinical.stai_k import (
                STAI_K_STATE_ITEMS_KO, STAI_K_STATE_RESPONSE_OPTIONS, STAI_K_STATE_CUTOFF,
            )
            from engine.clinical.psqi import PSQI_COMPONENTS, PSQI_CUTOFF
            from engine.clinical.isi import ISI_ITEMS_KO
            return {
                "ces_d": {
                    "items": CES_D_ITEMS_KO,
                    "response_options": CES_D_RESPONSE_OPTIONS,
                    "cutoff_adult": CES_D_CUTOFF_ADULT,
                    "cutoff_senior": CES_D_CUTOFF_SENIOR,
                    "instrument": "CES-D 한국판 (전겸구·이민규 1992)",
                },
                "bdi_k": {
                    "items": BDI_K_ITEMS_KO,
                    "cutoff": BDI_K_CUTOFF,
                    "instrument": "BDI 한국판 (이영호·송종용 1991)",
                },
                "stai_k_state": {
                    "items": STAI_K_STATE_ITEMS_KO,
                    "response_options": STAI_K_STATE_RESPONSE_OPTIONS,
                    "cutoff": STAI_K_STATE_CUTOFF,
                    "instrument": "STAI 상태 한국판 (한덕웅·이장호·전겸구 1996)",
                },
                "psqi": {
                    "components": PSQI_COMPONENTS,
                    "cutoff": PSQI_CUTOFF,
                    "instrument": "PSQI (Buysse 1989)",
                },
                "isi": {
                    "items": ISI_ITEMS_KO,
                    "instrument": "ISI (Bastien 2001)",
                },
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_clinical_log(self, req: ClinicalLogRequest) -> dict[str, Any]:
        """척도 채점 + 저장. 미저장 채점은 /api/clinical/screening 사용."""
        try:
            self._analytics["clinical_log_calls"] += 1
            from engine.storage import UserRepo, ClinicalLogRepo
            from engine.clinical import (
                score_ces_d, score_bdi_k, score_stai_k_state, score_psqi, score_isi,
            )
            from engine.safety import build_legal_footer

            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)

            inst = req.instrument
            if inst == "ces_d":
                result = await asyncio.to_thread(score_ces_d, req.responses, req.age)
            elif inst == "bdi_k":
                result = await asyncio.to_thread(score_bdi_k, req.responses)
            elif inst == "stai_k_state":
                result = await asyncio.to_thread(score_stai_k_state, req.responses)
            elif inst == "psqi":
                if not req.psqi_components:
                    raise HTTPException(400, "psqi_components 필요")
                result = await asyncio.to_thread(score_psqi, req.psqi_components)
            elif inst == "isi":
                result = await asyncio.to_thread(score_isi, req.responses)
            else:
                raise HTTPException(400, f"미지원 instrument: {inst}")

            log_id = await asyncio.to_thread(
                ClinicalLogRepo.add, req.user_id, inst, result,
                req.responses if inst != "psqi" else req.psqi_components,
            )

            is_crisis = bool(result.get("suicide_alert"))
            return {
                "log_id": log_id,
                "result": result,
                "legal_notice": build_legal_footer(is_crisis=is_crisis),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_clinical_trend(self, req: ClinicalLogRequest) -> dict[str, Any]:
        """척도 추세 (첫 측정 vs 최근)."""
        try:
            from engine.storage import ClinicalLogRepo
            from engine.safety import build_legal_footer
            trend = await asyncio.to_thread(
                ClinicalLogRepo.trend, req.user_id, req.instrument
            )
            return {**trend, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── Stickgold 72h 학습 로그 ───────────────────────────
