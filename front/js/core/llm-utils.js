/**
 * window.LLMUtils — 7인 점술가 공용 비동기 유틸 (ADR-037 + ADR-038 Phase 2 ES6 분리)
 *  - fetchWithRetry: 502/503/504 + network 오류 자동 1회 재시도 (백오프 3초)
 *  - postJSON: POST + JSON.stringify + Content-Type 자동, 5xx 시 재시도 포함
 *  - downsampleDataUrl: 1280px 다운샘플 (Railway 60s 타임아웃 회피 + Vision API 가속)
 *
 * 본 파일은 ES6 module 전환 전 단계: classic <script src=> 로 로드.
 * window 글로벌 노출 유지 → 모든 reader IIFE가 변경 없이 사용 가능.
 */
(function(){
  async function fetchWithRetry(url, init, opts) {
    const { retries = 1, backoffMs = 3000, onRetry = null } = opts || {};
    let lastErr = null;
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const resp = await fetch(url, init);
        if (resp.status >= 500 && resp.status < 600 && attempt < retries) {
          if (onRetry) onRetry(attempt + 1, resp.status);
          await new Promise(r => setTimeout(r, backoffMs));
          continue;
        }
        return resp;
      } catch (e) {
        lastErr = e;
        if (attempt < retries) {
          if (onRetry) onRetry(attempt + 1, 'network');
          await new Promise(r => setTimeout(r, backoffMs));
          continue;
        }
        throw e;
      }
    }
    if (lastErr) throw lastErr;
    throw new Error('재시도 실패');
  }

  async function postJSON(url, payload, opts) {
    return fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }, opts);
  }

  function downsampleDataUrl(dataUrl, maxSide = 1280, quality = 0.85) {
    return new Promise((resolve) => {
      if (!dataUrl || typeof dataUrl !== 'string') { resolve(dataUrl); return; }
      const img = new Image();
      img.onload = () => {
        const w0 = img.naturalWidth || img.width;
        const h0 = img.naturalHeight || img.height;
        if (!w0 || !h0) { resolve(dataUrl); return; }
        if (w0 <= maxSide && h0 <= maxSide) { resolve(dataUrl); return; }
        const scale = maxSide / Math.max(w0, h0);
        const w = Math.round(w0 * scale), h = Math.round(h0 * scale);
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) { resolve(dataUrl); return; }
        ctx.drawImage(img, 0, 0, w, h);
        try { resolve(canvas.toDataURL('image/jpeg', quality)); }
        catch (e) { resolve(dataUrl); }
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  window.LLMUtils = { fetchWithRetry, postJSON, downsampleDataUrl };
})();
