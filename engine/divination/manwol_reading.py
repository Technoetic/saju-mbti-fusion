"""만월아씨 · 사주 통합 서사 페르소나.

심야괴담회 방송실의 진행자 만월아씨가 사연자의 사주를 짚어주는 통합 서사.
사주 · 이름 · 관상 · 꿈 · 자미두수 · 타로 · 생활현황 · MBTI · 고민
모든 결정론 데이터를 하나의 산문으로 융합.

톤: 차도녀 · 시크 · 도도 · 테토 카리스마 · 반말 · 심야 방송실.
"""

from __future__ import annotations

import json
from typing import Any


MANWOL_SYSTEM = (
    '당신은 "만월아씨"다. 심야괴담회 방송실의 진행자.\n'
    "사연자가 사주 정보를 보내왔고, 지금 마이크 앞에서 그걸 짚어주는 중이다.\n\n"
    "[페르소나 · 절대 준수]\n"
    "  • 톤: 차도녀 · 시크 · 도도 · 테토 카리스마. 감정 절제된 반말.\n"
    "  • 반말 일관. 존댓말 금지. 어미는 \"~해\" \"~네\" \"~겠지\" \"~군\" \"~야\" \"~다\" \"~인가\" 로 마감.\n"
    "  • 사연자 호칭: \"너\" 만 사용. \"회원님/고객님/그대/자네/당신/낭자/도령\" 전부 금지.\n"
    "  • 자기 지칭 하지 않음. \"이 만월아씨가/낭자가/이 늙은이\" 같은 자기 언급 금지.\n"
    "  • 사극톤 사극 존댓말 절대 금지. \"허허/하시게/이로다/하옵니다/외다/하오/이로세/구먼\" X.\n"
    "  • 이모지 X. 따뜻한 위로 X. 축복 어휘 X. 감탄사 X.\n"
    "  • 밤 방송실 · 낮고 냉정한 목소리 · 짧은 문장 위주 · 절제된 리듬.\n\n"
    "[내용 규칙 · 절대 준수]\n"
    "  • 아래 [사주 결정론 데이터] 블록에 있는 값만 근거로 짚어라. 4기둥 · 오행 분포 · 신강 등급 · 격국 · 대운 · 이름 오격 · 자미 · 타로 · 관상 지표 · 꿈 원문 · 생활 현황 · MBTI · 고민.\n"
    "  • 데이터에 없는 값을 지어내지 마라. 특히 아래 것들은 데이터에 명시된 것 외엔 절대 새로 만들지 마라:\n"
    "      - 사주 기둥의 숫자 (\"일주 35\" 같은 임의의 숫자 금지)\n"
    "      - 이름 오격의 수치 (원격·형격·이격·정격·외격의 숫자는 데이터에 있는 것만)\n"
    "      - 이름 한자의 뜻 (亨=형통 같은 자의 해설은 데이터에 없으면 언급 X)\n"
    "      - 십성 · 신살 · 자미 주성 · 타로 카드 이름 — 데이터에 없으면 언급 X\n"
    "  • 없는 도메인은 그냥 스킵. 있는 도메인만 자연스럽게 언급.\n"
    "  • 단정 예언 금지: \"~된다/할 것이다/한다\" 금지. 대신 \"결이 보인다/기운이 있다/흐름이다\".\n"
    "  • 의료 · 법률 · 이혼 · 정신질환 · 투자 예언 절대 금지 (ADR-006). 건강은 \"몸 살펴\" 정도.\n"
    "  • 사연자 고민이 있으면 그거에 직접 응답. 없으면 사주 흐름 전반.\n\n"
    "[구성 · 유연]\n"
    "  1. 도입 (2~3문장) — 방송실 오프닝 · 사연 도착 · 사주 짚기 시작.\n"
    "  2. 사주 골격 — 일간 성정 · 격국 · 신강 · 오행 편중 · 현재 대운 흐름.\n"
    "  3. 이름 (있으면) — 음오행 · 오격 자연 언급.\n"
    "  4. 관상 (있으면) — 결정론 지표 근거로 짧게.\n"
    "  5. 꿈 (있으면) — 원문 짧게 인용하며 결의 방향으로 해석.\n"
    "  6. 자미두수 · 타로 (있으면) — 명궁 주성 · 3장 흐름 자연 융합.\n"
    "  7. 생활 · MBTI (있으면) — 지금 상황 · 사주 연결.\n"
    "  8. 사연자 고민 응답 (있으면) — 직접 · 짧게.\n"
    "  9. 마무리 한 마디 — 짧고 강렬. 만월아씨답게.\n\n"
    "[문장 스타일 예시]\n"
    "  \"너 일간 甲, 큰 나무야. 근데 지금 대운은 金이 강해. 뿌리 흔들리는 시기다.\"\n"
    "  \"이름 오격 보니까 원격 16, 리더격이네. 감당하는 시기가 좀 늦어.\"\n"
    "  \"이마 넓고 코 반듯해. 자기 확신 강한 얼굴이야.\"\n"
    "  \"꿈에 물이 나왔지. 감정이 넘치는 시기라는 뜻이야. 억누르지 말고.\"\n"
    "  \"자미궁에 자미성 앉았어. 리더의 별. 옆에 파군이 있어. 파란 많은 흐름이겠지.\"\n"
    "  \"타로 마지막 카드 - 별. 방향은 있어. 근데 아직 멀다.\"\n"
    "  \"고민이 이직이라고. 대운 봐. 지금은 확장보다 정리 시기야.\"\n"
    "  \"마이크 끈다. 오늘은 여기까지.\"\n\n"
    "[분량 · 형식]\n"
    "  • 1500 ~ 2500 자.\n"
    "  • 마크다운 없음. 자연 문장. 문단은 2줄 개행으로 구분.\n"
    "  • 제목 · 소제목 · 리스트 · 볼드 · 이모지 절대 X.\n"
    "  • 인사말 · 자기 소개 없이 방송 오프닝으로 바로 시작.\n"
    "  • 마지막 한 마디로 끝나야 함. 어물쩡 여운 X.\n"
)


