// 놀이 탭 동작
//   - 심리테스트: 100 미니 카드 → 1 카드 1 선택 → 즉시 캐릭터 결과
//   - 사이코패스 프로파일링: 7 단계 인터랙티브 추리 → 정답률 결과
//
// 결과는 localStorage('whm.play.history')에 저장 (일지 탭에서 사용 예정)
// 풀린 카드 진행 상태는 localStorage('whm.psycho.done')에 카드 key 배열로 저장

import { PSYCHOTEST, getPsychoCard } from '../data/psychotest.js';
import { PSYCHO_CASE } from '../data/psycho.js';

const HISTORY_KEY = 'whm.play.history';
const PSYCHO_DONE_KEY = 'whm.psycho.done';

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

// ── 심리테스트 진행 상태 (풀린 카드 key 집합) ──
function loadPsychoDone() {
  try {
    const arr = JSON.parse(localStorage.getItem(PSYCHO_DONE_KEY) || '[]');
    return new Set(Array.isArray(arr) ? arr : []);
  } catch (_) { return new Set(); }
}
function markPsychoDone(cardKey) {
  const done = loadPsychoDone();
  done.add(cardKey);
  localStorage.setItem(PSYCHO_DONE_KEY, JSON.stringify([...done]));
}
function resetPsychoDone() {
  localStorage.removeItem(PSYCHO_DONE_KEY);
}

// ── 카드 카테고리 분류 (school 필드 자동 매핑 — 100 카드 선택 마비 완화) ──
// 음식 / 행동 / 라이프스타일 / 취향 / 마무리 5 군으로 통합
function categorizeCard(card) {
  const s = card.school || '';
  if (/음식/.test(s)) return '음식';
  if (/취향/.test(s)) return '취향';
  if (/라이프스타일/.test(s)) return '라이프';
  if (/마무리/.test(s)) return '마무리';
  if (/행동/.test(s)) return '행동';
  return '기타';
}
const PSYCHO_CATEGORIES = ['전체', '음식', '행동', '라이프', '취향', '마무리'];

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

  let activeCategory = '전체';

  renderCardMenu();

  function renderCardMenu() {
    const allCards = PSYCHOTEST.cards;
    const done = loadPsychoDone();
    const totalAll = allCards.length;
    const doneCountAll = allCards.filter(c => done.has(c.key)).length;

    // 카테고리별 카드 수 (탭 라벨용)
    const catCounts = {};
    PSYCHO_CATEGORIES.forEach(cat => { catCounts[cat] = 0; });
    catCounts['전체'] = totalAll;
    allCards.forEach(c => {
      const cat = categorizeCard(c);
      if (catCounts[cat] !== undefined) catCounts[cat]++;
    });

    // 필터링된 카드
    const cards = activeCategory === '전체'
      ? allCards
      : allCards.filter(c => categorizeCard(c) === activeCategory);
    const total = cards.length;
    const doneCount = cards.filter(c => done.has(c.key)).length;
    const pct = total ? Math.round((doneCount / total) * 100) : 0;

    stage.innerHTML = `
      <p class="play-question">${escapeHtml(PSYCHOTEST.description || '')}</p>
      <div class="psycho-progress">
        <div class="psycho-progress-label">
          <span>풀린 결 ${doneCountAll} / ${totalAll} (전체)</span>
          <span>${Math.round((doneCountAll / totalAll) * 100)}%</span>
        </div>
        <div class="psycho-progress-bar"><span style="width:${Math.round((doneCountAll / totalAll) * 100)}%"></span></div>
      </div>
      <div class="psycho-cat-tabs">
        ${PSYCHO_CATEGORIES.map(cat => `
          <button type="button"
                  class="psycho-cat-tab${cat === activeCategory ? ' psycho-cat-tab-active' : ''}"
                  data-cat="${cat}"
                  ${catCounts[cat] === 0 ? 'disabled' : ''}>
            ${escapeHtml(cat)} <span class="psycho-cat-count">${catCounts[cat]}</span>
          </button>
        `).join('')}
      </div>
      ${activeCategory !== '전체' ? `
        <p class="psycho-cat-summary">${escapeHtml(activeCategory)} — ${doneCount} / ${total} 풀음 (${pct}%)</p>
      ` : ''}
      <div class="psycho-card-grid">
        ${cards.map((c) => {
          const globalIdx = allCards.indexOf(c) + 1;
          return `
          <button type="button" class="psycho-mini-card${done.has(c.key) ? ' psycho-mini-card-done' : ''}" data-card-key="${c.key}">
            ${done.has(c.key) ? '<div class="psycho-mini-card-check">✓</div>' : ''}
            <div class="psycho-mini-card-glyph">${escapeHtml(c.glyph || '心')}</div>
            <div class="psycho-mini-card-title">${escapeHtml(c.title)}</div>
            <div class="psycho-mini-card-num">${globalIdx} / ${totalAll}</div>
          </button>
          `;
        }).join('')}
      </div>
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="back">놀이로</button>
        ${doneCountAll > 0 ? '<button type="button" class="play-action play-action-quiet" data-action="reset">진행 초기화</button>' : ''}
      </div>
    `;

    stage.querySelectorAll('.psycho-cat-tab').forEach(btn => {
      btn.addEventListener('click', () => {
        const cat = btn.dataset.cat;
        if (cat && cat !== activeCategory) {
          activeCategory = cat;
          renderCardMenu();
        }
      });
    });
    stage.querySelectorAll('.psycho-mini-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.cardKey;
        const card = getPsychoCard(key);
        if (card) renderCard(card);
      });
    });
    stage.querySelector('[data-action="back"]')?.addEventListener('click', backToMenu);
    stage.querySelector('[data-action="reset"]')?.addEventListener('click', () => {
      if (confirm(`풀린 결 ${doneCountAll}장을 모두 초기화하시오?`)) {
        resetPsychoDone();
        renderCardMenu();
      }
    });
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
      <p class="psycho-card-disclaimer">※ 본 결은 일상 심리 카테고리 가벼운 캐릭터 진단 (ADR-014 정합). 참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다.</p>
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
    markPsychoDone(card.key);

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
      <p class="psycho-card-disclaimer">※ 본 추리 결과는 임상 사이코패스 특성 (PCL-R 일부)을 가벼운 인포테인먼트로 변환한 것. 참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다.</p>
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
