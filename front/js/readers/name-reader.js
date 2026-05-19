// ============================================================
// 묵향 선생 · 이름 풀이 (姓名學) — ADR-037 Phase 1b + ADR-038 외부 모듈화
// ============================================================
// 의존: window.BaseReader, window.LLMUtils, window.HtmlUtils
//       + 전역 splitName, 한글음_한자, 한자획수, 한자_뜻, 불용한자
// ============================================================
(function initNameReading() {
  const $ = (id) => document.getElementById(id);

  /**
   * NameReader — 묵향 선생 (성명학)
   *  - 한자 셀렉터 자동 생성 + 총 획수 표시
   *  - 본 reader는 카메라 없음 (텍스트 입력만)
   *  - window.BaseReader 글로벌 추상 class 상속
   */
  class NameReader extends window.BaseReader {
    constructor() {
      super({
        persona: '묵향 선생',
        endpoint: '/api/name/reading',
        tabId: 'tab-name',
        stepPrefix: 'name-step-',
        boardId: 'nameResultBoard',
        WHMKey: 'naming',
      });
    }
    updateReadButton() {
      const btn = $('nameReadBtn');
      if (!btn) return;
      btn.disabled = !( ($('nameFullKo')?.value || '').trim() );
    }
    collectHanjaText() {
      const cells = document.querySelectorAll('#nameHanjaSelectors .hanja-cell');
      if (!cells.length) return '';
      const parts = [];
      cells.forEach(cell => {
        const sel = cell.querySelector('.hanja-select');
        if (sel && sel.value) parts.push(sel.value);
      });
      return parts.join('');
    }
    /**
     * 한글 이름 변경 시 한자 셀 자동 생성 (개인 모드와 동일 로직).
     * 전역 splitName + 한글음_한자 + 한자획수 + 한자_뜻 + 불용한자 사용.
     */
    updateHanjaSelectors() {
      const fullName = ($('nameFullKo')?.value || '').trim();
      const { surname, givenName } = window.splitName(fullName);

      const splitHint = $('nameSplitHint');
      if (splitHint) {
        if (fullName) {
          splitHint.textContent = `→ 성: ${surname || '-'}  이름: ${givenName || '-'}`;
          splitHint.style.color = '#d4af37';
        } else {
          splitHint.textContent = '— 적은 이름에서 성과 이름을 자동으로 나눕니다.';
          splitHint.style.color = '';
        }
      }

      const container = $('nameHanjaSelectors');
      if (!container) return;
      const surnameChars = Array.from(surname);
      const nameChars = Array.from(givenName);
      const allChars = [...surnameChars, ...nameChars];

      if (allChars.length === 0) {
        container.innerHTML = '<span class="hint">이름을 적으면 글자마다 쓸 수 있는 한자가 아래에 나옵니다. 한자를 모르면 그냥 두셔도 풀이됩니다.</span>';
        this.updateStrokeTotal();
        this.updateReadButton();
        return;
      }

      const previous = {};
      container.querySelectorAll('.hanja-select').forEach(sel => {
        if (sel.value) previous[sel.dataset.char + ':' + sel.dataset.idx] = sel.value;
      });

      let html = '<div style="margin-bottom:6px;color:#d4af37;font-weight:600">한자 고르기 <span style="font-weight:normal;color:#8b7e5d;font-size:12px">(모르면 그냥 두세요)</span></div>';
      let hasUnknown = false;
      for (let i = 0; i < allChars.length; i++) {
        const ch = allChars[i];
        const isSurname = i < surnameChars.length;
        const candidates = (window['한글음_한자'][ch] || []).filter(h => window['한자획수'][h] && window['한자_뜻'][h]);
        if (candidates.length === 0) hasUnknown = true;
        const key = ch + ':' + i;
        const prevSel = previous[key] || '';
        const opts = [`<option value="">— 한자 안 씀 —</option>`,
          ...candidates.map(h => {
            const stroke = window['한자획수'][h];
            const meaning = window['한자_뜻'][h] || '';
            const sel = (h === prevSel) ? ' selected' : '';
            const strokePart = stroke ? ` (${stroke}획)` : '';
            const unusable = (typeof window['불용한자'] !== 'undefined' && window['불용한자'].has(h)) ? ' · [불용]' : '';
            return `<option value="${h}"${sel}>${h} ${meaning}${strokePart}${unusable}</option>`;
          })
        ].join('');
        html += `<span class="hanja-cell">
          <div class="hanja-han"><b>${ch}</b><small>${isSurname ? '성' : '이름'}</small></div>
          <select class="hanja-select" data-char="${ch}" data-idx="${i}">${opts}</select>
        </span>`;
      }
      if (hasUnknown) {
        html += '<div class="hint" style="margin-top:6px">※ "—" 표시된 글자는 후보가 없는 한자라 풀이에서 제외됩니다.</div>';
      }
      html += '<div class="hint" style="margin-top:4px;color:var(--text-dim)">※ [불용] 표시는 의미가 어둡거나 흉운으로 분류되는 한자 (참고용).</div>';
      container.innerHTML = html;
      this.updateStrokeTotal();
      this.updateReadButton();
    }
    updateStrokeTotal() {
      const target = $('nameStrokeTotal');
      if (!target) return;
      const cells = document.querySelectorAll('#nameHanjaSelectors .hanja-cell');
      if (cells.length === 0) {
        target.textContent = '이름을 적어주세요';
        return;
      }
      let total = 0;
      const rows = [];
      cells.forEach(cell => {
        const ch = cell.querySelector('.hanja-han b')?.textContent || '';
        const sel = cell.querySelector('.hanja-select');
        const han = sel ? sel.value : '';
        if (!han) {
          rows.push(`<span class="stroke-row stroke-empty">${ch} → 한자 없음</span>`);
          return;
        }
        const stroke = window['한자획수'][han] || 0;
        total += stroke;
        rows.push(`<span class="stroke-row">${ch}(${han}) ${stroke}획</span>`);
      });
      target.innerHTML = `${rows.join(' ')} <b style="color:var(--gold);margin-left:8px">총 ${total}획</b>`;
    }
    renderResult(data) {
      const text = (data && data.text) ? data.text : '(풀이를 받지 못했소.)';
      const cached = data && data.cached;
      const board = $(this.boardId);
      const escaped = window.HtmlUtils.escapeHtml(text);
      board.innerHTML = `
        <div class="face-result-card">
          <h2 class="face-result-title story-title">묵 향  선 생 의  이 름  풀 이</h2>
          <div class="face-result-text">${escaped}</div>
          <div class="face-result-meta">${cached ? '캐시 결과 · ' : ''}묵향 선생 · 성명학</div>
        </div>`;
    }
    async request() {
      const fullnameKo = ($('nameFullKo')?.value || '').trim();
      if (!fullnameKo) { alert('한글 이름을 먼저 적어주시오.'); return; }
      const payload = {
        fullname_ko: fullnameKo,
        fullname_han: this.collectHanjaText() || null,
        gender: ($('nameGender')?.value || '').trim() || null,
        birth: ($('nameBirth')?.value || '').trim() || null,
        saju_day_master: ($('nameDayMaster')?.value || '').trim() || null,
      };
      this.showStep('loading');
      const loadingMsgEl = document.querySelector('#name-step-loading .name-loading-msg');
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
    resetAll() {
      $(this.boardId).innerHTML = '';
      this.showStep('input');
    }
  }

  const reader = new NameReader();
  window.nameReader = reader;

  function bind() {
    if (!$('nameFullKo')) return;
    $('nameFullKo').addEventListener('input', () => reader.updateHanjaSelectors());
    const container = $('nameHanjaSelectors');
    if (container) {
      container.addEventListener('change', () => reader.updateStrokeTotal());
      container.addEventListener('input', () => reader.updateStrokeTotal());
    }
    $('nameReadBtn').addEventListener('click', () => reader.request());
    $('nameRestartBtn').addEventListener('click', () => reader.resetAll());
    reader.updateReadButton();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
