/**
 * ADR-182 — face-complexion.js
 *
 * MediaPipe Face Landmarker 478 keypoint → 8 ROI 평균 RGB 산출.
 * ADR-178 engine/divination/face/complexion.py 의 입력 형식 충족.
 *
 * ROI 정의 (Biomedical Dermatology 2017 N=543 표준):
 *   forehead, nose_tip, chin, cheekbone, cheek, jaw, neck, nose_bridge
 *
 * ROI 마스크는 keypoint 중심 + 작은 반경 사각형 평균 (보수적).
 * 큰 ROI 마스크는 다른 부위 색 섞임 위험 — 작은 반경 우선.
 */
(function () {
  'use strict';

  // MediaPipe Face Landmarker 478 keypoint 인덱스
  // 출처: front/js/readers/face-metrics.js 와 동일
  const KP = {
    FOREHEAD_CENTER: 9,       // 이마 중앙
    NOSE_TIP: 1,              // 코끝
    NOSE_BRIDGE_MID: 168,     // 콧대 중간
    CHIN_CENTER: 199,         // 턱 중앙
    CHEEK_LEFT: 234,          // 좌측 광대 옆
    CHEEK_RIGHT: 454,         // 우측 광대 옆
    CHEEKBONE_LEFT: 116,      // 좌측 광대
    CHEEKBONE_RIGHT: 345,     // 우측 광대
    JAW_LEFT: 172,            // 좌측 턱선
    JAW_RIGHT: 397,           // 우측 턱선
    NECK_LEFT: 152,           // 턱 최하단 (목 근사)
  };

  // ROI별 keypoint + 샘플링 반경 (얼굴 너비 대비 비율)
  // 반경 작을수록 다른 부위 색 섞임 ↓, 잡음 ↑
  const ROI_DEFS = {
    forehead: { kp: KP.FOREHEAD_CENTER, radius_ratio: 0.04 },
    nose_tip: { kp: KP.NOSE_TIP, radius_ratio: 0.02 },
    nose_bridge: { kp: KP.NOSE_BRIDGE_MID, radius_ratio: 0.02 },
    chin: { kp: KP.CHIN_CENTER, radius_ratio: 0.03 },
    cheekbone: { kp_pair: [KP.CHEEKBONE_LEFT, KP.CHEEKBONE_RIGHT], radius_ratio: 0.03 },
    cheek: { kp_pair: [KP.CHEEK_LEFT, KP.CHEEK_RIGHT], radius_ratio: 0.03 },
    jaw: { kp_pair: [KP.JAW_LEFT, KP.JAW_RIGHT], radius_ratio: 0.025 },
    neck: { kp: KP.NECK_LEFT, radius_ratio: 0.02 },
  };

  function _faceWidth(lm) {
    const dx = lm[KP.CHEEK_RIGHT].x - lm[KP.CHEEK_LEFT].x;
    const dy = lm[KP.CHEEK_RIGHT].y - lm[KP.CHEEK_LEFT].y;
    return Math.hypot(dx, dy);
  }

  /**
   * 캔버스에서 (cx,cy) 중심 반경 r 픽셀의 평균 RGB 산출.
   */
  function _samplePixelAverage(ctx, cx, cy, r, imgW, imgH) {
    const x0 = Math.max(0, Math.floor(cx - r));
    const y0 = Math.max(0, Math.floor(cy - r));
    const x1 = Math.min(imgW - 1, Math.ceil(cx + r));
    const y1 = Math.min(imgH - 1, Math.ceil(cy + r));
    const w = x1 - x0 + 1;
    const h = y1 - y0 + 1;
    if (w <= 0 || h <= 0) return null;
    try {
      const data = ctx.getImageData(x0, y0, w, h).data;
      let rSum = 0, gSum = 0, bSum = 0, n = 0;
      for (let i = 0; i < data.length; i += 4) {
        // 알파 0인 픽셀 제외
        if (data[i + 3] < 32) continue;
        rSum += data[i];
        gSum += data[i + 1];
        bSum += data[i + 2];
        n++;
      }
      if (n === 0) return null;
      return [rSum / n, gSum / n, bSum / n];
    } catch (err) {
      console.warn('[face-complexion] sample failed:', err);
      return null;
    }
  }

  /**
   * landmarks + 이미지 → 8 ROI 평균 RGB dict.
   * @param {Array} lm - MediaPipe 478 landmarks (normalized 0~1)
   * @param {HTMLCanvasElement} canvas - 사진 그려진 캔버스
   * @returns {object} {forehead: [r,g,b], nose_tip: [r,g,b], ...}
   */
  function computeRoiRgb(lm, canvas) {
    if (!lm || !canvas) return {};
    const ctx = canvas.getContext('2d');
    if (!ctx) return {};
    const W = canvas.width;
    const H = canvas.height;
    const faceWPx = _faceWidth(lm) * W;  // 정규화 좌표 → 픽셀
    const result = {};

    for (const [roiKey, def] of Object.entries(ROI_DEFS)) {
      const rPx = Math.max(2, def.radius_ratio * faceWPx);
      if (def.kp !== undefined) {
        const kp = lm[def.kp];
        const cx = kp.x * W;
        const cy = kp.y * H;
        const rgb = _samplePixelAverage(ctx, cx, cy, rPx, W, H);
        if (rgb) result[roiKey] = rgb;
      } else if (def.kp_pair) {
        // 좌·우 쌍 평균 RGB
        const samples = [];
        for (const kpIdx of def.kp_pair) {
          const kp = lm[kpIdx];
          const cx = kp.x * W;
          const cy = kp.y * H;
          const rgb = _samplePixelAverage(ctx, cx, cy, rPx, W, H);
          if (rgb) samples.push(rgb);
        }
        if (samples.length > 0) {
          const r = samples.reduce((s, x) => s + x[0], 0) / samples.length;
          const g = samples.reduce((s, x) => s + x[1], 0) / samples.length;
          const b = samples.reduce((s, x) => s + x[2], 0) / samples.length;
          result[roiKey] = [r, g, b];
        }
      }
    }
    return result;
  }

  window.FaceComplexion = { computeRoiRgb, ROI_DEFS };
})();
