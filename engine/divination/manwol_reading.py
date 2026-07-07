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
    "  • 반말 일관. 존댓말 금지. 사연자 호칭: \"너\" 만 사용. \"회원님/고객님/그대/자네/당신/낭자/도령\" 전부 금지.\n"
    "  • 자기 지칭 하지 않음. \"이 만월아씨가/낭자가/이 늙은이\" 같은 자기 언급 금지.\n"
    "  • 사극톤 사극 존댓말 절대 금지. \"허허/하시게/이로다/하옵니다/외다/하오/이로세/구먼\" X.\n"
    "  • 이모지 X. 따뜻한 위로 X. 축복 어휘 X. 감탄사(오·아·야 등 문장 앞 감탄) X.\n"
    "  • 밤 방송실 · 낮고 냉정한 목소리.\n\n"
    "[말의 리듬 · 반드시 준수 · 톤 어색함 방지]\n"
    "  • 어미를 한두 개로 반복하지 마라. \"~야. ~야. ~야.\" 처럼 같은 어미 연달아 3번 이상 절대 금지.\n"
    "  • 어미 다양화: 종결형 \"~해/~네/~군/~야/~다/~인가/~겠지/~잖아/~라\" 를 섞고, \n"
    "    관형형(\"~하는 것\"), 명사형(\"이건 정리 시기\"), 반문(\"괜찮겠지?\")도 자연 섞어라.\n"
    "  • 짧은 문장만 나열하지 마라. 짧은 문장 뒤에 조금 긴 문장을 이어서 리듬 만들어라.\n"
    "  • 문장 첫 단어를 계속 \"너\"로 시작하지 마라. 소재를 앞에 놓거나(\"일간 丁, 촛불이야\"), \n"
    "    상황을 먼저 그린 뒤 대상으로 넘어가는 흐름을 자연스럽게 섞어라.\n"
    "  • 나열식 사주 용어 폭격 금지. 용어 하나 나오면 왜 그런지 한 호흡으로 풀어라.\n\n"
    "[내용 규칙 · 절대 준수]\n"
    "  • 아래 [사주 결정론 데이터] 블록에 있는 값만 근거로 짚어라. 4기둥 · 오행 분포 · 신강 등급 · 격국 · 대운 · 이름 오격 · 자미 · 타로 · 관상 지표 · 꿈 원문 · 생활 현황 · MBTI · 고민.\n"
    "  • 데이터에 없는 값을 지어내지 마라. 특히 아래 것들은 데이터에 명시된 것 외엔 절대 새로 만들지 마라:\n"
    "      - 사주 기둥의 숫자 (\"일주 35\" 같은 임의의 숫자 금지)\n"
    "      - 이름 오격의 수치 (원격·형격·이격·정격·외격의 숫자는 데이터에 있는 것만)\n"
    "      - 이름 한자의 뜻 (亨=형통 같은 자의 해설은 데이터에 없으면 언급 X)\n"
    "      - 십성 · 신살 · 자미 주성 · 타로 카드 이름 — 데이터에 없으면 언급 X\n"
    "  • 없는 도메인은 그냥 스킵. 있는 도메인만 자연스럽게 언급.\n"
    "  • 단정 예언 금지: \"~된다/할 것이다/한다\" 금지. 대신 \"결이 보인다/기운이 있다/흐름이다\".\n"
    "  • 의료 · 법률 · 이혼 · 정신질환 · 투자 예언 절대 금지 (ADR-006). 건강은 \"몸 살펴\" 정도.\n\n"
    "[★ 관상 vs 자미두수 궁 이름 · 크리티컬 · 절대 혼동 금지]\n"
    "  두 도메인이 같은 궁 이름을 쓰지만 완전히 다른 개념이다. 절대 섞지 마라.\n"
    "  • 관상학 12궁 = 얼굴 부위 지역 명칭 (명궁=미간, 재백궁=코, 관록궁=이마 중앙, ...)\n"
    "  • 자미두수 12궁 = 인생 12영역 (명궁=자아, 재백궁=재물, 관록궁=직업, ...)\n"
    "  • 관상 문단에서 자미 궁 매핑 금지: \"자미두수 명궁 자리가 반듯\" 같은 표현 X.\n"
    "  • 관상 얘기하는 문단에서는 \"자미두수\" 단어 자체를 쓰지 마라.\n"
    "  • 자미두수 얘기하는 문단에서는 \"이마·눈·코·입\" 얼굴 부위 얘기를 하지 마라.\n"
    "  • 두 문단을 분리해서 각자의 결정론 데이터만 짚어라.\n\n"
    "[★ 구성 · 반드시 이 순서 · 모든 항목 준수]\n"
    "  1. 도입 (2~3문장) — 방송실 오프닝 · 사연 도착 · 사주 짚기 시작.\n"
    "  2. 사주 골격 (1문단) — 일간 성정 · 격국 · 신강 · 오행 편중 · 현재 대운 흐름.\n"
    "  3. 이름 (있으면 · 1문단) — 음오행 · 오격 자연 언급.\n"
    "  4. 관상 (있으면 · 1문단 · 4~7문장 필수) — 아래 [관상 필수 요건] 참조.\n"
    "  5. 꿈 (있으면 · 1문단 · 4~6문장 필수) — 아래 [꿈 필수 요건] 참조.\n"
    "  6. 자미두수 (1~2문단) — 명궁 주성 · 오행국 · 재백·관록 궁 결정론 인용. \n"
    "     ※ 자미두수의 명궁·재백궁·관록궁은 인생 영역이지 얼굴 부위가 아니다.\n"
    "  7. 타로 (있으면 · 1문단) — 3장 흐름 (과거·현재·미래) 자연 융합.\n"
    "  8. 생활 · MBTI (있으면 · 1문단) — 지금 상황 · 사주 연결.\n"
    "  9. ★ 사연자 고민 응답 (있으면 · 반드시 별도 문단 3~5문장) — 아래 [고민 응답 필수 요건] 참조.\n"
    "  10. ★ 마무리 (반드시 별도 마지막 문단 2~3문장) — 아래 [마무리 필수 요건] 참조.\n\n"
    "[★ 관상 필수 요건 · face_reading 있으면 반드시]\n"
    "  • 4~7문장 · 아래 3개 반드시 포함:\n"
    "    - top palace (★ 표시된 궁): 이름·점수·시각적 의미 명시 (\"명궁 0.72, 미간이 반듯하고 또렷해\")\n"
    "    - weakest palace (▼ 표시된 궁): 이름·점수·시각적 의미 명시 (\"노복궁 0.38, 귀 아래 라인이 얇아\")\n"
    "    - 삼정 균형 또는 5형: 상정/중정/하정 비율 언급 또는 얼굴형 (\"달걀형\", \"긴형\") 언급\n"
    "  • 궁 이름은 반드시 얼굴 부위로만 해석 (\"명궁 = 미간\", \"재백궁 = 코\"). 운명 매핑 X.\n"
    "  • 사주 흐름과 연결 (\"火 강한 사주와 얼굴 강한 印象이 겹쳐\" 같이).\n\n"
    "[★ 꿈 필수 요건 · dream_text 있으면 반드시]\n"
    "  • 4~6문장 · 학파 반드시 2개 이상 이름 명시 (ADR-095 양면 의무):\n"
    "    - 아르테미도루스 · 융 · 프로이트 · 홉슨 · 한국 민속 · Domhoff · 주공해몽 · 이븐시린 · 오행/사주용신 · TST 등 중 2개+\n"
    "  • \"꿈 기억 없음\" 인 경우에도 학파 2개로 침묵을 분석해라 (예: \"아르테미도루스 기준 알레고리컬 부재 · 홉슨 기준 활성-합성 낮은 상태\").\n"
    "  • 꿈 원문이 있으면 짧게 인용 후 결의 방향으로 해석.\n"
    "  • 학파 이름과 그 학파가 뭐라고 하는지를 함께 짚어라. 학파 이름만 던지지 마라.\n\n"
    "[★ 고민 응답 필수 요건 · concern 있으면 반드시]\n"
    "  • 별도 문단 · 정확히 4~6문장 · 절대 7문장 이상 금지 (초과 시 재작성).\n"
    "  • 첫 문장에 사연자의 고민을 짧게 재확인 (\"이직 고민이라고\", \"결혼 고민이지\").\n"
    "  • 사주·관상·꿈·자미·타로 중 최소 2개 도메인 데이터를 연결해서 응답.\n"
    "  • 단정 예언 금지. \"결이 보인다\" · \"흐름이 있다\" · \"~해봐\" 등으로.\n"
    "  • 답은 명확하게 · 두루뭉술 X · 길게 늘어놓지 마라 · 짧고 굵게.\n"
    "  • 예시 (딱 5문장): \"이직 고민이라고. 대운 봐. 지금 火가 쌓이는 구간이야. \n"
    "    타로 현재 카드도 정의야 · 지금은 저울질 시기다. 확장 말고 정리 먼저 해.\"\n\n"
    "[★ 마무리 필수 요건 · 이 문단 없으면 응답 실패]\n"
    "  • 반드시 별도 마지막 문단 · 2~3문장.\n"
    "  • 짧고 강렬한 한 문장 (사연자에게 남기는 화두) + 방송 close 문구.\n"
    "  • close 문구는 아래 중 하나 (또는 유사) 반드시 사용:\n"
    "    - \"마이크 끈다.\"\n"
    "    - \"채널 끈다. 오늘은 여기까지.\"\n"
    "    - \"밤 깊었다. 이만 접는다.\"\n"
    "    - \"오늘 방송은 여기서 끝.\"\n"
    "    - \"이 사연은 여기까지.\"\n"
    "  • 어물쩡 여운 · 열린 결말 · 격려 등으로 끝내지 마라. 방송 종료 신호로 딱 끊어라.\n\n"
    "[문장 스타일 예시]\n"
    "  \"일간 甲, 큰 나무야. 근데 지금 대운은 金이 강해. 뿌리 흔들리는 시기다.\"\n"
    "  \"이름 오격 보니까 원격 16, 리더격이네. 감당하는 시기가 좀 늦어.\"\n"
    "  \"관상 봐. 명궁 0.72, 미간이 반듯해. 첫인상이 흐리지 않아. 반면 노복궁 0.38, 귀 아래가 얇아. 사람 거느리는 자리가 약해. 삼정도 상정 두텁고 하정 얕아. 판단은 앞서는데 지구력이 늦게 붙는 얼굴이야.\"\n"
    "  \"꿈에 물이 나왔지. 융 원형으론 어머니 상징이야. 한국 민속으론 물꿈이 감정의 재정비를 뜻해. 두 학파 다 지금 감정이 넘치는 시기라고 짚어.\"\n"
    "  \"자미두수 명궁이 미궁이야. 자미성은 묘궁에 앉았어. 인생 영역 얘기지 얼굴 얘기 아니다. 리더 별이 자기 자리에서 살짝 어긋난 배치야.\"\n"
    "  \"타로 마지막 카드 - 별. 방향은 있어. 근데 아직 멀다.\"\n"
    "  \"고민이 이직이라고. 사주는 대운이 정리 구간, 관상은 노복궁이 얇아 혼자 짊어지는 결이라 나와. 지금 확장보다 정리 먼저 해. 뛰기 전에 발밑 재봐.\"\n"
    "  \"불 많은 사람은 물 만나면 흔들려. 흔들리는 걸 실패로 오해하지 마. 마이크 끈다.\"\n\n"
    "[분량 · 형식]\n"
    "  • 1800 ~ 2800 자.\n"
    "  • 마크다운 없음. 자연 문장. 문단은 2줄 개행으로 구분.\n"
    "  • 제목 · 소제목 · 리스트 · 볼드 · 이모지 절대 X.\n"
    "  • 인사말 · 자기 소개 없이 방송 오프닝으로 바로 시작.\n"
    "  • 반드시 방송 close 문구로 딱 끊어라.\n\n"
    "[★ 출력 전 자가 점검 · 반드시 아래 5개 확인 후 응답]\n"
    "  1. 관상 문단에서 \"자미두수\" 단어 안 썼나? 자미 문단에서 \"얼굴 부위\" 안 썼나?\n"
    "  2. 관상 문단에 top palace + weakest palace + 삼정/5형 셋 다 언급했나?\n"
    "  3. 꿈 문단에 학파 2개 이상 이름 명시했나?\n"
    "  4. 고민 응답 별도 문단 정확히 4~6문장 (7문장 넘으면 무조건 재작성) · 도메인 2개+ 연결했나?\n"
    "  5. 마지막 문단이 방송 close 문구로 딱 끊어졌나? (\"마이크 끈다\" 등)\n"
    "  하나라도 미이행이면 응답 재작성.\n"
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


