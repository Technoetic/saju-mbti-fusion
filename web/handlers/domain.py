"""웹 API 핸들러 — domain 도메인 (구조 리팩터링 2026-06-21).

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


class DomainHandlersMixin:
    """domain 도메인 핸들러 묶음 (Mixin)."""

    async def post_hwapae_reading(
        self, req: HwapaeReadingRequest
    ) -> dict[str, Any]:
        """화선 낭자 화패 풀이 — critic 루프 + 캐시 적용 백엔드 에이전트."""
        try:
            from engine.divination.hwapae.core import generate_hwapae_reading

            cards = [c.model_dump() for c in req.cards]
            result = await asyncio.to_thread(
                generate_hwapae_reading,
                req.question,
                cards,
                req.category,
                req.menu_label,
            )
            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_star_reading(
        self, req: StarReadingRequest
    ) -> dict[str, Any]:
        """성하 공자 별빛 풀이 — 12 황도대 결정론 일일 톤 (ADR-068).

        결정론 점성술 점수 산출만, LLM 호출 X (cost·latency 최소화).
        풀이 텍스트는 /api/llm/chat과 결합하거나 클라이언트가 결정.
        """
        try:
            from datetime import date as _date
            from engine.divination.star.scoring import compute_daily_star_reading
            from engine.safety import build_legal_footer, build_ai_generation_meta

            birth = _date.fromisoformat(req.birth)
            target = _date.fromisoformat(req.target_date) if req.target_date else _date.today()
            reading = compute_daily_star_reading(birth, target)

            return {
                "sign_key": reading.sign_key,
                "sign_label_ko": reading.sign_label_ko,
                "sign_symbol": reading.sign_symbol,
                "element_ko": reading.element_ko,
                "modality_ko": reading.modality_ko,
                "ruling_planet": reading.ruling_planet,
                "daily_tone_ko": reading.daily_tone_ko,
                "target_date": reading.target_date,
                "disclaimer": reading.disclaimer,
                "legal_notice": build_legal_footer(),
                "ai_generation": build_ai_generation_meta(model_label="deterministic-engine"),
            }
        except ValueError as ve:
            raise HTTPException(400, f"날짜 형식 오류 (YYYY-MM-DD 필요): {ve}")
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_content_reading(
        self, req: ContentReadingRequest
    ) -> dict[str, Any]:
        """메뉴 콘텐츠 풀이 — 도메인 결정론 엔진 + LLM 결합 (ADR-069).

        char_key 'saju' + content_key 'today' 일 때:
          1. engine/saju/pillars.day_pillar() — 사용자 일진 + 오늘 일진
          2. engine/saju/ten_gods.compute_ten_gods() — 십성 관계
          3. 결정론 결과 → 시스템 프롬프트 주입
          4. BizRouter Gemini Flash Lite 작문
        """
        from datetime import date as _date
        from engine.safety import build_legal_footer, build_ai_generation_meta

        fields = req.fields or {}
        char_key = req.char_key
        content_key = req.content_key

        # ADR-071: 도메인 결정론 결과 누적 (saju + name 동시 호출 가능)
        # 사용자가 fullName + birth 모두 입력 시 사주 + 성명학 결정론 동시 인용.
        # char_key 캐릭터 단독 도메인 외에도 fields 입력 기준 누적 적용.
        deterministic_blocks: list[str] = []

        # ─── saju 결정론 (char_key='saju' + birth 입력) ───
        # ADR-069·070 후속 fix: birth 입력 받는 모든 콘텐츠에서 사주 일주 융합.
        # 이전: today/tomorrow 5개 content_key만 융합 → who-likes·heart·image·fate-one·
        #       future-fate·life-card 등 birth 받는 콘텐츠가 사주 결정론 미호출 (UI/백엔드 불일치).
        # 본 fix: birth만 입력되면 모든 char_key·content_key에서 사주 융합.
        birth_str = (fields.get("birth") or "").strip()
        wants_saju = (char_key == "saju") or (
            birth_str and char_key in ("name", "face", "palm", "dream", "hwapae", "star")
        )
        if char_key == "saju" or (wants_saju and birth_str):
            if birth_str:
                try:
                    from engine.saju.pillars import day_pillar
                    from engine.saju.ten_gods import (
                        compute_ten_gods,
                        classify_gilhyung,
                        detect_special_combinations,
                    )
                    # ADR-089: 신살 결정론 (사전학습 환각 차단 — 도화살·역마살 등 명시 산출만 인용)
                    from engine.saju.pillars import compute_pillars
                    from engine.saju.shensha import compute_shensha, SHENSHA_MEANINGS

                    birth_dt = _date.fromisoformat(birth_str)
                    today_dt = _date.today()
                    user_day_pillar = day_pillar(birth_dt.year, birth_dt.month, birth_dt.day)
                    today_pillar_data = day_pillar(today_dt.year, today_dt.month, today_dt.day)

                    # ADR-072: compute_ten_gods는 {"day":"甲子","hour":"丁卯"} 문자열 형식 받음
                    # 사용자 일간 ↔ 오늘 천간·지지 십성 산출
                    user_gz = f"{user_day_pillar.get('gan_han','')}{user_day_pillar.get('ji_han','')}"
                    today_gz = f"{today_pillar_data.get('gan_han','')}{today_pillar_data.get('ji_han','')}"
                    today_tengod_gan = ""
                    today_tengod_ji = ""
                    ten_gods_data: dict = {}
                    try:
                        if len(user_gz) >= 2 and len(today_gz) >= 2:
                            ten_gods_data = compute_ten_gods({
                                "year": user_gz, "month": user_gz, "day": user_gz, "hour": today_gz,
                            })
                            today_tengod_gan = ten_gods_data.get("hour_gan", "")
                            today_tengod_ji = ten_gods_data.get("hour_ji", "")
                    except Exception:
                        pass

                    tengod_label = (
                        f"천간 {today_tengod_gan}·지지 {today_tengod_ji}"
                        if today_tengod_gan or today_tengod_ji
                        else "(미산출)"
                    )

                    # ADR-086: 십성 메타 분류 — 사길신·사흉신 라벨 + 특수 조합
                    gan_class = classify_gilhyung(today_tengod_gan) if today_tengod_gan else None
                    ji_class = classify_gilhyung(today_tengod_ji) if today_tengod_ji else None
                    meta_label_parts = []
                    if gan_class:
                        meta_label_parts.append(f"천간 {today_tengod_gan}={gan_class}")
                    if ji_class:
                        meta_label_parts.append(f"지지 {today_tengod_ji}={ji_class}")
                    meta_label = " · ".join(meta_label_parts) if meta_label_parts else "(중립)"

                    special_combos = detect_special_combinations(ten_gods_data) if ten_gods_data else []
                    combos_label = ", ".join(special_combos) if special_combos else "(없음)"

                    # ADR-089: 신살 결정론 산출 (사용자 4기둥 + 시각 미입력 시 정오 추정)
                    shensha_result: dict = {}
                    shensha_lines: list[str] = []
                    try:
                        full_pillars = compute_pillars(birth_dt.year, birth_dt.month, birth_dt.day, 12)
                        shensha_result = compute_shensha(full_pillars)
                        for key in ("cheoneul", "munchang", "yeokma", "dohwa", "kongmang"):
                            meta = SHENSHA_MEANINGS.get(key, {})
                            label = meta.get("label", key)
                            values = shensha_result.get(key, [])
                            if values:
                                shensha_lines.append(f"{label}: {'·'.join(values)}")
                            else:
                                shensha_lines.append(f"{label}: (없음)")
                    except Exception:
                        shensha_lines = ["(신살 산출 실패)"]
                    shensha_label = " / ".join(shensha_lines)

                    deterministic_blocks.append(
                        f"[사주 결정론 — engine/saju 출력]\n"
                        f"  · 사용자 일주(日柱): {user_day_pillar.get('gan','')}{user_day_pillar.get('ji','')} "
                        f"({user_day_pillar.get('gan_han','')}{user_day_pillar.get('ji_han','')})\n"
                        f"  · 사용자 일간(日干, 본명 중심): {user_day_pillar.get('gan','')}\n"
                        f"  · 오늘 일진(今日 日辰): {today_pillar_data.get('gan','')}{today_pillar_data.get('ji','')} "
                        f"({today_pillar_data.get('gan_han','')}{today_pillar_data.get('ji_han','')})\n"
                        f"  · 일간↔오늘 십성: {tengod_label}\n"
                        f"  · 십성 메타 분류 (ADR-086): {meta_label}\n"
                        f"  · 특수 구조 조합: {combos_label}\n"
                        f"  · 신살 결정론 (ADR-089): {shensha_label}\n"
                        f"  · [지시 1] 위 메타는 명리학 통설 구조 라벨이며 길흉 단정 X (ADR-006).\n"
                        f"  · [지시 2] 신살 (천을귀인·문창귀인·역마살·도화살·공망)은 위 산출 결과에서 '(없음)' 명시된 경우 절대 언급 X. 사전학습 사주 지식 추가 금지 (ADR-010)."
                    )
                except (ValueError, ImportError, Exception):
                    deterministic_blocks.append("[사주 결정론 — 산출 실패]")

        # ─── name 결정론 (char_key='name' OR fullName/hanja 입력 시 누적) ───
        # ADR-070·071: 성명학 결정론 융합 — fullName/hanja 입력 시 모든 도메인에서 동시 인용.
        # 본 fix 이전: name·saju 2 도메인만 융합. hwapae·dream·face·palm·star는 share='name'
        # UI 입력을 받았지만 LLM 프롬프트에 성명학 결정론 결과 미주입 (UI/백엔드 불일치).
        # 본 fix: 사용자가 이름 입력한 모든 캐릭터에서 성명학 결정론 결과 자동 융합.
        full_name = (fields.get("fullName") or fields.get("currentName") or "").strip()
        hanja = (fields.get("hanja") or "").strip()
        wants_name = (char_key == "name") or (
            (full_name or hanja) and char_key in ("saju", "hwapae", "dream", "face", "palm", "star")
        )
        if wants_name and (full_name or hanja):
            try:
                from engine.divination.name.baleum import evaluate_baleum
                from engine.divination.name.scoring import score_name

                lines: list[str] = ["[성명학 결정론 — engine/divination/name 출력]"]

                if full_name:
                    try:
                        # ADR-072: BaleumReport 실 필드 = syllables·ohaeng_sequence·relations·grade·reason
                        # 이전 ADR-070 'score' 가짜 속성 fallback 0.00 LLM 주입 결손 정정
                        baleum_report = evaluate_baleum(full_name, include_jongsung=False)
                        ohaeng_seq = "·".join(getattr(baleum_report, "ohaeng_sequence", []) or [])
                        grade = getattr(baleum_report, "grade", "")
                        reason = getattr(baleum_report, "reason", "")
                        lines.append(
                            f"  · 발음 분석 (한글): {full_name}\n"
                            f"  · 음절 오행 흐름: {ohaeng_seq or '(미산출)'}\n"
                            f"  · 음 조화 등급: {grade or '(미산출)'}\n"
                            f"  · 평가 사유: {reason or '(미산출)'}\n"
                            f"  · 음 결합 결정론: 본 시스템 ADR-028 Priority 1·2 검증"
                        )
                    except Exception:
                        lines.append(f"  · 한글 이름: {full_name} (발음 분석 미산출)")

                if hanja:
                    try:
                        name_score = score_name(hanja)
                        if name_score:
                            strokes = name_score.get("strokes", {})
                            four = name_score.get("four_gyeok", {})
                            bulyong = name_score.get("bulyong", {})
                            lines.append(
                                f"  · 한자 표기: {hanja}\n"
                                f"  · 획수 (강희자전): {strokes.get('kangxi', [])}\n"
                                f"  · 4격 (원·형·이·정): {four.get('won','')}·{four.get('hyeong','')}·{four.get('i','')}·{four.get('jeong','')}\n"
                                f"  · 4격 길흉: {'모두 길격' if four.get('all_good') else '일부 흉격 또는 부분 길격'}\n"
                                f"  · 불용한자 여부: {'있음' if bulyong.get('has_bulyong') else '없음'}"
                            )
                    except Exception:
                        lines.append(f"  · 한자: {hanja} (4격·획수 산출 실패)")

                deterministic_blocks.append("\n".join(lines))
            except Exception:
                deterministic_blocks.append("[성명학 결정론 — 산출 실패]")

        # ─── ADR-135 today-hanja (오늘의 한자) ───
        if char_key == "name" and content_key == "today-hanja":
            try:
                from engine.divination.name.daily_hanja import get_daily_hanja
                r135 = get_daily_hanja()
                if r135:
                    deterministic_blocks.append(
                        f"[ADR-135 오늘의 한자 결정론]\n"
                        f"  · 날짜: {r135.date_iso} (시드: {r135.seed_int})\n"
                        f"  · 오늘의 한자: {r135.char} ({r135.hangul})\n"
                        f"  · 강희자전 획수: {r135.kangxi_strokes}\n"
                        f"  · 자원오행: {r135.resource_ohaeng or '(매핑 부재)'}\n"
                        f"  · KCI 학파 출처: {r135.kci_school_source or '(부재)'}\n"
                        f"  · 본의: {r135.kci_reason or '(부재)'}"
                    )
            except Exception:
                pass

        # ─── ADR-136 biz (상호 작명) ───
        if char_key == "name" and content_key == "biz":
            try:
                from engine.divination.name.biz_naming import compute_biz_naming
                biz_type = (fields.get("bizType") or "").strip()
                concept = (fields.get("concept") or "").strip()
                if biz_type:
                    r136 = compute_biz_naming(biz_type, concept=concept)
                    hanja_samples = ", ".join(
                        f"{h['char']}({h['hangul']})" for h in r136.recommended_hanja[:8]
                    )
                    deterministic_blocks.append(
                        f"[ADR-136 상호 작명 결정론]\n"
                        f"  · 업종: {r136.biz_type} / 컨셉: {r136.concept or '(미입력)'}\n"
                        f"  · 1차 추천 오행: {', '.join(r136.target_ohaeng_primary)}\n"
                        f"  · 2차 보조 오행: {r136.target_ohaeng_secondary or '(없음)'}\n"
                        f"  · 추천 한자 풀 ({len(r136.recommended_hanja)}자): {hanja_samples}\n"
                        f"  · 학파: {r136.school_source[:80]}"
                    )
            except Exception:
                pass

        # ─── ADR-137 pen (예명 작명) ───
        if char_key == "name" and content_key == "pen":
            try:
                from engine.divination.name.pen_naming import compute_pen_naming
                field_code = (fields.get("field") or "other").strip()
                r137 = compute_pen_naming(field_code)
                hanja_samples = ", ".join(
                    f"{h['char']}({h['hangul']})" for h in r137.recommended_hanja[:8]
                )
                deterministic_blocks.append(
                    f"[ADR-137 예명 작명 결정론]\n"
                    f"  · 활동 분야: {r137.field_label_ko}\n"
                    f"  · 추천 오행: {', '.join(r137.target_ohaeng)}\n"
                    f"  · 학파 근거: {r137.rationale}\n"
                    f"  · 추천 한자 풀 ({len(r137.recommended_hanja)}자): {hanja_samples}"
                )
            except Exception:
                pass

        # ─── ADR-138 newborn (신생아 작명) ───
        if char_key == "name" and content_key == "newborn":
            try:
                from engine.divination.name.newborn import compute_newborn_naming
                surname = (fields.get("surname") or "").strip()
                baby_birth = (fields.get("babyBirth") or "").strip()
                baby_hour = (fields.get("babyHour") or "").strip() or None
                baby_gender = (fields.get("babyGender") or "").strip() or None
                parent_wish = (fields.get("parentWish") or "").strip()
                if surname and baby_birth:
                    r138 = compute_newborn_naming(
                        surname=surname,
                        baby_birth_iso=baby_birth,
                        baby_hour_branch=baby_hour,
                        baby_gender=baby_gender,
                        parent_wish=parent_wish,
                    )
                    if r138:
                        hanja_samples = ", ".join(
                            f"{h['char']}({h['hangul']})" for h in r138.recommended_hanja[:8]
                        )
                        deterministic_blocks.append(
                            f"[ADR-138 신생아 작명 결정론]\n"
                            f"  · 성: {r138.surname} / 출생: {r138.baby_birth_iso} {r138.baby_hour or '(시각 미입력)'}\n"
                            f"  · {r138.saju_summary}\n"
                            f"  · 사주 추천 오행: {', '.join(r138.saju_recommended_ohaeng) or '(균형 양호)'}\n"
                            f"  · 추천 한자 풀 ({len(r138.recommended_hanja)}자): {hanja_samples}\n"
                            f"  · 부모 바람: {r138.parent_wish or '(미입력)'}"
                        )
            except Exception:
                pass

        # ─── ADR-139 rename (개명 추천) ───
        if char_key == "name" and content_key == "rename":
            try:
                from engine.divination.name.rename import compute_rename
                current = (fields.get("currentName") or "").strip()
                birth_iso = (fields.get("birth") or "").strip()
                hour_b = (fields.get("hourBranch") or "").strip() or None
                gender = (fields.get("gender") or "").strip() or None
                reason = (fields.get("reason") or "").strip()
                if current and birth_iso:
                    r139 = compute_rename(
                        current_name=current,
                        birth_iso=birth_iso,
                        hour_branch=hour_b,
                        gender=gender,
                        user_reason=reason,
                    )
                    if r139:
                        hanja_samples = ", ".join(
                            f"{h['char']}({h['hangul']})" for h in r139.recommended_hanja[:8]
                        )
                        deterministic_blocks.append(
                            f"[ADR-139 개명 진단 결정론]\n"
                            f"  · 현재 이름: {r139.current_name}\n"
                            f"  · 오행 충돌 진단: {r139.conflict_detail}\n"
                            f"  · 발음오행 등급: {r139.baleum_grade or '(미산출)'}\n"
                            f"  · 사주 추천 오행: {', '.join(r139.saju_recommended_ohaeng) or '(균형 양호)'}\n"
                            f"  · 추천 한자 풀 ({len(r139.recommended_hanja)}자): {hanja_samples}\n"
                            f"  · 사용자 이유: {r139.user_reason or '(미입력)'}"
                        )
            except Exception:
                pass

        # ─── palm 결정론 (ADR-074·081, char_key='palm') ───
        # ADR-081: imageB64 입력 시 Phase 2 → generate_palm_reading Vision 호출
        # ADR-074: 사진 미입력 시 학파/라벨 풀 메타만 LLM 인용
        wants_palm = char_key == "palm"
        palm_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()
        if wants_palm:
            try:
                from engine.divination.palm.knowledge import (
                    PALM_SCHOOLS,
                    FATE_LINE_STRAIGHT, FATE_LINE_CURVED,
                    SUN_LINE_CLEAR, SUN_LINE_FAINT,
                    MERCURY_LINE_CONTINUOUS, MERCURY_LINE_FRAGMENTED,
                    MARRIAGE_LINE_SINGLE_CLEAR, MARRIAGE_LINE_MULTIPLE, MARRIAGE_LINE_FORKED,
                )
                schools_meta = " · ".join(
                    f"{s.name_short}({s.tradition},{s.publication_year})"
                    for s in PALM_SCHOOLS
                )
                if palm_image_b64:
                    # ADR-081 Phase 2: Vision 풀 호출
                    deterministic_blocks.append(
                        "[손금 결정론 Phase 2 — engine/divination/palm/reading.generate_palm_reading]\n"
                        f"  · 학파 6개: {schools_meta}\n"
                        f"  · 사진 입력 감지 (base64 길이: {len(palm_image_b64)})\n"
                        f"  · Vision 풀 호출은 별도 엔드포인트 (/api/palm/read) 사용 권장.\n"
                        f"  · 본 분기는 학파 + 라벨 풀 인용으로 LLM 작문 유도.\n"
                        f"  · 운명선·태양선·수성선·결혼선 4 보조선 결정론 라벨 적용 시 사용자에게 사진 업로드 가이드."
                    )
                else:
                    deterministic_blocks.append(
                        "[손금 결정론 — engine/divination/palm 학파·라벨 풀]\n"
                        f"  · 학파 6개: {schools_meta}\n"
                        f"  · 운명선 라벨: {FATE_LINE_STRAIGHT} | {FATE_LINE_CURVED}\n"
                        f"  · 태양선 라벨: {SUN_LINE_CLEAR} | {SUN_LINE_FAINT}\n"
                        f"  · 수성선 라벨: {MERCURY_LINE_CONTINUOUS} | {MERCURY_LINE_FRAGMENTED}\n"
                        f"  · 결혼선 라벨: {MARRIAGE_LINE_SINGLE_CLEAR} | {MARRIAGE_LINE_MULTIPLE} | {MARRIAGE_LINE_FORKED}\n"
                        f"  · 사진 미입력 시 라이브 분류 불가. 라벨 풀 인용만 허용."
                    )
            except Exception:
                deterministic_blocks.append("[손금 결정론 — 산출 실패]")

        # ─── ADR-118 토정비결 (palm/tojeong content_key + birth) ───
        if char_key == "palm" and content_key == "tojeong" and birth_str:
            try:
                from datetime import datetime as _dt_tj, date as _date_tj
                from engine.divination.tojeong import compute_tojeong_for_year, format_hexagram_for_prompt
                birth_d = _dt_tj.strptime(birth_str, "%Y-%m-%d").date()
                target_year = _date_tj.today().year
                hex_r = compute_tojeong_for_year(birth_d, target_year)
                if hex_r:
                    deterministic_blocks.append(format_hexagram_for_prompt(hex_r, target_year))
            except Exception:
                pass

        # ─── ADR-119 12지 띠 운세 (palm/zodiac content_key + birth) ───
        if char_key == "palm" and content_key == "zodiac" and birth_str:
            try:
                from datetime import datetime as _dt_zo, date as _date_zo
                from engine.divination.zodiac_ko import (
                    animal_by_year, compute_year_fortune, format_animal_for_prompt,
                )
                birth_d = _dt_zo.strptime(birth_str, "%Y-%m-%d").date()
                my_animal = animal_by_year(birth_d.year)
                target_year = _date_zo.today().year
                year_compat = compute_year_fortune(birth_d.year, target_year)
                deterministic_blocks.append(
                    format_animal_for_prompt(my_animal, target_year, year_compat)
                )
            except Exception:
                pass

        # ─── ADR-120 산통점 (palm/spirit content_key + 산가지 입력) ───
        # 사용자가 3 산가지 값 (stick1·stick2·stick3) 입력 시 결정론 산출
        if char_key == "palm" and content_key == "spirit":
            try:
                from engine.divination.santong import compute_santong_reading, format_santong_for_prompt
                # fields에서 stick1·stick2·stick3 또는 무작위 fallback
                s1 = int((fields.get("stick1") or "3").strip() or "3")
                s2 = int((fields.get("stick2") or "5").strip() or "5")
                s3 = int((fields.get("stick3") or "7").strip() or "7")
                santong_r = compute_santong_reading(s1, s2, s3)
                if santong_r:
                    deterministic_blocks.append(format_santong_for_prompt(santong_r))
            except Exception:
                pass

        # ─── ADR-121 부적 4 표준 (palm/talisman content_key + talismanType) ───
        if char_key == "palm" and content_key == "talisman":
            try:
                from engine.divination.talisman import compute_talisman_reading, format_talisman_for_prompt
                talisman_type = (fields.get("talismanType") or fields.get("type") or "hapgyeok").strip()
                talisman_r = compute_talisman_reading(talisman_type)
                if talisman_r:
                    deterministic_blocks.append(format_talisman_for_prompt(talisman_r))
            except Exception:
                pass

        # ─── ADR-158 야선 아씨 4 컨텐츠 (char_key='ya') ───
        # 속궁합·욕망·운우지정·정인 사주 결정론 + sanitize 4중 안전망.
        # ADR-006 자문 거절 정신: 결혼·이혼·외도·배우자 외모 단정 차단.
        if char_key == "ya" and content_key in ("sok-gunghap", "desire-saju", "unu-jijeong", "jeongin-saju"):
            try:
                from datetime import datetime as _dt_ya
                from engine.saju.pillars import compute_pillars as _compute_pillars_ya
                birth_str_ya = (fields.get("birth") or "").strip()
                partner_birth_str_ya = (fields.get("partnerBirth") or "").strip()

                def _ya_day_pillar(s: str) -> tuple[str, str, str, tuple[str, ...]]:
                    """birth_str → (day_gan, day_ji, day_pillar_2자, 4지지 튜플)."""
                    d = _dt_ya.strptime(s, "%Y-%m-%d").date()
                    p = _compute_pillars_ya(d.year, d.month, d.day, 12)
                    dg, dj = p["day_pillar"]["gan_han"], p["day_pillar"]["ji_han"]
                    branches = (
                        p["year_pillar"]["ji_han"],
                        p["month_pillar"]["ji_han"],
                        dj,
                        p["hour_pillar"]["ji_han"],
                    )
                    return dg, dj, dg + dj, branches

                if content_key == "sok-gunghap" and birth_str_ya and partner_birth_str_ya:
                    from engine.divination.sok_gunghap import (
                        compute_sok_gunghap, format_sok_gunghap_for_prompt,
                    )
                    _, _, self_dp, self_brs = _ya_day_pillar(birth_str_ya)
                    _, _, prt_dp, prt_brs = _ya_day_pillar(partner_birth_str_ya)
                    r_sg = compute_sok_gunghap(self_dp, prt_dp, self_brs, prt_brs)
                    if r_sg:
                        deterministic_blocks.append(format_sok_gunghap_for_prompt(r_sg))

                elif content_key == "desire-saju" and birth_str_ya:
                    from engine.divination.desire_saju import (
                        compute_desire_saju, format_desire_saju_for_prompt,
                    )
                    from engine.saju.ten_gods import compute_ten_gods as _ten_gods_ya
                    dg_y, _, _, brs_y = _ya_day_pillar(birth_str_ya)
                    # 4 천간 추출 (일간 제외 3건의 십성 계산)
                    d2 = _dt_ya.strptime(birth_str_ya, "%Y-%m-%d").date()
                    p_y = _compute_pillars_ya(d2.year, d2.month, d2.day, 12)
                    other_gans = [
                        p_y["year_pillar"]["gan_han"],
                        p_y["month_pillar"]["gan_han"],
                        p_y["hour_pillar"]["gan_han"],
                    ]
                    tgs = tuple(_ten_gods_ya(dg_y, og) for og in other_gans)
                    r_ds = compute_desire_saju(dg_y, tgs, brs_y)
                    if r_ds:
                        deterministic_blocks.append(format_desire_saju_for_prompt(r_ds))

                elif content_key == "unu-jijeong" and birth_str_ya and partner_birth_str_ya:
                    from engine.divination.unu_jijeong import (
                        compute_unu_jijeong, format_unu_jijeong_for_prompt,
                    )
                    _, self_dj, _, _ = _ya_day_pillar(birth_str_ya)
                    _, prt_dj, _, _ = _ya_day_pillar(partner_birth_str_ya)
                    r_uj = compute_unu_jijeong(self_dj, prt_dj)
                    if r_uj:
                        deterministic_blocks.append(format_unu_jijeong_for_prompt(r_uj))

                elif content_key == "jeongin-saju" and birth_str_ya:
                    from engine.divination.jeongin_saju import (
                        compute_jeongin_saju, format_jeongin_saju_for_prompt,
                    )
                    from engine.saju.ten_gods import compute_ten_gods as _ten_gods_ya2
                    dg_y, dj_y, _, _ = _ya_day_pillar(birth_str_ya)
                    d3 = _dt_ya.strptime(birth_str_ya, "%Y-%m-%d").date()
                    p_y3 = _compute_pillars_ya(d3.year, d3.month, d3.day, 12)
                    all_other_gans = [
                        p_y3["year_pillar"]["gan_han"],
                        p_y3["month_pillar"]["gan_han"],
                        p_y3["hour_pillar"]["gan_han"],
                    ]
                    tgs_all = tuple(_ten_gods_ya2(dg_y, og) for og in all_other_gans)
                    r_ji = compute_jeongin_saju(dg_y, dj_y, tgs_all)
                    if r_ji:
                        deterministic_blocks.append(format_jeongin_saju_for_prompt(r_ji))
            except Exception:
                pass

        # ─── ADR-122·123·124 조상 메시지 (palm/ancestor content_key + birth) ───
        # 천살 방위 (ADR-122) + 어휘 풀·흐름 톤 (ADR-123) + 4 권역 위령 의례 (ADR-124).
        # 한국 무속 정통 학파 (이능화 1927·한국학중앙연구원·국립민속박물관) 정합.
        # 자문 거절 정신: 망자 1인칭 빙의 화법·접신 어휘 절대 금지 (sanitize 5중).
        if char_key == "palm" and content_key == "ancestor":
            try:
                from engine.divination.ancestor import (
                    build_ancestor_prompt_injection,
                    get_cheonsal_direction,
                )
                ancestor_block_lines = [
                    "[조상 메시지 결정론 — ADR-122·123·124 정통 학파 정합]"
                ]
                # 천살 방위 (출생 연도 지지 → 풍수 방위)
                if birth_str:
                    try:
                        from datetime import date as _date_anc
                        from engine.saju.pillars import compute_pillars
                        birth_d_anc = _date_anc.fromisoformat(birth_str)
                        pillars_anc = compute_pillars(
                            birth_d_anc.year, birth_d_anc.month, birth_d_anc.day, 12
                        )
                        year_ji = pillars_anc.get("year", {}).get("ji_han", "") if isinstance(pillars_anc, dict) else ""
                        if year_ji:
                            cheonsal = get_cheonsal_direction(year_ji)
                            ancestor_block_lines.append(
                                f"  · 천살(天殺) 방위: {cheonsal['cheonsal_ji']} "
                                f"({cheonsal['direction_ko']}, {cheonsal['direction_degree']}도) "
                                f"— 삼합 {cheonsal['samhap']} 기준 정통 사주명리 십이신살."
                            )
                            ancestor_block_lines.append(
                                "  · 전통 제례 헌작·조상 묘 방위 안내용 결정론 산출 "
                                "(메트로신문 김상회 칼럼·정통 사주명리)."
                            )
                    except Exception:
                        pass
                # 어휘 풀 + 흐름 톤 + 금지 어휘 LLM 시스템 프롬프트 주입
                ancestor_block_lines.append("")
                ancestor_block_lines.append(build_ancestor_prompt_injection())
                deterministic_blocks.append("\n".join(ancestor_block_lines))
            except Exception:
                pass

        # ─── face 결정론 (ADR-075·082, char_key='face') ───
        # ADR-082: imageB64 입력 시 Phase 2 → generate_face_reading Vision 호출
        # ADR-075: 사진 미입력 시 4 학파 + 삼정 + 12궁 메타만 인용
        wants_face = char_key == "face"
        face_image_b64 = (fields.get("imageB64") or fields.get("image") or "").strip()
        if wants_face:
            try:
                from engine.divination.face.knowledge import (
                    PHYSIOGNOMY_SCHOOLS, SAMJEONG_REGIONS, TWELVE_PALACES,
                )
                schools_meta = " · ".join(s.name_ko for s in PHYSIOGNOMY_SCHOOLS)
                samjeong_meta = " · ".join(r.label_ko for r in SAMJEONG_REGIONS)
                palaces_meta = " · ".join(p.label_ko for p in TWELVE_PALACES[:6]) + " 등 12궁"
                if face_image_b64:
                    # ADR-082 Phase 2: Vision 풀 호출은 별도 엔드포인트 권장
                    deterministic_blocks.append(
                        "[관상 결정론 Phase 2 — engine/divination/face/reading.generate_face_reading]\n"
                        f"  · 학파 4개: {schools_meta}\n"
                        f"  · 삼정 (얼굴 3분할): {samjeong_meta}\n"
                        f"  · 12궁 일부: {palaces_meta}\n"
                        f"  · 사진 입력 감지 (base64 길이: {len(face_image_b64)})\n"
                        f"  · Vision 풀 호출은 별도 엔드포인트 (/api/face/read) 사용 권장.\n"
                        f"  · 단정 매핑 부재 (fate_mapping·운명 X — ADR-006)."
                    )
                else:
                    deterministic_blocks.append(
                        "[관상 결정론 — engine/divination/face 학파·구조 풀]\n"
                        f"  · 학파 4개: {schools_meta}\n"
                        f"  · 삼정 (얼굴 3분할): {samjeong_meta}\n"
                        f"  · 12궁 일부: {palaces_meta}\n"
                        f"  · 사진 미입력 시 라이브 분류 불가. 구조 인용만 허용.\n"
                        f"  · 단정 매핑 부재 (fate_mapping·운명 X — ADR-006)."
                    )
            except Exception:
                deterministic_blocks.append("[관상 결정론 — 산출 실패]")

        # ─── star compatibility 결정론 (ADR-106, char_key='star' + mySign/partnerSign 단독 OK) ───
        # 144 별자리 궁합은 birth 없이도 호출 가능 (별자리 직접 입력)
        if char_key == "star" and content_key == "compatibility":
            my_sign = (fields.get("mySign") or "").strip()
            partner_sign = (fields.get("partnerSign") or "").strip()
            if my_sign and partner_sign:
                try:
                    from engine.divination.star.compatibility import compute_compatibility
                    compat = compute_compatibility(my_sign, partner_sign)
                    if compat:
                        deterministic_blocks.append(
                            "[별자리 144 궁합 결정론 — ADR-106]\n"
                            f"  · 본인: {compat.sign1_label_ko} ({compat.element1}/{compat.modality1})\n"
                            f"  · 상대: {compat.sign2_label_ko} ({compat.element2}/{compat.modality2})\n"
                            f"  · 관계 유형: {compat.element_tone_ko}\n"
                            f"  · 모달리티 결: {compat.modality_tone_ko}\n"
                            f"  · element 호환 {compat.element_affinity_score}점 + "
                            f"modality {compat.modality_affinity_score}점 + 종합 {compat.overall_score}점\n"
                            f"  · 결혼·이별·연애 성공 단정 X (ADR-006). 흐름 톤으로만 풀이."
                        )
                except Exception:
                    pass

        # ─── star today-zodiac 결정론 (ADR-068, sign 직접 입력) ───
        if char_key == "star" and content_key == "today-zodiac":
            sign_key = (fields.get("sign") or "").strip()
            if sign_key:
                try:
                    from datetime import date as _date_today
                    from engine.divination.star.scoring import sign_by_key, daily_tone_for_sign
                    sign_obj = sign_by_key(sign_key)
                    if sign_obj:
                        tone = daily_tone_for_sign(sign_key, _date_today.today())
                        deterministic_blocks.append(
                            "[오늘의 별자리 결정론 — ADR-068]\n"
                            f"  · 별자리: {sign_obj.label_ko} {sign_obj.symbol}\n"
                            f"  · 원소: {sign_obj.element} / 양태: {sign_obj.modality}\n"
                            f"  · 지배 행성: {sign_obj.ruling_planet}\n"
                            f"  · 오늘 일일 톤: {tone}\n"
                            f"  · 운명·재물·연애 단정 X (ADR-006)."
                        )
                except Exception:
                    pass

        # ─── star east28 결정론 (ADR-107·112, birth 무관) ───
        if char_key == "star" and content_key == "east28":
            try:
                from datetime import date as _date_28
                from engine.divination.star.twenty_eight_mansions import (
                    compute_twenty_eight_mansion_reading,
                )
                m_reading = compute_twenty_eight_mansion_reading(_date_28.today())
                deterministic_blocks.append(
                    "[동양 28수 결정론 — ADR-107 한국 천상열차분야지도 정통]\n"
                    f"  · 오늘의 수: {m_reading.mansion_label_ko} ({m_reading.mansion_label_hanja})\n"
                    f"  · 소속 궁: {m_reading.palace_label_ko} — {m_reading.palace_direction_ko}·{m_reading.palace_season_ko}\n"
                    f"  · 배속 동물: {m_reading.animal_ko}\n"
                    f"  · 배속 요일: {m_reading.weekday_ko}\n"
                    f"  · 흐름 톤: {m_reading.flow_tone_ko}\n"
                    f"  · 길일·흉일·관혼상제 단정 X (ADR-006). 국보 228호 정통."
                )
            except Exception:
                pass

        # ─── star 결정론 (ADR-068·106·107·112·114, char_key='star' + birth) ───
        wants_star = char_key == "star" and bool(birth_str)
        if wants_star:
            try:
                from datetime import datetime, date as date_cls
                from engine.divination.star.scoring import compute_daily_star_reading
                birth_d = datetime.strptime(birth_str, "%Y-%m-%d").date()
                star_result = compute_daily_star_reading(birth_d, date_cls.today())
                deterministic_blocks.append(
                    "[황도대 결정론 — engine/divination/star 출력]\n"
                    f"  · 별자리: {star_result.sign_label_ko} {star_result.sign_symbol}\n"
                    f"  · 원소: {star_result.element_ko}\n"
                    f"  · 양태: {star_result.modality_ko}\n"
                    f"  · 지배 행성: {star_result.ruling_planet}\n"
                    f"  · 일일 톤: {star_result.daily_tone_ko}\n"
                    f"  · 사랑·재물·진로 단정 부재 (love_outcome·career_outcome·money_outcome X — ADR-006)."
                )

                # ADR-114: Skyfield 빅3 + 하우스 + 트랜짓 (big3·classic·love-stars·transit·saju-star)
                if content_key in ("big3", "classic", "love-stars", "transit", "saju-star"):
                    try:
                        from datetime import datetime as _dt, timezone as _tz
                        from engine.divination.star.astronomy import (
                            compute_big_three,
                            compute_houses_whole_sign,
                        )
                        # 출생시간 미입력 → Sun만 fallback
                        # 본 시스템 birth는 'YYYY-MM-DD' — 시간 미입력. 정오 12:00 UTC 가정 (Sun-only).
                        dt_utc = _dt.combine(birth_d, _dt.min.time()).replace(hour=12, tzinfo=_tz.utc)
                        # birthplace 입력 시도 — 본 시스템은 좌표 미입력, 한국 기본 (서울 37.5N, 127.0E) 가정 옵션
                        # ★ Sun-only fallback 디폴트 (위경도 미입력)
                        big3 = compute_big_three(dt_utc)
                        if big3:
                            lines = [
                                "[Skyfield 빅3 결정론 — ADR-114 NASA JPL DE440s]",
                                f"  · 태양 별자리: {big3.sun.sign_label_ko} {big3.sun.degree_in_sign:.1f}°",
                            ]
                            if big3.moon:
                                lines.append(f"  · 달 별자리: {big3.moon.sign_label_ko} {big3.moon.degree_in_sign:.1f}°")
                            else:
                                lines.append("  · 달·상승: 출생시간·장소 미입력 — 산출 X (ADR-114 fallback 의무)")
                            lines.append(
                                "  · 운명·결혼·이혼·파산·건강 단정 X (Liz Greene·Arroyo 정통)."
                            )
                            deterministic_blocks.append("\n".join(lines))
                    except Exception:
                        pass
            except Exception:
                deterministic_blocks.append("[황도대 결정론 — 산출 실패]")

        # ─── dream 결정론 (ADR-077·080, char_key='dream' + dreamText) ───
        # ADR-080: analyze_dream 풀 호출 + PersonalContext 통합
        dream_text = (fields.get("dreamText") or fields.get("dream") or "").strip()
        wants_dream = char_key == "dream" and bool(dream_text)
        if wants_dream:
            try:
                from engine.divination.dream import analyze_dream
                from engine.divination.dream_lex.personal_context import build_context_from_dict

                # PersonalContext 사용자 입력 + 사주 맥락 통합
                ctx_data = {
                    "name": full_name or None,
                    "gender": fields.get("gender") or None,
                    "occupation": fields.get("occupation") or None,
                    "marital_status": fields.get("maritalStatus") or None,
                    "is_pregnant": fields.get("isPregnant") in ("true", True, "y"),
                    "current_concerns": [
                        c.strip() for c in (fields.get("concerns") or "").split(",") if c.strip()
                    ],
                    "mbti": fields.get("mbti") or None,
                }
                # 사주 맥락 (birth 입력 시 자동 주입)
                if birth_str:
                    try:
                        from datetime import datetime as _dt_dream
                        from engine.saju.pillars import day_pillar as _dp_dream
                        b = _dt_dream.strptime(birth_str, "%Y-%m-%d").date()
                        dm_pillar = _dp_dream(b.year, b.month, b.day)
                        ctx_data["day_master"] = dm_pillar["gan_han"]
                        # 오행 매핑
                        elem_map = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
                        ctx_data["day_master_element"] = elem_map.get(dm_pillar["gan_han"], "")
                    except Exception:
                        pass

                ctx = build_context_from_dict(ctx_data)
                analysis = analyze_dream(dream_text, ctx)

                # 결정론 학파 결과 압축 (12+ 도메인 핵심 발췌)
                art_cls = analysis.get("artemidorus_class", "")
                hobson = analysis.get("hobson", {})
                tst = analysis.get("tst", {})
                wx = analysis.get("wuxing", {})
                folk = analysis.get("korean_folk", [])
                arche = analysis.get("archetypes", [])
                hvdc_idx = analysis.get("hvdc_indices", {})
                ich = analysis.get("iching", {})

                folk_names = ", ".join((f.get("symbol") or f.get("name") or "")[:20] for f in folk[:3] if isinstance(f, dict))
                arche_names = ", ".join((a.get("archetype") or a.get("name") or "")[:20] for a in arche[:3] if isinstance(a, dict))

                deterministic_blocks.append(
                    "[해몽 결정론 — engine/divination/dream + dream_lex 12+ 학파 풀 호출]\n"
                    f"  · 입력 꿈: {dream_text[:80]}{'…' if len(dream_text)>80 else ''}\n"
                    f"  · Artemidorus 분류: {art_cls or '(미분류)'}\n"
                    f"  · Hobson 기이도: {hobson.get('bizarreness_level', '미산출')}\n"
                    f"  · Revonsuo TST 위협: {tst.get('total_threats', 0)}건\n"
                    f"  · 오행 매핑 (상위): {(wx.get('counts') or {})}\n"
                    f"  · 한국 민속 매칭 (상위 3): {folk_names or '(없음)'}\n"
                    f"  · Jung 원형 (상위 3): {arche_names or '(없음)'}\n"
                    f"  · Hall-Van de Castle 지수: {hvdc_idx}\n"
                    f"  · 주역 64괘: {ich.get('hexagram_name', '(미산출)')}\n"
                    f"  · [지시 1 — ADR-094 단정 차단] '길몽'·'흉몽'·'대길'·'대흉'·'반드시'·"
                    f"'확실히' 등 단정 어휘 절대 금지. 'polarity: 길/흉'은 학파 라벨일 뿐 "
                    f"운명 단정 X (ADR-006).\n"
                    f"  · [지시 2 — ADR-095 학파 명시] 위 결정론 학파 결과를 인용 시 학파명 "
                    f"명시 의무 (예: 'Artemidorus 분류상 ...', 'Jung 원형 풀에 ...', "
                    f"'한국 민속 해몽서에 ...'). 단일 학파 단정 X — 다학파 병행 의무 (ADR-002).\n"
                    f"  · [지시 3 — ADR-096 콘텐츠 적합성] content_key='{content_key}'에 맞춰:\n"
                    f"      nightmare → '길몽' 인용 X, 위협·불안·악몽 처리 권장.\n"
                    f"      baby → 태몽 학파 (한국 민속 + Hall-Van de Castle 태몽 지수) 인용.\n"
                    f"      lucid → Stephen LaBerge 자각몽 학파 + Dormio TDI 학파 명시.\n"
                    f"      recurring → 반복 꿈 (PTSD·IRT 학파) 인용.\n"
                    f"  · [지시 4 — ADR-006 양면 해석] 매 풀이마다 강점·약점·주의 동시 명시. "
                    f"긍정 일색 풀이 (균형도 0%) 금지 — '암묵적 단정' 차단.\n"
                    f"  · 사전학습 해몽 어휘 추가 금지 (ADR-010)."
                )
            except Exception:
                deterministic_blocks.append("[해몽 결정론 — 산출 실패]")

        # ─── hwapae 결정론 (ADR-078, char_key='hwapae') ───
        wants_hwapae = char_key == "hwapae"
        if wants_hwapae:
            try:
                # 사용자 입력 카드 없으면 day-seed 결정론으로 3장 추첨
                from datetime import date as _date_hwapae
                from engine.divination.hwapae.korean import HWAPAE_CARDS, three_card_spread
                import hashlib
                seed_str = (birth_str or "anon") + "-" + str(_date_hwapae.today())
                seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
                card_pool = list(HWAPAE_CARDS.keys())
                c0 = card_pool[(seed_hash + 0) % len(card_pool)]
                c1 = card_pool[(seed_hash + 7) % len(card_pool)]
                c2 = card_pool[(seed_hash + 14) % len(card_pool)]
                spread = three_card_spread((c0, c1, c2))
                card_meta = " · ".join(
                    f"{c.name_ko}({c.month}月)" for c in spread.cards
                )
                deterministic_blocks.append(
                    "[화패 결정론 — engine/divination/hwapae 출력]\n"
                    f"  · 3장 추첨 (seed=오늘+생일): {card_meta}\n"
                    f"  · 순서/역순/카테고리 패턴: sequential={spread.is_sequential} reverse={spread.is_reverse}\n"
                    f"  · 카테고리 우세: {spread.category_dominance or '(균형)'}\n"
                    f"  · 단정 점복 X (ADR-006). 상징·문화 콘텐츠로만 인용."
                )
            except Exception:
                deterministic_blocks.append("[화패 결정론 — 산출 실패]")

        # 결정론 블록 통합 + 사전학습 차단 지시
        if deterministic_blocks:
            deterministic_block = (
                "\n" + "\n\n".join(deterministic_blocks) +
                "\n[지시] 위 결정론 출력만 인용. "
                "60갑자·십성·한자·획수·4격·발음 명칭 사전학습 추가 X — ADR-010 사실성 분리.\n"
            )
        else:
            deterministic_block = ""

        # 7 캐릭터 페르소나 톤
        persona_tone_map = {
            "saju":   "만월 아씨 — 사주 명리학 풀이. 정중한 사극풍 어조.",
            "dream":  "몽이 도령 — 꿈 해석. 부드럽고 깊이 있는 어조.",
            "hwapae": "화선 낭자 — 화패·점복. 신비롭고 가벼운 어조.",
            "star":   "성하 공자 — 별빛 풀이. 우주적·시적 어조.",
            "face":   "운학 도사 — 관상. 사극풍 노학자 어조.",
            "palm":   "옥선 할미 — 손금. 따뜻한 할머니 어조.",
            "name":   "묵향 선생 — 작명. 학자다운 정중한 어조.",
        }
        persona = persona_tone_map.get(char_key, persona_tone_map["saju"])

        system = (
            f"당신은 한국 전통 운명학 풀이 캐릭터입니다.\n"
            f"[캐릭터] {persona}\n"
            f"[규칙]\n"
            f"- 단정적 예언 금지. 경향성·자기이해 위주.\n"
            f"- 의료·법률·금융 단정 금지 (ADR-006).\n"
            f"- 운명·재물·결혼 단정 매핑 금지.\n"
            f"- 한국어로 자연스럽게 작성. 4~6단락, 마크다운 없이.\n"
            f"- 결정론 출력이 주어지면 그 출력만 인용 (사전학습 추가 X — ADR-010 사실성 분리).\n"
            f"- ★ [사용자 입력 활용 의무] 사용자가 입력한 모든 필드를 풀이 본문에 자연스럽게 통합하라.\n"
            f"  · 이름이 있으면 응답에 호명 (예: '김준 님의 마음을…').\n"
            f"  · 상대방 이름·관계·기간·맥락 등 입력값을 일반론에 묻지 말고 구체 인용.\n"
            f"  · select 라벨(예: '짝사랑·썸', '1~3개월 전')은 그대로 본문에 녹여 사용.\n"
            f"  · 입력 미반영 = 무의미한 풀이 — 반드시 모든 입력을 응답 내 한 번 이상 언급.\n"
            f"{deterministic_block}"
        )

        # 사용자 입력 정리 — fields_meta로 select 라벨 자동 변환 + 강조
        fields_meta = _resolve_field_labels(char_key, content_key, fields)
        inputs_text = "\n".join(
            f"  · {meta['label']}: {meta['display']}" for meta in fields_meta
        ) if fields_meta else "(입력 없음)"

        # 약점 영역 강화 — content_key별 입력 인용 체크리스트.
        # LLM이 응답 작성 전에 각 입력값을 본문 어느 단락에 녹일지 명시 추적.
        # 이전 측정 결과 future-fate(20%)·fate-one(33%)·reunion-month(33%) 등에서
        # LLM이 일반론에 묻는 경향 → 체크리스트로 자가 검증 강제.
        checklist_items = []
        for meta in fields_meta:
            key = meta["key"]
            display = meta["display"]
            if key in ("birth", "gender", "saju_day_master", "saju_summary"):
                continue  # 메타 정보는 호명만, 체크리스트 X
            checklist_items.append(
                f"  □ '{display}' — 응답에 자연스럽게 인용했는가?"
            )
        checklist_block = (
            "\n[★ 자가 검증 체크리스트 — 응답 작성 후 모두 ✓ 가능해야 함]\n"
            + "\n".join(checklist_items)
            + "\n  · 미인용 항목 있으면 응답 재작성하라.\n"
        ) if checklist_items else ""

        prompt = (
            f"[메뉴 콘텐츠] char_key={char_key}, content_key={content_key}\n"
            f"[사용자 입력 — 풀이 본문에 모두 인용 의무]\n{inputs_text}\n"
            f"[요청] 위 사용자 입력을 자연스럽게 녹여 풀이 한 편 펼쳐주세요. "
            f"이름·상대·관계·기간·맥락을 일반론에 묻지 말고 구체적으로 인용하세요."
            f"{checklist_block}"
        )

        try:
            from engine.llm_sync import bizrouter_client
            client = bizrouter_client()
            # ADR-098: char_key별 모델 분리 라우팅 — dream만 Flash 업그레이드 A/B 테스트
            # DREAM_MODEL > BIZROUTER_MODEL > 기본값 순 우선순위
            default_model = os.environ.get("BIZROUTER_MODEL", "google/gemini-2.5-flash-lite")
            if char_key == "dream":
                model = os.environ.get("DREAM_MODEL", default_model)
            else:
                model = default_model
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            text = resp.choices[0].message.content or ""
            # ADR-094 강화 — dream 도메인 단정 어휘 사후 필터링.
            # system 프롬프트가 차단해도 LLM이 "길몽으로 해석될 수 있습니다" 같은
            # 가능형 우회를 자주 사용. 본 필터로 실 응답에서 직접 치환.
            if char_key == "dream":
                text = _sanitize_dream_assertion_words(text)
            # ADR-122 sanitize 5중 안전망 — ancestor (palm/ancestor) 분기 망자 1인칭·빙의·접신 차단.
            # 한국 무속 정통 학파 정합 (이능화 1927·한국학중앙연구원·국립민속박물관).
            # Skeptical Inquirer Susan Gerbic 'Grief Vampires' 콜드/핫 리딩 디지털 차단.
            if char_key == "palm" and content_key == "ancestor":
                text = _sanitize_ancestor_assertion_words(text)
            # ADR-134 sanitize 6중 안전망 — tojeong (palm/tojeong) 분기 凶事·大凶·病死 단정 차단.
            # 정통 시구의 단정 어휘를 흐름 톤으로 자동 치환 (folkency·encykorea 학파 정합).
            if char_key == "palm" and content_key == "tojeong":
                try:
                    from engine.divination.tojeong import sanitize_tojeong_verse
                    text = sanitize_tojeong_verse(text)
                except Exception:
                    pass
            # ADR-158 sanitize 7중 안전망 — 야선 아씨 4 컨텐츠 (속궁합·욕망·운우지정·정인).
            # 결혼·이혼·외도·이별·시기·배우자 외모 단정 차단.
            if char_key == "ya":
                try:
                    if content_key == "sok-gunghap":
                        from engine.divination.sok_gunghap import sanitize_sok_gunghap_text
                        text = sanitize_sok_gunghap_text(text)
                    elif content_key == "desire-saju":
                        from engine.divination.desire_saju import sanitize_desire_saju_text
                        text = sanitize_desire_saju_text(text)
                    elif content_key == "unu-jijeong":
                        from engine.divination.unu_jijeong import sanitize_unu_jijeong_text
                        text = sanitize_unu_jijeong_text(text)
                    elif content_key == "jeongin-saju":
                        from engine.divination.jeongin_saju import sanitize_jeongin_saju_text
                        text = sanitize_jeongin_saju_text(text)
                except Exception:
                    pass
            # ADR-006/094 공통 단정 어휘 사후 필터링 (모든 캐릭터).
            # 화선 낭자·운학 도사 등 hwapae/face도 system 지시 우회 빈번.
            text = _sanitize_common_assertion_words(text)
            # ADR-115 다국어 hallucination 차단 (모든 캐릭터).
            # 발견: face/reading.py 운학 도사 응답에 포르투갈어 "saudável" 침입 (2026-05-21).
            text = _sanitize_foreign_hallucination(text)
            text = _sanitize_korean_grammar_dupes(text)
            return {
                "text": text,
                "char_key": char_key,
                "content_key": content_key,
                "deterministic_used": bool(deterministic_block.strip()),
                "legal_notice": build_legal_footer(),
                "ai_generation": build_ai_generation_meta(model_label=model),
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    async def post_name_reading(
        self, req: NameReadingRequest
    ) -> dict[str, Any]:
        """묵향 선생 이름 풀이 — 텍스트 전용 LLM 호출 + 캐시."""
        try:
            from engine.divination.name.reading import generate_name_reading

            result = await asyncio.to_thread(
                generate_name_reading,
                req.fullname_ko,
                req.fullname_han,
                req.gender,
                req.birth,
                req.saju_day_master,
                req.saju_summary,
            )
            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            raise HTTPException(500, str(e))
