"""nano-banana API 응답 형식 확인 — 작은 테스트."""
import base64
import json
import os
import sys
from pathlib import Path
from urllib import request

API_KEY = "sk-br-v1-ab47dd953c844611a9dda14f3a60fa54_uE2bL5jqIHgfnYnvP7pSxieymu10ORU9I_H-Gn7aCgU"
BASE = "https://api.bizrouter.ai/v1"
MODEL = "google/gemini-2.5-flash-image"

IMG = Path("front/media/saju_webtoon/p6.jpg")
if not IMG.exists():
    print("p6.jpg not found", file=sys.stderr)
    sys.exit(1)

raw = IMG.read_bytes()
print(f"image size: {len(raw)/1024:.1f} KB", file=sys.stderr)
b64 = base64.b64encode(raw).decode("ascii")
data_url = f"data:image/jpeg;base64,{b64}"

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "이 웹툰 페이지의 빈 갈색 박스에 '안녕하세요'라고 한국어로 글자를 그려 넣어주세요. 흰 타원 안에는 '반갑습니다'라고 넣어주세요. 박스와 타원의 위치·모양은 그대로 유지하고, 글자만 깔끔하게 가운데 정렬해서 그려주세요."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ],
    "max_tokens": 16384,
}

req = request.Request(
    f"{BASE}/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
)

try:
    with request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(2)

data = json.loads(body)
# 구조 요약 출력
print("=== Response top-level keys ===")
print(list(data.keys()))
print()
print("=== usage ===")
print(json.dumps(data.get("usage"), indent=2))
print()

choices = data.get("choices", [])
if choices:
    msg = choices[0].get("message", {})
    print("=== choices[0].message keys ===")
    print(list(msg.keys()))
    content = msg.get("content")
    if isinstance(content, str):
        print(f"\ncontent (string, {len(content)} chars):")
        print(content[:500])
    elif isinstance(content, list):
        print(f"\ncontent (list, {len(content)} items):")
        for i, item in enumerate(content):
            t = item.get("type") if isinstance(item, dict) else None
            if t == "text":
                print(f"  [{i}] text: {item.get('text','')[:200]}")
            elif t == "image_url":
                url = item.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    print(f"  [{i}] image_url: data URL ({len(url)} chars), starts: {url[:80]}...")
                    # 디코드 + 저장
                    if "," in url:
                        head, b64part = url.split(",", 1)
                        try:
                            img_bytes = base64.b64decode(b64part)
                            outp = Path("_test_nanobanana_out.png")
                            outp.write_bytes(img_bytes)
                            print(f"      → saved to {outp} ({len(img_bytes)/1024:.1f} KB)")
                        except Exception as e:
                            print(f"      decode failed: {e}")
                else:
                    print(f"  [{i}] image_url: {url[:200]}")
            else:
                print(f"  [{i}] {t}: {json.dumps(item)[:200]}")
    else:
        print(f"\ncontent (other type {type(content).__name__}): {str(content)[:300]}")
else:
    print("no choices")

# Bizrouter 가 별도 image field 줄 수도 있음
for k in ("images", "image", "media"):
    if k in data:
        print(f"\nextra key '{k}': {str(data[k])[:300]}")
