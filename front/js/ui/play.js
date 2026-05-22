// 놀이 탭 동작
//   - 심리테스트: 12 미니 카드 → 1 카드 1 선택 → 즉시 캐릭터 결과
//   - 사이코패스 프로파일링: 7 단계 인터랙티브 추리 → 정답률 결과
//
// 결과는 localStorage('whm.play.history')에 저장 (일지 탭에서 사용 예정)

import { PSYCHOTEST, getPsychoCard } from '../data/psychotest.js';
import { PSYCHO_CASE } from '../data/psycho.js';

const HISTORY_KEY = 'whm.play.history';

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch (_) { return []; }
}
function saveResult(entry) {
  const list = loadHistory();
  list.unshift({ ...entry, ts: Date.now() });
  // 최근 50개만
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 50)));
}

// ──────────────────────────────────────────────
// 화면 전환 helpers
// ──────────────────────────────────────────────
function showView(viewId) {
  ['playMenu', 'playPsychotest', 'playPsycho'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = (id === viewId) ? 'block' : 'none';
  });
}

function backToMenu() {
  showView('playMenu');
}

// ──────────────────────────────────────────────
// 심리 테스트 — 12 미니 카드 (1 카드 1 선택 → 즉시 캐릭터)
// ──────────────────────────────────────────────
function runPsychotest() {
  showView('playPsychotest');
  const stage = document.getElementById('psychotestStage');
  if (!stage) return;

  renderCardMenu();

  function renderCardMenu() {
    const cards = PSYCHOTEST.cards;
    stage.innerHTML = `
      <p class="play-question">${escapeHtml(PSYCHOTEST.description || '')}</p>
      <div class="psycho-card-grid">
        ${cards.map((c, i) => `
          <button type="button" class="psycho-mini-card" data-card-key="${c.key}">
            <div class="psycho-mini-card-glyph">${escapeHtml(c.glyph || '心')}</div>
            <div class="psycho-mini-card-title">${escapeHtml(c.title)}</div>
            <div class="psycho-mini-card-num">${i + 1} / ${cards.length}</div>
          </button>
        `).join('')}
      </div>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="back">놀이로</button>
      </div>
    `;

    stage.querySelectorAll('.psycho-mini-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.cardKey;
        const card = getPsychoCard(key);
        if (card) renderCard(card);
      });
    });
    stage.querySelector('[data-action="back"]')?.addEventListener('click', backToMenu);
  }

  function renderCard(card) {
    stage.innerHTML = `
      <div class="psycho-card-header">
        <span class="psycho-card-glyph">${escapeHtml(card.glyph || '心')}</span>
        <h3 class="psycho-card-title">${escapeHtml(card.title)}</h3>
      </div>
      <p class="play-question">${escapeHtml(card.scene)}</p>
      <div class="play-choices">
        ${card.choices.map((c, i) => `
          <button type="button" class="play-choice" data-i="${i}">${escapeHtml(c.text)}</button>
        `).join('')}
      </div>
      <p class="psycho-card-school">학파: ${escapeHtml(card.school || '')}</p>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="cards">다른 카드</button>
      </div>
    `;

    stage.querySelectorAll('.play-choice').forEach(btn => {
      btn.addEventListener('click', () => {
        const i = parseInt(btn.dataset.i, 10);
        renderResult(card, i);
      });
    });
    stage.querySelector('[data-action="cards"]')?.addEventListener('click', renderCardMenu);
  }

  function renderResult(card, choiceIdx) {
    const choice = card.choices[choiceIdx];
    const ch = choice.character || {};

    stage.innerHTML = `
      <div class="psycho-card-header">
        <span class="psycho-card-glyph">${escapeHtml(card.glyph || '心')}</span>
        <h3 class="psycho-card-title">${escapeHtml(card.title)}</h3>
      </div>
      <h3 class="play-result-title">${escapeHtml(ch.title || '결의 결')}</h3>
      <p class="play-result-subtitle">${escapeHtml(ch.archetype || '')}</p>
      <div class="play-result-body">${escapeHtml(ch.body || '')}</div>
      ${ch.shadow ? `<p class="psycho-card-shadow">그림자: ${escapeHtml(ch.shadow)}</p>` : ''}
      <p class="psycho-card-school">학파: ${escapeHtml(card.school || '')}</p>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="retry">이 카드 다시</button>
        <button type="button" class="play-action play-action-quiet" data-action="cards">다른 카드</button>
        <button type="button" class="play-action" data-action="done">놀이로</button>
      </div>
    `;

    saveResult({
      kind: 'psychotest_mini',
      card_key: card.key,
      card_title: card.title,
      choice_idx: choiceIdx,
      character_title: ch.title || '',
      character_archetype: ch.archetype || '',
      school: card.school || '',
    });

    stage.querySelector('[data-action="retry"]')?.addEventListener('click', () => renderCard(card));
    stage.querySelector('[data-action="cards"]')?.addEventListener('click', renderCardMenu);
    stage.querySelector('[data-action="done"]')?.addEventListener('click', backToMenu);
  }
}

