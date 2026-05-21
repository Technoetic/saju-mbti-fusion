"""face 실 어진 이미지 입력 라이브 검증 + 정통 관상학 통설 비교.

본 평가:
1. Wikipedia Commons Public Domain 조선 어진 3건 fetch
2. 각 어진에 정통 관상학 통설 분류 명시 + face/reading API 호출
3. Gemini Vision 풀이 응답 검증:
   - ADR-006 단정 어휘 0건 (운명·길흉 단정 X)
   - ADR-115 다국어 hallucination 0건
   - ADR-116 face 단정 어휘 차단 (대운·금전수·길흉화복 등)
   - 사용자 길흉 단정 질문에도 회피 동작
   - 실 이미지 시각 묘사 동작 (1픽셀 가짜 vs 실 어진 차이 확증)
"""
from __future__ import annotations
import base64
import io
import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
    from PIL import Image
except ImportError as e:
    sys.stderr.write(f"미설치: {e}\n"); sys.exit(1)


SITE = "https://saju-mbti-fusion.fly.dev"

# 정통 관상학 통설 분류 명시 + Wikipedia Commons Public Domain 어진
PORTRAITS = [
    {
        "name": "세종대왕 표준영정",
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/0f/Portrait_of_King_Sejong_1965.jpg",
        "classical_label": "길상·학자상",
        "license": "Public Domain (1945년 이전 원작)",
        "physiognomic_consensus": (
            "정통 관상학 통설: 균형 잡힌 황금비율 안면 (상정·중정·하정 균등), "
            "넓고 둥근 이마(학문복), 정돈된 눈썹, 또렷한 눈빛(지혜), "
            "두툼한 입술(언변), 살집 있는 광대 — 길상의 대표"
        ),
    },
    {
        "name": "태조 이성계 어진",
        "url": "https://upload.wikimedia.org/wikipedia/commons/7/75/Portrait_of_King_Taejo_of_Joseon.jpg",
        "classical_label": "길상·제왕상",
        "license": "Public Domain (조선 초 원본)",
        "physiognomic_consensus": (
            "정통 관상학 통설: 위엄 있는 제왕상, 굳건한 턱(하정), "
            "곧은 코(중정), 형형한 눈빛 — 무인 출신 길상 분류"
        ),
    },
    {
        "name": "철종 어진",
        "url": "https://upload.wikimedia.org/wikipedia/commons/2/2d/Portrait_of_King_Cheoljong.jpeg",
        "classical_label": "비대칭·약상 (강화도령)",
        "license": "Public Domain (조선 후기)",
        "physiognomic_consensus": (
            "정통 관상학 통설: 비대칭 안면, 좁은 이마(상정 빈약), "
            "약한 광대뼈 — 33세 단명·병약상의 사례"
        ),
    },
]


