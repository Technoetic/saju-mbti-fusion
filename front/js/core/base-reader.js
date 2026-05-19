/**
 * window.BaseReader — 7인 점술가 공용 추상 클래스 (ADR-037 + ADR-038 Phase 2)
 *  - showStep / post / renderError / markCompleted 공통 메서드
 *  - 각 reader IIFE는 extends BaseReader로 캐릭터별 메서드 추가
 *  - constructor 옵션: persona·endpoint·tabId·stepPrefix·boardId·WHMKey
 *
 * 의존: window.LLMUtils (llm-utils.js 먼저 로드 필요)
 */
(function(){
  class BaseReader {
    constructor({ persona, endpoint, tabId, stepPrefix, boardId, WHMKey }) {
      this.persona = persona;
      this.endpoint = endpoint;
      this.tabId = tabId;
      this.stepPrefix = stepPrefix;
      this.boardId = boardId;
      this.WHMKey = WHMKey;
    }
    showStep(stepName) {
      const fullId = this.stepPrefix + stepName;
      const stepClass = this.stepPrefix.slice(0, -1);  // 'name-step-' → 'name-step'
      document.querySelectorAll(`#${this.tabId} .${stepClass}`).forEach(s => {
        s.classList.toggle('active', s.id === fullId);
      });
    }
    async post(payload, opts) {
      return window.LLMUtils.postJSON(this.endpoint, payload, opts);
    }
    renderError(err) {
      const board = document.getElementById(this.boardId);
      if (!board) return;
      board.innerHTML = `
        <div class="face-result-card">
          <div class="face-result-text" style="color:#e9b3a8">
            이 사람이 풀이를 마치지 못했소.<br><br>
            <code style="font-size:12px">${(err.message || err).toString().replace(/</g,'&lt;')}</code>
          </div>
        </div>`;
      this.showStep('result');
    }
    markCompleted(extra = {}) {
      if (window.WHM && this.WHMKey) window.WHM.markCompleted(this.WHMKey, extra);
    }
  }
  window.BaseReader = BaseReader;
})();
