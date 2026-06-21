"""웹 API 핸들러 — saju 도메인 (구조 리팩터링 2026-06-21).

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


class SajuHandlersMixin:
    """saju 도메인 핸들러 묶음 (Mixin)."""

    async def post_saju(self, req: SajuRequest) -> dict[str, Any]:
        """SajuCLI 기반 결정론적 사주 평가 (engine.saju). interpret=True 면 LLM 해설 첨부."""
        if req.mbti:
            self._analytics["mbti_counts"][req.mbti.upper()] = (
                self._analytics["mbti_counts"].get(req.mbti.upper(), 0) + 1
            )
        try:
            # time_unknown + time_hint 조합: 시간대 힌트로 시:분 보정 + time_unknown 해제
            dt_local = req.dt_local
            time_unknown = req.time_unknown
            if req.time_unknown and req.time_hint:
                hour = self._TIME_HINT_HOUR.get(req.time_hint.lower())
                if hour is not None and "T" in dt_local:
                    date_part = dt_local.split("T")[0]
                    dt_local = f"{date_part}T{hour:02d}:00"
                    time_unknown = False
            result = await asyncio.to_thread(
                self.saju_cli.assess,
                dt_local=dt_local,
                tz=req.tz,
                longitude=req.longitude,
                latitude=req.latitude,
                is_lunar=req.is_lunar,
                is_leap_month=req.is_leap_month,
                time_unknown=time_unknown,
                gender=req.gender,
            )
            # 추정 시각 메타에 기록 (프론트엔드 표시용)
            if req.time_unknown and req.time_hint:
                result.setdefault("meta", {})["time_hint"] = req.time_hint
                result["meta"]["estimated_hour"] = self._TIME_HINT_HOUR.get(
                    req.time_hint.lower()
                )

            # 성명학 분석 (이름 입력 시) — 보완도 계산 후 result 에 첨부
            myeong = None
            if req.name_ko:
                try:
                    from engine.saju.myeong import analyze_name

                    myeong = await asyncio.to_thread(
                        analyze_name,
                        req.name_ko,
                        result.get("wuxing_dist"),
                        req.name_han,
                    )
                    result["myeong"] = myeong
                except Exception as e:
                    result["myeong_error"] = str(e)

            # 융합 별칭 v2 (이름 수식어 추가)
            if myeong and req.mbti:
                try:
                    from engine.saju.alias import compute_fusion_alias_v2

                    result["fusion_alias"] = compute_fusion_alias_v2(
                        result, req.mbti, myeong
                    )
                except Exception as e:
                    result["fusion_alias_error"] = str(e)

            if req.interpret:
                try:
                    if req.mbti:
                        from engine.saju.explain import explain_fusion_with_critic

                        fusion = await asyncio.to_thread(
                            explain_fusion_with_critic,
                            result,
                            req.mbti,
                            None,
                            2,
                            myeong,
                            req.lang,
                        )
                        result["interpretation"] = fusion["text"]
                        result["interpretation_meta"] = {
                            "rounds": fusion["rounds"],
                            "critic_history": fusion["critic_history"],
                        }
                    else:
                        from engine.saju.explain import explain_saju

                        interpretation = await asyncio.to_thread(explain_saju, result)
                        result["interpretation"] = interpretation
                except Exception as e:
                    result["interpretation_error"] = str(e)
            return result
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_saju_explain(self, req: SajuExplainRequest) -> dict[str, Any]:
        """카드별 부분 해설 (pillar/wuxing/tengods/luck/shensha)."""
        try:
            from engine.saju.explain import explain_section

            text = await asyncio.to_thread(
                explain_section, req.section, req.saju, None, req.context
            )
            return {"section": req.section, "text": text}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_fusion(self, req: SajuFusionRequest) -> dict[str, Any]:
        """사주 + MBTI 융합 해설 + 결정론적 융합 별칭."""
        try:
            from engine.saju.alias import compute_fusion_alias
            from engine.saju.explain import explain_fusion

            alias = compute_fusion_alias(req.saju, req.mbti)
            text = await asyncio.to_thread(
                explain_fusion, req.saju, req.mbti, None, None, req.lang
            )
            return {"mbti": req.mbti.upper(), "text": text, "alias": alias}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_music(self, req: SajuMusicRequest) -> dict[str, Any]:
        """페르소나 사운드트랙 — 가사 에이전트 + MiniMax music-2.6."""
        self._analytics["music_calls"] += 1
        try:
            from engine.saju.music_gen import generate_music_with_critic

            ctx = {
                "persona": req.persona,
                "mbti": req.mbti,
                "strongest_wuxing": req.strongest_wuxing,
                "weakest_wuxing": req.weakest_wuxing,
                "day_master": req.day_master,
                "name_ko": req.name_ko,
                "grids": req.grids,
            }
            result = await asyncio.to_thread(
                generate_music_with_critic, ctx, max_rounds=2
            )
            self._analytics[
                "cache_music_hit" if result.get("cached") else "cache_music_miss"
            ] += 1
            self._analytics["minimax_last_ok"] = time.time() if not result.get("cached") else self._analytics["minimax_last_ok"]
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_compat_music(
        self, req: SajuCompatMusicRequest
    ) -> dict[str, Any]:
        """궁합 듀엣 사운드트랙 — 두 사람의 합/충/생/극을 한 곡에."""
        self._analytics["compat_music_calls"] += 1
        if req.grade:
            self._analytics["compat_grade_counts"][req.grade] = (
                self._analytics["compat_grade_counts"].get(req.grade, 0) + 1
            )
        try:
            from engine.saju.music_gen import generate_compat_music

            ctx = {
                "a_persona": req.a_persona,
                "b_persona": req.b_persona,
                "a_mbti": req.a_mbti,
                "b_mbti": req.b_mbti,
                "a_day_master": req.a_day_master,
                "b_day_master": req.b_day_master,
                "a_name_ko": req.a_name_ko,
                "b_name_ko": req.b_name_ko,
                "a_strongest_wuxing": req.a_strongest_wuxing,
                "b_strongest_wuxing": req.b_strongest_wuxing,
                "a_grids": req.a_grids,
                "b_grids": req.b_grids,
                "score": req.score,
                "grade": req.grade,
                "stem_rel": req.stem_rel,
                "branch_rel": req.branch_rel,
                "relation_mode": req.relation_mode,
            }
            result = await asyncio.to_thread(
                generate_compat_music, ctx, max_rounds=2
            )
            self._analytics[
                "cache_music_hit" if result.get("cached") else "cache_music_miss"
            ] += 1
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_image(self, req: SajuImageRequest) -> dict[str, Any]:
        """Nano Banana 일러스트 — 프롬프트 에이전트가 입력 데이터 보고 작성."""
        if req.kind == "compat":
            self._analytics["compat_image_calls"] += 1
        else:
            self._analytics["image_calls"] += 1
        try:
            from engine.saju.image_gen import generate_image, smart_prompt

            ctx: dict[str, Any] = {}
            if req.kind == "persona" and req.alias:
                ctx["persona"] = req.alias.get("persona") or req.alias.get("headline")
                ctx["mbti"] = req.alias.get("mbti")
                ctx["strongest_wuxing"] = req.alias.get("strongest")
                ctx["weakest_wuxing"] = req.alias.get("weakest")
                ctx["day_master"] = (req.saju or {}).get("day_master")
            elif req.kind == "pillar" and req.saju:
                ctx["year"] = req.saju.get("year")
                ctx["month"] = req.saju.get("month")
                ctx["day"] = req.saju.get("day")
                ctx["hour"] = req.saju.get("hour")
                ctx["day_master"] = req.saju.get("day_master")
            elif req.kind == "wuxing" and req.saju:
                wx = req.saju.get("wuxing_dist", {})
                ctx["wuxing_distribution"] = ", ".join(f"{k}={v}" for k, v in wx.items())
                ctx["strongest"] = max(wx, key=lambda k: wx[k]) if wx else None
                ctx["weakest"] = min(wx, key=lambda k: wx[k]) if wx else None
            elif req.kind == "luck" and req.saju:
                lc = req.saju.get("luck_cycle", [])
                ctx["luck_first"] = lc[0] if lc else None
                ctx["luck_last"] = lc[-1] if lc else None
                ctx["day_master"] = req.saju.get("day_master")
            elif req.kind == "compat":
                ctx["score"] = req.compat_score or 50
                ctx["grade"] = req.compat_grade or "중"
                a = req.compat_a or {}
                b = req.compat_b or {}
                if a.get("persona"):
                    ctx["a_persona"] = a.get("persona")
                if b.get("persona"):
                    ctx["b_persona"] = b.get("persona")
                if a.get("mbti"):
                    ctx["a_mbti"] = a.get("mbti")
                if b.get("mbti"):
                    ctx["b_mbti"] = b.get("mbti")
                _STEM_EN = {
                    "甲": "Wood (tall upright tree)",
                    "乙": "Vine-Wood (flexible grass)",
                    "丙": "Sun-Fire (radiant)",
                    "丁": "Candle-Fire (intimate warmth)",
                    "戊": "Mountain-Earth (grounded)",
                    "己": "Field-Earth (nurturing soil)",
                    "庚": "Metal (sharp steel)",
                    "辛": "Jewel-Metal (refined gem)",
                    "壬": "Ocean-Water (vast flow)",
                    "癸": "Mist-Water (soft dew)",
                }
                if a.get("day_master"):
                    ctx["a_day_master"] = a.get("day_master")
                    ctx["a_element_en"] = _STEM_EN.get(a.get("day_master"), "")
                if b.get("day_master"):
                    ctx["b_day_master"] = b.get("day_master")
                    ctx["b_element_en"] = _STEM_EN.get(b.get("day_master"), "")
                if a.get("name_ko"):
                    ctx["a_name_ko"] = a.get("name_ko")
                if b.get("name_ko"):
                    ctx["b_name_ko"] = b.get("name_ko")
                if a.get("gender"):
                    ctx["a_gender"] = a.get("gender")
                if b.get("gender"):
                    ctx["b_gender"] = b.get("gender")
                if req.compat_stem_rel:
                    ctx["stem_rel"] = req.compat_stem_rel
                if req.compat_branch_rel:
                    ctx["branch_rel"] = req.compat_branch_rel
            else:
                raise HTTPException(400, f"invalid kind or missing data: {req.kind}")

            from engine.saju.image_gen import generate_image_with_critic

            prompt = await asyncio.to_thread(smart_prompt, req.kind, ctx)
            result = await asyncio.to_thread(
                generate_image_with_critic, prompt, ctx, max_rounds=2
            )
            self._analytics[
                "cache_image_hit" if result.get("cached") else "cache_image_miss"
            ] += 1
            # critic 통계
            hist = result.get("critic_history") or []
            if hist:
                last = hist[-1]
                if last.get("total"):
                    self._analytics["image_critic_totals"].append(last["total"])
                    # 최근 100개만 유지
                    self._analytics["image_critic_totals"] = self._analytics["image_critic_totals"][-100:]
                self._analytics["image_critic_rounds"].append(len(hist))
                self._analytics["image_critic_rounds"] = self._analytics["image_critic_rounds"][-100:]
            return {"kind": req.kind, "prompt": prompt, **result}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_hanja_candidates(
        self, ko: str, weak: str = "", strong: str = ""
    ) -> dict[str, Any]:
        """한글 음 → 후보 한자 리스트 (음/획수/자원오행/뜻).

        weak: 사주의 약한 오행 (목/화/토/금/수). 해당 오행 한자에 `recommended=True` 부여.
        strong: 사주의 강한 오행. 해당 오행 한자에 `overload=True` 부여 (과한 보강 경고).
        """
        try:
            from engine.saju.hanja_data import candidates_by_ko

            cands = candidates_by_ko(ko)
            for c in cands:
                wx = c.get("wuxing") or c.get("자원오행") or ""
                if weak and wx == weak:
                    c["recommended"] = True
                if strong and wx == strong:
                    c["overload"] = True
            # 추천 한자를 앞으로 정렬
            cands.sort(
                key=lambda c: (not c.get("recommended"), c.get("overload", False))
            )
            return {"ko": ko, "candidates": cands}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_compat(self, req: SajuCompatRequest) -> dict[str, Any]:
        """두 사람 사주 + MBTI + 이름 → 궁합 분석."""
        try:
            from engine.saju.compat import analyze_compat
            from engine.saju.explain import explain_compat

            saju_a = await self._assess_person(req.a)
            saju_b = await self._assess_person(req.b)
            compat = analyze_compat(
                saju_a,
                saju_b,
                mbti_a=req.a.mbti,
                mbti_b=req.b.mbti,
                myeong_a=saju_a.get("myeong"),
                myeong_b=saju_b.get("myeong"),
            )
            interpretation = None
            if req.interpret:
                try:
                    interpretation = await asyncio.to_thread(
                        explain_compat, compat, None, req.relation_mode, req.lang
                    )
                except Exception as e:
                    interpretation = f"(궁합 해설 생성 실패: {e})"
            return {
                "a": {
                    "day_master": saju_a.get("day_master"),
                    "day": saju_a.get("day"),
                    "myeong": saju_a.get("myeong"),
                    "mbti": req.a.mbti,
                    "name_ko": req.a.name_ko,
                    "gender": req.a.gender,
                    "alias": saju_a.get("alias"),
                },
                "b": {
                    "day_master": saju_b.get("day_master"),
                    "day": saju_b.get("day"),
                    "myeong": saju_b.get("myeong"),
                    "mbti": req.b.mbti,
                    "name_ko": req.b.name_ko,
                    "gender": req.b.gender,
                    "alias": saju_b.get("alias"),
                },
                "compat": compat,
                "interpretation": interpretation,
                "relation_mode": req.relation_mode,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_compat_batch(
        self, req: SajuCompatBatchRequest
    ) -> dict[str, Any]:
        """한 명(a) vs 여러 명(others) — 점수만 비교 표로 반환."""
        try:
            from engine.saju.compat import analyze_compat

            saju_a = await self._assess_person(req.a)
            # 친구들 사주 계산을 병렬화 (gather)
            others = req.others[:10]

            async def _process(b):
                try:
                    saju_b = await self._assess_person(b)
                    c = analyze_compat(
                        saju_a, saju_b,
                        mbti_a=req.a.mbti, mbti_b=b.mbti,
                        myeong_a=saju_a.get("myeong"),
                        myeong_b=saju_b.get("myeong"),
                    )
                    return {
                        "name_ko": b.name_ko,
                        "mbti": b.mbti,
                        "day_master": saju_b.get("day_master"),
                        "score": c.get("score"),
                        "grade": c.get("grade"),
                    }
                except Exception as e:
                    return {"name_ko": b.name_ko, "error": str(e)}

            rows = list(await asyncio.gather(*(_process(b) for b in others)))
            rows.sort(key=lambda r: -(r.get("score") or 0))
            return {
                "a": {
                    "name_ko": req.a.name_ko,
                    "mbti": req.a.mbti,
                    "day_master": saju_a.get("day_master"),
                },
                "rows": rows,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_myeong(self, req: SajuMyeongRequest) -> dict[str, Any]:
        """성명학 결정론적 분석 — 음령오행 + 수리오격 + 사주 보완도."""
        try:
            from engine.saju.myeong import analyze_name

            return await asyncio.to_thread(
                analyze_name, req.name_ko, req.saju_wuxing, req.name_han
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_tarot(self, req: TarotRequest) -> dict[str, Any]:
        if self.engine is None:
            raise HTTPException(503, "tarot 모듈은 본 배포에서 비활성화됨")
        try:
            return await self.engine.cast_tarot_async(
                req.question, req.spread, req.seed
            )
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_iching(self, req: IChingRequest) -> dict[str, Any]:
        if self.engine is None:
            raise HTTPException(503, "iching 모듈은 본 배포에서 비활성화됨")
        try:
            return await self.engine.cast_iching_async(req.question, req.seed)
        except Exception as e:
            raise HTTPException(400, str(e))

    async def post_assess_all(self, req: AssessAllRequest) -> dict[str, Any]:
        """9 시스템 병렬 평가 — Engine.assess_all_async 직접 위임."""
        if self.engine is None:
            raise HTTPException(503, "assess_all 모듈은 본 배포에서 비활성화됨")
        try:
            saju_kwargs: dict[str, Any] | None = None
            if req.saju:
                saju_kwargs = {
                    "dt_local": datetime.fromisoformat(req.saju.dt_local),
                    "tz": req.saju.tz,
                    "longitude": req.saju.longitude,
                    "latitude": req.saju.latitude,
                    "is_lunar": req.saju.is_lunar,
                    "is_leap_month": req.saju.is_leap_month,
                    "time_unknown": req.saju.time_unknown,
                    "gender": req.saju.gender,
                }
            result = await self.engine.assess_all_async(
                nl_text=req.nl_text,
                saju_kwargs=saju_kwargs,
                oracle_question=req.oracle_question,
                oracle_seed=req.oracle_seed,
            )
            return result.to_dict()
        except Exception as e:
            raise HTTPException(400, str(e))

    async def get_profile(self, type_: str) -> dict[str, Any]:
        type_ = type_.upper()
        if type_ in self._MBTI_TYPES:
            try:
                from mbti.profiles.lookup import profile_for

                profile = await asyncio.to_thread(profile_for, type_)
                return profile.to_dict()
            except KeyError:
                pass
        raise HTTPException(404, f"unknown type: {type_}")

    async def get_saju_daily(self, day_master: str = "", date: str = "") -> dict[str, Any]:
        """오늘(또는 지정 날짜) 일진 + 본명 일간과의 십신 관계.

        Args:
            day_master: 본명 일간 한자 (甲~癸). 없으면 일진만 반환.
            date: YYYY-MM-DD (없으면 KST 오늘).

        일주 경계(자시) 회피를 위해 정오(12시) 기준으로 만세력 계산.
        """
        from datetime import datetime, timezone, timedelta
        from engine.saju.pillars import compute_pillars
        from engine.saju.ten_gods import ten_god

        kst = timezone(timedelta(hours=9))
        try:
            d = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now(kst)
        except Exception:
            d = datetime.now(kst)
        # 일주 경계 회피 위해 정오 12시
        pillars = compute_pillars(d.year, d.month, d.day, 12)
        dp = pillars["day_pillar"]
        result: dict[str, Any] = {
            "date": d.strftime("%Y-%m-%d"),
            "day_pillar": {
                "ganzhi_ko": f"{dp.get('gan','')}{dp.get('ji','')}",
                "ganzhi_han": f"{dp.get('gan_han','')}{dp.get('ji_han','')}",
                "gan_han": dp.get("gan_han"),
                "ji_han": dp.get("ji_han"),
            },
            "month_pillar": pillars["month_pillar"],
            "year_pillar": pillars["year_pillar"],
        }
        if day_master and day_master in "甲乙丙丁戊己庚辛壬癸":
            today_gan = dp.get("gan_han")
            relation = ten_god(day_master, today_gan) if today_gan else None
            result["relation"] = relation
            result["natal_day_master"] = day_master
            # 한 줄 톤 가이드
            tone_map = {
                "비견": "협력자·동지의 기운. 사람과 함께 움직이기 좋은 날.",
                "겁재": "경쟁·도전의 기운. 경계심 갖고 자기 입장을 지킬 것.",
                "식신": "베풂·창작의 기운. 표현·요리·여유 시간에 좋음.",
                "상관": "재능·반항의 기운. 새로운 시도가 빛나지만 규칙 충돌 주의.",
                "편재": "기회·확장의 기운. 외부 활동과 인맥에 좋음.",
                "정재": "안정·정착의 기운. 재산·관리·꼼꼼한 일에 좋음.",
                "편관": "압박·도전 과제. 결단력 필요한 날, 무리는 금물.",
                "정관": "질서·책임의 기운. 공식 일정·약속·계약에 좋음.",
                "편인": "직관·영감의 기운. 학습·명상·아이디어에 좋음.",
                "정인": "보호·인덕의 기운. 부모·스승·도움을 받는 날.",
            }
            result["tone"] = tone_map.get(relation, "")
        return result

    async def get_saju_daily_month(
        self, day_master: str = "", year: int = 0, month: int = 0
    ) -> dict[str, Any]:
        """한 달 일진 캘린더 — 본명 일간 기준 길흉 분류.

        길(吉) = 정관·정재·정인·식신, 평(平) = 비견·편재, 흉(凶) = 겁재·편관·상관·편인.
        """
        from datetime import datetime, timezone, timedelta
        from calendar import monthrange
        from engine.saju.pillars import compute_pillars
        from engine.saju.ten_gods import ten_god

        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        y = int(year) if year else now.year
        m = int(month) if month else now.month
        last_day = monthrange(y, m)[1]
        TONE = {
            "정관": "길", "정재": "길", "정인": "길", "식신": "길",
            "비견": "평", "편재": "평",
            "겁재": "흉", "편관": "흉", "상관": "흉", "편인": "흉",
        }
        days: list[dict[str, Any]] = []
        best_day = None
        worst_day = None
        for d in range(1, last_day + 1):
            try:
                pillars = compute_pillars(y, m, d, 12)
                gan = pillars["day_pillar"]["gan_han"]
                ji = pillars["day_pillar"]["ji_han"]
                rel = ten_god(day_master, gan) if day_master else None
                tone = TONE.get(rel, "평") if rel else "평"
                days.append({
                    "day": d,
                    "ganzhi": f"{gan}{ji}",
                    "relation": rel,
                    "tone": tone,
                })
                if rel == "정관" or rel == "정인":
                    if not best_day:
                        best_day = d
                if rel == "편관" or rel == "겁재":
                    if not worst_day:
                        worst_day = d
            except Exception:
                pass
        return {
            "year": y,
            "month": m,
            "day_master": day_master,
            "days": days,
            "best_day": best_day,
            "worst_day": worst_day,
        }

    async def post_saju_ask(self, req: SajuAskRequest) -> dict[str, Any]:
        """사주 페르소나에게 질문 — 사주 데이터를 컨텍스트로 LLM 대화. 세션당 10턴 제한."""
        from engine.saju.explain import MAX_CHAT_TURNS
        from engine.safety import detect_crisis, CRISIS_RESPONSE_KO, EMERGENCY_HOTLINES_KR, build_legal_footer

        # 0. 위기 신호 검사 — 자살/자해 키워드 즉시 차단
        crisis = detect_crisis(req.question or "")
        if crisis["crisis_detected"]:
            return {
                "answer": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
                "lang": req.lang,
                "turns_used": sum(1 for m in (req.history or []) if (m or {}).get("role") == "user") + 1,
                "turns_max": MAX_CHAT_TURNS,
                "crisis_alert": {
                    "severity": crisis["severity"],
                    "hotlines": EMERGENCY_HOTLINES_KR,
                    "matched_count": len(crisis["matched_keywords"]),
                },
                "legal_notice": None,
            }

        # 턴 수 체크 — 1턴 = user/assistant 한 쌍 (2 메시지)
        user_turns = sum(1 for m in (req.history or []) if (m or {}).get("role") == "user")
        if user_turns >= MAX_CHAT_TURNS:
            return {
                "answer": (
                    f"한 세션 최대 {MAX_CHAT_TURNS}개 질문까지 지원합니다. "
                    "새 분석을 시작하면 다시 대화할 수 있어요."
                ),
                "lang": req.lang,
                "limited": True,
            }
        try:
            from engine.llm_sync import call_llm_sync

            saju = req.saju
            day_master = saju.get("day_master")
            wx = saju.get("wuxing_dist") or {}
            strongest = max(wx, key=lambda k: wx.get(k, 0)) if wx else None
            weakest = min(wx, key=lambda k: wx.get(k, 0)) if wx else None
            alias = saju.get("alias") or {}
            ctx_lines = (
                f"[사용자 사주 컨텍스트]\n"
                f"  • 일간: {day_master}\n"
                f"  • 강한 오행: {strongest}, 약한 오행: {weakest}\n"
                f"  • 4기둥: {saju.get('year')} {saju.get('month')} {saju.get('day')} {saju.get('hour')}\n"
                f"  • 페르소나: {alias.get('persona', '')}\n"
            )
            lang_directive = {
                "en": "Answer in natural English.",
                "ja": "自然な日本語で回答してください。",
            }.get(req.lang, "한국어로 답변하세요.")
            system = (
                f"당신은 위 사주 데이터를 가진 사용자의 사주 페르소나 입장에서 답변하는 명리 상담사입니다.\n"
                f"엄격한 가드레일:\n"
                f"  • **단정적 예언 절대 금지**: '~가 좋다/나쁘다', '~할 것이다', '~이다' 같은 단언 X.\n"
                f"  • 대신 '~경향이 있다', '~을 점검해보면 좋다', '~흐름이 두드러진다' 같은 경향성 표현.\n"
                f"  • 점쟁이 톤 금지 (재물운/금전수/대박/대운 폭발 같은 자극 어휘 금지).\n"
                f"  • 의료/법률/투자 자문 거절 ('전문가 상담 권장').\n"
                f"  • 답변은 3~5문장, 통찰적·따뜻한 톤.\n"
                f"  • 사주는 한 가지 관점일 뿐이며 본인 판단이 최종임을 자연스럽게 환기.\n\n"
                f"{lang_directive}\n\n{ctx_lines}"
            )
            # 이전 대화 + 새 질문 (최근 6개만)
            messages_text = ""
            for m in (req.history or [])[-6:]:
                role = m.get("role", "user")
                content = m.get("content", "")
                messages_text += f"[{role}] {content}\n"
            messages_text += f"[user] {req.question}\n[assistant] "
            answer = await asyncio.to_thread(
                call_llm_sync, user_text=messages_text, system_prompt=system
            )
            return {
                "answer": (answer or "").strip(),
                "lang": req.lang,
                "turns_used": user_turns + 1,
                "turns_max": MAX_CHAT_TURNS,
                "crisis_alert": None,
                "legal_notice": build_legal_footer(),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_saju_webtoon(self, req: Request) -> dict[str, Any]:
        """정통 사주 풀이 텍스트로부터 nano-banana 웹툰 5장 생성."""
        try:
            body = await req.json()
            reading = (body or {}).get("reading", "").strip()
            if not reading or len(reading) < 50:
                raise HTTPException(400, "reading text required (min 50 chars)")
            from engine.divination.saju_webtoon import generate_webtoon_images
            images = await asyncio.to_thread(generate_webtoon_images, reading)
            return {"images": images, "count": len(images)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_iching_divine(
        self, req: IChingDivinationRequest
    ) -> dict[str, Any]:
        """주역 64괘 점단 — 꿈 본문에서 팔괘 추출 → 괘 도출 → 길흉·메시지."""
        try:
            from engine.divination.dream_lex.iching import divine_hexagram
            from engine.safety import build_legal_footer
            result = await asyncio.to_thread(divine_hexagram, req.dream_text)
            return {**result, "legal_notice": build_legal_footer()}
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_translate(self, req: TranslateRequest) -> dict[str, Any]:
        """가벼운 번역 — Bizrouter LLM 호출. 짧은 텍스트(가사·해설) 용."""
        try:
            from engine.llm_sync import call_llm_sync

            if not req.text or not req.text.strip():
                return {"translation": "", "target": req.target}
            tgt = req.target
            sys_map = {
                "en": "Translate the following Korean text to natural English. Keep section "
                      "tags like [Verse], [Chorus] as is. Output only the translation, no preamble.",
                "ja": "次の韓国語を自然な日本語に翻訳してください。[Verse]、[Chorus] などの "
                      "タグはそのまま残します。翻訳本文のみ出力。",
            }
            system = sys_map.get(tgt) or sys_map["en"]
            translation = await asyncio.to_thread(
                call_llm_sync, user_text=req.text[:3000], system_prompt=system
            )
            return {"translation": (translation or "").strip(), "target": tgt}
        except Exception as e:
            raise HTTPException(500, str(e))