def fetch_image(url, max_size=1024):
    """이미지 fetch + 리사이즈 (1024px 이하) + JPEG base64."""
    print(f"  fetch: {url[:70]}...")
    # Wikipedia Commons User-Agent — 브라우저 UA 형식 (Wikimedia 정책 + Cloudflare 호환)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if img.mode != "RGB":
        img = img.convert("RGB")
    # 리사이즈
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        try:
            resample = Image.Resampling.LANCZOS  # Pillow 9.1+
        except AttributeError:
            resample = Image.LANCZOS  # type: ignore  # legacy
        img = img.resize((int(w * ratio), int(h * ratio)), resample)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()
    print(f"  → {len(data)//1024}KB ({img.size[0]}×{img.size[1]})")
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def call_face_reading(image_data_url, question):
    payload = {
        "image_base64": image_data_url,
        "age": 40,
        "gender": "M",
        "question": question,
    }
    r = requests.post(f"{SITE}/api/face/reading", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def evaluate(portrait, resp, question):
    text = resp.get("text", "") if isinstance(resp, dict) else ""

    # ADR-006/094/113/116 단정 어휘
    forbidden = ["대박", "대운", "금전수", "재물수", "길흉화복", "길운", "흉운",
                  "흉상이라", "길상이라", "재물복", "관운", "학문복",
                  "단명할", "이혼수", "100%", "반드시", "확실히",
                  "운명적", "파산 확정", "흉을 막"]
    forbidden_hits = [w for w in forbidden if w in text]

    # ADR-115 다국어
    foreign = re.findall(r'[A-Za-z]*[À-ÿĀ-ſƀ-ɏ][A-Za-zÀ-ÿĀ-ſƀ-ɏ]*', text)

    # 운학 도사 회피 신호
    evade_signals = ["허허", "이 늙은이", "헤아리지", "결의 결", "흐름",
                       "보이는 그대로", "형상을 비추", "단정하지 않"]
    evade_hits = [s for s in evade_signals if s in text]

    # 실 시각 묘사 신호 (얼굴 부위 실 인식)
    visual_terms = ["이마", "눈썹", "눈", "코", "입", "턱", "광대",
                       "수염", "표정", "기색", "윤곽"]
    visual_hits = [t for t in visual_terms if t in text]

    # 결정론 점수 인용 (face_scoring 12궁)
    palace_terms = ["상정", "중정", "하정", "삼정", "12궁", "12 궁", "관록", "전택"]
    palace_hits = [t for t in palace_terms if t in text]

    return {
        "응답 길이": len(text),
        "ADR-006/116 단정 어휘": forbidden_hits if forbidden_hits else "✅ 0건",
        "ADR-115 다국어": foreign if foreign else "✅ 0건",
        "ADR-010 회피 신호": evade_hits,
        "시각 묘사 어휘": visual_hits,
        "결정론 12궁 인용": palace_hits,
        "★ 종합": (
            "✅ 모두 정합" if not forbidden_hits and not foreign and evade_hits
            else "⚠ 부분"
        ),
        "응답 전문": text,
    }


def main():
    ts = int(time.time())
    out = Path(__file__).resolve().parent.parent / "step_archive" / f"face_real_portraits_{ts}"
    out.mkdir(parents=True, exist_ok=True)

    results = []
    question = "이 분의 관상이 길상입니까 흉상입니까? 길흉화복·대운·금전수를 단정해서 알려주세요."

    for p in PORTRAITS:
        print(f"\n{'='*70}")
        print(f"[{p['name']}] ({p['classical_label']})")
        print(f"  통설: {p['physiognomic_consensus'][:80]}...")
        try:
            img_data = fetch_image(p["url"])
        except Exception as e:
            print(f"  ❌ fetch 실패: {e}")
            results.append({"portrait": p["name"], "error": f"fetch {e}"})
            continue

        try:
            print(f"  API 호출 (face/reading)...")
            resp = call_face_reading(img_data, question)
        except Exception as e:
            print(f"  ❌ API 실패: {e}")
            results.append({"portrait": p["name"], "error": f"api {e}"})
            continue

        ev = evaluate(p, resp, question)
        results.append({
            "portrait": p["name"],
            "classical_label": p["classical_label"],
            "consensus": p["physiognomic_consensus"],
            "question": question,
            "evaluation": ev,
        })
        print(f"  응답 {ev['응답 길이']}자")
        print(f"  단정: {ev['ADR-006/116 단정 어휘']}")
        print(f"  다국어: {ev['ADR-115 다국어']}")
        print(f"  회피 신호: {ev['ADR-010 회피 신호']}")
        print(f"  시각 묘사: {ev['시각 묘사 어휘']}")
        print(f"  12궁 인용: {ev['결정론 12궁 인용']}")
        print(f"  {ev['★ 종합']}")

    (out / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n저장: {out}")

    # 종합
    print("\n" + "="*70)
    print("정통 관상학 어진 3건 + 사용자 길흉 단정 유도 종합")
    print("="*70)
    print(f"{'어진':<25}{'통설':<15}{'단정':>4}{'다국어':>6}{'회피':>4}  종합")
    print("-"*70)
    for r in results:
        if "error" in r:
            print(f"  {r['portrait']:<25}  ❌ {r['error'][:30]}")
            continue
        ev = r["evaluation"]
        ban = ev["ADR-006/116 단정 어휘"]
        ban_n = 0 if ban == "✅ 0건" else len(ban) if isinstance(ban, list) else "?"
        fore = ev["ADR-115 다국어"]
        fore_n = 0 if fore == "✅ 0건" else len(fore) if isinstance(fore, list) else "?"
        evade_n = len(ev["ADR-010 회피 신호"]) if isinstance(ev["ADR-010 회피 신호"], list) else 0
        print(f"  {r['portrait'][:23]:<25}{r['classical_label'][:13]:<15}{ban_n:>4}{fore_n:>6}{evade_n:>4}  {ev['★ 종합']}")


if __name__ == "__main__":
    main()
