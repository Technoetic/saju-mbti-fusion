"""라이브 손금 API 호출 + backend 확인."""
import base64
import json
import sys
import urllib.request


def main():
    img_path = "D:/palm_dataset/eval_holdout/Hand_0000068.jpg"
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    keypoints = {
        f"kp{i}": [0.15 + (i % 7) * 0.1, 0.15 + (i // 7) * 0.25, 0.0]
        for i in range(21)
    }

    body = {
        "image_base64": b64,
        "hand": "right",
        "metrics": {"keypoints": keypoints, "hand_side_mp": "right"},
    }
    data = json.dumps(body).encode()

    req = urllib.request.Request(
        "https://saju-mbti-fusion.fly.dev/api/palm/reading",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.load(resp)
        block = result.get("deterministic_block", "")
        print("=== deterministic_block ===")
        print(block[:600])
        print("...")
        if "ADR-250 CFM 융합" in block:
            print("\n[OK] ADR-250 CFM 융합 라이브 작동")
        if "CFM" in block:
            print("[OK] CFM 언급 확인")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