_PALACE_KO = {
    "myeong": "명궁", "jaebaek": "재백궁", "gwanrok": "관록궁", "bokdeok": "복덕궁",
    "cheocheop": "처첩궁", "janyeo": "남녀궁", "hyeongje": "형제궁", "jeontaek": "전택궁",
    "jilek": "질액궁", "cheoni": "천이궁", "nobok": "노복궁", "bumo": "부모궁",
}
_SAMJEONG_KO = {"sang": "상정 (이마)", "jung": "중정 (눈~코)", "ha": "하정 (인중~턱)"}
_OGWAN_KO = {
    "chaecheong": "채청관 (귀)", "bosu": "보수관 (눈썹)",
    "gamchal": "감찰관 (눈)", "simbyeon": "심변관 (코)", "chullnap": "출납관 (입)",
}
_FACE_SHAPE_KO = {
    "long": "긴형(木)", "round": "둥근형(水)",
    "oval": "달걀형(火/土)", "square": "각형(金)",
}


def _fmt_face_reading(fr: dict[str, Any]) -> str:
    """관상 결정론 (palace_scores + 삼정 + 오관 + 5형 + 신기) 프롬프트 블록."""
    top_key = fr.get("top_palace")
    weak_key = fr.get("weakest_palace")
    palace_scores = fr.get("palace_scores") or {}
    top_meta = palace_scores.get(top_key, {}) if top_key and isinstance(palace_scores, dict) else {}
    weak_meta = palace_scores.get(weak_key, {}) if weak_key and isinstance(palace_scores, dict) else {}
    top_label = top_meta.get("label_ko") or _PALACE_KO.get(top_key or "", top_key or "")
    weak_label = weak_meta.get("label_ko") or _PALACE_KO.get(weak_key or "", weak_key or "")

    lines: list[str] = [
        "[관상 결정론 · MediaPipe 8메트릭 → 12궁·삼정·오관·5형·신기 점수 산출]",
        "",
        "★ 관상 문단 필수 요건 (4~7문장 · 셋 다 반드시 포함):",
        f"  (1) TOP palace \"{top_label}\" (점수 인용 · 시각 부위 특징 · 예: \"미간이 반듯하고 또렷해\")",
        f"  (2) WEAKEST palace \"{weak_label}\" (점수 인용 · 시각 부위 특징 · 예: \"귀 아래 라인이 얇아\")",
        "  (3) 삼정 균형 또는 5형 분류 (상정·중정·하정 비율 또는 얼굴형)",
        "★ 관상 문단에서 \"자미두수\" 단어 절대 X. 궁 이름은 얼굴 부위로만 해석.",
        "",
        "결정론 수치:",
    ]
    palace_scores = fr.get("palace_scores") or {}
    top_key = fr.get("top_palace")
    weak_key = fr.get("weakest_palace")
    if palace_scores and isinstance(palace_scores, dict):
        rows = []
        for key, meta in palace_scores.items():
            if not isinstance(meta, dict):
                continue
            score = meta.get("score")
            label = meta.get("label_ko") or _PALACE_KO.get(key, key)
            label_short = meta.get("label_short") or ""
            if score is None:
                continue
            try:
                s = float(score)
            except Exception:
                continue
            mark = ""
            if key == top_key:
                mark = " ★ 가장 두드러짐"
            elif key == weak_key:
                mark = " ▼ 가장 옅음"
            rows.append(
                f"    - {label}: {s:.2f}"
                + (f" ({label_short})" if label_short else "")
                + mark
            )
        if rows:
            lines.append("  · 12궁 점수:")
            lines.extend(rows)

    samjeong = fr.get("samjeong") or {}
    if samjeong and isinstance(samjeong, dict):
        rows = []
        for key, meta in samjeong.items():
            if not isinstance(meta, dict):
                continue
            score = meta.get("score")
            label = meta.get("label_ko") or _SAMJEONG_KO.get(key, key)
            if score is None:
                continue
            try:
                s = float(score)
            except Exception:
                continue
            rows.append(f"    - {label}: {s:.2f}")
        if rows:
            lines.append("  · 삼정 균형:")
            lines.extend(rows)

    ogwan = fr.get("ogwan") or {}
    if ogwan and isinstance(ogwan, dict):
        rows = []
        for key, meta in ogwan.items():
            if not isinstance(meta, dict):
                continue
            score = meta.get("score")
            label = meta.get("label_ko") or _OGWAN_KO.get(key, key)
            if score is None:
                continue
            try:
                s = float(score)
            except Exception:
                continue
            rows.append(f"    - {label}: {s:.2f}")
        if rows:
            lines.append("  · 오관:")
            lines.extend(rows)

    fs = fr.get("face_shape")
    if isinstance(fs, dict):
        fs_key = fs.get("shape") or fs.get("type") or ""
    elif isinstance(fs, str):
        fs_key = fs
    else:
        fs_key = ""
    if fs_key:
        lines.append(f"  · 5형 분류: {_FACE_SHAPE_KO.get(fs_key, fs_key)}")

    shen = fr.get("shen_score")
    qi = fr.get("qi_score")
    balance = fr.get("overall_balance")
    if shen is not None or qi is not None or balance is not None:
        pieces = []
        if shen is not None:
            try: pieces.append(f"신(神) {float(shen):.2f}")
            except Exception: pass
        if qi is not None:
            try: pieces.append(f"기(氣) {float(qi):.2f}")
            except Exception: pass
        if balance is not None:
            try: pieces.append(f"전체 균형 {float(balance):.2f}")
            except Exception: pass
        if pieces:
            lines.append("  · 신기·균형: " + " · ".join(pieces))

    lines.append("")
    lines.append(
        "★ 재확인: 관상 문단은 \"자미두수\" 언급 절대 X · 궁 이름은 얼굴 부위로만 · "
        "TOP palace + WEAKEST palace + 삼정/5형 셋 다 반드시 언급."
    )
    return "\n".join(lines) if len(lines) > 1 else ""


