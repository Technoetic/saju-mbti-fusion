"""웹 API 핸들러 — ops 도메인 (구조 리팩터링 2026-06-21).

PersonalityAPIServer 가 본 Mixin 을 상속. self.engine·self.saju_cli·self._analytics 등
공유 상태는 최종 클래스에서 제공되므로 본 파일에서 정의하지 않는다.
원본 web/server.py 에서 메서드 블록을 물리적으로 분리 (동작 불변).
"""
from __future__ import annotations

import asyncio  # noqa: F401
import os  # noqa: F401
import time  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Any  # noqa: F401

from fastapi import HTTPException, Request  # noqa: F401
from fastapi.responses import StreamingResponse  # noqa: F401

import web.schemas as _schemas
from web.schemas import *  # noqa: F401,F403


class OpsHandlersMixin:
    """ops 도메인 핸들러 묶음 (Mixin)."""

    async def get_health(self) -> dict[str, Any]:
        # 외부 API 키 존재 점검 (실제 ping은 비용/지연 때문에 skip)
        ext = {
            "minimax_api_key_set": bool(os.environ.get("MINIMAX_API_KEY", "").strip()),
            "bizrouter_api_key_set": bool(os.environ.get("BIZROUTER_API_KEY", "").strip()),
            # BizRouter 장애 시 LLM 폴백 가능 여부 진단용.
            "anthropic_api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
            "rate_limit_per_min": self._rate_limit_per_min,
        }
        if self.engine is None:
            return {"status": "ok", "engine_config": {"mode": "saju-only"}, "external": ext}
        return {
            "status": "ok",
            "engine_config": {
                "parallel": self.engine.config.parallel,
                "enable_llm": self.engine.config.enable_llm,
            },
            "external": ext,
        }

    async def get_metrics(self) -> dict[str, Any]:
        m = self._metrics
        total = m["requests_total"] or 1
        samples = sorted(m["duration_samples"])

        def percentile(p: float) -> float:
            if not samples:
                return 0.0
            idx = min(len(samples) - 1, int(len(samples) * p))
            return samples[idx]

        return {
            "requests_total": m["requests_total"],
            "errors_total": m["errors_total"],
            "error_rate": m["errors_total"] / total,
            "avg_duration_ms": m["duration_sum_ms"] / total,
            "p50_ms": percentile(0.5),
            "p95_ms": percentile(0.95),
            "p99_ms": percentile(0.99),
            "sample_count": len(samples),
        }

    async def get_service_worker(self) -> Any:
        """Service Worker 응답 — 매 배포마다 캐시 무효화 위해 버전 자동 증가.

        SW_VERSION env var이 있으면 사용, 없으면 서버 시작 시각 기반 fallback.
        """
        from fastapi.responses import Response

        version = os.environ.get("SW_VERSION") or os.environ.get("RAILWAY_DEPLOYMENT_ID")
        if not version:
            # 서버 부팅 시각 한 번 (인스턴스 lifecycle 동안 고정)
            if not hasattr(self, "_sw_version"):
                self._sw_version = str(int(time.time()))
            version = self._sw_version
        # front/sw.js 우선, 없으면 web/sw.js fallback
        front_sw = Path(__file__).resolve().parent.parent / "front" / "sw.js"
        web_sw = Path(__file__).resolve().parent / "sw.js"
        sw_path = front_sw if front_sw.exists() else web_sw
        try:
            body = sw_path.read_text(encoding="utf-8")
        except Exception:
            body = ""
        # 캐시 이름의 v1 → 동적 버전
        body = body.replace("saju-app-shell-v1", f"saju-app-shell-{version}")
        return Response(
            content=body,
            media_type="text/javascript; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    async def post_llm_chat(self, req: LLMChatRequest) -> Any:
        """raw prompt → Bizrouter Gemini Flash Lite. 스트리밍 chunk text 응답.

        front 의 callFreeAI(prompt) 호환 — Pollinations 대체.
        """
        from fastapi.responses import StreamingResponse
        from engine.llm_sync import bizrouter_client

        client = bizrouter_client()
        system = req.system or (
            "당신은 따뜻하고 깊이 있는 사주·운명학 풀이 작가입니다. "
            "단정적 예언 금지, 경향성·자기이해 위주. 점쟁이 톤 금지. "
            "한국어로 자연스럽게 작성하세요."
        )
        # 요청에 model이 명시되면 우선 사용(클라이언트 모델 선택 허용), 없으면 env 기본.
        bizrouter_model = req.model or os.environ.get(
            "BIZROUTER_MODEL", "google/gemini-2.5-flash-lite"
        )

        if not req.stream:
            # 비스트리밍 — 단일 JSON 응답
            try:
                resp = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": req.prompt},
                    ],
                )
                content = resp.choices[0].message.content or ""
                return {"text": content}
            except Exception as e:
                raise HTTPException(500, str(e))

        # 스트리밍 — text/plain chunks (OpenAI SDK stream=True)
        async def _gen():
            try:
                stream = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=bizrouter_model,
                    max_tokens=req.max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": req.prompt},
                    ],
                    stream=True,
                )
                for chunk in stream:
                    try:
                        delta = chunk.choices[0].delta
                        piece = getattr(delta, "content", None) or ""
                        if piece:
                            yield piece
                    except Exception:
                        continue
            except Exception as e:
                yield f"\n\n[스트리밍 오류: {e}]"

        return StreamingResponse(_gen(), media_type="text/plain; charset=utf-8")

    async def get_ops_error_log(self, limit: int = 50, severity: str | None = None) -> dict[str, Any]:
        """최근 N개 에러 로그 (DB 영구). 관리용."""
        try:
            from engine.storage import ErrorLogRepo
            errors = await asyncio.to_thread(ErrorLogRepo.recent, limit, severity)
            return {"count": len(errors), "errors": errors}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_ops_crisis_stats(self, days: int = 30) -> dict[str, Any]:
        """최근 N일 위기 익명 통계. PRIVACY_POLICY §5 — 사용자 ID·텍스트 X."""
        try:
            from engine.storage import CrisisStatsRepo
            stats = await asyncio.to_thread(CrisisStatsRepo.summary, days)
            return stats
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_ops_backup(self) -> dict[str, Any]:
        """수동 DB 백업 트리거 (gzip → /data/backups/, 최근 7개 보관)."""
        try:
            from engine.storage import backup_db
            return await asyncio.to_thread(backup_db, max_keep=7)
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_legal_terms(self) -> dict[str, Any]:
        """이용약관 텍스트."""
        try:
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "docs" / "legal" / "TERMS_OF_SERVICE.md"
            return {"format": "markdown", "content": p.read_text(encoding="utf-8") if p.exists() else "(약관 파일 없음)"}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_legal_privacy(self) -> dict[str, Any]:
        """개인정보처리방침 텍스트."""
        try:
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "docs" / "legal" / "PRIVACY_POLICY.md"
            return {"format": "markdown", "content": p.read_text(encoding="utf-8") if p.exists() else "(방침 파일 없음)"}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_diag_kasi_verify(self, count: int = 100, start: str | None = None) -> dict[str, Any]:
        """KASI 음양력 API vs 본 시스템 day_pillar 정합 검증 (ADR-084).

        Args:
            count: 검증 일자 수 (기본 100, 최대 1000)
            start: 시작 일자 YYYY-MM-DD (기본 오늘부터 거꾸로)

        Returns:
            { kasi_called: bool, match: int, mismatch: int, skip: int, samples_mismatched: list }
            - 키 부재 시 kasi_called=False + match=N (graceful skip)
            - 키 등록 시 라이브 호출 + 통계 + 불일치 샘플 (개별 키 노출 X)
        """
        from datetime import date as _d, timedelta as _td, datetime as _dt
        from engine.saju.kasi_verifier import batch_verify, kasi_key_available

        count = max(1, min(int(count), 1000))
        if start:
            try:
                start_d = _dt.strptime(start, "%Y-%m-%d").date()
            except Exception:
                start_d = _d.today()
        else:
            start_d = _d.today()

        targets = [start_d - _td(days=i) for i in range(count)]
        match_n, mismatch_n, skip_n, results = batch_verify(targets)

        mismatched_samples = [
            {
                "date": str(r.target_date),
                "local": r.local_iljin_han,
                "kasi": r.kasi_iljin_han,
            }
            for r in results if r.kasi_called and not r.match
        ][:10]

        return {
            "kasi_key_available": kasi_key_available(),
            "kasi_called": any(r.kasi_called for r in results),
            "count_requested": count,
            "count_called": sum(1 for r in results if r.kasi_called),
            "match": match_n,
            "mismatch": mismatch_n,
            "skip": skip_n,
            "samples_mismatched": mismatched_samples,
            "match_rate_pct": round(100 * match_n / max(1, match_n + mismatch_n), 2) if (match_n + mismatch_n) else None,
        }

    async def post_error_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        """클라이언트 에러 로그 수집 — in-memory 50개 + DB 영구."""
        try:
            err = {
                "msg": str(payload.get("msg", ""))[:300],
                "stack": str(payload.get("stack", ""))[:600],
                "url": str(payload.get("url", ""))[:200],
                "ua": str(payload.get("ua", ""))[:200],
                "at": time.time(),
            }
            self._analytics["client_errors"].append(err)
            self._analytics["client_errors"] = self._analytics["client_errors"][-50:]
            # DB 영구화
            try:
                from engine.storage import ErrorLogRepo
                await asyncio.to_thread(
                    ErrorLogRepo.add,
                    err["msg"], "client",
                    stack=err.get("stack"),
                    url=err.get("url"),
                    user_agent=err.get("ua"),
                    user_id=payload.get("user_id"),
                    severity=payload.get("severity", "error"),
                )
            except Exception:
                pass
        except Exception:
            pass
        return {"ok": True}

    async def get_analytics(self) -> dict[str, Any]:
        """가벼운 in-memory 카운터 — 어떤 MBTI/등급이 인기인지 + 비용 추정."""
        a = self._analytics
        m_total = a["cache_music_hit"] + a["cache_music_miss"]
        i_total = a["cache_image_hit"] + a["cache_image_miss"]
        critic_totals = a["image_critic_totals"]
        critic_rounds = a["image_critic_rounds"]
        # 비용 추정 (USD) — 캐시 hit는 비용 0
        # MiniMax music-2.6-free: 무료 / Bizrouter Gemini Flash Lite: ~$0.001/호출 / Nano Banana: ~$0.04/이미지
        est_cost = round(
            (a["cache_music_miss"] + a["cache_image_miss"]) * 0.001  # LLM 평균
            + a["cache_image_miss"] * 0.04  # Nano Banana 이미지
            + a["cache_music_miss"] * 0.0  # MiniMax free
            , 4)
        return {
            "mbti_top": sorted(a["mbti_counts"].items(), key=lambda x: -x[1])[:10],
            "compat_grade_top": sorted(
                a["compat_grade_counts"].items(), key=lambda x: -x[1]
            ),
            "music_calls": a["music_calls"],
            "image_calls": a["image_calls"],
            "compat_music_calls": a["compat_music_calls"],
            "compat_image_calls": a["compat_image_calls"],
            "cache_music_hit_rate": (a["cache_music_hit"] / m_total) if m_total else 0,
            "cache_image_hit_rate": (a["cache_image_hit"] / i_total) if i_total else 0,
            "image_critic_avg_total": (sum(critic_totals) / len(critic_totals)) if critic_totals else None,
            "image_critic_avg_rounds": (sum(critic_rounds) / len(critic_rounds)) if critic_rounds else None,
            "estimated_cost_usd": est_cost,
            "rate_limited_ips": len(self._rate_window),
            "client_errors_count": len(a["client_errors"]),
            "client_errors_recent": a["client_errors"][-5:],
            # v2 오케스트레이션 통계
            "dream_v2_calls": a.get("dream_v2_calls", 0),
            "dream_v2_crisis_blocked": a.get("dream_v2_crisis_blocked", 0),
            "dream_v2_cathartic_counts": a.get("dream_v2_cathartic_counts", 0),
            "dream_v2_persona_top": sorted(
                (a.get("dream_v2_persona_counts") or {}).items(), key=lambda x: -x[1]
            )[:10],
            "dream_v2_avg_elapsed_ms": (
                sum(a.get("dream_v2_elapsed_ms_samples") or [0]) /
                max(1, len(a.get("dream_v2_elapsed_ms_samples") or [1]))
            ),
            "clinical_log_calls": a.get("clinical_log_calls", 0),
            "diary_add_calls": a.get("diary_add_calls", 0),
            "irt_rescript_calls": a.get("irt_rescript_calls", 0),
        }


# === ASGI 앱 인스턴스 (uvicorn 진입점) ===
