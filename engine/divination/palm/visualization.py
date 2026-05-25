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
    hand_bbox = None  # (x0, y0, x1, y1) 픽셀
    if keypoints:
        xs, ys = [], []
        for k, v in keypoints.items():
            if not k.startswith("kp"):
                continue
            if not isinstance(v, (list, tuple)) or len(v) < 2:
                continue
            x, y = float(v[0]), float(v[1])
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                xs.append(x * w)
                ys.append(y * h)
            else:
                xs.append(x)
                ys.append(y)
        if len(xs) >= 5:
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            bw, bh = x1 - x0, y1 - y0
            if bw > 0 and bh > 0:
                # padding 15% (손가락 끝/손목 여유)
                pad_x = bw * 0.15
                pad_y = bh * 0.15
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

    # 2. 영역 박스 + 점수 라벨 (ADR-263 — hand_bbox 기준 변환)
    if show_regions:
        # 영역 박스의 기준 좌표 (손 bbox 안에 그리거나, 부재 시 전체 이미지)
        if hand_bbox:
            rx0, ry0, rx1, ry1 = hand_bbox
            rw, rh = rx1 - rx0, ry1 - ry0
        else:
            rx0, ry0 = 0, 0
            rw, rh = w, h
        for key, (x0n, y0n, x1n, y1n, label, color) in LINE_REGIONS.items():
            x0 = int(rx0 + x0n * rw)
            y0 = int(ry0 + y0n * rh)
            x1 = int(rx0 + x1n * rw)
            y1 = int(ry0 + y1n * rh)
            # 박스 (점선 효과 — 짧은 선 여러 개)
            for offset in range(0, max(x1 - x0, y1 - y0), 14):
                # 상단
                if offset + 7 <= x1 - x0:
                    draw.line([(x0 + offset, y0), (x0 + offset + 7, y0)], fill=color + (180,), width=2)
                # 하단
                if offset + 7 <= x1 - x0:
                    draw.line([(x0 + offset, y1), (x0 + offset + 7, y1)], fill=color + (180,), width=2)
                # 좌측
                if offset + 7 <= y1 - y0:
                    draw.line([(x0, y0 + offset), (x0, y0 + offset + 7)], fill=color + (180,), width=2)
                # 우측
                if offset + 7 <= y1 - y0:
                    draw.line([(x1, y0 + offset), (x1, y0 + offset + 7)], fill=color + (180,), width=2)
            # 라벨 + 점수
            score = (line_scores or {}).get(key)
            label_text = f"{label}"
            if score is not None:
                label_text += f" {float(score):.2f}"
            # 라벨 배경 박스
            if font_label is not None:
                try:
                    bbox = draw.textbbox((0, 0), label_text, font=font_label)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except Exception:
                    tw, th = len(label_text) * 8, 16
            else:
                tw, th = len(label_text) * 7, 14
            # 라벨 위치: 영역 안쪽 좌상단 (절대 화면 밖으로 안 나가게)
            label_x = max(8, x0 + 6)
            label_y = max(8, y0 + 6)
            # 라벨이 다른 영역과 겹치지 않게 영역별 약간 오프셋
            label_y += {"lifeline": 4, "headline": 28, "heartline": 4,
                       "fateline": 52, "girdle_of_venus": 4}.get(key, 0)
            if label_y + th > h - 4:
                label_y = h - th - 4
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
