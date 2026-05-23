/**
 * ADR-194 + ADR-195 — 디바이스 호환성 감지 + 사용자 경고
 *
 * 1. iOS 16+ 검증 (MediaPipe WebGL 안정 작동 기준)
 * 2. WebGPU 지원 감지 (성능 향상 기회 안내)
 * 3. WebGL 2 fallback 검증
 *
 * 출처:
 *   - WebKit Safari 26.2 (iOS 26+ WebGPU)
 *   - https://docs.uaparser.dev/guides/how-to-detect-ios-26-using-javascript.html
 *   - https://ai.google.dev/edge/mediapipe/framework/getting_started/gpu_support
 */
(function () {
  'use strict';

  /**
   * ADR-194 — iOS Safari 버전 감지.
   * iOS 26+ 부터 user-agent 가 frozen — Version/26.0 토큰이 Safari major 노출.
   *
   * @returns {object} {is_ios, is_safari, major_version, supported}
   *   supported = iOS 16+ (MediaPipe WebGL 안정 작동 기준)
   */
  function detectIOS() {
    const ua = navigator.userAgent || '';
    const isIOS = /iPad|iPhone|iPod/.test(ua) ||
      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isSafari = /^((?!chrome|android).)*safari/i.test(ua);

    let major = 0;

    // iOS 26+ frozen user-agent — Version/<safariMajor> 가 가장 신뢰
    const versionMatch = ua.match(/Version\/(\d+)/);
    if (versionMatch) {
      const safariMajor = parseInt(versionMatch[1], 10);
      // Safari major ↔ iOS major (iOS 16+ 부터 일치 보장 안 됨, frozen 시 Safari 만 ↑)
      if (safariMajor >= 26) major = 26;  // iOS 26+ (frozen)
      else if (safariMajor >= 16) major = safariMajor;
    }

    // iOS 25 이하 — OS 토큰 사용 (frozen 전)
    if (major === 0) {
      const osMatch = ua.match(/OS (\d+)_/);
      if (osMatch) {
        const osMajor = parseInt(osMatch[1], 10);
        if (osMajor >= 1 && osMajor <= 25) major = osMajor;
      }
    }

    return {
      is_ios: isIOS,
      is_safari: isSafari,
      major_version: major,
      supported: !isIOS || major >= 16,  // 비 iOS 또는 iOS 16+ 면 지원
    };
  }

  /**
   * ADR-195 — WebGPU 지원 감지 (비동기 — adapter 요청까지).
   *
   * @returns {Promise<object>} {webgpu_available, webgl2_available, backend}
   *   backend = 'webgpu' | 'webgl2' | 'cpu'
   */
  async function detectGpuBackend() {
    let webgpuOk = false;
    let webgl2Ok = false;

    // WebGPU 감지
    if (typeof navigator !== 'undefined' && navigator.gpu) {
      try {
        const adapter = await navigator.gpu.requestAdapter();
        if (adapter) {
          webgpuOk = true;
        }
      } catch (err) {
        webgpuOk = false;
      }
    }

    // WebGL2 fallback 감지
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2');
      if (gl) {
        webgl2Ok = true;
      }
    } catch (err) {
      webgl2Ok = false;
    }

    let backend;
    if (webgpuOk) backend = 'webgpu';
    else if (webgl2Ok) backend = 'webgl2';
    else backend = 'cpu';

    return {
      webgpu_available: webgpuOk,
      webgl2_available: webgl2Ok,
      backend,
    };
  }

  /**
   * 통합 호환성 체크 — iOS + GPU.
   *
   * @returns {Promise<object>} {compatible, warning, ios, gpu}
   *   compatible = true 면 MediaPipe 작동 보장
   *   warning = 사용자 표시할 한국어 메시지 (또는 빈 문자열)
   */
  async function checkCompatibility() {
    const ios = detectIOS();
    const gpu = await detectGpuBackend();

    const compatible = ios.supported && (gpu.webgpu_available || gpu.webgl2_available);

    let warning = '';
    if (ios.is_ios && !ios.supported) {
      warning = (
        'iOS 15 이하 버전에서는 관상·손금 분석 정확도가 떨어질 수 있습니다. ' +
        'iOS 16 이상으로 업그레이드하시면 더 정확한 결과를 받으실 수 있습니다.'
      );
    } else if (!gpu.webgl2_available && !gpu.webgpu_available) {
      warning = (
        '이 기기는 GPU 가속을 지원하지 않아 분석 속도가 느릴 수 있습니다.'
      );
    }

    return { compatible, warning, ios, gpu };
  }

  window.DeviceCompat = { detectIOS, detectGpuBackend, checkCompatibility };
})();
