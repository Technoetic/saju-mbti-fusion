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
      const viz = data && data.visualization;
      const board = $(this.boardId);
      const escaped = window.HtmlUtils.escapeHtml(text);
      let crisisBlock = '';
      if (crisis) {
        crisisBlock = `<div style="margin-top:16px;padding:14px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-size:13px;line-height:1.7;font-family:\'Nanum Myeongjo\',serif;letter-spacing:1px">
          마음이 무거우시다면 혼자 견디지 마시게.<br>
          자살예방상담전화 <b>1393</b> · 정신건강위기상담 <b>1577-0199</b>
        </div>`;
      }
      // ADR-259 — 손금 시각화 오버레이 (CFM 마스크 + 21 keypoint + 영역 박스)
      let vizBlock = '';
      if (viz && viz.image_base64) {
        const kpN = Number(viz.n_keypoints || 0);
        const hasMask = !!viz.has_cfm_mask;
        const density = viz.metadata && viz.metadata.cfm_overall_density;
        const densityPct = density != null ? (density * 100).toFixed(1) + '%' : '—';
        vizBlock = `
          <div class="palm-viz-block" style="margin:18px 0;padding:14px;background:rgba(40,30,20,0.55);border:1px solid rgba(176,140,79,0.35);border-radius:3px">
            <div style="font-family:'Nanum Myeongjo',serif;color:#e0c9a0;font-size:13px;letter-spacing:1px;margin-bottom:10px">
              그대의 손에 새겨진 결을 살펴보았네 ─ AI가 본 손금
            </div>
            <img src="${viz.image_base64}" alt="손금 분석 시각화"
                 style="width:100%;max-width:600px;border-radius:3px;display:block;margin:0 auto" />
            <div style="margin-top:10px;font-size:12px;color:#b8a47e;text-align:center;letter-spacing:1px">
              🔴 MediaPipe 21 keypoint · 🟡 CFM 손금 마스크 · ⬜ 4선+금성대 영역
            </div>
            <div style="margin-top:6px;font-size:11px;color:#8a7d61;text-align:center">
              CFM 손금 밀도: ${densityPct} · keypoint: ${kpN}개 ${hasMask ? '· CFM 마스크 활성' : ''}
            </div>
          </div>
        `;
      }
      board.innerHTML = `
        <div class="face-result-card">
          <h2 class="face-result-title story-title">옥 선  할 미 의  손 금  풀 이</h2>
          ${vizBlock}
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
      this.showStep('loading');
      const loadingMsgEl = document.querySelector('#palm-step-loading .palm-loading-msg');
      const originalLoadingMsg = loadingMsgEl ? loadingMsgEl.textContent : null;
      try {
        // ADR-160 Phase 1.5 — MediaPipe Hand Landmarker 메트릭 산출 (실패 시 LLM Vision 단독 폴백)
        let metrics = null;
        if (window.PalmMetrics && window.PalmMetrics.computeMetrics) {
          if (loadingMsgEl) loadingMsgEl.textContent = '허허, 그대의 손금을 살피는 중이외다…';
          const img = $('palmPreviewImg');
          try {
            metrics = await window.PalmMetrics.computeMetrics(img);
          } catch (e) {
            console.warn('[palm-reader] 메트릭 산출 건너뜀:', e);
          }
        }
        const payload = {
          image_base64: this.capturedDataUrl,
          age: Number.isFinite(age) ? age : null,
          gender: ($('palmGender').value || '').trim() || null,
          hand: ($('palmHand').value || '').trim() || null,
          question: ($('palmQuestion').value || '').trim() || null,
          metrics,
        };
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
