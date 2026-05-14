"""Nano Banana (Gemini 2.5 Flash Image) — 사주/페르소나 일러스트 생성.

Bizrouter 의 OpenAI 호환 엔드포인트로 호출.
응답: choices[0].message.content 가 list — text + image_url(data URL base64).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

# 캐시 디렉토리 — 같은 프롬프트는 재호출 안 함
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "img_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_IMG_MODEL = os.environ.get("BIZROUTER_IMAGE_MODEL", "google/gemini-2.5-flash-image")


def _bizrouter_client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("BIZROUTER_API_KEY"),
        base_url=os.environ.get(
            "BIZROUTER_BASE_URL", "https://api.bizrouter.ai/v1"
        ),
    )


def _extract_image_url(content: Any) -> str | None:
    """LLM 응답 content (list 또는 str) 에서 첫 image_url 추출."""
    if isinstance(content, str):
        m = re.search(r"data:image/[^\s\"]+", content)
        return m.group(0) if m else None
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "image_url":
                    url = (part.get("image_url") or {}).get("url")
                    if url:
                        return url
                elif part.get("type") == "image" and part.get("source"):
                    src = part["source"]
                    if isinstance(src, dict) and src.get("data"):
                        media = src.get("media_type", "image/png")
                        return f"data:{media};base64,{src['data']}"
    return None


def generate_image(prompt: str, *, force: bool = False) -> dict[str, Any]:
    """프롬프트 → 이미지 data URL.

    Returns:
        {"data_url": str, "cached": bool}
    """
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"{key}.txt"
    if cache_file.exists() and not force:
        return {"data_url": cache_file.read_text(encoding="utf-8"), "cached": True}

    client = _bizrouter_client()
    r = client.chat.completions.create(
        model=_IMG_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    content = r.choices[0].message.content
    url = _extract_image_url(content)
    if not url:
        raise RuntimeError("image_url not found in response")
    cache_file.write_text(url, encoding="utf-8")
    return {"data_url": url, "cached": False}


# 카드별 프롬프트 빌더
def prompt_for_persona(alias: dict[str, Any]) -> str:
    """융합 페르소나 일러스트 프롬프트."""
    persona = alias.get("persona") or alias.get("headline") or ""
    return (
        f"동양과 서양이 만나는 미니멀 추상 일러스트. "
        f"주제: '{persona}'. "
        f"스타일: 검은 배경(#0a0a0a), 황금(#e4d44c) 강조선과 도형, "
        f"한국 전통 수묵화 + 모던 기하학 결합. "
        f"인물·텍스트·로고 없음. 16:9 가로 비율. "
        f"고요하고 신비로운 분위기."
    )


def prompt_for_pillar(saju: dict[str, Any]) -> str:
    year = saju.get("year", "")
    month = saju.get("month", "")
    day = saju.get("day", "")
    hour = saju.get("hour", "")
    return (
        f"사주 8글자를 상징하는 동양 추상 일러스트. "
        f"4기둥: {year} / {month} / {day} / {hour}. "
        f"스타일: 검은 배경, 4개의 황금 빛 기둥이 우주 공간에 떠 있는 모습, "
        f"각 기둥에 흐릿한 한자 그림자. 16:9. 인물·로고·실제 텍스트 없음."
    )


def prompt_for_wuxing(wuxing: dict[str, float]) -> str:
    return (
        f"오행(목·화·토·금·수) 균형을 상징하는 추상 일러스트. "
        f"5원소가 원형으로 배치된 미니멀 디자인, 검은 배경, "
        f"각 원소는 부드러운 황금/녹/적/갈/청 음영. 16:9. 텍스트 없음."
    )


def prompt_for_luck(saju: dict[str, Any]) -> str:
    return (
        f"인생의 10년 단위 흐름을 표현하는 동양 추상 일러스트. "
        f"검은 배경에 황금 길이 시간의 곡선처럼 흐르고, "
        f"각 구간마다 별/달의 약한 빛. 16:9. 인물·텍스트 없음."
    )


# 10간 → 인물 외형 모티프 (의상색·분위기)
_STEM_PORTRAIT: dict[str, dict[str, str]] = {
    "甲": {"color": "deep forest green", "feel": "tall and upright, dignified", "element": "tree/wood"},
    "乙": {"color": "soft sage green", "feel": "graceful, flexible, vine-like", "element": "vine/grass"},
    "丙": {"color": "warm crimson", "feel": "radiant, energetic, sun-like presence", "element": "sun/fire"},
    "丁": {"color": "amber orange", "feel": "warm intimate, candle-like glow", "element": "candle/flame"},
    "戊": {"color": "earthy ochre", "feel": "grounded, steady, mountain-like", "element": "mountain/earth"},
    "己": {"color": "soft beige", "feel": "nurturing, gentle, field-like", "element": "field/soil"},
    "庚": {"color": "cool steel gray", "feel": "sharp, refined, blade-like clarity", "element": "metal/steel"},
    "辛": {"color": "pale silver white", "feel": "delicate, jewel-like precision", "element": "jewel/metal"},
    "壬": {"color": "deep navy blue", "feel": "vast, flowing, ocean-like depth", "element": "ocean/water"},
    "癸": {"color": "translucent blue-gray", "feel": "soft, misty, dew-like sensitivity", "element": "dew/mist"},
}

# MBTI → 인물 표정·자세·의상·헤어 통합 힌트 (의상 차별화로 같은 일간도 구분되게)
_MBTI_PORTRAIT: dict[str, str] = {
    "INTJ": "calm calculating gaze, architectural straight posture, sharply tailored minimalist clothing, dark slicked-back hair",
    "INTP": "curious thoughtful eyes, head slightly tilted, layered casual academic outfit, slightly messy intellectual hair",
    "ENTJ": "confident direct stare, commanding upright stance, structured sharp-shouldered formal wear, polished groomed hair",
    "ENTP": "playful sharp expression, dynamic angled stance, bold eclectic mixed-pattern attire, animated tousled hair",
    "INFJ": "deep introspective eyes, quiet still poise, flowing layered modest attire, soft natural hair falling gently",
    "INFP": "dreamy gentle gaze, soft contemplative posture, romantic bohemian flowing clothing, loose wavy hair",
    "ENFJ": "warm engaging smile, open inviting stance, refined sociable attire with warm tones, elegantly arranged hair",
    "ENFP": "bright animated expression, expansive gesture, vibrant colorful eclectic outfit, free-flowing voluminous hair",
    "ISTJ": "steady serious gaze, composed grounded stance, traditional conservative buttoned attire, neatly combed hair",
    "ISFJ": "kind protective expression, gentle modest posture, soft cardigan-layered modest attire, simply pinned natural hair",
    "ESTJ": "firm grounded look, organized squared stance, crisp business formal attire, tightly groomed precise hair",
    "ESFJ": "warm sociable smile, attentive forward-leaning posture, polished classic warm-toned attire, carefully styled hair",
    "ISTP": "cool observant eyes, relaxed neutral stance, practical utilitarian rugged clothing, low-maintenance natural hair",
    "ISFP": "soft artistic gaze, fluid graceful posture, artistic textured handcrafted clothing, loose artistic hair with subtle accent",
    "ESTP": "bold confident smile, dynamic active leaning stance, athletic sleek modern attire, sharp short kinetic hair",
    "ESFP": "vibrant joyful expression, lively dynamic gesture, eye-catching bold patterned clothing, bouncy expressive hair",
}


_GENDER_DESC = {
    "M": "a man",
    "F": "a woman",
    "남": "a man",
    "여": "a woman",
}


def prompt_for_compat(
    score: int,
    grade: str,
    a_day_master: str | None = None,
    b_day_master: str | None = None,
    a_mbti: str | None = None,
    b_mbti: str | None = None,
    a_name_ko: str | None = None,
    b_name_ko: str | None = None,
    a_gender: str | None = None,
    b_gender: str | None = None,
) -> str:
    """두 인물 초상화 프롬프트 — 두 캐릭터를 한 장면에."""
    relation = (
        "facing each other in warm harmony, close intimate distance, mutual gaze"
        if grade in ("최상", "상")
        else "facing each other with subtle tension and quiet attraction, moderate distance"
        if grade == "중"
        else "facing each other with charged tension, contrasting energies, dramatic distance"
    )
    a_stem = _STEM_PORTRAIT.get(a_day_master or "", {
        "color": "neutral tone", "feel": "balanced presence", "element": "unspecified",
    })
    b_stem = _STEM_PORTRAIT.get(b_day_master or "", {
        "color": "neutral tone", "feel": "balanced presence", "element": "unspecified",
    })
    a_mbti_hint = _MBTI_PORTRAIT.get((a_mbti or "").upper(), "thoughtful expression")
    b_mbti_hint = _MBTI_PORTRAIT.get((b_mbti or "").upper(), "thoughtful expression")

    a_gd = _GENDER_DESC.get((a_gender or "").upper(), "a person")
    b_gd = _GENDER_DESC.get((b_gender or "").upper(), "a person")
    grade_en = {
        "최상": "highest",
        "상": "high",
        "중": "moderate",
        "하": "low",
        "최하": "lowest",
    }.get(grade, "moderate")

    # 같은 일간이면 색상 톤을 미세하게 어긋나게 + MBTI 차별성 강조
    same_stem = bool(a_day_master) and a_day_master == b_day_master
    if same_stem:
        a_color = f"{a_stem['color']} in cool dark shade"
        b_color = f"{b_stem['color']} in warm light shade"
        differentiation = (
            f" CRITICAL: although both share the same {a_stem['element']} element, "
            f"the two MUST look visually distinct through their MBTI-driven clothing style, "
            f"hair style, and posture. Avoid making them look like twins or wearing matching outfits."
        )
    else:
        a_color = a_stem["color"]
        b_color = b_stem["color"]
        differentiation = ""

    return (
        f"CRITICAL: pure visual scene only. NO TEXT of any kind in the image — "
        f"no Korean Hangul, no Chinese Hanja characters, no Latin letters, no numbers, "
        f"no captions, no titles, no logos, no watermarks, no signs, no UI elements. "
        f"The entire frame is pictorial.\n\n"
        f"Cinematic photorealistic double portrait of two distinct Korean characters "
        f"in 16:9 ratio against a pure deep black backdrop with subtle golden particle accents. "
        f"Person A on the LEFT is {a_gd} wearing {a_color} attire reflecting "
        f"{a_stem['element']} energy. A's appearance: {a_stem['feel']}, {a_mbti_hint}. "
        f"Person B on the RIGHT is {b_gd} wearing {b_color} attire reflecting "
        f"{b_stem['element']} energy. B's appearance: {b_stem['feel']}, {b_mbti_hint}. "
        f"They are {relation}, expressing a {grade_en} grade compatibility between them."
        f"{differentiation} "
        f"Subtle visual motifs of each element ({a_stem['element']} vs {b_stem['element']}) "
        f"swirl softly behind each person as atmospheric texture (no symbols, no glyphs). "
        f"Korean traditional + modern hybrid aesthetic, sharp focus, 85mm lens equivalent, "
        f"moody volumetric lighting, highly detailed faces and clothing. "
        f"Reminder: completely text-free composition."
    )


_COMPAT_PORTRAIT_SYSTEM = (
    "You are a visual director for a Korean character compatibility portrait illustration.\n"
    "Output a single English prompt paragraph (100~160 words) for an image generation model.\n\n"
    "STRUCTURE: Begin the prompt with a strong CAPITALIZED no-text directive in the FIRST\n"
    "sentence, then describe the visual scene, then repeat the no-text directive at the end.\n\n"
    "REQUIREMENTS:\n"
    "  • Depict TWO distinct human characters in one cinematic double portrait, 16:9 ratio.\n"
    "  • Person A on the LEFT, Person B on the RIGHT. Both clearly visible.\n"
    "  • **GENDER IS MANDATORY**: When input lists gender (M/남=man, F/여=woman),\n"
    "    state the gender of each person explicitly in the prompt body. Never omit it.\n"
    "  • **NEVER INCLUDE RAW HANJA OR HANGUL IN THE PROMPT BODY** — image models often\n"
    "    paint these into the picture as text. Always translate day-master to its English\n"
    "    element name (甲=Wood, 乙=Vine-Wood, 丙=Sun-Fire, 丁=Candle-Fire, 戊=Mountain-Earth,\n"
    "    己=Field-Earth, 庚=Metal, 辛=Jewel-Metal, 壬=Ocean-Water, 癸=Mist-Water). MBTI\n"
    "    codes (INFJ, ENFP, etc.) should be described as cognitive style in English words,\n"
    "    not as letter codes.\n"
    "  • Reflect each person's element (color, attire, atmospheric motif) and MBTI\n"
    "    cognitive style (expression, posture, gaze) using English descriptive language only.\n"
    "  • **MBTI MUST drive visual differentiation**: clothing style, hair style, posture,\n"
    "    and accessories must clearly differ between the two characters according to MBTI.\n"
    "    Map: N (intuitive) = flowing/abstract textures vs S (sensing) = practical/concrete;\n"
    "    T (thinking) = structured/geometric vs F (feeling) = soft/warm; J (judging) =\n"
    "    polished/orderly vs P (perceiving) = relaxed/dynamic. The two characters MUST NOT\n"
    "    look like twins or wear matching outfits — describe distinct clothing for each.\n"
    "  • Compatibility grade shapes relational geometry:\n"
    "      - 최상/상: facing each other, warm intimate distance, mutual gaze.\n"
    "      - 중: quarter-turned, moderate distance, subtle attraction.\n"
    "      - 하/최하: contrasting angles, charged dramatic distance, tension.\n"
    "  • Aesthetic: cinematic photorealistic Korean style, deep black backdrop, gold particles,\n"
    "    85mm lens look, moody volumetric lighting, sharp focus.\n"
    "  • Do NOT specify exact age.\n"
    "  • **ABSOLUTELY NO TEXT in the rendered image**: no Hangul, no Hanja, no Latin letters,\n"
    "    no numbers, no captions, no logos, no titles, no watermarks, no symbols overlaid on\n"
    "    the scene. State this constraint in BOTH the opening and closing of the prompt.\n\n"
    "Output the prompt body only, no preamble or markdown."
)


_PROMPT_AGENT_SYSTEM = (
    "당신은 동양 사주·MBTI·이름 융합 캐릭터의 일러스트 프롬프트를 작성하는 "
    "비주얼 디렉터입니다. 다음 규칙을 반드시 따르세요:\n"
    "  • 출력은 영어 또는 한국어로 60~120 단어, 한 단락 평문.\n"
    "  • 색상: 검은 배경 (#0a0a0a) + 황금 강조 (#e4d44c) + 보조 1~2색 한정.\n"
    "  • 스타일: 한국 전통 수묵화 + 모던 미니멀 기하학 결합, 추상.\n"
    "  • 인물·실제 텍스트·로고·서구식 캐릭터 금지.\n"
    "  • 사주 일간(자연 원소), 강한 오행, MBTI 인지 기능, 이름의 음령오행 등 "
    "    입력된 데이터를 시각 모티프로 자연스럽게 녹여낼 것.\n"
    "  • 비율은 16:9 가로.\n"
    "최종 출력은 프롬프트 본문만 출력하고 다른 설명·인사·markdown 금지."
)


def _agent_prompt(kind: str, context: dict[str, Any]) -> str:
    """프롬프트 에이전트 (Gemini 2.5 Flash Lite) 가 작성한 일러스트 프롬프트.

    compat: 두 인물 초상 전용 시스템 프롬프트 사용.
    그 외: 추상 일러스트 시스템 프롬프트 사용.
    실패 시 결정론적 fallback 으로 자동 회귀.
    """
    from engine.llm_sync import call_llm_sync

    kind_brief = {
        "persona": "융합 페르소나 (사주 + MBTI + 이름) 전체를 한 장면으로 상징",
        "pillar": "사주 4기둥(8글자)을 우주 공간의 4기둥으로 추상화",
        "wuxing": "오행 5원소 균형/편중을 원형 구도로 시각화",
        "luck": "10년 단위 대운의 흐름을 시간의 곡선/길로 표현",
        "compat": "Double portrait of two characters with their saju + MBTI energies",
    }.get(kind, "사주 결과 추상 일러스트")

    user = (
        f"[Visualization subject] {kind_brief}\n\n"
        f"[Input data]\n"
        + "\n".join(f"  • {k}: {v}" for k, v in context.items() if v)
        + "\n\nOutput the prompt only."
    )
    system = (
        _COMPAT_PORTRAIT_SYSTEM if kind == "compat" else _PROMPT_AGENT_SYSTEM
    )
    try:
        text = call_llm_sync(user_text=user, system_prompt=system)
        return (text or "").strip().strip('"').strip("'")
    except Exception:
        return ""


def smart_prompt(kind: str, context: dict[str, Any]) -> str:
    """프롬프트 에이전트 → 실패 시 결정론적 fallback."""
    agent_text = _agent_prompt(kind, context)
    if agent_text and len(agent_text) > 20:
        return agent_text
    # fallback
    if kind == "persona":
        return prompt_for_persona({"persona": context.get("persona", "")})
    if kind == "pillar":
        return prompt_for_pillar(context)
    if kind == "wuxing":
        return prompt_for_wuxing(context)
    if kind == "luck":
        return prompt_for_luck(context)
    if kind == "compat":
        return prompt_for_compat(
            context.get("score", 50),
            context.get("grade", "중"),
            a_day_master=context.get("a_day_master"),
            b_day_master=context.get("b_day_master"),
            a_mbti=context.get("a_mbti"),
            b_mbti=context.get("b_mbti"),
            a_name_ko=context.get("a_name_ko"),
            b_name_ko=context.get("b_name_ko"),
            a_gender=context.get("a_gender"),
            b_gender=context.get("b_gender"),
        )
    return f"동양 추상 일러스트, 검은 배경, 황금 강조, 미니멀, {kind}"


_CRITIC_SYSTEM = (
    "당신은 사주·동양 미학 일러스트 평가 에이전트입니다. 1~10 점.\n"
    "  1. 미학 — 검은 배경 + 황금 강조 + 미니멀 동양\n"
    "  2. 추상성 — 인물·실제 텍스트·로고·워터마크 없으면 만점\n"
    "  3. 사주 정합 — 입력 컨텍스트가 시각 모티프로 반영\n"
    "  4. 구도 — 한 점 집중·산만하지 않음\n\n"
    "판정: 총점 ≥ 28 이고 추상성 ≥ 7 → PASS, 그 외 FAIL.\n"
    "비율 16:9 미세 어긋남·색감 미세 차이는 감점 사유 아님 (통과).\n\n"
    "정확히 한 줄로 출력:\n"
    "  PASS|FAIL | aesthetic=N | abstract=N | saju_fit=N | composition=N | total=N/40 | reason=1문장"
)


_COMPAT_CRITIC_SYSTEM = (
    "You evaluate a Korean compatibility double-portrait illustration. Score each 1~10.\n"
    "  1. aesthetic — cinematic photorealistic, deep black backdrop + golden accents, "
    "moody volumetric lighting\n"
    "  2. two_characters — TWO distinct human characters clearly visible "
    "(A on left, B on right). Both faces and figures present. No single-person image.\n"
    "  3. gender_match — if the input context lists a_gender / b_gender (M=man, F=woman, "
    "남=man, 여=woman), the depicted gender of A and B must match exactly. "
    "If both are the same gender when input said one M + one F, that is a critical failure.\n"
    "  4. differentiation — A and B should NOT look like twins. Their clothing style, hair, "
    "and overall silhouette should clearly differ based on their MBTI types. Matching outfits, "
    "same hair, or near-identical posture = low score. Even when the two share the same "
    "saju day-master element, MBTI must drive visible visual difference.\n\n"
    "AUTOMATIC FAIL (set passed=FAIL) if ANY of these are present:\n"
    "  • Any visible text inside the image (Korean 한글, Latin letters, numbers, captions, titles)\n"
    "  • Any logo or watermark\n"
    "  • Gender mismatch when gender was specified in input\n"
    "  • Only one person visible (single portrait)\n"
    "  • The two characters look like twins (matching outfits + matching hair + same posture)\n\n"
    "Otherwise PASS only if total ≥ 28 AND two_characters ≥ 7 AND gender_match ≥ 7 "
    "AND differentiation ≥ 6.\n\n"
    "Output exactly one line:\n"
    "  PASS|FAIL | aesthetic=N | two_characters=N | gender_match=N | differentiation=N | total=N/40 | reason=1 sentence"
)


def critique_image(data_url: str, context: dict[str, Any]) -> dict[str, Any]:
    """이미지 적대적 평가 (Vision LLM).

    context에 두 사람 키(a_day_master·b_day_master 등)가 있으면 compat 전용 critic 사용.
    """
    from engine.llm_sync import bizrouter_client

    is_compat = any(
        k in context for k in ("a_day_master", "b_day_master", "a_mbti", "b_mbti")
    )
    critic_system = _COMPAT_CRITIC_SYSTEM if is_compat else _CRITIC_SYSTEM

    client = bizrouter_client()
    ctx_lines = "\n".join(f"  • {k}: {v}" for k, v in context.items() if v)
    text_part = (
        f"[Input context]\n{ctx_lines or '(none)'}\n\n"
        f"Evaluate the image above per the system rubric. Output one line only."
    )
    try:
        r = client.chat.completions.create(
            model=os.environ.get("BIZROUTER_MODEL", "google/gemini-2.5-flash-lite"),
            messages=[
                {"role": "system", "content": critic_system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_part},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            max_tokens=400,
        )
        verdict = (r.choices[0].message.content or "").strip()
        if isinstance(verdict, list):
            verdict = " ".join(
                part.get("text", "") for part in verdict if isinstance(part, dict)
            )
        first_line = verdict.splitlines()[0] if verdict else ""
        import re as _re
        m = _re.search(r"total\s*=\s*(\d+)", first_line)
        total = int(m.group(1)) if m else None
        passed = first_line.upper().startswith("PASS")
        if is_compat:
            m_two = _re.search(r"two_characters\s*=\s*(\d+)", first_line)
            two_char = int(m_two.group(1)) if m_two else None
            m_gen = _re.search(r"gender_match\s*=\s*(\d+)", first_line)
            gen_match = int(m_gen.group(1)) if m_gen else None
            m_diff = _re.search(r"differentiation\s*=\s*(\d+)", first_line)
            diff = int(m_diff.group(1)) if m_diff else None
            if (
                not passed
                and total is not None
                and total >= 28
                and (two_char is None or two_char >= 7)
                and (gen_match is None or gen_match >= 7)
                and (diff is None or diff >= 6)
            ):
                passed = True
        else:
            m_abs = _re.search(r"abstract\s*=\s*(\d+)", first_line)
            abstract = int(m_abs.group(1)) if m_abs else None
            if not passed and total is not None and total >= 28 and (abstract is None or abstract >= 7):
                passed = True
        return {"passed": passed, "verdict": first_line[:300], "total": total}
    except Exception as e:
        return {"passed": True, "verdict": f"(critic 실패, 통과 처리: {e})", "total": None}


_TEXT_GATE_SYSTEM = (
    "You are an OCR gate. Look at the image and answer in exactly one line:\n"
    "  TEXT_PRESENT | YES_OR_NO | brief detail\n"
    "Return YES if you see ANY of: Korean Hangul, Chinese Hanja, Japanese characters, "
    "Latin letters, numbers, captions, titles, logos, watermarks, signs, or any rendered\n"
    "glyph or written symbol on the image. Stylized brush strokes that do NOT form readable\n"
    "characters are NO. When in doubt, lean YES."
)


def detect_image_text(data_url: str) -> dict[str, Any]:
    """OCR 게이트 — 이미지에 글자가 있는지 검출.

    Returns: {has_text: bool, detail: str}
    """
    from engine.llm_sync import bizrouter_client

    client = bizrouter_client()
    try:
        r = client.chat.completions.create(
            model=os.environ.get("BIZROUTER_MODEL", "google/gemini-2.5-flash-lite"),
            messages=[
                {"role": "system", "content": _TEXT_GATE_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is there any text/character on this image?"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            max_tokens=100,
        )
        verdict = (r.choices[0].message.content or "").strip()
        if isinstance(verdict, list):
            verdict = " ".join(
                p.get("text", "") for p in verdict if isinstance(p, dict)
            )
        first_line = verdict.splitlines()[0] if verdict else ""
        has_text = "YES" in first_line.upper().split("|")[1] if "|" in first_line else False
        return {"has_text": bool(has_text), "detail": first_line[:200]}
    except Exception as e:
        # 검출 실패 시 안전한 쪽으로 — 통과 처리 (critic이 한 번 더 봄)
        return {"has_text": False, "detail": f"(text gate 실패: {e})"}


def generate_image_with_critic(
    prompt: str, context: dict[str, Any], *, max_rounds: int = 2
) -> dict[str, Any]:
    """1차 생성 → 평가 → FAIL 시 프롬프트 보강 재생성.

    compat (사람 두 명)와 그 외 (추상)는 재생성 가이드가 다름.
    compat은 추가로 OCR 게이트로 텍스트 발견 시 자동 FAIL.
    """
    is_compat = any(
        k in context for k in ("a_day_master", "b_day_master", "a_mbti", "b_mbti")
    )
    prompts_used: list[str] = []
    critic_history: list[dict[str, Any]] = []
    current_prompt = prompt
    last_result: dict[str, Any] | None = None

    for round_idx in range(1, max_rounds + 1):
        prompts_used.append(current_prompt)
        result = generate_image(current_prompt, force=(round_idx > 1))
        last_result = result
        critique = critique_image(result["data_url"], context)

        # OCR 게이트 — compat 에서 텍스트 발견 시 critic 결과를 덮어쓴다
        if is_compat:
            gate = detect_image_text(result["data_url"])
            critique["text_gate"] = gate
            if gate["has_text"]:
                critique["passed"] = False
                critique["verdict"] = (
                    f"FAIL (OCR gate) | text detected: {gate['detail']} | "
                    + (critique.get("verdict") or "")
                )[:300]

        critic_history.append({"round": round_idx, **critique})
        if critique["passed"]:
            break

        # 재생성 가이드 — compat은 인물 보존, 그 외는 인물 금지
        if is_compat:
            current_prompt = (
                "CRITICAL FIX: completely remove ALL text, captions, hanja, hangul, "
                "Latin letters, numbers, logos, watermarks from the image. "
                "Pure visual scene only. Keep the two characters and gender as before.\n\n"
                + current_prompt
            )
        else:
            current_prompt = (
                current_prompt
                + "\nFix issues from review: "
                + (critique.get("verdict") or "")
                + ". Strictly avoid people, real text, logos, purple gradients, Western character art."
            )

    return {
        **(last_result or {}),
        "prompts": prompts_used,
        "critic_history": critic_history,
        "rounds": len(critic_history),
    }


__all__ = [
    "generate_image",
    "generate_image_with_critic",
    "critique_image",
    "prompt_for_persona",
    "prompt_for_pillar",
    "prompt_for_wuxing",
    "prompt_for_luck",
    "prompt_for_compat",
    "smart_prompt",
]
