// ============================================================
// 관상 메트릭 산출 — MediaPipe Face Landmarker 클라이언트 측 추론 (ADR-159)
// ============================================================
// 의존: @mediapipe/tasks-vision (CDN 동적 import, 관상 탭 진입 시에만 로드)
// 출력: engine/divination/face/scoring.py `score_face` 가 기대하는 metrics dict
// ============================================================
(function initFaceMetrics() {
  const TASKS_VISION_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/vision_bundle.mjs';
  const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';
  const WASM_ROOT = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm';

  let _landmarkerPromise = null;

  async function getLandmarker() {
    if (_landmarkerPromise) return _landmarkerPromise;
    _landmarkerPromise = (async () => {
      const vision = await import(TASKS_VISION_CDN);
      const fileset = await vision.FilesetResolver.forVisionTasks(WASM_ROOT);
      return vision.FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'IMAGE',
        numFaces: 1,
        outputFaceBlendshapes: true,
        outputFacialTransformationMatrixes: false,
      });
    })().catch(err => { _landmarkerPromise = null; throw err; });
    return _landmarkerPromise;
  }

  // MediaPipe Face Landmarker 478 keypoint 인덱스
  // 출처: https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
  const KP = {
    FOREHEAD_TOP: 10,        // 발제(이마 최상단)
    CHIN_BOTTOM: 152,        // 턱 최하단
    BROW_LEFT_INNER: 55,     // 좌측 눈썹 안쪽
    BROW_RIGHT_INNER: 285,   // 우측 눈썹 안쪽
    NOSE_TIP: 1,             // 코끝
    NOSE_BRIDGE_TOP: 6,      // 산근 (콧대 시작)
    EYE_LEFT_OUTER: 33,      // 좌측 눈꼬리(어미)
    EYE_LEFT_INNER: 133,     // 좌측 눈머리
    EYE_RIGHT_OUTER: 263,    // 우측 눈꼬리(어미)
    EYE_RIGHT_INNER: 362,    // 우측 눈머리
    FACE_LEFT: 234,          // 얼굴 좌측 가장자리 (광대 옆)
    FACE_RIGHT: 454,         // 얼굴 우측 가장자리
    NOSE_ALAR_LEFT: 49,      // 좌측 콧방울
    NOSE_ALAR_RIGHT: 279,    // 우측 콧방울
    MOUTH_CORNER_LEFT: 61,
    MOUTH_CORNER_RIGHT: 291,
    MOUTH_UPPER_CENTER: 13,
    MOUTH_LOWER_CENTER: 14,
    UNDER_EYE_LEFT: 145,     // 좌측 와잠 하단
    UNDER_EYE_RIGHT: 374,    // 우측 와잠 하단
  };

  function dist(p1, p2) {
    return Math.hypot(p2.x - p1.x, p2.y - p1.y);
  }

  function _computeThreeThirds(lm) {
    // 삼정 (상정·중정·하정) — 발제~눈썹, 눈썹~코끝, 인중~턱
    const top = lm[KP.FOREHEAD_TOP].y;
    const browY = (lm[KP.BROW_LEFT_INNER].y + lm[KP.BROW_RIGHT_INNER].y) / 2;
    const noseTipY = lm[KP.NOSE_TIP].y;
    const chinY = lm[KP.CHIN_BOTTOM].y;
    const total = chinY - top;
    if (total <= 0) return null;
    const upper = ((browY - top) / total) * 100;
    const middle = ((noseTipY - browY) / total) * 100;
    const lower = ((chinY - noseTipY) / total) * 100;
    return [upper, middle, lower];
  }

  function _computeEyeDistanceRatio(lm) {
    // 양 눈머리 거리 / 평균 눈 너비
    const inner = dist(lm[KP.EYE_LEFT_INNER], lm[KP.EYE_RIGHT_INNER]);
    const leftEyeW = dist(lm[KP.EYE_LEFT_OUTER], lm[KP.EYE_LEFT_INNER]);
    const rightEyeW = dist(lm[KP.EYE_RIGHT_OUTER], lm[KP.EYE_RIGHT_INNER]);
    const avgEyeW = (leftEyeW + rightEyeW) / 2;
    if (avgEyeW <= 0) return null;
    return inner / avgEyeW;
  }

  function _computeAlarRatio(lm) {
    // 콧방울 너비 / 얼굴 너비
    const alar = dist(lm[KP.NOSE_ALAR_LEFT], lm[KP.NOSE_ALAR_RIGHT]);
    const face = dist(lm[KP.FACE_LEFT], lm[KP.FACE_RIGHT]);
    if (face <= 0) return null;
    return alar / face;
  }

  function _computeCheoCheopRatio(lm) {
    // 눈꼬리(어미) 길이 — 외측 눈꼬리에서 광대까지 거리 / 얼굴 절반 너비
    const leftTail = dist(lm[KP.EYE_LEFT_OUTER], lm[KP.FACE_LEFT]);
    const rightTail = dist(lm[KP.EYE_RIGHT_OUTER], lm[KP.FACE_RIGHT]);
    const halfFace = dist(lm[KP.FACE_LEFT], lm[KP.FACE_RIGHT]) / 2;
    if (halfFace <= 0) return null;
    return ((leftTail + rightTail) / 2) / halfFace;
  }

  function _computeWajamRatio(lm) {
    // 와잠 두께 = 눈 아래 라인과 눈 외각선 거리 평균 / 눈 너비
    const leftEyeBottom = lm[KP.UNDER_EYE_LEFT];
    const rightEyeBottom = lm[KP.UNDER_EYE_RIGHT];
    const leftEyeOuter = lm[KP.EYE_LEFT_OUTER];
    const rightEyeOuter = lm[KP.EYE_RIGHT_OUTER];
    const leftW = dist(leftEyeOuter, lm[KP.EYE_LEFT_INNER]);
    const rightW = dist(rightEyeOuter, lm[KP.EYE_RIGHT_INNER]);
    const leftThick = Math.abs(leftEyeBottom.y - leftEyeOuter.y);
    const rightThick = Math.abs(rightEyeBottom.y - rightEyeOuter.y);
    const avgW = (leftW + rightW) / 2;
    if (avgW <= 0) return null;
    return ((leftThick + rightThick) / 2) / avgW;
  }

  function _computeAsymmetry(lm) {
    // 좌우 비대칭 — 코끝 기준 좌우 대응점 x 차이 평균 (정규화)
    const centerX = lm[KP.NOSE_TIP].x;
    const pairs = [
      [KP.EYE_LEFT_OUTER, KP.EYE_RIGHT_OUTER],
      [KP.EYE_LEFT_INNER, KP.EYE_RIGHT_INNER],
      [KP.BROW_LEFT_INNER, KP.BROW_RIGHT_INNER],
      [KP.NOSE_ALAR_LEFT, KP.NOSE_ALAR_RIGHT],
      [KP.MOUTH_CORNER_LEFT, KP.MOUTH_CORNER_RIGHT],
      [KP.FACE_LEFT, KP.FACE_RIGHT],
    ];
    const faceW = dist(lm[KP.FACE_LEFT], lm[KP.FACE_RIGHT]);
    if (faceW <= 0) return null;
    let sum = 0;
    for (const [l, r] of pairs) {
      const dL = centerX - lm[l].x;
      const dR = lm[r].x - centerX;
      sum += Math.abs(dL - dR) / faceW;
    }
    return sum / pairs.length;
  }

  function _computeHeadTilt(lm) {
    // 양 눈 외각선의 각도 (수평 대비, 도)
    const lEye = lm[KP.EYE_LEFT_OUTER];
    const rEye = lm[KP.EYE_RIGHT_OUTER];
    const dx = rEye.x - lEye.x;
    const dy = rEye.y - lEye.y;
    return Math.atan2(dy, dx) * (180 / Math.PI);
  }

  function _computeMouthCornerLift(lm) {
    // 입꼬리 올림 — 입꼬리 평균 y와 입 중심 y의 차이를 입 너비로 정규화
    const leftC = lm[KP.MOUTH_CORNER_LEFT];
    const rightC = lm[KP.MOUTH_CORNER_RIGHT];
    const upper = lm[KP.MOUTH_UPPER_CENTER];
    const lower = lm[KP.MOUTH_LOWER_CENTER];
    const cornerY = (leftC.y + rightC.y) / 2;
    const centerY = (upper.y + lower.y) / 2;
    const mouthW = dist(leftC, rightC);
    if (mouthW <= 0) return null;
    // +값 = 입꼬리가 중심보다 위 (앙월구 방향) — y 좌표가 위로 갈수록 작아짐
    return (centerY - cornerY) / mouthW;
  }

  function _extractBlendshapes(blendshapes) {
    // MediaPipe 52 blendshapes → 본 시스템 사용 키만 추출
    if (!blendshapes || !blendshapes.categories) return {};
    const map = {};
    for (const cat of blendshapes.categories) {
      // categoryName 은 'browInnerUp', 'mouthSmileLeft' 등 camelCase
      map[cat.categoryName] = cat.score;
    }
    return {
      brow_inner_up: map.browInnerUp,
      brow_down_left: map.browDownLeft,
      brow_down_right: map.browDownRight,
      eye_blink_left: map.eyeBlinkLeft,
      eye_blink_right: map.eyeBlinkRight,
      mouth_smile_left: map.mouthSmileLeft,
      mouth_smile_right: map.mouthSmileRight,
      jaw_open: map.jawOpen,
    };
  }

  function _classifyFaceShape(lm) {
    // ADR-022 5형 단순 분류 — face_width/face_height + 턱·이마 너비 비교
    const faceW = dist(lm[KP.FACE_LEFT], lm[KP.FACE_RIGHT]);
    const faceH = lm[KP.CHIN_BOTTOM].y - lm[KP.FOREHEAD_TOP].y;
    if (faceW <= 0 || faceH <= 0) return null;
    const ratio = faceH / faceW;
    if (ratio > 1.45) return 'long';
    if (ratio < 1.05) return 'round';
    // 중간대 — 턱 너비 vs 이마 너비
    // 단순화: oval 폴백 (정밀 분류는 백엔드 shape.py 위임 가능)
    return 'oval';
  }

  /**
   * 이미지 element/canvas/dataURL → 메트릭 dict 산출.
   * @param {HTMLImageElement|HTMLCanvasElement} imageSource
   * @returns {Promise<object|null>} metrics dict (실패 시 null)
   */
  async function computeMetrics(imageSource) {
    try {
      const landmarker = await getLandmarker();
      const result = landmarker.detect(imageSource);
      if (!result || !result.faceLandmarks || result.faceLandmarks.length === 0) {
        return null;
      }
      const lm = result.faceLandmarks[0];
      const blendshapes = (result.faceBlendshapes && result.faceBlendshapes[0]) || null;

      // ADR-273 — visualization 용 핵심 keypoint 추출 (전체 478 대신 12궁 매핑에 필요한 ~30개)
      const KP_FOR_VIZ = [10, 152, 55, 285, 1, 6, 33, 263, 133, 362,
                          234, 454, 49, 279, 61, 291, 13, 14, 145, 374,
                          168, 105, 334, 70, 300, 9, 175, 199, 17, 200];
      const keypoints_viz = {};
      for (const i of KP_FOR_VIZ) {
        if (lm[i]) {
          keypoints_viz[`kp${i}`] = [lm[i].x, lm[i].y, lm[i].z || 0];
        }
      }

      return {
        three_thirds: _computeThreeThirds(lm),
        eye_distance_ratio: _computeEyeDistanceRatio(lm),
        alar_ratio: _computeAlarRatio(lm),
        cheo_cheop_ratio: _computeCheoCheopRatio(lm),
        wajam_ratio: _computeWajamRatio(lm),
        asymmetry: _computeAsymmetry(lm),
        head_tilt_deg: _computeHeadTilt(lm),
        mouth_corner_lift: _computeMouthCornerLift(lm),
        blendshapes: _extractBlendshapes(blendshapes),
        face_shape: _classifyFaceShape(lm),
        face_keypoints: keypoints_viz,  // ADR-273 시각화용
      };
    } catch (err) {
      console.warn('[face-metrics] 메트릭 산출 실패 — 결정론 점수는 0.5 폴백:', err);
      return null;
    }
  }

  window.FaceMetrics = { computeMetrics };
})();