_STEM_KO = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}
_BRANCH_KO = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}
_ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def _fmt_pillar(p: dict[str, Any] | None, label: str) -> str:
    if not p:
        return f"  · {label}: 정보 없음"
    stem = p.get("gan_han") or p.get("gan") or p.get("stem") or ""
    branch = p.get("ji_han") or p.get("ji") or p.get("branch") or ""
    stem_ko = _STEM_KO.get(stem, "")
    branch_ko = _BRANCH_KO.get(branch, "")
    combo = f"{stem}{branch}".strip() or "?"
    combo_ko = f"({stem_ko}{branch_ko})" if stem_ko and branch_ko else ""
    return f"  · {label}: {combo} {combo_ko}".rstrip()


def _fmt_wuxing(dist: dict[str, float] | None) -> str:
    if not dist:
        return "  · 오행: 정보 없음"
    parts = []
    for el, val in dist.items():
        el_ko = _ELEMENT_KO.get(el, el)
        try:
            v = float(val)
            parts.append(f"{el}({el_ko}) {v:.1f}")
        except Exception:
            parts.append(f"{el}({el_ko}) {val}")
    return "  · 오행 분포: " + ", ".join(parts)


def _fmt_luck_cycle(cycle: list[dict[str, Any]] | None, current_age: int | None) -> str:
    if not cycle:
        return "  · 대운: 정보 없음"
    lines = ["  · 대운 흐름 (최근~향후):"]
    shown = 0
    for c in cycle:
        age = c.get("age")
        if age is None:
            continue
        if current_age is not None and (age < current_age - 12 or age > current_age + 22):
            continue
        stem = c.get("gan_han") or c.get("gan") or ""
        branch = c.get("ji_han") or c.get("ji") or ""
        lines.append(f"    - {age}세 ~: {stem}{branch}")
        shown += 1
        if shown >= 5:
            break
    if shown == 0:
        for c in cycle[:5]:
            age = c.get("age", "?")
            stem = c.get("gan_han") or c.get("gan") or ""
            branch = c.get("ji_han") or c.get("ji") or ""
            lines.append(f"    - {age}세 ~: {stem}{branch}")
    return "\n".join(lines)


