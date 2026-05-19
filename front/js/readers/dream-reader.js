// ============================================================
// 몽이 도령 · 꿈 해몽 (v2 오케스트레이션) — ADR-042 외부 모듈화
// ============================================================
// 의존: window.LLMUtils, window.HtmlUtils, window.simpleMarkdown,
//       window.USER_LOCALE, window.WHM, window.SAJU, window.lastSajuResult
// ============================================================
(function initDreamReader() {
  const ANON_ID_KEY = 'dream_anon_uid';

  function getOrCreateAnonId() {
    return localStorage.getItem(ANON_ID_KEY) || null;
  }
  async function ensureAnonId() {
    let uid = localStorage.getItem(ANON_ID_KEY);
    if (uid) return uid;
    try {
      const res = await fetch('/api/user/new', { method: 'POST' });
      if (!res.ok) return null;
      const d = await res.json();
      if (d.user_id) {
        localStorage.setItem(ANON_ID_KEY, d.user_id);
        return d.user_id;
      }
    } catch (_) {}
    return null;
  }

  // ─── 사주 결과 → v2 profile 추출 ───
  function extractProfileFromSaju() {
    const p = {};
    try {
      if (window.lastSajuResult) {
        const lsr = window.lastSajuResult;
        if (lsr.day && lsr.day[0]) {
          p.day_master = lsr.day[0];
          const elem = (window.SAJU && window.SAJU.천간_오행) ? window.SAJU.천간_오행[p.day_master] : null;
          if (elem) p.day_master_element = elem;
        }
        const a = (window.SAJU && window.SAJU.analyzeSaju) ? window.SAJU.analyzeSaju(lsr) : null;
        if (a && a.wuxing_dist) {
          const wx = a.wuxing_dist;
          const weakest = Object.keys(wx).reduce((min, k) => (wx[k] < (wx[min] ?? Infinity) ? k : min), Object.keys(wx)[0]);
          if (weakest) p.yongsin = weakest;
        }
        const gEl = document.querySelector('input[name="gender"]:checked');
        if (gEl) p.gender = gEl.value === 'male' ? 'M' : 'F';
        const yearEl = document.getElementById('year');
        if (yearEl && yearEl.value) {
          const birthYear = parseInt(yearEl.value);
          if (!isNaN(birthYear)) p.age = new Date().getFullYear() - birthYear;
        }
      }
    } catch (e) {
      console.warn('[dream] profile extract failed:', e);
    }
    return p;
  }

  // ─── 해몽 결과 렌더링 — 카드형 UI ───
  function renderDreamResultV2(d) {
    const escape = window.HtmlUtils.escapeHtml;
    const am = d.agent_meta || {};
    const ds = d.domain_analysis_summary || {};
    const isCrisis = !!d.crisis_alert;

    if (isCrisis) {
      return `
        <div style="background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.55);border-radius:3px;padding:24px;margin-top:16px;font-family:'Nanum Myeongjo',serif">
          <h2 style="color:#e9b3a8;margin-top:0;font-family:'Nanum Myeongjo',serif;letter-spacing:3px">한 번 멈추소서</h2>
          <div style="color:#ffe;line-height:1.7;white-space:pre-line">${escape(d.text || '')}</div>
          <div style="margin-top:18px;display:flex;gap:8px;flex-wrap:wrap">
            <a href="tel:1393" style="background:rgba(80,30,30,0.65);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.55);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px;font-weight:600">자살예방상담 1393</a>
            <a href="tel:1577-0199" style="background:rgba(80,30,30,0.55);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.45);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">정신건강위기 1577-0199</a>
            <a href="tel:119" style="background:rgba(80,30,30,0.55);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.45);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">긴급 119</a>
          </div>
        </div>
      `;
    }

    const personaLabel = am.persona ? `${am.persona.primary} · ${am.persona.primary_label}` : '-';
    const cathartic = am.is_cathartic ? '<span style="color:#f9a;font-weight:bold"> 카타르시스 꿈</span>' : (am.cathartic_arc || '-');
    const lakoffCards = (am.lakoff_top_hypotheses || []).map(h =>
      `<li><b>${escape(h.source_schema || '-')}</b> → <b>${escape(h.target_domain || '-')}</b><br><span style="opacity:0.85">${escape((h.hypothesis || '').slice(0, 150))}</span></li>`
    ).join('') || '<li style="opacity:0.6">감지된 도식 없음</li>';
    const bivalentCounts = am.bivalent_cards_count || {};

    const ragInfo = d.rag_gate ? `${d.rag_gate.passed ? '' : ''} 도메인 인용 ${d.rag_gate.domain_citations}개` : '';
    const elapsedSec = d.elapsed_ms ? (d.elapsed_ms / 1000).toFixed(1) : '-';

    return `
      <h2 class="story-title"> 꿈 해몽 (v2 오케스트레이션) </h2>

      <div class="claude-output">${window.simpleMarkdown ? window.simpleMarkdown(d.text || '') : escape(d.text || '')}</div>

      <details style="margin-top:18px;background:rgba(10,15,30,0.55);border:1px solid var(--gold-dp);border-radius:3px;padding:14px">
        <summary style="cursor:pointer;font-weight:bold"> 분석 메타 (14 에이전트)</summary>
        <div style="margin-top:12px;font-size:0.9em;line-height:1.6">
          <div><b>페르소나:</b> ${escape(personaLabel)}</div>
          <div><b>감정 아크:</b> ${cathartic}</div>
          <div><b>융 원형:</b> ${escape(am.jung_primary || '-')} · 단계: ${escape(am.jung_stage || '-')}</div>
          <div><b>양가 카드:</b> 길 ${bivalentCounts['길'] || 0} · 흉 ${bivalentCounts['흉'] || 0} · 양가 ${bivalentCounts['양가'] || 0}</div>
          <div><b>도메인 분석:</b> 주역=${escape(ds.hexagram || '-')} · 오행=${escape(ds.wuxing_dominant || '-')} · 기괴성=${ds.bizarreness ?? '-'}</div>
          ${am.biomarker_signal ? `<div><b>바이오마커:</b> ${escape(am.biomarker_signal)}</div>` : ''}
          ${am.hanbang_synthesis ? `<div style="margin-top:8px"><b>한방:</b> ${escape(am.hanbang_synthesis)}</div>` : ''}

          <div style="margin-top:10px"><b>⭐ Lakoff 토폴로지 (표면 직역 회피)</b></div>
          <ul style="margin:4px 0 0 16px">${lakoffCards}</ul>

          <div style="margin-top:10px;opacity:0.7;font-size:0.85em">
            ${ragInfo} · critic ${d.critic_total ?? '-'}/40 ${d.critic_passed ? '' : ''} ·
            rounds ${d.rounds} · ${elapsedSec}초
          </div>
        </div>
      </details>

      ${d.legal_notice ? `<div style="margin-top:14px;padding:10px 14px;background:rgba(0,0,0,0.25);border-radius:6px;font-size:0.82em;opacity:0.8;white-space:pre-line">${escape(d.legal_notice)}</div>` : ''}
    `;
  }

  // 꿈 해몽 버튼 핸들러
  async function onDreamSubmit() {
    const dreamText = document.getElementById('dreamText').value.trim();
    if (!dreamText) {
      alert('꿈 내용을 적어주세요.');
      document.getElementById('dreamText').focus();
      return;
    }

    const out = document.getElementById('dreamResult');
    out.innerHTML = `
      <h2 class="story-title"> 꿈 해몽 </h2>
      <div class="claude-output claude-loading" id="dreamLoadingMsg">
        <div id="dreamLoadingStage"> 위기 신호 검사 + 30 도메인 결정론 분석 중 ⋯</div>
        <small style="opacity:0.6;display:block;margin-top:8px">예상 소요 30~60초</small>
        <div style="margin-top:14px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden">
          <div id="dreamProgress" style="height:100%;background:linear-gradient(90deg,var(--gold-dp),var(--gold),var(--gold-bri));width:0%;transition:width 0.5s"></div>
        </div>
      </div>
    `;

    const stages = [
      { pct: 5, msg: ' 위기 신호 검사 + 30 도메인 결정론 분석 중 ⋯' },
      { pct: 20, msg: ' 페르소나 분기 + 텍스트 정제 중 ⋯' },
      { pct: 35, msg: '🃏 양가 카드 + 융 원형 분류 (LLM) ⋯' },
      { pct: 55, msg: ' Lakoff 도식 + 카타르시스 아크 (LLM 병렬) ⋯' },
      { pct: 75, msg: ' 본문 합성 중 ⋯' },
      { pct: 90, msg: ' critic 검수 + RAG 게이트 ⋯' },
    ];
    let stageIdx = 0;
    const stageTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        const s = stages[stageIdx];
        const el = document.getElementById('dreamLoadingStage');
        const pg = document.getElementById('dreamProgress');
        if (el) el.textContent = s.msg;
        if (pg) pg.style.width = s.pct + '%';
        stageIdx++;
      }
    }, 7000);

    try {
      const uid = await ensureAnonId();
      const profile = extractProfileFromSaju();
      const res = await window.LLMUtils.postJSON('/api/dream/interpret_v2', {
        dream_text: dreamText,
        user_id: uid,
        profile: profile,
        locale: window.USER_LOCALE,
        enable_llm_agents: true,
      }, { retries: 1, backoffMs: 3000 });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`서버 오류 (${res.status}): ${errText.slice(0, 200)}`);
      }
      const d = await res.json();
      clearInterval(stageTimer);
      out.innerHTML = renderDreamResultV2(d);
      if (window.WHM) window.WHM.markCompleted('dream', {});
      const dreamNextCard = document.querySelector('#tab-dream .next-card[data-from="dream"]');
      if (dreamNextCard) dreamNextCard.style.display = '';
    } catch (err) {
      clearInterval(stageTimer);
      out.innerHTML = `
        <h2 class="story-title"> 꿈 해몽 </h2>
        <div class="claude-output">
          <pre style="color:#e9b3a8;white-space:pre-wrap;font-family:'Nanum Myeongjo',serif;font-size:13px;line-height:1.6">${window.HtmlUtils.escapeHtml((err.message || err).toString())}</pre>
          <p class="hint" style="margin-top:12px">잠시 후 다시 시도해주세요.</p>
        </div>
      `;
    }
  }

  // window 노출 (디버깅·외부 호출용)
  window.DreamReader = {
    getOrCreateAnonId,
    ensureAnonId,
    extractProfileFromSaju,
    renderDreamResultV2,
    onDreamSubmit,
  };

  // bind on DOMContentLoaded
  function bind() {
    const btn = document.getElementById('dreamBtn');
    if (btn) btn.addEventListener('click', onDreamSubmit);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
