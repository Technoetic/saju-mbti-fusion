"""웹 API 핸들러 — user 도메인 (구조 리팩터링 2026-06-21).

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


class UserHandlersMixin:
    """user 도메인 핸들러 묶음 (Mixin)."""

    async def post_user_new(self) -> dict[str, Any]:
        """새 익명 사용자 생성 — 클라이언트가 user_id를 localStorage 보관."""
        try:
            from engine.storage import new_user_id, UserRepo
            uid = new_user_id()
            user = await asyncio.to_thread(UserRepo.get_or_create, uid)
            return {"user_id": uid, "created_at_iso": user.get("created_at_iso")}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_profile(self, req: UserProfileRequest) -> dict[str, Any]:
        """사용자 프로필 갱신 (사주·MBTI·연령 등). 갱신 시 v2 캐시 만료분 정리."""
        try:
            from engine.storage import UserRepo
            from engine.agents.orchestrator import invalidate_user_cache
            profile = {
                k: v for k, v in req.model_dump().items()
                if k != "user_id" and v is not None
            }
            user = await asyncio.to_thread(
                UserRepo.get_or_create, req.user_id, **profile
            )
            # 프로필 변경 → 캐시 만료 청소
            cache_result = await asyncio.to_thread(invalidate_user_cache, req.user_id)
            return {"user": user, "cache": cache_result}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_consent(self, req: ConsentRequest) -> dict[str, Any]:
        """민감정보 별도 동의 (개인정보보호법 제23조)."""
        try:
            from engine.storage import UserRepo
            await asyncio.to_thread(UserRepo.set_consent, req.user_id, req.consent)
            return {"user_id": req.user_id, "consent": req.consent}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_user_delete(self, req: UserScopedRequest) -> dict[str, Any]:
        """사용자 + 모든 데이터 삭제 (개인정보보호법 삭제권)."""
        try:
            from engine.storage import UserRepo
            result = await asyncio.to_thread(UserRepo.delete, req.user_id)
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 회원가입 / 로그인 ───────────────────────────
    async def post_auth_signup(self, req: SignupRequest) -> dict[str, Any]:
        """이메일/비번 회원가입. 가입 후 user_id + 프로필 반환."""
        try:
            from engine.storage import AccountRepo, AccountError
            profile = req.model_dump(exclude={"email", "password", "nickname"})
            try:
                account = await asyncio.to_thread(
                    AccountRepo.signup,
                    req.email,
                    req.password,
                    req.nickname,
                    **profile,
                )
            except AccountError as ae:
                raise HTTPException(400, {"code": ae.code, "message": ae.message})
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_auth_login(self, req: LoginRequest) -> dict[str, Any]:
        """이메일/비번 로그인."""
        try:
            from engine.storage import AccountRepo, AccountError
            try:
                account = await asyncio.to_thread(
                    AccountRepo.login, req.email, req.password
                )
            except AccountError as ae:
                raise HTTPException(401, {"code": ae.code, "message": ae.message})
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_auth_me(self, user_id: str) -> dict[str, Any]:
        """user_id로 계정 정보 조회 (세션 복원용)."""
        try:
            from engine.storage import AccountRepo
            account = await asyncio.to_thread(AccountRepo.get_account, user_id)
            if not account:
                raise HTTPException(404, "account not found")
            return {"ok": True, "account": account}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── Schredl 일기 + 묘에 통합 ───────────────────────────
    async def post_diary_add(self, req: DiaryAddRequest) -> dict[str, Any]:
        """일기 저장. analyze=True면 dream 분석 결과도 함께 저장."""
        try:
            self._analytics["diary_add_calls"] += 1
            from engine.storage import UserRepo, DreamDiaryRepo
            from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, build_legal_footer

            # 0. 위기 검사
            crisis = detect_crisis(req.narrative_text)
            if crisis["crisis_detected"]:
                return {
                    "saved": False,
                    "crisis_alert": {
                        "severity": crisis["severity"],
                        "matched_count": len(crisis["matched_keywords"]),
                    },
                    "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                }

            # 사용자 존재 보장
            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)

            # 선택: 분석
            analysis_summary = None
            if req.analyze:
                from engine.divination.dream import analyze_dream
                from engine.divination.dream_lex.personal_context import (
                    build_context_from_dict,
                )
                user = await asyncio.to_thread(UserRepo.get, req.user_id)
                ctx = build_context_from_dict(user or {})
                analysis = await asyncio.to_thread(analyze_dream, req.narrative_text, ctx)
                # 요약만 저장 (전체 분석은 크니)
                analysis_summary = {
                    "artemidorus_class": (analysis.get("artemidorus_class") or {}).get("class"),
                    "wuxing_dominant": (analysis.get("wuxing") or {}).get("dominant_element"),
                    "folk_dominant": (analysis.get("korean_folk") or {}).get("dominant_category"),
                    "archetype_dominant": (analysis.get("archetypes") or {}).get("dominant_archetype"),
                    "bizarreness": (analysis.get("hobson") or {}).get("bizarreness_score"),
                    "cathartic_arc": (analysis.get("cathartic") or {}).get("arc_type"),
                    "hexagram": ((analysis.get("iching") or {}).get("hexagram") or {}).get("name"),
                }

            diary_id = await asyncio.to_thread(
                DreamDiaryRepo.add,
                req.user_id,
                narrative_text=req.narrative_text,
                recall_quality=req.recall_quality,
                vividness=req.vividness,
                valence=req.valence,
                lucidity=req.lucidity,
                wake_time_iso=req.wake_time_iso,
                sleep_duration_min=req.sleep_duration_min,
                core_image=req.core_image,
                felt_meaning=req.felt_meaning,
                spiritual_resonance=req.spiritual_resonance,
                next_intention=req.next_intention,
                analysis_summary=analysis_summary,
            )
            return {
                "saved": True,
                "diary_id": diary_id,
                "analysis_summary": analysis_summary,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_diary_list(self, req: UserScopedRequest) -> dict[str, Any]:
        """사용자 일기 목록 (최근 30일)."""
        try:
            from engine.storage import DreamDiaryRepo
            diaries = await asyncio.to_thread(DreamDiaryRepo.list_recent, req.user_id, 30, 60)
            return {"diaries": diaries, "count": len(diaries)}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── 임상 척도 영구 저장 ───────────────────────────
    async def post_learning_add(self, req: LearningLogRequest) -> dict[str, Any]:
        """학습/작업 로그 추가 — Stickgold dream lag 매칭용."""
        try:
            from engine.storage import UserRepo, LearningLogRepo
            await asyncio.to_thread(UserRepo.get_or_create, req.user_id)
            log_id = await asyncio.to_thread(
                LearningLogRepo.add,
                req.user_id, req.activity_text, req.domain, req.activity_at_iso,
            )
            return {"log_id": log_id}
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─────────────────────────── v2 오케스트레이터 ───────────────────────────