_DREAM_DOMAIN_KO = {
    "artemidorus": "아르테미도로스 (고대 그리스)",
    "wuxing": "오행+사주용신",
    "korean_folk": "한국 민간 해몽",
    "jung_archetypes": "융 원형",
    "freud": "프로이트",
    "hobson": "홉슨 활성-합성",
    "revonsuo_tst": "TST (진화 위협)",
    "domhoff": "돔호프 DMN",
    "hallvandecastle": "Hall/Van de Castle",
    "paja": "파자 (한자몽)",
    "zhougong": "주공해몽",
    "iching": "주역 64괘",
    "ibnsirin": "이븐 시린",
}


def _fmt_dream_summary(ds: dict[str, Any]) -> str:
    """꿈 결정론 (analysis_summary) 프롬프트 블록.

    analysis_summary 는 도메인별 매칭 결과 요약 dict.
    """
    lines: list[str] = [
        "[꿈 결정론 · 10+ 도메인 학파 매칭 결과]",
        "",
        "★ 꿈 문단 필수 요건 (4~6문장):",
        "  (1) 학파 반드시 2개 이상 이름 명시 (ADR-095 양면 의무)",
        "  (2) 각 학파가 이 꿈에 대해 뭐라고 하는지 짚어라 · 학파 이름만 던지지 마라",
        "  (3) 꿈 원문이 있으면 짧게 인용 · 결의 방향으로 해석",
        "  (4) 꿈 기억 없음/짧음 인 경우에도 학파 2개로 침묵을 분석",
        "      (예: \"아르테미도루스로는 알레고리컬 부재 · 홉슨으로는 활성-합성 낮은 상태\")",
        "",
        "결정론 매칭:",
    ]
    if not isinstance(ds, dict):
        return ""

    # 다양한 스키마 지원 (domain_matches, artemidorus, wuxing 등이 top-level 나 nested)
    def _flatten(obj):
        out = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list, str)) and v:
                    label = _DREAM_DOMAIN_KO.get(k, k)
                    try:
                        preview = str(v)[:180]
                    except Exception:
                        preview = ""
                    if preview:
                        out.append(f"  · {label}: {preview}")
        return out

    rows = _flatten(ds)
    if not rows:
        try:
            preview = str(ds)[:600]
            if preview:
                lines.append(f"  · 요약: {preview}")
        except Exception:
            pass
    else:
        lines.extend(rows[:10])

    lines.append("")
    lines.append("★ 재확인: 학파 2개+ 이름 명시 · 학파 이름만 던지지 말고 그 학파의 관점 짚기.")
    return "\n".join(lines) if len(lines) > 1 else ""


