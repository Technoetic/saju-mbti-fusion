"""ADR-259 — 손금 시각화 오버레이.

목적: 사용자 신뢰도 향상 — "AI가 내 손금을 이렇게 보는구나" 시각 확인.

요소:
  1. MediaPipe 21 keypoint (빨간 점 + 번호)
  2. CFM 마스크 오버레이 (노란 반투명, alpha=0.4)
  3. 4선 영역 박스 (생명선/두뇌선/감정선/운명선/금성대) + 점수 라벨
  4. 메타 텍스트 (overall density, consistency)

순수 PIL — scipy/cv2 의존성 0. 라이브 추가 부담 미미 (~50ms).

ADR 정합:
  · ADR-006 학파 명시 + 단정 어휘 X
  · ADR-010 사실성 분리 (시각화 = 객관 데이터)
  · ADR-250 CFM 결합 결과 시각화
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Optional

import numpy as np


# 4 손금선 + 금성대 영역 매핑 (256x256 정규화)
# x0, y0, x1, y1 (정규화 0~1) + 라벨 + 색상 (R,G,B)
LINE_REGIONS = {
    "lifeline":        (0.0, 0.50, 0.50, 1.0, "생명선", (255, 100, 100)),  # 좌하 (엄지 아래)
    "headline":        (0.0, 0.33, 1.0, 0.67, "두뇌선", (100, 200, 255)),  # 중부
    "heartline":       (0.0, 0.0,  1.0, 0.33, "감정선", (255, 180, 100)),  # 상부
    "fateline":        (0.25, 0.0, 0.75, 1.0, "운명선", (180, 150, 255)),  # 중앙 수직
    "girdle_of_venus": (0.0, 0.0,  1.0, 0.25, "금성대", (255, 200, 200)),  # 최상부 호
}

KP_COLOR = (255, 50, 50)
MASK_OVERLAY_COLOR = (255, 200, 0)  # 노란/오렌지


@dataclass(frozen=True)
class VisualizationResult:
    image_base64: str            # data:image/png;base64,...
    width: int
    height: int
    overlay_alpha: float
    n_keypoints: int
    has_cfm_mask: bool
    metadata: dict


def overlay_palm_analysis(
    image: np.ndarray,
    keypoints: dict | None = None,
    cfm_mask: np.ndarray | None = None,
    line_scores: dict | None = None,
    cfm_metrics: dict | None = None,
    overlay_alpha: float = 0.4,
    show_keypoints: bool = True,
    show_mask: bool = True,
    show_regions: bool = True,
) -> VisualizationResult:
    """원본 이미지 위에 손금 분석 결과 오버레이.

    Args:
        image: 원본 손바닥 (H, W, 3) RGB numpy.
        keypoints: MediaPipe 21 keypoint dict {"kp0": [x,y,z], ...}.
                   정규화 좌표 (0~1) 또는 픽셀 좌표 자동 감지.
        cfm_mask: CFM 손금 마스크 (h, w) bool 또는 0/1. 원본 크기와 다를 수 있음 (리사이즈).
        line_scores: {"lifeline": 0.65, ...} score_palm_with_cfm 결과.
        cfm_metrics: {"overall_density": 0.07, ...} 메타 표시용.
        overlay_alpha: 마스크 투명도 (0~1).
        show_keypoints, show_mask, show_regions: 토글.

    Returns:
        VisualizationResult — base64 PNG.
    """
    from PIL import Image as PILImage, ImageDraw, ImageFont

    # 원본 이미지 PIL 변환
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    pil = PILImage.fromarray(image).convert("RGBA")
    h, w = image.shape[:2]

    # 오버레이 레이어 (투명)
    overlay = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # ADR-263 — keypoints 가 있으면 손 bbox 계산 (영역 박스 + 마스크를 손 안에만 표시)
    # ADR-266 — keypoint 별 위치 (kp0=손목, kp5/9/13/17=손가락 mcp) 활용해
    # 영역 박스를 keypoint 기반 직접 계산 (손 회전 자동 대응).
    hand_bbox = None  # (x0, y0, x1, y1) 픽셀
    kp_px = {}  # 픽셀 좌표
    if keypoints:
        xs, ys = [], []
        for k, v in keypoints.items():
            if not k.startswith("kp"):
                continue
            if not isinstance(v, (list, tuple)) or len(v) < 2:
                continue
            x, y = float(v[0]), float(v[1])
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                px, py = x * w, y * h
            else:
                px, py = x, y
            xs.append(px)
            ys.append(py)
            kp_px[k] = (px, py)
        if len(xs) >= 5:
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            bw, bh = x1 - x0, y1 - y0
            if bw > 0 and bh > 0:
                # ADR-265 — padding 15% → 5% (셀카에서 배경 노이즈 침입 방지).
                # 손가락 끝/손목 약간 여유 확보, 그러나 인접 배경은 제외.
                pad_x = bw * 0.05
                pad_y = bh * 0.05
                hand_bbox = (
                    max(0, int(x0 - pad_x)),
                    max(0, int(y0 - pad_y)),
                    min(w, int(x1 + pad_x)),
                    min(h, int(y1 + pad_y)),
                )

    # ADR-264 — 폰트 다단계 fallback (Windows / Linux 라이브 / 기본)
    _font_candidates = [
        "malgun.ttf",  # Windows
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux Debian fonts-nanum
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "NanumGothic.ttf",
    ]
    font_small = None
    font_label = None
    for fp in _font_candidates:
        try:
            font_small = ImageFont.truetype(fp, max(12, w // 80))
            font_label = ImageFont.truetype(fp, max(16, w // 50))
            break
        except Exception:
            continue
    if font_small is None:
        try:
            font_small = ImageFont.load_default()
            font_label = ImageFont.load_default()
        except Exception:
            pass

    # 1. CFM 마스크 오버레이
    n_mask_pixels = 0
    if show_mask and cfm_mask is not None:
        try:
            mask_arr = cfm_mask.astype(bool)
            # 원본 크기로 리사이즈 (nearest)
            if mask_arr.shape != (h, w):
                m_pil = PILImage.fromarray((mask_arr * 255).astype(np.uint8))
                m_pil = m_pil.resize((w, h), PILImage.NEAREST)
                mask_arr = np.array(m_pil) > 127
            # ADR-263 — 손 bbox 있으면 그 밖은 마스크 false (배경 검출 노이즈 제거)
            if hand_bbox:
                hx0, hy0, hx1, hy1 = hand_bbox
                clipped = np.zeros_like(mask_arr, dtype=bool)
                clipped[hy0:hy1, hx0:hx1] = mask_arr[hy0:hy1, hx0:hx1]
                mask_arr = clipped
            # 노란 반투명 색 오버레이
            mask_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            mask_rgba[mask_arr] = [*MASK_OVERLAY_COLOR, int(255 * overlay_alpha)]
            mask_pil = PILImage.fromarray(mask_rgba, mode="RGBA")
            overlay = PILImage.alpha_composite(overlay, mask_pil)
            draw = ImageDraw.Draw(overlay)
            n_mask_pixels = int(mask_arr.sum())
        except Exception:
            pass

    # 2. 영역 박스 + 점수 라벨 (ADR-266 — keypoint 기반 회전 좌표계)
    # 좌표계: u = 손목→중지 방향 (정 손바닥), v = u 90° 회전 (좌우)
    # 손바닥 원점: kp0(손목)와 kp9(중지 mcp) 중점.
    # 손바닥 길이: |kp9 - kp0|, 폭: 손바닥 너비 추정.
    if show_regions and kp_px and "kp0" in kp_px and "kp9" in kp_px:
        import math as _math
        wx, wy = kp_px["kp0"]  # 손목
        mx, my = kp_px["kp9"]  # 중지 mcp
        # u 방향 (손목 → 중지)
        ux, uy = mx - wx, my - wy
        u_len = _math.hypot(ux, uy)
        if u_len > 5:  # 최소 5px
            ux, uy = ux / u_len, uy / u_len
            # v 방향 (u 90° 시계방향 — 손바닥 좌→우)
            vx, vy = -uy, ux
            # 손바닥 폭: kp5(검지 mcp) - kp17(새끼 mcp) 거리
            if "kp5" in kp_px and "kp17" in kp_px:
                x5, y5 = kp_px["kp5"]
                x17, y17 = kp_px["kp17"]
                palm_width = _math.hypot(x5 - x17, y5 - y17) * 1.2
            else:
                palm_width = u_len * 0.7
            palm_length = u_len * 1.2  # 손목~손가락 끝까지

            # 손바닥 중심 = kp9
            cx, cy = mx, my

            def hand_to_pixel(s, t):
                """손바닥 좌표 (s=u축, t=v축, 0~1 정규화) → 픽셀.
                s=0 손목, s=1 손가락 끝. t=0 좌측, t=1 우측 (kp17→kp5)."""
                # u축 변환: s=0(손목 kp0) → s=1(손가락 끝 = kp9 + u_len * 0.5)
                # 즉 origin = kp0, length = palm_length
                u_off = (s - (u_len / palm_length)) * palm_length  # kp9 기준 offset
                v_off = (t - 0.5) * palm_width
                px = cx + ux * u_off + vx * v_off
                py = cy + uy * u_off + vy * v_off
                return px, py

            # ADR-268 — 사각형 박스 → 실제 손금 곡선 + 나이 마커.
            # 표준 손금 학술 위치 (Cheiro/Indian/Korean 통합):
            #   생명선(life): 검지-엄지 사이 시작 → 엄지 둘레 → 손목 (주황)
            #   두뇌선(head): 검지-엄지 사이 시작 → 손바닥 중앙 가로 (파랑)
            #   감정선(heart): 새끼 아래 → 검지/중지 사이 (빨강)
            #   운명선(fate): 손목 중앙 → 중지 mcp (파랑 진한)
            #   결혼선(marriage): 새끼 아래 짧은 가로선 (짙은 빨강)
            #   금성대(girdle): 검지-새끼 위 호 (분홍)
            # 곡선 색상 (R,G,B)
            LINE_COLORS = {
                "lifeline":        (255, 165, 60),   # 주황
                "headline":        (60, 150, 220),   # 파랑
                "heartline":       (220, 60, 60),    # 빨강
                "fateline":        (60, 100, 200),   # 진한 파랑
                "marriage":        (180, 40, 70),    # 짙은 빨강 (보조)
                "girdle_of_venus": (240, 140, 170),  # 분홍
            }
            LINE_LABELS = {
                "lifeline": "생명선", "headline": "두뇌선",
                "heartline": "감정선", "fateline": "운명선",
                "marriage": "결혼선", "girdle_of_venus": "금성대",
            }

            def smooth_curve(points, n_steps=40):
                """Catmull-Rom spline 근사 (4점 이상 입력)."""
                if len(points) < 2:
                    return points
                if len(points) == 2:
                    return points
                # 양 끝 패딩
                pts = [points[0]] + list(points) + [points[-1]]
                result = []
                for i in range(len(pts) - 3):
                    p0, p1, p2, p3 = pts[i:i+4]
                    for t_i in range(n_steps):
                        t = t_i / n_steps
                        t2 = t * t
                        t3 = t2 * t
                        # Catmull-Rom basis
                        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                                   (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
                                   (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
                        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                                   (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
                                   (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
                        result.append((x, y))
                result.append(points[-1])
                return result

            def draw_curve(pts_hand, color, width=4):
                """손바닥 좌표 (s, t) 리스트 → 픽셀 곡선."""
                if len(pts_hand) < 2:
                    return
                pix = [hand_to_pixel(s, t) for s, t in pts_hand]
                smooth = smooth_curve(pix)
                for i in range(len(smooth) - 1):
                    draw.line([smooth[i], smooth[i+1]], fill=color + (220,), width=width)

            def label_at(pos_hand, text, color, offset_px=(0, -18)):
                """손바닥 좌표 → 라벨 그리기."""
                px, py = hand_to_pixel(*pos_hand)
                px += offset_px[0]
                py += offset_px[1]
                if font_label is None:
                    return
                try:
                    bbox = draw.textbbox((0, 0), text, font=font_label)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except Exception:
                    tw, th = len(text) * 8, 16
                lx = int(px - tw / 2)
                ly = int(py - th / 2)
                lx = max(4, min(w - tw - 4, lx))
                ly = max(4, min(h - th - 4, ly))
                draw.rectangle([(lx - 3, ly - 3), (lx + tw + 5, ly + th + 5)],
                               fill=(0, 0, 0, 200))
                draw.text((lx, ly), text, fill=color + (255,), font=font_label)

            # 좌표계: hand_to_pixel(s, t).
            # s = u축 (손목→중지). s=0=손목 부근, s=1=중지 손가락 끝.
            # t = v축 (u 90° 시계). t=0/1은 좌우 새끼/엄지인데 회전 따라 다름.
            # ※ 직접 keypoint로 검증: kp17(새끼 mcp)와 kp5(검지 mcp) 픽셀 위치 비교.
            # 학술적 손금 위치는 keypoint 직접 활용이 가장 안전.

            # kp 픽셀 좌표 (이미 kp_px 에 있음)
            kp0 = kp_px.get("kp0")    # 손목
            kp1 = kp_px.get("kp1")    # 엄지 cmc
            kp2 = kp_px.get("kp2")    # 엄지 mcp
            kp5 = kp_px.get("kp5")    # 검지 mcp
            kp9 = kp_px.get("kp9")    # 중지 mcp
            kp13 = kp_px.get("kp13")  # 약지 mcp
            kp17 = kp_px.get("kp17")  # 새끼 mcp

            def lerp(p, q, r):
                """p와 q 사이 r비율 점."""
                return (p[0] + (q[0] - p[0]) * r, p[1] + (q[1] - p[1]) * r)

            # ━━ 생명선 — 검지-엄지 사이 시작 → 엄지 둘레 곡선 → 손목 ━━
            if kp5 and kp1 and kp2 and kp0:
                life_pts = [
                    lerp(kp5, kp1, 0.3),  # 검지-엄지 사이 시작
                    lerp(kp1, kp2, 0.5),  # 엄지 윗부분
                    kp1,                   # 엄지 cmc (가장 바깥)
                    lerp(kp1, kp0, 0.6),  # 손목 쪽
                    lerp(kp1, kp0, 0.9),
                ]
                draw_curve(life_pts, LINE_COLORS["lifeline"], width=4)
                label_at_pix = lerp(kp1, kp0, 0.5)
                if font_label is not None:
                    text = LINE_LABELS["lifeline"]
                    try:
                        bb = draw.textbbox((0,0), text, font=font_label)
                        tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    except: tw, th = 50, 18
                    # 엄지 바깥쪽으로 오프셋
                    lx = int(label_at_pix[0] - tw - 10)
                    ly = int(label_at_pix[1] - th/2)
                    lx = max(4, min(w-tw-4, lx))
                    ly = max(4, min(h-th-4, ly))
                    draw.rectangle([(lx-3, ly-3),(lx+tw+5, ly+th+5)], fill=(0,0,0,200))
                    draw.text((lx, ly), text, fill=LINE_COLORS["lifeline"]+(255,), font=font_label)

            # ━━ 두뇌선 — 검지-엄지 사이 → 손바닥 중앙 가로 → 새끼 쪽 ━━
            if kp5 and kp9 and kp13 and kp17 and kp1:
                # 손바닥 중앙 가로선: 검지 아래(kp5와 kp1 중간) → 새끼 아래
                head_pts = [
                    lerp(kp5, kp1, 0.4),
                    lerp(kp5, kp9, 0.6),
                    lerp(kp9, kp13, 0.6),
                    lerp(kp13, kp17, 0.6),
                    lerp(kp17, kp0, 0.4),
                ]
                # 두뇌선은 손바닥 중간 위치 → 모든 점을 손목쪽으로 약간 시프트
                center_palm = ((kp5[0]+kp17[0]+kp0[0])/3, (kp5[1]+kp17[1]+kp0[1])/3)
                head_pts = [lerp(p, center_palm, 0.15) for p in head_pts]
                draw_curve(head_pts, LINE_COLORS["headline"], width=4)
                label_at_pix = head_pts[2]
                if font_label is not None:
                    text = LINE_LABELS["headline"]
                    try:
                        bb = draw.textbbox((0,0), text, font=font_label)
                        tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    except: tw, th = 50, 18
                    lx = int(label_at_pix[0] - tw/2)
                    ly = int(label_at_pix[1] + 15)
                    lx = max(4, min(w-tw-4, lx))
                    ly = max(4, min(h-th-4, ly))
                    draw.rectangle([(lx-3, ly-3),(lx+tw+5, ly+th+5)], fill=(0,0,0,200))
                    draw.text((lx, ly), text, fill=LINE_COLORS["headline"]+(255,), font=font_label)

            # ━━ 감정선 — 새끼 아래 → 검지/중지 사이 (두뇌선 위) ━━
            if kp5 and kp9 and kp13 and kp17:
                heart_pts = [
                    lerp(kp17, kp_px.get("kp18", kp17), 0.3),  # 새끼 mcp 부근
                    lerp(kp17, kp13, 0.5),
                    lerp(kp13, kp9, 0.5),
                    lerp(kp9, kp5, 0.5),
                ]
                # 손가락 mcp 라인보다 약간 손목 쪽 (감정선은 두뇌선 위)
                # 손목 방향 = kp0 방향
                if kp0:
                    finger_avg = ((kp5[0]+kp9[0]+kp13[0]+kp17[0])/4, (kp5[1]+kp9[1]+kp13[1]+kp17[1])/4)
                    wrist_dir = (kp0[0]-finger_avg[0], kp0[1]-finger_avg[1])
                    # 손목 쪽으로 약간 시프트
                    heart_pts = [(p[0] + wrist_dir[0]*0.12, p[1] + wrist_dir[1]*0.12) for p in heart_pts]
                draw_curve(heart_pts, LINE_COLORS["heartline"], width=4)
                label_at_pix = heart_pts[1]
                if font_label is not None:
                    text = LINE_LABELS["heartline"]
                    try:
                        bb = draw.textbbox((0,0), text, font=font_label)
                        tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    except: tw, th = 50, 18
                    lx = int(label_at_pix[0] - tw/2)
                    ly = int(label_at_pix[1] - th - 20)
                    lx = max(4, min(w-tw-4, lx))
                    ly = max(4, min(h-th-4, ly))
                    draw.rectangle([(lx-3, ly-3),(lx+tw+5, ly+th+5)], fill=(0,0,0,200))
                    draw.text((lx, ly), text, fill=LINE_COLORS["heartline"]+(255,), font=font_label)

            # ━━ 운명선 — 손목 중앙 → 중지 mcp + 나이 마커 ━━
            fate_pts = []
            if kp0 and kp9:
                fate_pts = [
                    kp0,
                    lerp(kp0, kp9, 0.25),
                    lerp(kp0, kp9, 0.50),
                    lerp(kp0, kp9, 0.75),
                    kp9,
                ]
                draw_curve(fate_pts, LINE_COLORS["fateline"], width=4)

                # 나이 마커 — 운명선 위 9 지점 (손가락쪽=10대, 손목쪽=90대)
                age_marker_color = (40, 40, 40)
                ages = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대"]
                for idx, age in enumerate(ages):
                    # r=0 (kp9 중지 손가락쪽 = 10대) ~ r=1 (kp0 손목 = 90대)
                    r_age = idx / (len(ages) - 1)
                    px, py = lerp(kp9, kp0, r_age)
                    draw.ellipse([(px-3, py-3), (px+3, py+3)],
                                 fill=LINE_COLORS["fateline"] + (255,))
                    if font_small is not None:
                        try:
                            bb = draw.textbbox((0,0), age, font=font_small)
                            atw, ath = bb[2]-bb[0], bb[3]-bb[1]
                        except: atw, ath = 24, 12
                        # 운명선 옆 (수직 방향) 으로 오프셋 — v 축 사용 (10px)
                        lx = int(px + vx * 16 - atw/2)
                        ly = int(py + vy * 16 - ath/2)
                        lx = max(2, min(w-atw-2, lx))
                        ly = max(2, min(h-ath-2, ly))
                        draw.rectangle([(lx-1, ly-1),(lx+atw+2, ly+ath+2)],
                                       fill=(255,255,255,200))
                        draw.text((lx, ly), age, fill=age_marker_color, font=font_small)

                # 운명선 라벨 (kp9 위쪽)
                label_at_pix = lerp(kp9, kp0, 0.3)
                if font_label is not None:
                    text = LINE_LABELS["fateline"]
                    try:
                        bb = draw.textbbox((0,0), text, font=font_label)
                        tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    except: tw, th = 50, 18
                    lx = int(label_at_pix[0] - vx*40 - tw/2)
                    ly = int(label_at_pix[1] - vy*40 - th/2)
                    lx = max(4, min(w-tw-4, lx))
                    ly = max(4, min(h-th-4, ly))
                    draw.rectangle([(lx-3, ly-3),(lx+tw+5, ly+th+5)], fill=(0,0,0,200))
                    draw.text((lx, ly), text, fill=LINE_COLORS["fateline"]+(255,), font=font_label)

            # ━━ 결혼선 — 새끼 mcp 옆 짧은 가로선 ━━
            if kp17 and kp_px.get("kp18"):
                kp18 = kp_px["kp18"]
                # 새끼 mcp에서 손바닥 안쪽 방향으로 짧은 선
                mar_start = lerp(kp17, kp13 if kp13 else kp9, 0.05)
                mar_end = lerp(kp17, kp13 if kp13 else kp9, 0.30)
                draw_curve([mar_start, mar_end], LINE_COLORS["marriage"], width=3)
                if font_label is not None:
                    text = LINE_LABELS["marriage"]
                    try:
                        bb = draw.textbbox((0,0), text, font=font_label)
                        tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    except: tw, th = 50, 18
                    px, py = mar_start
                    lx = int(px - tw - 12)
                    ly = int(py - th/2)
                    lx = max(4, min(w-tw-4, lx))
                    ly = max(4, min(h-th-4, ly))
                    draw.rectangle([(lx-3, ly-3),(lx+tw+5, ly+th+5)], fill=(0,0,0,200))
                    draw.text((lx, ly), text, fill=LINE_COLORS["marriage"]+(255,), font=font_label)

    # 3. MediaPipe 21 keypoint
    n_kp = 0
    if show_keypoints and keypoints:
        for k, v in keypoints.items():
            if not k.startswith("kp"):
                continue
            if not isinstance(v, (list, tuple)) or len(v) < 2:
                continue
            x, y = float(v[0]), float(v[1])
            # 정규화 좌표 자동 감지
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                px, py = int(x * w), int(y * h)
            else:
                px, py = int(x), int(y)
            if 0 <= px < w and 0 <= py < h:
                r = max(4, w // 200)
                draw.ellipse(
                    [(px - r, py - r), (px + r, py + r)],
                    fill=KP_COLOR + (255,),
                    outline=(255, 255, 255, 255),
                    width=1,
                )
                # 번호
                num = k.replace("kp", "")
                if font_small is not None:
                    draw.text(
                        (px + r + 2, py - r),
                        num, fill=(255, 255, 255, 255), font=font_small,
                    )
                n_kp += 1

    # 4. 메타 텍스트 (좌하단)
    if cfm_metrics:
        overall = cfm_metrics.get("overall_density", 0.0)
        meta_text = f"CFM density: {overall*100:.1f}% | keypoints: {n_kp}"
        if font_small is not None:
            try:
                bbox = draw.textbbox((0, 0), meta_text, font=font_small)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                tw, th = len(meta_text) * 7, 14
        else:
            tw, th = len(meta_text) * 7, 14
        draw.rectangle(
            [(10 - 2, h - th - 14), (10 + tw + 4, h - 8)],
            fill=(0, 0, 0, 200),
        )
        draw.text((10, h - th - 12), meta_text, fill=(255, 255, 255, 255), font=font_small)

    # 합성
    final = PILImage.alpha_composite(pil, overlay).convert("RGB")

    # base64 인코딩
    buf = io.BytesIO()
    final.save(buf, format="PNG", optimize=True)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return VisualizationResult(
        image_base64=f"data:image/png;base64,{img_b64}",
        width=w,
        height=h,
        overlay_alpha=overlay_alpha,
        n_keypoints=n_kp,
        has_cfm_mask=n_mask_pixels > 0,
        metadata={
            "n_mask_pixels": n_mask_pixels,
            "n_keypoints_drawn": n_kp,
            "regions_shown": list(LINE_REGIONS.keys()) if show_regions else [],
            "cfm_overall_density": (cfm_metrics or {}).get("overall_density"),
        },
    )
