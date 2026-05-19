// ============================================================
// 운학 도사 · 얼굴 풀이 (관상) — ADR-037 Phase 1c + ADR-038 외부 모듈화
// ============================================================
// 의존: window.BaseReader, window.LLMUtils, window.HtmlUtils, window.FaceVisualizations
// ============================================================
(function initFaceReading() {
  const $ = (id) => document.getElementById(id);

  /**
   * FaceReader — 운학 도사 (관상)
   *  - 카메라(전면) + 사진 업로드 → 얼굴 캡처 → Opus Vision + Gemini 풀이
   *  - 다운샘플 1280px (Railway 60s 타임아웃 회피) — LLMUtils 사용
   *  - 시각화는 window.FaceVisualizations 글로벌 직접 호출
   *  - window.BaseReader 글로벌 추상 class 상속
   */
  class FaceReader extends window.BaseReader {
    constructor() {
      super({
        persona: '운학 도사',
        endpoint: '/api/face/reading',
        tabId: 'tab-face',
        stepPrefix: 'face-step-',
        boardId: 'faceResultBoard',
        WHMKey: 'physiognomy',
      });
      this.stream = null;
      this.capturedDataUrl = null;
    }
    updateReadButton() {
      const btn = $('faceReadBtn');
      if (!btn) return;
      btn.disabled = !this.capturedDataUrl;
    }
    async startCamera() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          alert('이 브라우저에서는 카메라를 쓸 수 없네. 사진 파일을 올려주시게나.');
          return;
        }
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1024 }, height: { ideal: 1024 } },
          audio: false,
        });
        const video = $('faceVideo');
        video.srcObject = this.stream;
        $('faceCameraArea').style.display = 'block';
        $('facePreviewArea').style.display = 'none';
      } catch (err) {
        alert('카메라를 열 수 없네: ' + (err.message || err));
        console.error(err);
      }
    }
    stopCamera() {
      if (this.stream) {
        this.stream.getTracks().forEach(t => t.stop());
        this.stream = null;
      }
      $('faceCameraArea').style.display = 'none';
    }
    captureFromVideo() {
      const video = $('faceVideo');
      if (!video || !video.videoWidth) return;
      const canvas = $('faceCanvas');
      const maxSide = 1024;
      let w = video.videoWidth, h = video.videoHeight;
      const scale = Math.min(1, maxSide / Math.max(w, h));
      w = Math.round(w * scale); h = Math.round(h * scale);
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(video, 0, 0, w, h);
      this.capturedDataUrl = canvas.toDataURL('image/jpeg', 0.85);
      this.showCapturedPreview();
      this.stopCamera();
    }
    showCapturedPreview() {
      if (!this.capturedDataUrl) return;
      $('facePreviewImg').src = this.capturedDataUrl;
      $('facePreviewArea').style.display = 'block';
      this.updateReadButton();
    }
    loadFromFile(file) {
      if (!file) return;
      if (!file.type.startsWith('image/')) { alert('사진 파일만 올려주시게나.'); return; }
      const maxFileSize = 5 * 1024 * 1024;
      if (file.size > maxFileSize) {
        alert('사진이 커서 자동으로 크기를 조정했습니다. 선명한 사진이라면 다시 올려주시게나.');
      }
      const fr = new FileReader();
      fr.onload = () => {
        const img = new Image();
        img.onload = () => {
          const canvas = $('faceCanvas');
          const maxSide = 1024;
          let w = img.naturalWidth, h = img.naturalHeight;
          const scale = Math.min(1, maxSide / Math.max(w, h));
          w = Math.round(w * scale); h = Math.round(h * scale);
          canvas.width = w; canvas.height = h;
          canvas.getContext('2d').drawImage(img, 0, 0, w, h);
          this.capturedDataUrl = canvas.toDataURL('image/jpeg', 0.85);
          const originalMaxSide = Math.max(img.naturalWidth, img.naturalHeight);
          if (originalMaxSide > maxSide) {
            const infoDiv = document.createElement('div');
            infoDiv.style.cssText = 'margin-top: 10px; padding: 8px 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; font-size: 13px; color: #856404; text-align: center;';
            infoDiv.textContent = `(${originalMaxSide}px에서 ${maxSide}px로 자동 조정됨)`;
            const preview = $('facePreviewArea');
            if (preview && !preview.querySelector('[style*="ffc107"]')) preview.appendChild(infoDiv);
          }
          this.showCapturedPreview();
          this.stopCamera();
        };
        img.onerror = () => alert('사진을 읽을 수 없네.');
        img.src = fr.result;
      };
      fr.onerror = () => alert('사진을 읽을 수 없네.');
      fr.readAsDataURL(file);
    }
    resetAll() {
      this.capturedDataUrl = null;
      this.stopCamera();
      $('facePreviewArea').style.display = 'none';
      const upload = $('faceUploadInput');
      if (upload) upload.value = '';
      $(this.boardId).innerHTML = '';
      this.updateReadButton();
      this.showStep('input');
    }
    renderResult(data) {
      const text = (data && data.text) ? data.text : '(풀이를 받지 못했네.)';
      const cached = data && data.cached;
      const crisis = data && data.crisis_alert;
      const board = $(this.boardId);
      const escaped = window.HtmlUtils.escapeHtml(text);

      let crisisBlock = '';
      if (crisis) {
        crisisBlock = `<div style="margin-top:16px;padding:14px;background:rgba(176,79,79,0.10);border:1px solid rgba(176,79,79,0.35);border-radius:3px;color:#e9b3a8;font-size:13px;line-height:1.7;font-family:'Nanum Myeongjo',serif;letter-spacing:1px">
          마음이 무거우시다면 혼자 견디지 마시게.<br>
          자살예방상담전화 <b>1393</b> &nbsp;·&nbsp; 정신건강위기상담 <b>1577-0199</b>
        </div>`;
      }

      const vizBlock = (window.FaceVisualizations && window.FaceVisualizations.renderVisualizations)
        ? window.FaceVisualizations.renderVisualizations(data) : '';

      board.innerHTML = `
        <div class="face-result-card">
          <h2 class="story-title">운 학 도 사 의 얼 굴 풀 이</h2>
          ${vizBlock}
          <div class="face-result-text">${escaped}</div>
          ${crisisBlock}
          <div class="face-result-meta">
            ${cached ? '이전에 풀었던 상이로세' : '운학 도사가 갓 살핀 상이로세'}
          </div>
        </div>
      `;
    }
    async request() {
      if (!this.capturedDataUrl) { alert('사진을 먼저 담아주시게나.'); return; }
      const ageRaw = ($('faceAge').value || '').trim();
      const age = ageRaw ? parseInt(ageRaw, 10) : null;
      const gender = ($('faceGender').value || '').trim() || null;
      const question = ($('faceQuestion').value || '').trim() || null;

      this.showStep('loading');
      const loadingMsgEl = document.querySelector('#face-step-loading .face-loading-msg');
      const originalLoadingMsg = loadingMsgEl ? loadingMsgEl.textContent : null;
      try {
        const sentImage = await window.LLMUtils.downsampleDataUrl(this.capturedDataUrl, 1280, 0.85);
        const resp = await this.post({
          image_base64: sentImage,
          age: Number.isFinite(age) ? age : null,
          gender,
          question,
        }, {
          retries: 1,
          backoffMs: 3000,
          onRetry: (attempt, status) => {
            if (loadingMsgEl) loadingMsgEl.textContent = `허허, 길이 잠시 막혔으니 다시 살펴보겠네… (${status})`;
          },
        });
        if (!resp.ok) {
          const errText = await resp.text();
          throw new Error(`서버 오류 (${resp.status}): ${errText}`);
        }
        const data = await resp.json();
        this.renderResult(data);
        this.showStep('result');
        this.markCompleted({});
      } catch (err) {
        $(this.boardId).innerHTML = `
          <div class="face-result-card">
            <div class="face-result-text" style="color:#ffb3b3">
              허허, 풀이 도중 길이 막혔구먼.<br><br>
              <code style="font-size:12px;color:#ffd6d6">${window.HtmlUtils.escapeHtml(err.message || err)}</code>
            </div>
          </div>`;
        this.showStep('result');
      } finally {
        if (loadingMsgEl && originalLoadingMsg != null) loadingMsgEl.textContent = originalLoadingMsg;
      }
    }
  }

  const reader = new FaceReader();
  window.faceReader = reader;

  function bind() {
    if (!$('faceStartCameraBtn')) return;

    $('faceStartCameraBtn').addEventListener('click', () => reader.startCamera());
    $('faceCancelCameraBtn').addEventListener('click', () => reader.stopCamera());
    $('faceCaptureBtn').addEventListener('click', () => reader.captureFromVideo());
    $('faceRetakeBtn').addEventListener('click', () => {
      reader.capturedDataUrl = null;
      $('facePreviewArea').style.display = 'none';
      const upload = $('faceUploadInput');
      if (upload) upload.value = '';
      reader.updateReadButton();
      reader.startCamera();
    });
    $('faceUploadInput').addEventListener('change', (e) => {
      reader.loadFromFile(e.target.files && e.target.files[0]);
    });
    $('faceReadBtn').addEventListener('click', () => reader.request());
    $('faceRestartBtn').addEventListener('click', () => reader.resetAll());

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.tab !== 'face') reader.stopCamera();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
