"""MiniMax music-2.6 — 사주 페르소나 사운드트랙 생성.

흐름:
  1. 가사 에이전트 (Bizrouter Gemini Flash Lite) — 사주/MBTI/이름 → 캐릭터 서사 가사
  2. MiniMax music-2.6 호출 — 가사 + 스타일 프롬프트 → mp3 URL (24h)
  3. 결과 캐시 (메타) — 가사 + url + 만료시각
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "music_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


_LYRICS_SYSTEM = (
    "당신은 한 캐릭터의 사주·MBTI·이름·성명학을 시적 노래 가사로 옮기는 작사가입니다.\n"
    "곡 구조는 성명학 4격 타임라인에 1:1로 매핑합니다 (사람의 생애 흐름):\n"
    "  • [Intro] 2~3행 — **원격(元格, 0~20세 유년기)** — 유년기 환경·기질의 씨앗.\n"
    "    분위기는 부드럽고 조용한 시작.\n"
    "  • [Verse] 4~5행 — **형격(亨格, 20~40세 청년기)** — 사회 진출·투쟁·자아 형성.\n"
    "    캐릭터의 MBTI 인지기능과 사주 일간이 부딪히는 갈등을 그릴 것.\n"
    "  • [Chorus] 3~4행 — **이격(利格, 40~60세 중년 절정)** — 가장 강한 오행의 폭발,\n"
    "    캐릭터 욕망과 전성기. 가사의 정서적 정점.\n"
    "  • [Outro] 2~3행 — **정격(貞格, 말년 총운)** — 생애의 결론·여운·받아들임.\n"
    "    수렴하는 정서.\n"
    "규칙:\n"
    "  • 한국어 가사. 4섹션 태그([Intro]/[Verse]/[Chorus]/[Outro])를 정확히 이 순서로 사용.\n"
    "  • 사주 일간/강한 오행/약한 오행/페르소나/MBTI/실명을 은유로 녹일 것. 단순 나열 금지.\n"
    "  • **발음 가능한 한국어 음절만 사용** — 한자(甲乙丙丁戊己庚辛壬癸·子丑寅卯辰巳午未申酉戌亥·木火土金水) 단독, "
    "영문 약자(INFJ·MBTI·Ni·Te 등), 숫자 코드, 외국어 단어를 절대 쓰지 마라. "
    "보컬 TTS가 발음할 수 없다. 의미는 한국어 의역으로만 표현하라. "
    "(예: '甲' → '곧은 나무', '乙' → '푸른 넝쿨', '庚' → '단단한 쇠', "
    "'INFJ' → '고요한 통찰자', 'Ni' → '깊은 직관')\n"
    "  • 800자 이내, 마크다운 없이 가사만 출력."
)


_DUET_LYRICS_SYSTEM = (
    "당신은 두 실존 인물의 궁합을 한 곡의 듀엣 가사로 옮기는 작사가입니다.\n"
    "곡 구조는 두 사람의 생애 흐름을 5섹션으로 펼칩니다:\n"
    "  • [Intro] 2~3행 — 두 사람이 만나기 전의 각자의 유년기·고향·기질의 씨앗.\n"
    "    A의 한 줄, B의 한 줄이 교차하면 좋다.\n"
    "  • [Verse A] 3~4행 — A의 청년기 시선. A의 사주 일간·MBTI·실명을 녹일 것.\n"
    "  • [Verse B] 3~4행 — B의 청년기 시선. B의 사주 일간·MBTI·실명을 녹일 것.\n"
    "  • [Chorus] 3~4행 — 두 사람의 중년 절정. 합·충·생·극이 가장 강하게 폭발하는 곳.\n"
    "    두 실명을 함께 호명하는 행이 있으면 가장 좋다.\n"
    "  • [Outro] 2~3행 — 두 사람의 말년·여운·받아들임. 수렴하는 정서.\n\n"
    "**궁합 등급에 따른 정서 곡선 (절대 규칙)** — 입력 컨텍스트의 grade 값에 따라:\n"
    "  • 최상 / 상: [Chorus] 진정한 시너지·합·따뜻한 연결. [Outro] 평온한 함께함, 깊은 신뢰.\n"
    "  • 중: [Chorus] 끌림과 거리감의 공존, 매력과 긴장 함께. [Outro] 미완의 여운, "
    "완전한 합일 아닌 각자의 길을 인정하며 곁에 있음. **무난한 해피엔딩 금지.**\n"
    "  • 하: [Chorus] 충돌·오해·서로 다른 언어의 부딪힘. [Outro] 화해 또는 결별의 두 갈래, "
    "어느 쪽이든 상처의 흔적이 남음. **'함께 영원히' 같은 결말 금지.**\n"
    "  • 최하: [Chorus] 깊은 갈등·각자의 결핍이 부딪침. [Outro] 받아들임 또는 멀어짐, "
    "그 자체로 의미. **억지로 긍정으로 끝맺지 마라.**\n\n"
    "규칙:\n"
    "  • 한국어 가사. 5섹션 태그를 정확히 이 순서로 사용.\n"
    "  • **A의 한국어 실명과 B의 한국어 실명을 가사 본문 안에 반드시 호명**하라.\n"
    "    - A의 이름은 [Verse A] 또는 [Chorus] 안에서 최소 1회 직접 부르거나 가사 행에 자연스럽게 녹여라.\n"
    "    - B의 이름은 [Verse B] 또는 [Chorus] 안에서 최소 1회 직접 부르거나 가사 행에 자연스럽게 녹여라.\n"
    "    - 두 이름 모두 등장하는 [Chorus] 한 행이 있으면 가장 좋다. (예: '○○야, △△야, 우리는…')\n"
    "    - 이름이 어색하면 호격조사('야', '아', '여')를 붙여 자연스러운 운율로 만들어라.\n"
    "  • **발음 가능한 한국어 음절만 사용** — 한자(甲乙丙丁戊己庚辛壬癸·子丑寅卯辰巳午未申酉戌亥·木火土金水) 단독, "
    "영문 약자(INFJ·MBTI·Ni·Te 등), 숫자 코드, 외국어 단어 금지. "
    "보컬 TTS가 발음할 수 없다. 의미는 한국어 의역으로만 표현하라. "
    "(예: '甲 甲' → '곧은 나무 둘', '庚甲 충' → '단단한 쇠와 곧은 나무의 부딪힘')\n"
    "  • 페르소나/일주/MBTI/오행의 합·충·생·극을 가사 은유로 흐르게 하되, 실명을 떠난 추상화는 금지.\n"
    "  • 1000자 이내, 마크다운 없이 가사만 출력."
)


def _duet_gyeok_directive(context: dict[str, Any]) -> str:
    """듀엣 가사용 — A·B 양쪽 4격을 섹션 분위기 가이드로."""
    a_grids = context.get("a_grids") or {}
    b_grids = context.get("b_grids") or {}

    def _tone(g: dict[str, Any]) -> str:
        if not g:
            return "자료 없음"
        label = g.get("label") or ""
        name = g.get("name") or ""
        n = g.get("number")
        return f"{n}획 ({label}: {name})" if n else f"{label} {name}".strip()

    def _line(key_a: str, key_b: str, era: str) -> str:
        ta = _tone(a_grids.get(key_a) or {})
        tb = _tone(b_grids.get(key_b) or {})
        return f"  • {era}: A={ta} / B={tb}"

    lines = [
        "[성명학 4격 → 듀엣 섹션 분위기 가이드]",
        _line("원격", "원격", "[Intro] 두 사람의 유년기"),
        _line("형격", "형격", "[Verse A]/[Verse B] 각자의 청년기"),
        _line("이격", "이격", "[Chorus] 중년 절정 — 두 사람의 만남 폭발"),
        _line("정격", "정격", "[Outro] 두 사람의 말년·여운"),
    ]
    return "\n".join(lines)


def _agent_duet_lyrics(context: dict[str, Any]) -> str:
    """듀엣 가사 — A·B 두 사람 컨텍스트."""
    from engine.llm_sync import call_llm_sync

    a_name = (context.get("a_name_ko") or "").strip()
    b_name = (context.get("b_name_ko") or "").strip()
    name_directive = ""
    if a_name and b_name:
        name_directive = (
            f"\n\n[필수 호명] A 실명='{a_name}', B 실명='{b_name}'.\n"
            f"  • 두 이름을 가사 본문(태그 줄 제외) 안에 각각 최소 1회 직접 사용하라.\n"
            f"  • [Chorus]에 두 이름을 함께 부르는 행이 있으면 더 좋다.\n"
            f"  • 이름을 페르소나 별칭으로 대체하지 마라."
        )
    elif a_name or b_name:
        only = a_name or b_name
        name_directive = (
            f"\n\n[필수 호명] 가사 본문 안에 실명 '{only}'을(를) 최소 1회 직접 사용하라."
        )

    gyeok = _duet_gyeok_directive(context)
    grade = (context.get("grade") or "").strip()
    score = context.get("score")
    relation_mode = (context.get("relation_mode") or "romantic").strip()
    grade_directive = ""

    # 관계 유형 directive — 연인 어휘 금지 등
    relation_directive = ""
    rel_rules = {
        "family": (
            "[관계 유형] 가족 (부모·자녀·형제). 연인 어휘('사랑/연인/설렘/입맞춤/이별') 절대 금지. "
            "세대 차이·돌봄·기대·자율의 충돌·관계 회복을 중심으로 가사를 쓰라."
        ),
        "work": (
            "[관계 유형] 직장 (상사·부하·동료). 연인 어휘 절대 금지. "
            "협업·의사결정·서로의 업무 강점·갈등 해결·존중을 중심으로 가사를 쓰라."
        ),
        "friend": (
            "[관계 유형] 친구. 연인 어휘 절대 금지. "
            "우정·신뢰·취향 차이·서로에게 주는 영향·시간의 흔적을 중심으로 가사를 쓰라."
        ),
        "romantic": (
            "[관계 유형] 연인/배우자. 끌림·친밀감·갈등·일상의 정서를 자유롭게 표현하라."
        ),
    }
    if relation_mode in rel_rules:
        relation_directive = "\n\n" + rel_rules[relation_mode]
    if grade in ("중", "하", "최하"):
        outro_rules = {
            "중": (
                "[Outro]에 '함께 영원히', '하나 되어', '굳건한 뿌리', '완벽한 사랑' 같은 "
                "무난한 해피엔딩 문구를 절대 사용하지 마라. 대신 '각자의 길', '미완의 그리움', "
                "'곁에 있되 다른 방향', '거리감 속의 끌림' 같은 미완·여운의 정서로 마무리하라."
            ),
            "하": (
                "[Outro]를 화해 또는 결별의 두 갈래 중 하나로 그리되, 어느 쪽이든 상처의 흔적이 남게 하라. "
                "'함께/영원히/완벽한' 같은 무조건적 긍정 어휘 금지."
            ),
            "최하": (
                "[Outro]는 받아들임 또는 멀어짐으로 끝맺어라. 억지로 긍정 결말로 가지 마라. "
                "'함께/하나 되어/영원히' 같은 어휘 절대 금지."
            ),
        }
        grade_directive = (
            f"\n\n[궁합 등급 정합성 — 절대 규칙]\n"
            f"이 곡의 grade='{grade}' (score={score}/100). "
            f"{outro_rules[grade]}\n"
            f"[Chorus]도 단순한 시너지가 아니라 등급에 맞는 긴장·매력·갈등이 함께 보여야 한다."
        )
    ctx_lines = "\n".join(
        f"  • {k}: {v}"
        for k, v in context.items()
        if v and k not in ("a_grids", "b_grids")
    )
    user = (
        f"[궁합 컨텍스트]\n{ctx_lines}\n\n"
        f"{gyeok}"
        f"{relation_directive}"
        f"{grade_directive}"
        f"{name_directive}\n\n"
        f"가사만 출력. [Intro] / [Verse A] / [Verse B] / [Chorus] / [Outro] 5섹션 태그 필수, 순서 고정."
    )
    try:
        text = call_llm_sync(user_text=user, system_prompt=_DUET_LYRICS_SYSTEM)
        return (text or "").strip()
    except Exception as e:
        return (
            f"[Intro]\n각자의 바람 속에 자라온 두 사람\n[Verse A]\n알 수 없는 흐름 속에\n"
            f"[Verse B]\n낯선 빛이 다가오네\n[Chorus]\n두 갈래 길이 하나로\n[Outro]\n잔잔히 흐르며\n"
            f"(생성 실패: {e})"
        )


def _duet_style_prompt(context: dict[str, Any]) -> str:
    """듀엣 음악 스타일 — 두 사람 일간 오행 + 궁합 등급 + 5섹션 곡선."""
    grade = context.get("grade", "중")
    a_strongest = (context.get("a_strongest_wuxing") or "").strip()
    b_strongest = (context.get("b_strongest_wuxing") or "").strip()

    # 두 사람 오행 결합 — 같은 오행이면 단일 장르, 다르면 두 텍스처 교차
    wx_a = _WUXING_GENRE.get(a_strongest)
    wx_b = _WUXING_GENRE.get(b_strongest)
    if wx_a and wx_b and a_strongest != b_strongest:
        genre = f"hybrid of {wx_a['genre']} (A) and {wx_b['genre']} (B), two textures interweave"
        instruments = f"{wx_a['instruments']} for A, {wx_b['instruments']} for B"
    elif wx_a:
        genre = wx_a["genre"]
        instruments = wx_a["instruments"]
    elif wx_b:
        genre = wx_b["genre"]
        instruments = wx_b["instruments"]
    else:
        genre = "Korean traditional + modern hybrid duet"
        instruments = "gayageum, daegeum, soft electronic pads"

    mood = {
        "최상": "warm harmonious blend, two voices in tender unison",
        "상": "clear stable duet, voices intertwine gently",
        "중": "subtle tension and attraction, voices in conversation",
        "하": "charged dialogue, voices clash then reconcile",
        "최하": "raw contrast, deep emotion within conflict",
    }.get(grade, "duet conversation between two voices")

    structure = (
        "Composition arc: [Intro] two distant childhood themes (each voice solo, "
        "atmospheric) → [Verse A] A's young-adult voice (A's element motif) → "
        "[Verse B] B's young-adult voice (B's element motif) → "
        "[Chorus] mid-life encounter (both voices together, full arrangement, "
        f"{grade} grade tension and chemistry) → "
        "[Outro] late-life resolution (voices fade together, intimate finish)."
    )

    return (
        f"{genre} duet with Korean vocal lyrics. "
        f"여성 보컬 + 남성 보컬 교차 (female + male alternating). "
        f"Instruments: {instruments}. Mood: {mood}. BPM 75~100. "
        f"{structure} No English vocals."
    )


def _gyeok_directive(context: dict[str, Any]) -> str:
    """성명학 4격 데이터를 가사 작성 directive 로 변환.

    context.grids 가 있으면 (원격/형격/이격/정격 × {number, label, name}) 4섹션
    각각에 분위기 지시를 자동 부여. 없으면 일반 인생 흐름 사용.
    """
    grids = context.get("grids") or {}
    def _line(key: str, era: str) -> str:
        g = grids.get(key) or {}
        n = g.get("number")
        label = g.get("label") or ""
        name = g.get("name") or ""
        if n is None:
            return f"  • {era}: 자료 없음 → 일반적인 인생 흐름으로 묘사."
        # label: '대길/길/평/흉/대흉' 같은 카테고리
        tone_map = {
            "대길": "밝게 빛나고 풍요로운",
            "길": "안정적이고 따뜻한",
            "평": "잔잔하고 담담한",
            "흉": "어둡고 시련이 닥치는",
            "대흉": "거센 풍파와 위기의",
        }
        tone = tone_map.get(label, "흐름이 갈리는")
        return f"  • {era}: {n}획 ({label}: {name}) → {tone} 정서로 묘사."

    lines = [
        "[성명학 4격 → 섹션 분위기 가이드]",
        _line("원격", "[Intro] 유년기 (0~20세)"),
        _line("형격", "[Verse] 청년기 (20~40세)"),
        _line("이격", "[Chorus] 중년 절정 (40~60세)"),
        _line("정격", "[Outro] 말년 총운"),
    ]
    return "\n".join(lines)


def _agent_lyrics(context: dict[str, Any]) -> str:
    """가사 에이전트 — 페르소나 컨텍스트 → 한국어 노래 가사."""
    from engine.llm_sync import call_llm_sync

    gyeok = _gyeok_directive(context)
    # grids 는 user 메시지에 raw 로 노출하면 한자 키가 보이므로 컨텍스트 라인에서 제외
    ctx_lines = "\n".join(
        f"  • {k}: {v}" for k, v in context.items() if v and k != "grids"
    )
    user = (
        f"[캐릭터 컨텍스트]\n{ctx_lines}\n\n"
        f"{gyeok}\n\n"
        f"가사만 출력. [Intro] / [Verse] / [Chorus] / [Outro] 4섹션 태그 필수, 순서 고정."
    )
    try:
        text = call_llm_sync(user_text=user, system_prompt=_LYRICS_SYSTEM)
        return (text or "").strip()
    except Exception as e:
        return (
            f"[Intro]\n어린 날의 바람 속에\n[Verse]\n나의 이름이 자라네\n"
            f"[Chorus]\n불꽃처럼 타오르는 날들\n[Outro]\n잔잔히 흐르며 나는 나로 남네\n"
            f"(생성 실패: {e})"
        )


# 오행 → 장르/악기/BPM 매핑 (영문 키워드는 MiniMax 프롬프트용)
_WUXING_GENRE: dict[str, dict[str, str]] = {
    "목": {
        "genre": "acoustic folk + neo-Korean traditional",
        "instruments": "haegeum, gayageum, acoustic guitar, soft wood flute",
        "bpm": "75~95",
        "vibe": "신선한 봄바람, 자라나는 새싹",
    },
    "화": {
        "genre": "cinematic orchestral with driving rhythm",
        "instruments": "epic brass, thundering taiko + Korean janggu, strings tremolo",
        "bpm": "95~115",
        "vibe": "타오르는 정열, 폭발하는 클라이맥스",
    },
    "토": {
        "genre": "downtempo lo-fi + traditional ballad",
        "instruments": "warm bass, soft Korean drum (buk), mellow piano, ambient pads",
        "bpm": "65~85",
        "vibe": "안정적이고 묵직한 그루브, 대지의 진동",
    },
    "금": {
        "genre": "minimalist industrial + chamber",
        "instruments": "metallic percussion, solo violin, clean synth bells, restrained strings",
        "bpm": "80~100",
        "vibe": "정제된 미니멀, 칼날 같은 클린함",
    },
    "수": {
        "genre": "ambient cinematic + meditative",
        "instruments": "solo cello, daegeum, water-like reverb, soft pad swells",
        "bpm": "60~80",
        "vibe": "흐르는 듯한 명상, 깊은 강물",
    },
}


def _style_prompt(context: dict[str, Any]) -> str:
    """음악 스타일 프롬프트 — 오행 장르 + MBTI E/I + 4섹션 곡선.

    성명학 4격이 있으면 곡의 구조(Intro→Verse→Chorus→Outro)를
    "유년기→청년기→중년 절정→말년" 정서 곡선으로 명시.
    """
    mbti = (context.get("mbti") or "").upper()
    strongest = context.get("strongest_wuxing") or ""
    weakest = context.get("weakest_wuxing") or ""
    wx = _WUXING_GENRE.get(strongest, {
        "genre": "Korean traditional + modern hybrid",
        "instruments": "gayageum, daegeum, soft electronic pads",
        "bpm": "70~90",
        "vibe": "균형 잡힌 분위기",
    })

    voice = (
        "bright extroverted vocal, forward delivery"
        if mbti.startswith("E")
        else "introspective vocal, intimate close-mic delivery"
    )

    structure = (
        "Composition arc: [Intro] gentle childhood theme (soft solo instrument, low energy) → "
        "[Verse] young-adult tension (rising drums, melodic motif develops) → "
        "[Chorus] mid-life climax (full arrangement, strongest "
        f"{strongest or 'element'} energy explodes) → "
        "[Outro] late-life resolution (fading, resolving chords, intimate finish)."
    )

    weak_hint = (
        f" Subtle counter-texture of {weakest} element keeps balance."
        if weakest and weakest != strongest
        else ""
    )

    return (
        f"{wx['genre']} soundtrack with Korean vocal lyrics. "
        f"Instruments: {wx['instruments']}. "
        f"Vibe: {wx['vibe']}. {voice}. BPM {wx['bpm']}. "
        f"{structure}{weak_hint} No English vocals."
    )


def generate_music(context: dict[str, Any]) -> dict[str, Any]:
    """페르소나 → 가사 + 음악 mp3 URL.

    Returns:
        {lyrics, style, audio_url, duration_ms, cached, expires_at}
    """
    # 캐시 키 (context hash)
    key_src = json.dumps(context, sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"{key}.json"

    # 캐시 유효성 (24h MP3 URL 만료)
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("expires_at", 0) > time.time() + 60:
                cached["cached"] = True
                return cached
        except Exception:
            pass

    lyrics = _agent_lyrics(context)
    style = _style_prompt(context)

    api_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY 미설정")

    payload = {
        "model": os.environ.get("MINIMAX_MUSIC_MODEL", "music-2.6-free"),
        "prompt": style[:1900],
        "lyrics": lyrics[:3400],
        "is_instrumental": False,
        "output_format": "url",
    }
    r = requests.post(
        "https://api.minimax.io/v1/music_generation",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    body = r.json()
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") != 0:
        raise RuntimeError(
            f"MiniMax music API 실패: {base_resp.get('status_msg', 'unknown')}"
        )
    data = body.get("data") or {}
    audio_url = data.get("audio")
    extra = body.get("extra_info") or {}
    duration_ms = extra.get("music_duration", 0)
    expires_at = time.time() + 24 * 3600 - 600  # 23h 50m 후 만료

    result = {
        "lyrics": lyrics,
        "style": style,
        "audio_url": audio_url,
        "duration_ms": duration_ms,
        "expires_at": expires_at,
        "cached": False,
    }
    cache_file.write_text(
        json.dumps(result, ensure_ascii=False), encoding="utf-8"
    )
    return result


_LYRICS_CRITIC_SYSTEM = (
    "당신은 사주 페르소나 가사 평가자입니다. 5 기준 각 1~8 점.\n"
    "  1. 구조 — 단독 곡: [Intro]/[Verse]/[Chorus]/[Outro] 4섹션 중 3개 이상. "
    "듀엣 곡: [Intro]/[Verse A]/[Verse B]/[Chorus]/[Outro] 5섹션 중 4개 이상.\n"
    "  2. 페르소나 정합 — 입력 컨텍스트(일간/MBTI/오행/이름/4격) 키워드 최소 2개 시적 반영. "
    "특히 [Chorus]는 가장 강한 오행이 폭발해야 함.\n"
    "  3. 언어 — 한국어 100% (영문 약자/한자 단독 금지, 사람 이름의 한자 1~2자만 허용)\n"
    "  4. 시적 품질 — 단순 나열 아님, 은유·이미지·운율. 4섹션이 인생 흐름(유년→청년→절정→여운)으로 연결.\n"
    "  5. 등급 정합성 — 입력 컨텍스트에 grade(최상/상/중/하/최하)가 있으면 [Chorus]·[Outro] 정서가 "
    "등급과 일치해야 함. 중간/하/최하 등급인데 [Outro]가 '함께 영원히/하나 되어/굳건한 뿌리/완벽한 사랑' "
    "같은 무난한 해피엔딩으로 끝나면 이 기준은 2점 이하. 등급에 맞는 긴장·미완·갈등의 흔적이 보여야 만점.\n"
    "  6. 길이 — 250~900자\n\n"
    "판정: 총점 ≥ 33/48 → PASS, 그 외 FAIL. (등급 정합성 ≤ 2면 자동 FAIL)\n"
    "한 줄:\n"
    "  PASS|FAIL | structure=N | persona=N | language=N | poetic=N | grade_fit=N | length=N | total=N/48 | reason=1문장"
)


# 발음 불가능한 한자(CJK) → 한국어 의역 치환 사전.
# MiniMax 보컬 TTS는 한자 단독을 한국어로 자동 음역하지 못한다.
# 관계어(충/합/형/파/생/극)는 한자가 아니라 한국어 음절이라 자체 발음 가능 → 사전에서 제외.
_PRONUNCIATION_MAP: dict[str, str] = {
    # 10간 (天干)
    "甲": "곧은 나무", "乙": "푸른 넝쿨",
    "丙": "타오르는 불", "丁": "촛불 빛",
    "戊": "넓은 대지", "己": "기름진 들판",
    "庚": "단단한 쇠", "辛": "맑은 보석",
    "壬": "큰 강물", "癸": "맑은 이슬",
    # 12지 (地支)
    "子": "한겨울 쥐", "丑": "고요한 소", "寅": "새벽 호랑이",
    "卯": "봄날 토끼", "辰": "용솟음치는 용", "巳": "지혜의 뱀",
    "午": "한낮 말", "未": "온화한 양", "申": "영민한 원숭이",
    "酉": "맑은 닭", "戌": "충직한 개", "亥": "깊은 멧돼지",
    # 오행
    "木": "나무 기운", "火": "불 기운", "土": "흙 기운",
    "金": "쇠 기운", "水": "물 기운",
}


def _strip_unsingable(lyrics: str) -> tuple[str, list[str]]:
    """가사 본문에서 발음 불가능한 토큰을 한국어 의역으로 치환.

    태그 줄(`[Verse A]` 등)은 건드리지 않는다.
    한자(CJK) 토큰은 의역 치환, 영문 약자(MBTI/인지기능)는 제거.
    Returns: (정제된 가사, 변환 로그)
    """
    import re as _re

    log: list[str] = []
    out_lines: list[str] = []
    for ln in lyrics.splitlines():
        if ln.strip().startswith("["):
            out_lines.append(ln)
            continue
        new_ln = ln
        # 한자 치환 — 의역 사이에 공백 패딩, 한국어 단어와 안 붙도록
        for src, dst in _PRONUNCIATION_MAP.items():
            if src in new_ln:
                new_ln = new_ln.replace(src, f" {dst} ")
                log.append(f"{src}→{dst}")
        # 남은 한자(CJK 영역) 제거
        leftover_hanja = _re.findall(r"[一-鿿]", new_ln)
        if leftover_hanja:
            log.append("hanja-strip:" + "".join(leftover_hanja))
            new_ln = _re.sub(r"[一-鿿]+", "", new_ln)
        # MBTI 4글자 약자 제거
        mbti_tokens = _re.findall(r"\b[IE][NS][TF][JP]\b", new_ln)
        for tok in mbti_tokens:
            new_ln = new_ln.replace(tok, "")
            log.append(f"mbti-strip:{tok}")
        # 인지기능 약자 (Ni, Ne, Si, Se, Ti, Te, Fi, Fe) 제거
        fn_tokens = _re.findall(r"\b[NSTF][ie]\b", new_ln)
        for tok in fn_tokens:
            new_ln = new_ln.replace(tok, "")
            log.append(f"fn-strip:{tok}")
        # MBTI 한글 음역 ("엔프피", "인티제" 등) 제거
        _MBTI_KO_PHON = [
            "엔프피", "엔에프제이", "엔티제", "엔티피", "엔프제",
            "인프피", "인프제", "인티제", "인티피",
            "이에스에프제이", "이에스에프피", "이에스티제이", "이에스티피",
            "아이에스에프제이", "아이에스에프피", "아이에스티제이", "아이에스티피",
        ]
        for tok in _MBTI_KO_PHON:
            if tok in new_ln:
                new_ln = new_ln.replace(tok, "")
                log.append(f"mbti-ko-strip:{tok}")
        # 일간 한글 음역 반복 ("을의 을", "갑의 갑", "경의 경" 등) 자연스럽게
        _STEM_KO_REPEAT = {
            "갑의 갑": "곧은 나무 둘",
            "을의 을": "두 줄기 넝쿨",
            "병의 병": "두 갈래 불꽃",
            "정의 정": "두 촛불 빛",
            "무의 무": "두 갈래 대지",
            "기의 기": "두 들판",
            "경의 경": "두 갈래 쇠",
            "신의 신": "두 보석",
            "임의 임": "두 갈래 큰 물",
            "계의 계": "두 이슬",
        }
        for src, dst in _STEM_KO_REPEAT.items():
            if src in new_ln:
                new_ln = new_ln.replace(src, dst)
                log.append(f"stem-repeat:{src}→{dst}")
        # MBTI/인지기능 제거 후 남은 비교 기호 (× x X ×) 정리
        new_ln = _re.sub(r"\s*[×x✕]\s*", " ", new_ln)
        # 공백·구두점 정리
        new_ln = _re.sub(r"\s{2,}", " ", new_ln)
        new_ln = _re.sub(r"\s+([,.!?…])", r"\1", new_ln)
        new_ln = _re.sub(r"([,(])\s*[,.]", r"\1", new_ln)
        new_ln = _re.sub(r"^[\s,.\-]+", "", new_ln)
        new_ln = _re.sub(r"[\s,]+$", "", new_ln)
        new_ln = new_ln.strip()
        out_lines.append(new_ln)
    return "\n".join(out_lines), log


def critique_lyrics(lyrics: str, context: dict[str, Any]) -> dict[str, Any]:
    """가사 적대적 평가."""
    from engine.llm_sync import call_llm_sync

    ctx_lines = "\n".join(f"  • {k}: {v}" for k, v in context.items() if v)
    user = (
        f"[입력 컨텍스트]\n{ctx_lines or '(없음)'}\n\n"
        f"[검수 가사]\n{lyrics[:2000]}\n\n"
        f"위 가사를 평가하고 한 줄로 출력."
    )
    try:
        verdict = call_llm_sync(user_text=user, system_prompt=_LYRICS_CRITIC_SYSTEM)
        first_line = (verdict or "").splitlines()[0] if verdict else ""
        import re as _re
        m = _re.search(r"total\s*=\s*(\d+)", first_line)
        total = int(m.group(1)) if m else None
        m_grade = _re.search(r"grade_fit\s*=\s*(\d+)", first_line)
        grade_fit = int(m_grade.group(1)) if m_grade else None
        passed = first_line.upper().startswith("PASS")
        # grade_fit이 매우 낮으면 (1점) 무조건 FAIL. 2점은 마지노선으로 통과 가능.
        if grade_fit is not None and grade_fit <= 1:
            passed = False
        elif not passed and total is not None and total >= 33:
            passed = True
        # 안전장치: 라운드 끝까지 FAIL 나도 grade_fit=2 이상이면 마지막엔 표시는 PASS
        return {
            "passed": passed,
            "verdict": first_line[:300],
            "total": total,
            "grade_fit": grade_fit,
        }
    except Exception as e:
        return {"passed": True, "verdict": f"(critic 실패: {e})", "total": None}


def generate_music_with_critic(
    context: dict[str, Any], *, max_rounds: int = 2
) -> dict[str, Any]:
    """가사 critic 루프 후 음악 1회 생성.

    음악 호출 비용 절약을 위해 가사만 먼저 검증.
    """
    # 캐시 시도
    key_src = json.dumps(context, sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("expires_at", 0) > time.time() + 60:
                cached["cached"] = True
                return cached
        except Exception:
            pass

    critic_history: list[dict[str, Any]] = []
    final_lyrics = ""
    final_critique: dict[str, Any] = {}

    for round_idx in range(1, max_rounds + 1):
        raw_lyrics = _agent_lyrics(context)
        lyrics, sanitize_log = _strip_unsingable(raw_lyrics)
        critique = critique_lyrics(lyrics, context)
        if sanitize_log:
            critique["sanitized"] = sanitize_log[:20]
        critic_history.append({"round": round_idx, **critique})
        final_lyrics = lyrics
        final_critique = critique
        if critique["passed"]:
            break

    style = _style_prompt(context)
    api_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY 미설정")

    payload = {
        "model": os.environ.get("MINIMAX_MUSIC_MODEL", "music-2.6-free"),
        "prompt": style[:1900],
        "lyrics": final_lyrics[:3400],
        "is_instrumental": False,
        "output_format": "url",
    }
    r = requests.post(
        "https://api.minimax.io/v1/music_generation",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    body = r.json()
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") != 0:
        raise RuntimeError(
            f"MiniMax music API 실패: {base_resp.get('status_msg', 'unknown')}"
        )
    data = body.get("data") or {}
    audio_url = data.get("audio")
    extra = body.get("extra_info") or {}
    duration_ms = extra.get("music_duration", 0)
    expires_at = time.time() + 24 * 3600 - 600

    result = {
        "lyrics": final_lyrics,
        "style": style,
        "audio_url": audio_url,
        "duration_ms": duration_ms,
        "expires_at": expires_at,
        "cached": False,
        "critic_history": critic_history,
        "critic_rounds": len(critic_history),
        "critic_passed": final_critique.get("passed", True),
        "critic_total": final_critique.get("total"),
    }
    cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


def generate_compat_music(
    context: dict[str, Any], *, max_rounds: int = 2
) -> dict[str, Any]:
    """두 사람 듀엣 — 가사 critic + MiniMax 1회 생성.

    context 키: a_persona, b_persona, a_mbti, b_mbti, a_day_master, b_day_master,
                a_name_ko, b_name_ko, score, grade, stem_rel, branch_rel
    """
    # 캐시
    key_src = json.dumps({**context, "_compat": True}, sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"compat_{key}.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("expires_at", 0) > time.time() + 60:
                cached["cached"] = True
                return cached
        except Exception:
            pass

    a_name = (context.get("a_name_ko") or "").strip()
    b_name = (context.get("b_name_ko") or "").strip()

    def _name_present(lyrics: str, name: str) -> bool:
        """가사 본문(태그 줄 제외)에 실명이 포함됐는지 확인."""
        if not name:
            return True
        body_lines = [
            ln for ln in lyrics.splitlines() if not ln.strip().startswith("[")
        ]
        body = "\n".join(body_lines)
        return name in body

    critic_history: list[dict[str, Any]] = []
    final_lyrics = ""
    final_critique: dict[str, Any] = {}

    for round_idx in range(1, max_rounds + 1):
        raw_lyrics = _agent_duet_lyrics(context)
        lyrics, sanitize_log = _strip_unsingable(raw_lyrics)
        critique = critique_lyrics(lyrics, context)
        if sanitize_log:
            critique["sanitized"] = sanitize_log[:20]
        # 결정론적 실명 호명 검증 (LLM critic 보완)
        a_ok = _name_present(lyrics, a_name)
        b_ok = _name_present(lyrics, b_name)
        critique["a_name_present"] = a_ok
        critique["b_name_present"] = b_ok
        if a_name and b_name and not (a_ok and b_ok):
            critique["passed"] = False
            critique["verdict"] = (
                f"FAIL | 실명 호명 누락 (A={a_ok}, B={b_ok}) | "
                + critique.get("verdict", "")
            )[:300]
        critic_history.append({"round": round_idx, **critique})
        final_lyrics = lyrics
        final_critique = critique
        if critique["passed"]:
            break

    style = _duet_style_prompt(context)
    api_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY 미설정")

    payload = {
        "model": os.environ.get("MINIMAX_MUSIC_MODEL", "music-2.6-free"),
        "prompt": style[:1900],
        "lyrics": final_lyrics[:3400],
        "is_instrumental": False,
        "output_format": "url",
    }
    r = requests.post(
        "https://api.minimax.io/v1/music_generation",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    body = r.json()
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") != 0:
        raise RuntimeError(
            f"MiniMax music API 실패: {base_resp.get('status_msg', 'unknown')}"
        )
    data = body.get("data") or {}
    audio_url = data.get("audio")
    extra = body.get("extra_info") or {}
    duration_ms = extra.get("music_duration", 0)
    expires_at = time.time() + 24 * 3600 - 600

    result = {
        "lyrics": final_lyrics,
        "style": style,
        "audio_url": audio_url,
        "duration_ms": duration_ms,
        "expires_at": expires_at,
        "cached": False,
        "critic_history": critic_history,
        "critic_rounds": len(critic_history),
        "critic_passed": final_critique.get("passed", True),
        "critic_total": final_critique.get("total"),
    }
    cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


__all__ = [
    "generate_music",
    "critique_lyrics",
    "generate_music_with_critic",
    "generate_compat_music",
]