def _fmt_name(name_analysis: dict[str, Any] | None) -> str:
    if not name_analysis:
        return ""
    lines = ["[이름 · 성명학 결정론]"]
    surname = name_analysis.get("surname") or ""
    given = name_analysis.get("givenName") or name_analysis.get("given_name") or ""
    if surname or given:
        lines.append(f"  · 성명: {surname}{given}")
    oh_haeng = name_analysis.get("음오행분석") or name_analysis.get("eumOhaeng")
    if oh_haeng:
        lines.append(f"  · 음오행: {json.dumps(oh_haeng, ensure_ascii=False)[:200]}")
    ogyeok = name_analysis.get("오격") or name_analysis.get("ogyeok")
    if ogyeok:
        try:
            summary_bits = []
            for key in ("원격", "형격", "이격", "정격", "외격"):
                v = ogyeok.get(key) if isinstance(ogyeok, dict) else None
                if isinstance(v, dict):
                    num = v.get("수") or v.get("num")
                    grade = v.get("평가") or v.get("grade") or ""
                    summary_bits.append(f"{key} {num}({grade})")
            if summary_bits:
                lines.append("  · 오격: " + ", ".join(summary_bits))
        except Exception:
            pass
    return "\n".join(lines)


def _fmt_life_context(life: dict[str, Any] | None) -> str:
    if not life:
        return ""
    lines = ["[생활 현황]"]
    job = life.get("job") or {}
    if isinstance(job, dict) and job:
        state = job.get("상태") or job.get("state") or ""
        dur = job.get("기간") or job.get("duration") or ""
        if state:
            lines.append(f"  · 직장: {state}" + (f" ({dur})" if dur else ""))
    love = life.get("love") or {}
    if isinstance(love, dict) and love:
        state = love.get("상태") or love.get("state") or ""
        dur = love.get("기간") or love.get("duration") or ""
        if state:
            lines.append(f"  · 연애: {state}" + (f" ({dur})" if dur else ""))
    mbti = life.get("mbti")
    if mbti:
        lines.append(f"  · MBTI: {mbti}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _fmt_extras(payload: dict[str, Any]) -> str:
    bits: list[str] = []
    dream = payload.get("dream_text") or payload.get("dreamText")
    if dream and isinstance(dream, str) and dream.strip():
        clipped = dream.strip()[:500]
        bits.append(f"[꿈 (사연자 원문)]\n  {clipped}")
    face_metrics = payload.get("face_metrics") or payload.get("faceMetrics")
    if face_metrics and isinstance(face_metrics, dict):
        try:
            keys = list(face_metrics.keys())[:8]
            summary = ", ".join(
                f"{k}={face_metrics[k]:.2f}" if isinstance(face_metrics[k], (int, float))
                else f"{k}={face_metrics[k]}"
                for k in keys
            )
            bits.append(f"[관상 결정론 지표]\n  {summary}")
        except Exception:
            bits.append("[관상] 사연자가 사진을 제출했음")
    ziwei_summary = payload.get("ziwei_summary") or payload.get("ziweiSummary")
    if ziwei_summary and isinstance(ziwei_summary, str) and ziwei_summary.strip():
        bits.append(f"[자미두수 명반 요약]\n  {ziwei_summary.strip()[:400]}")
    tarot_cards = payload.get("tarot_cards") or payload.get("tarotCards")
    if tarot_cards and isinstance(tarot_cards, list) and tarot_cards:
        try:
            names = [
                (c.get("name") if isinstance(c, dict) else str(c))
                for c in tarot_cards
            ]
            bits.append("[타로 3장] " + " · ".join(str(n) for n in names if n))
        except Exception:
            pass
    return "\n\n".join(bits)


def build_manwol_user_prompt(payload: dict[str, Any]) -> str:
    """결정론 페이로드 → 만월아씨용 사용자 프롬프트 구성.

    payload 예상 키 (모두 optional):
      - saju: dict (pillars, day_master, wuxing_dist, luck_cycle, ...)
      - name_analysis: dict
      - life_context: dict (job, love, mbti)
      - concern: str (사연자 고민)
      - dream_text: str (꿈 원문)
      - face_metrics: dict (관상 결정론 지표)
      - ziwei_summary: str
      - tarot_cards: list[dict]
      - gender: str
      - age: int
    """
    parts: list[str] = []

    saju = payload.get("saju") or {}
    pillars = saju.get("pillars") or {}

    parts.append("[사주 결정론 데이터 · 이 내용을 절대 새로 만들지 말고 그대로 인용해 짚어라]")
    parts.append(_fmt_pillar(pillars.get("year"), "년주"))
    parts.append(_fmt_pillar(pillars.get("month"), "월주"))
    parts.append(_fmt_pillar(pillars.get("day"), "일주"))
    parts.append(_fmt_pillar(pillars.get("hour") or pillars.get("time"), "시주"))

    day_master = saju.get("day_master") or saju.get("dayMaster")
    if day_master:
        parts.append(f"  · 일간: {day_master} ({_STEM_KO.get(day_master, '')})")

    strength = saju.get("strength") or saju.get("sinKang") or {}
    if isinstance(strength, dict) and strength:
        grade = strength.get("grade") or strength.get("등급") or ""
        if grade:
            parts.append(f"  · 신강: {grade}")

    gyeokguk = saju.get("gyeokguk") or saju.get("격국")
    if isinstance(gyeokguk, dict):
        name = gyeokguk.get("name") or gyeokguk.get("명")
        if name:
            parts.append(f"  · 격국: {name}")
    elif isinstance(gyeokguk, str):
        parts.append(f"  · 격국: {gyeokguk}")

    parts.append(_fmt_wuxing(saju.get("wuxing_dist") or saju.get("wuxingDist")))

    current_age = payload.get("age") or saju.get("age")
    parts.append(_fmt_luck_cycle(saju.get("luck_cycle") or saju.get("luckCycle"), current_age))

    gender = payload.get("gender") or saju.get("gender")
    if gender:
        parts.append(f"  · 성별: {gender}")

    name_block = _fmt_name(payload.get("name_analysis") or payload.get("nameAnalysis"))
    if name_block:
        parts.append("")
        parts.append(name_block)

    extras = _fmt_extras(payload)
    if extras:
        parts.append("")
        parts.append(extras)

    life_block = _fmt_life_context(payload.get("life_context") or payload.get("lifeContext"))
    if life_block:
        parts.append("")
        parts.append(life_block)

    concern = payload.get("concern") or payload.get("userConcern")
    if concern and isinstance(concern, str) and concern.strip():
        parts.append("")
        parts.append(f"[사연자 고민 · 직접 응답]\n  {concern.strip()[:600]}")

    parts.append("")
    parts.append(
        "[지시]\n"
        "  위 결정론 데이터를 근거로 만월아씨의 통합 서사를 작성해라.\n"
        "  방송 오프닝으로 시작 → 사주 골격 → 있는 도메인 자연 융합 → 마무리 한 마디.\n"
        "  1500~2500자, 마크다운 없이 자연 문장, 반말, 존댓말 · 이모지 · 사극톤 절대 X."
    )
    return "\n".join(parts)
