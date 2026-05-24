"""ADR-252 - CFM 마스크 후처리 (morphology + skeletonization).

목적: CFM raw 마스크는 점 형태 false positive · 끊긴 선 · 두꺼운 영역 포함.
선 검출 정확도 향상을 위한 순수 numpy 후처리.

알고리즘:
  1. opening (erosion → dilation): 작은 노이즈 제거
  2. closing (dilation → erosion): 끊긴 선 연결
  3. small component removal: 면적 < threshold 컴포넌트 제거
  4. (선택) skeletonization: 두꺼운 선 → 1픽셀 두께 (시각화·길이 측정)

순수 numpy — scipy/cv2/skimage 의존성 0. 라이브 인프라 영향 0.

ADR 정합:
  · ADR-251 CFM 마스크 → 본 모듈 → density 측정
  · ADR-006 픽셀 처리만, 운명·길흉 매핑 X
"""

from __future__ import annotations

import numpy as np


def _binary_erode(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """3x3 cross structuring element 침식 (순수 numpy).

    Args:
        mask: (H, W) binary array (bool or 0/1).
        iterations: 반복 횟수.

    Returns:
        침식된 마스크.
    """
    m = mask.astype(bool).copy()
    for _ in range(iterations):
        # 3x3 cross: 상하좌우 모두 True → True
        up = np.roll(m, -1, axis=0)
        down = np.roll(m, 1, axis=0)
        left = np.roll(m, -1, axis=1)
        right = np.roll(m, 1, axis=1)
        # 경계는 외부가 False라 가정 — roll로 wrap-around 되므로 경계 강제 False
        up[-1, :] = False
        down[0, :] = False
        left[:, -1] = False
        right[:, 0] = False
        m = m & up & down & left & right
    return m


def _binary_dilate(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """3x3 cross structuring element 팽창 (순수 numpy)."""
    m = mask.astype(bool).copy()
    for _ in range(iterations):
        up = np.roll(m, -1, axis=0)
        down = np.roll(m, 1, axis=0)
        left = np.roll(m, -1, axis=1)
        right = np.roll(m, 1, axis=1)
        up[-1, :] = False
        down[0, :] = False
        left[:, -1] = False
        right[:, 0] = False
        m = m | up | down | left | right
    return m


def opening(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """침식 → 팽창 (작은 노이즈 제거, 굵은 선 형태 유지)."""
    eroded = _binary_erode(mask, iterations)
    return _binary_dilate(eroded, iterations)


def closing(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """팽창 → 침식 (끊긴 선 연결, 작은 구멍 메움)."""
    dilated = _binary_dilate(mask, iterations)
    return _binary_erode(dilated, iterations)


def remove_small_components(
    mask: np.ndarray, min_size: int = 30,
) -> np.ndarray:
    """연결 컴포넌트 중 픽셀 수 < min_size 제거 (BFS, 순수 numpy).

    Args:
        mask: (H, W) binary.
        min_size: 유지할 최소 컴포넌트 픽셀 수.

    Returns:
        작은 컴포넌트 제거된 마스크.
    """
    m = mask.astype(bool).copy()
    h, w = m.shape
    visited = np.zeros_like(m, dtype=bool)
    result = np.zeros_like(m, dtype=bool)

    for y in range(h):
        for x in range(w):
            if not m[y, x] or visited[y, x]:
                continue
            # BFS 컴포넌트 추출 (4-connectivity)
            stack = [(y, x)]
            component = []
            while stack:
                cy, cx = stack.pop()
                if cy < 0 or cy >= h or cx < 0 or cx >= w:
                    continue
                if visited[cy, cx] or not m[cy, cx]:
                    continue
                visited[cy, cx] = True
                component.append((cy, cx))
                stack.extend([(cy - 1, cx), (cy + 1, cx),
                              (cy, cx - 1), (cy, cx + 1)])
            if len(component) >= min_size:
                for cy, cx in component:
                    result[cy, cx] = True
    return result


def skeletonize(mask: np.ndarray, max_iterations: int = 100) -> np.ndarray:
    """Zhang-Suen 알고리즘 (1984) — 1픽셀 두께 골격 추출.

    학술 출처:
      Zhang, T.Y. and Suen, C.Y. (1984)
      "A fast parallel algorithm for thinning digital patterns"
      Communications of the ACM, 27(3), 236-239.

    Args:
        mask: (H, W) binary.
        max_iterations: 무한 루프 방지.

    Returns:
        skeleton (1픽셀 두께).
    """
    m = mask.astype(bool).copy()
    h, w = m.shape

    for _ in range(max_iterations):
        # Sub-iteration 1
        to_remove = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not m[y, x]:
                    continue
                # 8-neighbors (P2~P9, clockwise from top)
                p = [
                    m[y - 1, x],     # P2 top
                    m[y - 1, x + 1], # P3 top-right
                    m[y, x + 1],     # P4 right
                    m[y + 1, x + 1], # P5 bottom-right
                    m[y + 1, x],     # P6 bottom
                    m[y + 1, x - 1], # P7 bottom-left
                    m[y, x - 1],     # P8 left
                    m[y - 1, x - 1], # P9 top-left
                ]
                B = sum(p)
                if B < 2 or B > 6:
                    continue
                # A = 0→1 전이 수 (시계 방향)
                p_cyc = p + [p[0]]
                A = sum(1 for i in range(8) if not p_cyc[i] and p_cyc[i + 1])
                if A != 1:
                    continue
                # P2*P4*P6 = 0 and P4*P6*P8 = 0
                if p[0] and p[2] and p[4]:
                    continue
                if p[2] and p[4] and p[6]:
                    continue
                to_remove.append((y, x))
        if not to_remove:
            break
        for y, x in to_remove:
            m[y, x] = False

        # Sub-iteration 2 (대칭 조건)
        to_remove2 = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not m[y, x]:
                    continue
                p = [
                    m[y - 1, x], m[y - 1, x + 1], m[y, x + 1], m[y + 1, x + 1],
                    m[y + 1, x], m[y + 1, x - 1], m[y, x - 1], m[y - 1, x - 1],
                ]
                B = sum(p)
                if B < 2 or B > 6:
                    continue
                p_cyc = p + [p[0]]
                A = sum(1 for i in range(8) if not p_cyc[i] and p_cyc[i + 1])
                if A != 1:
                    continue
                # P2*P4*P8 = 0 and P2*P6*P8 = 0
                if p[0] and p[2] and p[6]:
                    continue
                if p[0] and p[4] and p[6]:
                    continue
                to_remove2.append((y, x))
        if not to_remove2:
            break
        for y, x in to_remove2:
            m[y, x] = False

    return m


def postprocess_palm_mask(
    raw_mask: np.ndarray,
    apply_closing: bool = True,
    apply_opening: bool = True,
    min_component_size: int = 30,
    apply_skeleton: bool = False,
) -> dict:
    """ADR-252 — 종합 후처리 파이프라인.

    순서:
      1. closing (끊긴 선 연결, iter=1)
      2. opening (점 노이즈 제거, iter=1)
      3. small component removal (< min_component_size 픽셀)
      4. (선택) skeletonize (시각화·선 길이 측정)

    Args:
        raw_mask: CFM 원본 마스크 (H, W) binary.
        apply_closing, apply_opening: morphology 적용 여부.
        min_component_size: 컴포넌트 제거 임계값.
        apply_skeleton: skeleton 추출 여부 (느림, 옵션).

    Returns:
        {
            "raw": 원본,
            "closed": closing 결과,
            "opened": opening 결과,
            "cleaned": component 제거 결과 (최종 후처리 마스크),
            "skeleton": (선택) 골격,
        }
    """
    result: dict = {"raw": raw_mask.astype(bool)}
    current = raw_mask.astype(bool)
    if apply_closing:
        current = closing(current)
        result["closed"] = current.copy()
    if apply_opening:
        current = opening(current)
        result["opened"] = current.copy()
    if min_component_size > 0:
        current = remove_small_components(current, min_component_size)
        result["cleaned"] = current.copy()
    else:
        result["cleaned"] = current
    if apply_skeleton:
        result["skeleton"] = skeletonize(current)
    return result
