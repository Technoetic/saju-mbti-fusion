"""ADR-273 — 관상 시각화 오버레이.

전통 한국·중국 관상학 기준 12궁(十二宮) + 5악(五嶽) 영역 표시.

학술 출처:
  - 麻衣相法 (마의상법, 송대 진박)
  - 柳莊相法 (유장상법, 명대)
  - 神相全編 (신상전편)

12궁:
  명궁(命宮)      — 미간 중앙
  재백궁(財帛宮)  — 코 (재물)
  형제궁(兄弟宮)  — 눈썹
  전택궁(田宅宮)  — 눈썹과 눈 사이
  남녀궁(男女宮)  — 와잠 (눈 아래)
  노복궁(奴僕宮)  — 턱 좌우
  처첩궁(妻妾宮)  — 눈꼬리 (어미)
  질액궁(疾厄宮)  — 산근 (콧대 시작)
  천이궁(遷移宮)  — 이마 양옆
  관록궁(官祿宮)  — 이마 정중앙
  복덕궁(福德宮)  — 미간 위
  부모궁(父母宮)  — 이마 위 좌우

5악:
  남악(이마), 동악(좌광대), 서악(우광대), 중악(코), 북악(턱)

ADR 정합: ADR-006/010 관상 단정 어휘 X, 형태 메타만.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass

import numpy as np


# MediaPipe Face Landmarker 478 keypoint 중 시각화에 사용하는 핵심
KP_INDEX = {
    "forehead_top": 10,    # 발제
    "chin": 152,           # 턱끝
    "brow_l_inner": 55,    # 좌측 눈썹 안쪽
    "brow_r_inner": 285,   # 우측 눈썹 안쪽
    "nose_tip": 1,         # 코끝
    "nose_bridge": 6,      # 산근 (콧대 시작)
    "eye_l_outer": 33,     # 좌측 눈꼬리
    "eye_r_outer": 263,    # 우측 눈꼬리
    "eye_l_inner": 133,    # 좌측 눈머리
    "eye_r_inner": 362,    # 우측 눈머리
    "face_left": 234,      # 얼굴 좌측 가장자리
    "face_right": 454,     # 얼굴 우측 가장자리
    "alar_left": 49,       # 좌측 콧방울
    "alar_right": 279,     # 우측 콧방울
    "mouth_l": 61,         # 입꼬리 좌
    "mouth_r": 291,        # 입꼬리 우
    "lip_upper": 13,
    "lip_lower": 14,
    "under_eye_l": 145,    # 좌측 와잠
    "under_eye_r": 374,    # 우측 와잠
    "glabella": 168,       # 미간
    "brow_l_peak": 105,    # 좌 눈썹 정점
    "brow_r_peak": 334,    # 우 눈썹 정점
    "brow_l_outer": 70,    # 좌 눈썹 바깥쪽
    "brow_r_outer": 300,   # 우 눈썹 바깥쪽
}

# 12궁 색상 (R, G, B)
PALACE_COLORS = {
    "명궁":   (220, 60, 60),     # 빨강 (생명력)
    "재백궁": (255, 165, 0),     # 주황 (재물)
    "관록궁": (60, 100, 200),    # 파랑 (직업)
    "복덕궁": (180, 120, 200),   # 보라 (복)
    "처첩궁": (240, 140, 170),   # 분홍 (배우자)
    "남녀궁": (100, 180, 100),   # 녹색 (자녀)
    "형제궁": (200, 180, 100),   # 노랑 (형제)
    "전택궁": (120, 200, 180),   # 청록 (집)
    "노복궁": (160, 140, 120),   # 갈색 (부하)
    "천이궁": (140, 180, 220),   # 하늘 (이동)
    "부모궁": (200, 100, 140),   # 자홍 (부모)
    "질액궁": (180, 80, 80),     # 진빨강 (건강)
}


@dataclass(frozen=True)
class FaceVisualizationResult:
    image_base64: str
    width: int
    height: int
    n_palaces_drawn: int
    metadata: dict


def overlay_face_analysis(
    image: np.ndarray,
    keypoints: dict | None = None,
    palace_scores: dict | None = None,
    show_palaces: bool = True,
    show_five_peaks: bool = True,
    show_keypoints: bool = False,
) -> FaceVisualizationResult:
    """원본 얼굴 이미지 위에 12궁 + 5악 오버레이.

    Args:
        image: 얼굴 RGB (H, W, 3).
        keypoints: MediaPipe Face 478 keypoint dict {"kp0": [x,y,z], ...}.
                   정규화 좌표 (0~1) 또는 픽셀 좌표 자동 감지.
        palace_scores: {"명궁": 0.65, ...} (옵션 라벨 점수 표시).
        show_palaces: 12궁 영역 박스/라벨 표시.
        show_five_peaks: 5악 (이마/광대/코/턱) 표시.
        show_keypoints: 478 점 표시 (디버그용, 기본 False).

    Returns:
        FaceVisualizationResult — base64 PNG.
    """
    from PIL import Image as PILImage, ImageDraw, ImageFont

    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    pil = PILImage.fromarray(image).convert("RGBA")
    h, w = image.shape[:2]

    overlay = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 폰트 (ADR-264)
    _font_candidates = [
        "malgun.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "NanumGothic.ttf",
    ]
    font_label = None
    font_small = None
    for fp in _font_candidates:
        try:
            font_label = ImageFont.truetype(fp, max(16, w // 45))
            font_small = ImageFont.truetype(fp, max(12, w // 70))
            break
        except Exception:
            continue

    # keypoint 픽셀 변환
    kp_px = {}
    if keypoints:
        for k, v in keypoints.items():
            if not k.startswith("kp"):
                continue
            if not isinstance(v, (list, tuple)) or len(v) < 2:
                continue
            x, y = float(v[0]), float(v[1])
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                kp_px[k] = (x * w, y * h)
            else:
                kp_px[k] = (x, y)

    # KP 헬퍼
    def get_kp(name):
        idx = KP_INDEX.get(name)
        if idx is None:
            return None
        return kp_px.get(f"kp{idx}")

    n_palaces = 0
    if show_palaces and kp_px:
        # 핵심 keypoint
        forehead = get_kp("forehead_top")
        chin = get_kp("chin")
        brow_li = get_kp("brow_l_inner")
        brow_ri = get_kp("brow_r_inner")
        nose_tip = get_kp("nose_tip")
        nose_bridge = get_kp("nose_bridge")
        eye_lo = get_kp("eye_l_outer")
        eye_ro = get_kp("eye_r_outer")
        eye_li = get_kp("eye_l_inner")
        eye_ri = get_kp("eye_r_inner")
        face_l = get_kp("face_left")
        face_r = get_kp("face_right")
        alar_l = get_kp("alar_left")
        alar_r = get_kp("alar_right")
        under_eye_l = get_kp("under_eye_l")
        under_eye_r = get_kp("under_eye_r")
        glabella = get_kp("glabella")
        brow_lp = get_kp("brow_l_peak")
        brow_rp = get_kp("brow_r_peak")
        brow_lo = get_kp("brow_l_outer")
        brow_ro = get_kp("brow_r_outer")

        # 라벨 + 영역 점 (얼굴 위 점 + 라벨 텍스트)
        def draw_palace(center, label, color, radius=8):
            nonlocal n_palaces
            if center is None:
                return
            cx, cy = center
            # 원 (영역 표시)
            draw.ellipse([(cx-radius, cy-radius), (cx+radius, cy+radius)],
                         outline=color + (255,), width=3)
            # 라벨
            if font_small is not None:
                try:
                    bb = draw.textbbox((0,0), label, font=font_small)
                    tw, th = bb[2]-bb[0], bb[3]-bb[1]
                except: tw, th = 40, 14
                # 라벨 위치 — 점 위 오프셋
                lx = int(cx - tw/2)
                ly = int(cy + radius + 4)
                lx = max(2, min(w-tw-2, lx))
                ly = max(2, min(h-th-2, ly))
                draw.rectangle([(lx-2, ly-1),(lx+tw+3, ly+th+3)],
                               fill=(0,0,0,180))
                draw.text((lx, ly), label, fill=color + (255,), font=font_small)
            n_palaces += 1

        # 12궁 위치 정의
        # 명궁 — 미간 중앙
        draw_palace(glabella, "명궁", PALACE_COLORS["명궁"])
        # 재백궁 — 코끝
        draw_palace(nose_tip, "재백궁", PALACE_COLORS["재백궁"])
        # 관록궁 — 이마 정중앙 (발제와 미간 중간)
        if forehead and glabella:
            cx = (forehead[0] + glabella[0]) / 2
            cy = (forehead[1] + glabella[1]) / 2 + (glabella[1] - forehead[1]) * 0.2
            draw_palace((cx, cy), "관록궁", PALACE_COLORS["관록궁"])
        # 복덕궁 — 미간 위쪽
        if glabella and forehead:
            cx = glabella[0]
            cy = glabella[1] - (glabella[1] - forehead[1]) * 0.3
            draw_palace((cx, cy), "복덕궁", PALACE_COLORS["복덕궁"])
        # 처첩궁 좌우 — 눈꼬리 옆
        if eye_lo and face_l:
            cx = (eye_lo[0] + face_l[0]) / 2
            cy = eye_lo[1]
            draw_palace((cx, cy), "처첩(좌)", PALACE_COLORS["처첩궁"])
        if eye_ro and face_r:
            cx = (eye_ro[0] + face_r[0]) / 2
            cy = eye_ro[1]
            draw_palace((cx, cy), "처첩(우)", PALACE_COLORS["처첩궁"])
        # 남녀궁 — 와잠 (눈 아래)
        if under_eye_l:
            draw_palace(under_eye_l, "남녀(좌)", PALACE_COLORS["남녀궁"])
        if under_eye_r:
            draw_palace(under_eye_r, "남녀(우)", PALACE_COLORS["남녀궁"])
        # 형제궁 — 눈썹 정점
        if brow_lp:
            draw_palace(brow_lp, "형제(좌)", PALACE_COLORS["형제궁"])
        if brow_rp:
            draw_palace(brow_rp, "형제(우)", PALACE_COLORS["형제궁"])
        # 전택궁 — 눈썹과 눈 사이
        if brow_li and eye_li:
            cx = (brow_li[0] + eye_li[0]) / 2
            cy = (brow_li[1] + eye_li[1]) / 2
            draw_palace((cx, cy), "전택(좌)", PALACE_COLORS["전택궁"])
        if brow_ri and eye_ri:
            cx = (brow_ri[0] + eye_ri[0]) / 2
            cy = (brow_ri[1] + eye_ri[1]) / 2
            draw_palace((cx, cy), "전택(우)", PALACE_COLORS["전택궁"])
        # 질액궁 — 산근 (콧대 시작)
        draw_palace(nose_bridge, "질액궁", PALACE_COLORS["질액궁"])
        # 천이궁 — 이마 양옆 (관자놀이 근처)
        if forehead and brow_lo and brow_ro:
            # 좌천이 = brow_lo와 face_l 중간 위쪽
            if face_l:
                cx = (brow_lo[0] + face_l[0]) / 2
                cy = (forehead[1] + brow_lo[1]) / 2
                draw_palace((cx, cy), "천이(좌)", PALACE_COLORS["천이궁"])
            if face_r:
                cx = (brow_ro[0] + face_r[0]) / 2
                cy = (forehead[1] + brow_ro[1]) / 2
                draw_palace((cx, cy), "천이(우)", PALACE_COLORS["천이궁"])
        # 부모궁 — 이마 위쪽 좌우 (관록궁 옆)
        if forehead and brow_li and brow_ri:
            mid = (forehead[1] + (brow_li[1]+brow_ri[1])/2) / 2
            cx_l = brow_lp[0] if brow_lp else brow_li[0] - 20
            cx_r = brow_rp[0] if brow_rp else brow_ri[0] + 20
            draw_palace((cx_l, mid - 20), "부모(좌)", PALACE_COLORS["부모궁"])
            draw_palace((cx_r, mid - 20), "부모(우)", PALACE_COLORS["부모궁"])
        # 노복궁 — 턱 좌우
        if chin and face_l and face_r:
            cy = chin[1] - 30
            cx_l = (face_l[0] + chin[0]) / 2
            cx_r = (face_r[0] + chin[0]) / 2
            draw_palace((cx_l, cy), "노복(좌)", PALACE_COLORS["노복궁"])
            draw_palace((cx_r, cy), "노복(우)", PALACE_COLORS["노복궁"])

        # ADR-273 입 부위 추가 — 출납관/인중/법령/승장
        mouth_l_kp = get_kp("mouth_l")
        mouth_r_kp = get_kp("mouth_r")
        lip_upper = get_kp("lip_upper")
        lip_lower = get_kp("lip_lower")
        nose_tip_kp = get_kp("nose_tip")
        # 출납관 — 입 중앙 (윗입술과 아랫입술 중간)
        if lip_upper and lip_lower:
            cx = (lip_upper[0] + lip_lower[0]) / 2
            cy = (lip_upper[1] + lip_lower[1]) / 2
            draw_palace((cx, cy), "출납관", (255, 100, 100))
        # 인중 — 코끝과 윗입술 중간
        if nose_tip_kp and lip_upper:
            cx = (nose_tip_kp[0] + lip_upper[0]) / 2
            cy = (nose_tip_kp[1] + lip_upper[1]) / 2
            draw_palace((cx, cy), "인중", (220, 140, 100))
        # 법령(좌·우) — 콧방울 옆 ~ 입꼬리 옆
        if alar_l and mouth_l_kp:
            cx = (alar_l[0] + mouth_l_kp[0]) / 2 - 8
            cy = (alar_l[1] + mouth_l_kp[1]) / 2
            draw_palace((cx, cy), "법령(좌)", (180, 60, 140))
        if alar_r and mouth_r_kp:
            cx = (alar_r[0] + mouth_r_kp[0]) / 2 + 8
            cy = (alar_r[1] + mouth_r_kp[1]) / 2
            draw_palace((cx, cy), "법령(우)", (180, 60, 140))
        # 승장 — 아랫입술과 턱 사이
        if lip_lower and chin:
            cx = (lip_lower[0] + chin[0]) / 2
            cy = (lip_lower[1] * 2 + chin[1]) / 3
            draw_palace((cx, cy), "승장", (140, 100, 200))

    # 5악 라벨 (선택)
    if show_five_peaks and kp_px:
        peak_color = (200, 200, 200)
        peak_bg = (40, 40, 40, 220)
        forehead = get_kp("forehead_top")
        chin = get_kp("chin")
        nose_tip = get_kp("nose_tip")
        face_l = get_kp("face_left")
        face_r = get_kp("face_right")
        peaks = []
        if forehead:
            peaks.append((forehead[0], forehead[1] - 18, "南嶽 이마"))
        if chin:
            peaks.append((chin[0], chin[1] + 18, "北嶽 턱"))
        if nose_tip:
            peaks.append((nose_tip[0] + 30, nose_tip[1], "中嶽 코"))
        if face_l:
            peaks.append((face_l[0] - 35, face_l[1], "東嶽 광대"))
        if face_r:
            peaks.append((face_r[0] + 35, face_r[1], "西嶽 광대"))
        if font_small is not None:
            for px, py, label in peaks:
                try:
                    bb = draw.textbbox((0,0), label, font=font_small)
                    tw, th = bb[2]-bb[0], bb[3]-bb[1]
                except: tw, th = 40, 14
                lx = int(px - tw/2); ly = int(py - th/2)
                lx = max(2, min(w-tw-2, lx))
                ly = max(2, min(h-th-2, ly))
                draw.rectangle([(lx-2, ly-1),(lx+tw+3, ly+th+3)], fill=peak_bg)
                draw.text((lx, ly), label, fill=peak_color + (255,), font=font_small)

    if show_keypoints and kp_px:
        for k, (px, py) in kp_px.items():
            r = 2
            draw.ellipse([(px-r, py-r),(px+r, py+r)], fill=(255,80,80,255))

    final = PILImage.alpha_composite(pil, overlay).convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="PNG", optimize=True)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return FaceVisualizationResult(
        image_base64=f"data:image/png;base64,{img_b64}",
        width=w,
        height=h,
        n_palaces_drawn=n_palaces,
        metadata={
            "palaces_drawn": n_palaces,
            "show_five_peaks": show_five_peaks,
            "show_keypoints": show_keypoints,
        },
    )
