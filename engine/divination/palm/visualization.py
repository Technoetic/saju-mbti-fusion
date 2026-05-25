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

            for key, (x0n, y0n, x1n, y1n, label, color) in LINE_REGIONS.items():
                # LINE_REGIONS는 (x0n=좌, y0n=상, x1n=우, y1n=하).
                # 표준 손바닥: x=좌우=v, y=상하=u(상=손가락, 하=손목).
                # → s=1-y (y=0 손가락 → s=1, y=1 손목 → s=0), t=x
                # 네 모서리 polygon
                p1 = hand_to_pixel(1 - y0n, x0n)  # 좌상 (상=손가락 쪽)
                p2 = hand_to_pixel(1 - y0n, x1n)  # 우상
                p3 = hand_to_pixel(1 - y1n, x1n)  # 우하 (하=손목 쪽)
                p4 = hand_to_pixel(1 - y1n, x0n)  # 좌하
                # 점선 polygon
                def dotted_line(pa, pb):
                    dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                    seg_len = _math.hypot(dx, dy)
                    if seg_len < 2:
                        return
                    n = max(1, int(seg_len // 14))
                    for i in range(n):
                        t0 = i / n
                        t1 = min(1.0, (i + 0.5) / n)
                        sa = (pa[0] + dx * t0, pa[1] + dy * t0)
                        sb = (pa[0] + dx * t1, pa[1] + dy * t1)
                        draw.line([sa, sb], fill=color + (180,), width=2)
                dotted_line(p1, p2)
                dotted_line(p2, p3)
                dotted_line(p3, p4)
                dotted_line(p4, p1)
                # 라벨 = 박스 중심
                cx_l = sum(p[0] for p in [p1, p2, p3, p4]) / 4
                cy_l = sum(p[1] for p in [p1, p2, p3, p4]) / 4
                # 라벨 + 점수
                score = (line_scores or {}).get(key)
                label_text = f"{label}"
                if score is not None:
                    label_text += f" {float(score):.2f}"
                # 라벨 크기 측정
                if font_label is not None:
                    try:
                        bbox = draw.textbbox((0, 0), label_text, font=font_label)
                        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    except Exception:
                        tw, th = len(label_text) * 8, 16
                else:
                    tw, th = len(label_text) * 7, 14
                # 라벨 위치: 박스 중심에 중앙 정렬
                label_x = int(cx_l - tw / 2)
                label_y = int(cy_l - th / 2)
                label_x = max(4, min(w - tw - 4, label_x))
                label_y = max(4, min(h - th - 4, label_y))
                draw.rectangle(
                    [(label_x - 3, label_y - 3), (label_x + tw + 5, label_y + th + 5)],
                    fill=(0, 0, 0, 200),
                )
                draw.text((label_x, label_y), label_text, fill=color + (255,), font=font_label)

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
