// ============================================================
// 손금 메트릭 산출 — MediaPipe Hand Landmarker 클라이언트 측 추론 (ADR-160)
// ============================================================
// 의존: @mediapipe/tasks-vision (CDN 동적 import, 손금 탭 진입 시에만 로드)
// 출력: engine/divination/palm/scoring.py `score_palm` 가 기대하는 keypoints dict
//   { "kp0": [x, y, z], "kp1": [...], ..., "kp20": [...] }
// MediaPipe Hand Landmarker 21 keypoint 표준
// 출처: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
// ============================================================
(function initPalmMetrics() {
  const TASKS_VISION_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/vision_bundle.mjs';
  const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';
  const WASM_ROOT = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm';

  let _landmarkerPromise = null;

  async function getLandmarker() {
    if (_landmarkerPromise) return _landmarkerPromise;
    _landmarkerPromise = (async () => {
      const vision = await import(TASKS_VISION_CDN);
      const fileset = await vision.FilesetResolver.forVisionTasks(WASM_ROOT);
      return vision.HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'IMAGE',
        numHands: 1,
        // ADR-271 — 검출 임계 낮춤 (어두운 사진/얼굴 가림 등에도 검출)
        minHandDetectionConfidence: 0.3,
        minHandPresenceConfidence: 0.3,
        minTrackingConfidence: 0.3,
      });
    })().catch(err => { _landmarkerPromise = null; throw err; });
    return _landmarkerPromise;
  }

  // MediaPipe Hand Landmarker 21 keypoint 인덱스 (표준 손 모델)
  // 0: WRIST (손목)
  // 1-4: THUMB (엄지) — CMC·MCP·IP·TIP
  // 5-8: INDEX (검지) — MCP·PIP·DIP·TIP
  // 9-12: MIDDLE (중지) — MCP·PIP·DIP·TIP
  // 13-16: RING (약지) — MCP·PIP·DIP·TIP
  // 17-20: PINKY (소지) — MCP·PIP·DIP·TIP
  const KP_NAMES = {
    0: 'WRIST',
    1: 'THUMB_CMC', 2: 'THUMB_MCP', 3: 'THUMB_IP', 4: 'THUMB_TIP',
    5: 'INDEX_MCP', 6: 'INDEX_PIP', 7: 'INDEX_DIP', 8: 'INDEX_TIP',
    9: 'MIDDLE_MCP', 10: 'MIDDLE_PIP', 11: 'MIDDLE_DIP', 12: 'MIDDLE_TIP',
    13: 'RING_MCP', 14: 'RING_PIP', 15: 'RING_DIP', 16: 'RING_TIP',
    17: 'PINKY_MCP', 18: 'PINKY_PIP', 19: 'PINKY_DIP', 20: 'PINKY_TIP',
  };

  /**
   * MediaPipe 21 landmark → score_palm 기대 keypoints dict.
   * 입력: normalized landmarks (x·y∈[0,1], z 상대 깊이)
   * 출력: {"kp0": [x, y, z], "kp1": [...], ..., "kp20": [...]}
   */
  function _toKeypointsDict(landmarks) {
    const out = {};
    for (let i = 0; i < landmarks.length && i <= 20; i++) {
      const p = landmarks[i];
      out[`kp${i}`] = [p.x, p.y, p.z || 0];
    }
    return out;
  }

  /**
   * 손 좌·우 분류 (MediaPipe handedness 결과 → 본 시스템 한국어 라벨).
   * 주의: MediaPipe는 셀카 미러 기준 — 'Left' 라벨이 실 오른손인 경우 다수.
   * 본 시스템은 MediaPipe 라벨 그대로 전달 + 사용자 입력 hand가 우선.
   */
  function _classifyHandSide(handedness) {
    if (!handedness || !handedness.length) return 'unknown';
    const cat = handedness[0]?.categoryName || '';
    if (cat === 'Left') return 'left_mp';   // MediaPipe 'Left' (셀카 미러 영향)
    if (cat === 'Right') return 'right_mp';
    return 'unknown';
  }

  /**
   * 이미지 element/canvas/dataURL → palm keypoints + 메타.
   * @param {HTMLImageElement|HTMLCanvasElement} imageSource
   * @returns {Promise<object|null>} { keypoints, hand_side_mp, confidence } 또는 null
   */
  async function computeMetrics(imageSource) {
    try {
      const landmarker = await getLandmarker();
      const result = landmarker.detect(imageSource);
      if (!result || !result.landmarks || result.landmarks.length === 0) {
        return null;
      }
      const lm = result.landmarks[0];
      const handedness = result.handedness && result.handedness[0];
      return {
        keypoints: _toKeypointsDict(lm),
        hand_side_mp: _classifyHandSide(handedness),
        keypoint_names: KP_NAMES,
        landmark_count: lm.length,
      };
    } catch (err) {
      console.warn('[palm-metrics] 메트릭 산출 실패 — 결정론 점수는 LLM Vision 폴백:', err);
      return null;
    }
  }

  window.PalmMetrics = { computeMetrics };
})();
