/**
 * ADR-088 — 결과 이미지 공유 유틸리티.
 *
 * 사용자가 운세 결과 DOM 영역을 캔버스로 캡처 + 다운로드 또는 네이티브 공유 시트 호출.
 *
 * 외부 의존 X (html2canvas 부재 시 native canvas + html2img.js 동적 fallback).
 * CORS 방어: image crossOrigin="anonymous" 자동 설정.
 *
 * ADR-006 면책: 이미지 캡처에는 사용자가 본 시스템 결과만 포함.
 * 인용 시 EU AI Act §50 라벨 자동 합성.
 */

(function () {
  'use strict';

  /**
   * Web Share API 지원 여부 확인.
   */
  function canShareFiles() {
    if (!navigator.share || !navigator.canShare) return false;
    try {
      const testFile = new File([new Blob([''])], 'test.txt', { type: 'text/plain' });
      return navigator.canShare({ files: [testFile] });
    } catch (e) {
      return false;
    }
  }

  /**
   * 강제 다운로드 (모든 브라우저 fallback).
   *
   * @param {Blob} blob - 이미지 Blob
   * @param {string} filename - 다운로드 파일명
   */
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 500);
  }

  /**
   * Web Share API 호출 (모바일 네이티브 공유 시트).
   *
   * @param {Blob} blob - 이미지 Blob
   * @param {string} filename
   * @param {object} opts - { title, text }
   * @returns {Promise<boolean>} 공유 성공 여부
   */
  async function shareImage(blob, filename, opts = {}) {
    if (!canShareFiles()) {
      // fallback to download
      downloadBlob(blob, filename);
      return false;
    }
    try {
      const file = new File([blob], filename, { type: blob.type || 'image/png' });
      const shareData = {
        files: [file],
        title: opts.title || '운세 결과',
        text: opts.text || '본 결과는 AI에 의해 생성되었습니다 (EU AI Act §50).',
      };
      if (!navigator.canShare(shareData)) {
        downloadBlob(blob, filename);
        return false;
      }
      await navigator.share(shareData);
      return true;
    } catch (err) {
      // 사용자 취소 또는 권한 거부 — fallback
      if (err && err.name !== 'AbortError') {
        downloadBlob(blob, filename);
      }
      return false;
    }
  }

  /**
   * DOM 엘리먼트 → Canvas 변환 (CORS 방어).
   *
   * 외부 라이브러리 의존 없이 SVG foreignObject 기법 사용.
   * 모든 <img> 태그에 crossOrigin="anonymous" 자동 설정.
   *
   * @param {HTMLElement} element - 캡처 대상
   * @param {object} opts - { width, height, scale }
   * @returns {Promise<HTMLCanvasElement>}
   */
  async function domToCanvas(element, opts = {}) {
    if (!element) throw new Error('element required');

    const rect = element.getBoundingClientRect();
    const scale = opts.scale || (window.devicePixelRatio || 1);
    const width = opts.width || rect.width;
    const height = opts.height || rect.height;

    // 모든 외부 img에 crossOrigin 강제 (Tainted Canvas 방어)
    const imgs = element.querySelectorAll('img');
    await Promise.all(Array.from(imgs).map((img) => {
      return new Promise((resolve) => {
        if (img.complete && img.naturalWidth > 0) {
          if (!img.crossOrigin) img.crossOrigin = 'anonymous';
          resolve();
        } else {
          img.crossOrigin = 'anonymous';
          img.onload = () => resolve();
          img.onerror = () => resolve();
        }
      });
    }));

    // DOM HTML → SVG foreignObject
    const clone = element.cloneNode(true);
    const xhtml = new XMLSerializer().serializeToString(clone);
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
        <foreignObject width="100%" height="100%">
          <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: sans-serif;">
            ${xhtml}
          </div>
        </foreignObject>
      </svg>`;

    const svgBlob = new Blob([svg], { type: 'image/svg+xml' });
    const svgUrl = URL.createObjectURL(svgBlob);

    const canvas = document.createElement('canvas');
    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext('2d');

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        ctx.scale(scale, scale);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(svgUrl);
        resolve(canvas);
      };
      img.onerror = () => {
        URL.revokeObjectURL(svgUrl);
        reject(new Error('SVG to canvas conversion failed'));
      };
      img.src = svgUrl;
    });
  }

  /**
   * Canvas → Blob (JPEG 우선, PNG fallback).
   *
   * @param {HTMLCanvasElement} canvas
   * @param {string} mime - 'image/jpeg' | 'image/png'
   * @param {number} quality - 0.0~1.0
   * @returns {Promise<Blob>}
   */
  function canvasToBlob(canvas, mime = 'image/jpeg', quality = 0.92) {
    return new Promise((resolve, reject) => {
      if (canvas.toBlob) {
        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
          else reject(new Error('toBlob returned null'));
        }, mime, quality);
      } else {
        // Old browsers fallback
        try {
          const dataUrl = canvas.toDataURL(mime, quality);
          fetch(dataUrl).then((r) => r.blob()).then(resolve).catch(reject);
        } catch (e) {
          reject(e);
        }
      }
    });
  }

  /**
   * 통합 헬퍼 — DOM → 다운로드 또는 공유.
   *
   * @param {HTMLElement} element
   * @param {object} opts - { filename, title, text, mime, quality, scale }
   * @returns {Promise<{shared: boolean, downloaded: boolean}>}
   */
  async function shareOrDownload(element, opts = {}) {
    const canvas = await domToCanvas(element, opts);
    const blob = await canvasToBlob(canvas, opts.mime, opts.quality);
    const filename = opts.filename || `운세-${Date.now()}.jpg`;

    if (canShareFiles()) {
      const shared = await shareImage(blob, filename, opts);
      return { shared, downloaded: !shared };
    } else {
      downloadBlob(blob, filename);
      return { shared: false, downloaded: true };
    }
  }

  // 글로벌 노출
  window.ShareUtils = {
    canShareFiles,
    downloadBlob,
    shareImage,
    domToCanvas,
    canvasToBlob,
    shareOrDownload,
  };
})();