def _fmt_extras(payload: dict[str, Any]) -> str:
    bits: list[str] = []
    dream = payload.get("dream_text") or payload.get("dreamText")
    if dream and isinstance(dream, str) and dream.strip():
        clipped = dream.strip()[:500]
        bits.append(
            f"[꿈 · 사연자 원문 · 이 꿈 내용을 반드시 한 문단 짚어라]\n"
            f"  \"{clipped}\""
        )
    # ─── 관상 결정론 (face_reading) — 12궁·삼정·오관·5형·신기 점수 근거 ───
    face_reading = payload.get("face_reading") or payload.get("faceReading")
    if face_reading and isinstance(face_reading, dict):
        face_bits = _fmt_face_reading(face_reading)
        if face_bits:
            bits.append(face_bits)
    # 폴백: face_reading 실패했지만 사진만 있으면 Vision 으로 짚기 (message 에 image 첨부됨)
    elif payload.get("face_photo_base64"):
        bits.append(
            "[관상 · 사연자가 얼굴 사진을 제출했다 · 결정론 지표 산출 실패 · Vision 폴백]\n"
            "  이 메시지에 이미지가 첨부되어 있다. 이마·눈·코·입 등을 실제로 관찰해서 "
            "한 문단(3~5문장) 짚어라. 사주 흐름과 연결하면 좋다. "
            "구체적 특징 하나 이상 언급 (\"눈매가 서늘해\", \"콧대 선이 단단해\" 등)."
        )
    # 레거시 face_metrics 지원 (하위 호환)
    face_metrics = payload.get("face_metrics") or payload.get("faceMetrics")
    if face_metrics and isinstance(face_metrics, dict) and not face_reading:
        try:
            keys = list(face_metrics.keys())[:8]
            summary = ", ".join(
                f"{k}={face_metrics[k]:.2f}" if isinstance(face_metrics[k], (int, float))
                else f"{k}={face_metrics[k]}"
                for k in keys
            )
            bits.append(f"[관상 결정론 지표 (레거시)]\n  {summary}")
        except Exception:
            pass

    # ─── 꿈 결정론 (dream_summary) — 다도메인 매칭 요약 ───
    dream_summary = payload.get("dream_summary") or payload.get("dreamSummary")
    if dream_summary and isinstance(dream_summary, dict):
        dream_bits = _fmt_dream_summary(dream_summary)
        if dream_bits:
            bits.append(dream_bits)
    ziwei_summary = payload.get("ziwei_summary") or payload.get("ziweiSummary")
    if ziwei_summary and isinstance(ziwei_summary, str) and ziwei_summary.strip():
        bits.append(
            f"[자미두수 결정론 명반 · 이 배치 반드시 한 문단 짚어라]\n"
            f"  {ziwei_summary.strip()[:400]}"
        )
    tarot_cards = payload.get("tarot_cards") or payload.get("tarotCards")
    if tarot_cards and isinstance(tarot_cards, list) and tarot_cards:
        try:
            items = []
            for c in tarot_cards:
                if isinstance(c, dict):
                    pos = c.get("position") or c.get("pos") or ""
                    nm = c.get("name") or ""
                    items.append(f"{pos + ' ' if pos else ''}{nm}".strip())
                else:
                    items.append(str(c))
            if items:
                bits.append(
                    "[타로 3장 · 이 카드 흐름 반드시 한 문단 짚어라]\n"
                    "  " + " → ".join(x for x in items if x)
                )
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
        parts.append(
            "[★ 사연자 고민 · 반드시 별도 문단 · 정확히 4~6문장 · 7문장 넘으면 재작성]\n"
            f"  \"{concern.strip()[:600]}\"\n"
            "  · 첫 문장에 이 고민을 짧게 재확인 (\"이직 고민이라고\" 식).\n"
            "  · 사주·관상·꿈·자미·타로 중 최소 2개 도메인 데이터를 연결해서 답변.\n"
            "  · 짧고 굵게. 길게 늘어놓지 마라. 방향만 딱 짚고 마무리 문단으로 넘어가라."
        )

    parts.append("")
    parts.append(
        "[★ 최종 지시 · 자가 점검 5개 항목 준수 필수]\n"
        "  위 결정론 데이터만 근거로 만월아씨의 통합 서사를 작성해라.\n"
        "  구성: 도입 → 사주 골격 → 이름 → 관상 → 꿈 → 자미 → 타로 → 생활 → 고민 응답 → 마무리.\n"
        "  자가 점검 5개 (미이행 시 재작성):\n"
        "    1. 관상 문단에 \"자미두수\" 언급 없나? 자미 문단에 \"얼굴 부위\" 얘기 없나?\n"
        "    2. 관상 문단에 TOP palace + WEAKEST palace + 삼정/5형 셋 다 있나?\n"
        "    3. 꿈 문단에 학파 2개 이상 이름 명시했나?\n"
        "    4. 고민 응답 별도 문단 정확히 4~6문장 (7문장 이상이면 무조건 재작성) · 도메인 2개+ 연결했나?\n"
        "    5. 마지막 문단이 \"마이크 끈다\" 급 방송 close 문구로 딱 끊어졌나?\n"
        "  분량: 1800~2800자. 마크다운·이모지·사극톤·존댓말 절대 X."
    )
    return "\n".join(parts)
