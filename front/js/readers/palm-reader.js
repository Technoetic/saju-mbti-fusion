// ============================================================
// 옥선 할미 · 손금 풀이 (手相) — ADR-037 Phase 1b + ADR-038 외부 모듈화
// ============================================================
// 의존: window.BaseReader (base-reader.js), window.LLMUtils (llm-utils.js),
//       window.HtmlUtils (html-utils.js)
// ============================================================
(function initPalmReading() {
  const $ = (id) => document.getElementById(id);

  /**
   * PalmReader — 옥선 할미 (수상학)
   *  - 카메라 + 사진 업로드 → 손바닥 캡처 → LLM 비전 호출
   *  - window.BaseReader 글로벌 추상 class 상속
   *  - capturedDataUrl·stream은 인스턴스 상태로 캡슐화
   */
  class PalmReader extends window.BaseReader {
    constructor() {
      super({
        persona: '옥선 할미',
        endpoint: '/api/palm/reading',
        tabId: 'tab-palm',
        stepPrefix: 'palm-step-',
        boardId: 'palmResultBoard',
        WHMKey: 'palmistry',
      });
      this.stream = null;
      this.capturedDataUrl = null;
    }
    updateReadButton() {
      const btn = $('palmReadBtn');
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
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 1280 } },
          audio: false,
        });
        const video = $('palmVideo');
        video.srcObject = this.stream;
        $('palmCameraArea').style.display = 'block';
        $('palmPreviewArea').style.display = 'none';
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
      $('palmCameraArea').style.display = 'none';
    }
    captureFromVideo() {
      const video = $('palmVideo');
      if (!video || !video.videoWidth) return;
      const canvas = $('palmCanvas');
      const maxSide = 1280;
      let w = video.videoWidth, h = video.videoHeight;
      const scale = Math.min(1, maxSide / Math.max(w, h));
      w = Math.round(w * scale); h = Math.round(h * scale);
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(video, 0, 0, w, h);
      this.capturedDataUrl = canvas.toDataURL('image/jpeg', 0.88);
      this.showCapturedPreview();
      this.stopCamera();
    }
    showCapturedPreview() {
      if (!this.capturedDataUrl) return;
      $('palmPreviewImg').src = this.capturedDataUrl;
      $('palmPreviewArea').style.display = 'block';
      this.updateReadButton();
    }
    loadFromFile(file) {
      if (!file) return;
      if (!file.type.startsWith('image/')) { alert('사진 파일만 올려주시게나.'); return; }
      const maxFileSize = 5 * 1024 * 1024;
      if (file.size > maxFileSize) {
        alert('사진이 커서 자동으로 크기를 조정했습니다. 선명한 손 사진이라면 다시 올려주시게나.');
      }
      const fr = new FileReader();
      fr.onload = () => {
        const img = new Image();
        img.onload = () => {
          const canvas = $('palmCanvas');
          const maxSide = 1280;
          let w = img.naturalWidth, h = img.naturalHeight;
          const scale = Math.min(1, maxSide / Math.max(w, h));
          w = Math.round(w * scale); h = Math.round(h * scale);
          canvas.width = w; canvas.height = h;
          canvas.getContext('2d').drawImage(img, 0, 0, w, h);
          this.capturedDataUrl = canvas.toDataURL('image/jpeg', 0.88);
          const originalMaxSide = Math.max(img.naturalWidth, img.naturalHeight);
          if (originalMaxSide > maxSide) {
            const infoDiv = document.createElement('div');
            infoDiv.style.cssText = 'margin-top: 10px; padding: 8px 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; font-size: 13px; color: #856404; text-align: center;';
            infoDiv.textContent = `(${originalMaxSide}px에서 ${maxSide}px로 자동 조정됨)`;
            const preview = $('palmPreviewArea');
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
      $('palmPreviewArea').style.display = 'none';
      const upload = $('palmUploadInput');
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
        crisisBlock = `<div style="margin-top:16px;padding:14px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-size:13px;line-height:1.7;font-family:\'Nanum Myeongjo\',serif;letter-spacing:1px">
          마음이 무거우시다면 혼자 견디지 마시게.<br>
          자살예방상담전화 <b>1393</b> · 정신건강위기상담 <b>1577-0199</b>
        </div>`;
      }
      board.innerHTML = `
        <div class="face-result-card">
          <h2 class="face-result-title story-title">옥 선  할 미 의  손 금  풀 이</h2>
          <div class="face-result-text">${escaped}</div>
          ${crisisBlock}
          <div class="face-result-meta">
            ${cached ? '캐시 결과 · ' : ''}Gemini 비전 멀티모달
          </div>
        </div>
      `;
    }
    async request() {
      if (!this.capturedDataUrl) {
        alert('손바닥 사진을 먼저 담아주시게나.');
        return;
      }
      const ageRaw = ($('palmAge').value || '').trim();
      const age = ageRaw ? parseInt(ageRaw, 10) : null;
      const payload = {
        image_base64: this.capturedDataUrl,
        age: Number.isFinite(age) ? age : null,
        gender: ($('palmGender').value || '').trim() || null,
        hand: ($('palmHand').value || '').trim() || null,
        question: ($('palmQuestion').value || '').trim() || null,
      };
      this.showStep('loading');
      const loadingMsgEl = document.querySelector('#palm-step-loading .palm-loading-msg');
      const originalLoadingMsg = loadingMsgEl ? loadingMsgEl.textContent : null;
      try {
        const resp = await this.post(payload, {
          retries: 1,
          backoffMs: 3000,
          onRetry: (attempt, status) => {
            if (loadingMsgEl) loadingMsgEl.textContent = `허허, 잠시 길이 막혔으니 다시 살펴보겠소… (${status})`;
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
        this.renderError(err);
      } finally {
        if (loadingMsgEl && originalLoadingMsg != null) loadingMsgEl.textContent = originalLoadingMsg;
      }
    }
  }

  const reader = new PalmReader();
  window.palmReader = reader;  // 외부 진단·테스트용

  function bind() {
    if (!$('palmStartCameraBtn')) return;

    $('palmStartCameraBtn').addEventListener('click', () => reader.startCamera());
    $('palmCancelCameraBtn').addEventListener('click', () => reader.stopCamera());
    $('palmCaptureBtn').addEventListener('click', () => reader.captureFromVideo());
    $('palmRetakeBtn').addEventListener('click', () => {
      reader.capturedDataUrl = null;
      $('palmPreviewArea').style.display = 'none';
      const upload = $('palmUploadInput');
      if (upload) upload.value = '';
      reader.updateReadButton();
      reader.startCamera();
    });
    $('palmUploadInput').addEventListener('change', (e) => {
      reader.loadFromFile(e.target.files && e.target.files[0]);
    });
    $('palmReadBtn').addEventListener('click', () => reader.request());
    $('palmRestartBtn').addEventListener('click', () => reader.resetAll());

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.tab !== 'palm') reader.stopCamera();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