// ──────────────────────────────────────────────
// 사이코패스 프로파일링
// ──────────────────────────────────────────────
function runPsycho() {
  showView('playPsycho');
  const stage = document.getElementById('psychoStage');
  if (!stage) return;

  let step = -1; // -1 = 프롤로그
  let correctCount = 0;
  const log = [];

  function renderPrologue() {
    stage.innerHTML = `
      <h3 class="play-result-title">${escapeHtml(PSYCHO_CASE.title)}</h3>
      <p class="play-result-subtitle">${escapeHtml(PSYCHO_CASE.subtitle)}</p>
      <div class="play-narration">${escapeHtml(PSYCHO_CASE.prologue)}</div>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="back">놀이로</button>
        <button type="button" class="play-action" data-action="start">추리 시작</button>
      </div>
    `;
    stage.querySelector('[data-action="back"]')?.addEventListener('click', backToMenu);
    stage.querySelector('[data-action="start"]')?.addEventListener('click', () => {
      step = 0;
      renderStep();
    });
  }

  function renderStep() {
    const total = PSYCHO_CASE.steps.length;
    if (step >= total) {
      renderResult();
      return;
    }
    const s = PSYCHO_CASE.steps[step];
    const pct = Math.round((step / total) * 100);

    stage.innerHTML = `
      <div class="play-progress">
        <span>第 ${step + 1} 章 / ${total}</span>
        <div class="play-progress-bar"><span style="width:${pct}%"></span></div>
        <span>${pct}%</span>
      </div>
      <div class="play-narration">${escapeHtml(s.narration)}</div>
      <p class="play-question">${escapeHtml(s.question)}</p>
      <div class="play-choices">
        ${s.choices.map((c, i) => `
          <button type="button" class="play-choice" data-i="${i}">${escapeHtml(c.text)}</button>
        `).join('')}
      </div>
    `;

    stage.querySelectorAll('.play-choice').forEach((btn, i) => {
      btn.addEventListener('click', () => {
        const choice = s.choices[i];
        // 모든 선택지 비활성, 정답·오답 강조
        stage.querySelectorAll('.play-choice').forEach((b, j) => {
          b.disabled = true;
          if (s.choices[j].correct) b.classList.add('correct');
          else if (j === i) b.classList.add('wrong');
        });
        if (choice.correct) correctCount += 1;
        log.push({ step: step + 1, chosen: i, correct: choice.correct });

        // 해설 + 다음 단계 버튼
        const explain = document.createElement('div');
        explain.className = 'play-narration';
        explain.style.marginTop = '14px';
        explain.style.borderTop = '1px dashed rgba(212,175,55,0.25)';
        explain.style.paddingTop = '14px';
        explain.innerHTML = `<strong style="color:${choice.correct ? '#b8e8c0' : '#f0b8b0'};letter-spacing:2px;">${choice.correct ? '✓ 정확한 추리' : '✗ 빗나간 추리'}</strong><br>${escapeHtml(choice.explain)}`;
        stage.appendChild(explain);

        const next = document.createElement('button');
        next.type = 'button';
        next.className = 'play-action';
        next.style.marginTop = '18px';
        next.style.width = '100%';
        next.textContent = step + 1 >= total ? '결과 보기' : '다음 단서';
        next.addEventListener('click', () => {
          step += 1;
          renderStep();
        });
        stage.appendChild(next);
      });
    });
  }

  function renderResult() {
    const total = PSYCHO_CASE.steps.length;
    const result = PSYCHO_CASE.resultByScore(correctCount, total);
    const pct = Math.round((correctCount / total) * 100);

    stage.innerHTML = `
      <h3 class="play-result-title">${escapeHtml(result.title)}</h3>
      <p class="play-result-subtitle">${escapeHtml(result.subtitle)}</p>
      <div class="play-result-body">${escapeHtml(result.body)}</div>
      <div class="play-result-meter">
        <span class="play-result-meter-key">정답률</span>
        <div class="play-result-meter-bar"><span style="width:${pct}%"></span></div>
        <span class="play-result-meter-val">${correctCount}/${total}</span>
      </div>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="retry">다시 추리</button>
        <button type="button" class="play-action" data-action="done">놀이로</button>
      </div>
    `;

    saveResult({
      kind: 'psycho',
      title: result.title,
      correct: correctCount,
      total,
      log,
    });

    stage.querySelector('[data-action="retry"]')?.addEventListener('click', runPsycho);
    stage.querySelector('[data-action="done"]')?.addEventListener('click', backToMenu);
  }

  renderPrologue();
}

// ──────────────────────────────────────────────
// 초기화: 메뉴 카드 클릭 + 뒤로 가기 버튼
// ──────────────────────────────────────────────
function init() {
  document.querySelectorAll('[data-play-open]').forEach(card => {
    card.addEventListener('click', () => {
      const kind = card.dataset.playOpen;
      if (kind === 'psychotest') runPsychotest();
      else if (kind === 'psycho') runPsycho();
    });
  });

  document.querySelectorAll('[data-play-back]').forEach(btn => {
    btn.addEventListener('click', backToMenu);
  });
}

// helpers
function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

window.WHM_PLAY = { runPsychotest, runPsycho, history: loadHistory };
