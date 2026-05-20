// 놀이 탭 동작
//   - 심리테스트: 12 문항 → 4축 누적 → 8 유형 결과
//   - 사이코패스 프로파일링: 7 단계 인터랙티브 추리 → 정답률 결과
//
// 결과는 localStorage('whm.play.history')에 저장 (일지 탭에서 사용 예정)

import { PSYCHOTEST, resolvePsychoType } from '../data/psychotest.js';
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
// 심리 테스트
// ──────────────────────────────────────────────
function runPsychotest() {
  showView('playPsychotest');
  const stage = document.getElementById('psychotestStage');
  if (!stage) return;

  const scores = { yang_yin: 0, dong_jeong: 0, in_ui: 0, gang_yu: 0 };
  let idx = 0;

  function renderQuestion() {
    const total = PSYCHOTEST.questions.length;
    if (idx >= total) {
      renderResult();
      return;
    }
    const q = PSYCHOTEST.questions[idx];
    const pct = Math.round((idx / total) * 100);

    stage.innerHTML = `
      <div class="play-progress">
        <span>${idx + 1} / ${total}</span>
        <div class="play-progress-bar"><span style="width:${pct}%"></span></div>
        <span>${pct}%</span>
      </div>
      <p class="play-question">${escapeHtml(q.q)}</p>
      <div class="play-choices">
        ${q.choices.map((c, i) => `
          <button type="button" class="play-choice" data-i="${i}">${escapeHtml(c.text)}</button>
        `).join('')}
      </div>
    `;

    stage.querySelectorAll('.play-choice').forEach(btn => {
      btn.addEventListener('click', () => {
        const i = parseInt(btn.dataset.i, 10);
        const delta = q.choices[i].s || {};
        Object.keys(delta).forEach(k => {
          scores[k] = (scores[k] || 0) + delta[k];
        });
        idx += 1;
        renderQuestion();
      });
    });
  }

  function renderResult() {
    const typeKey = resolvePsychoType(scores);
    const type = PSYCHOTEST.types[typeKey] || PSYCHOTEST.types['yang_yu_in'];

    // 4축을 0~100 비율로 환산해서 표시
    const meters = [
      { key: '陽 / 陰', val: scores.yang_yin },
      { key: '動 / 靜', val: scores.dong_jeong },
      { key: '仁 / 義', val: scores.in_ui },
      { key: '剛 / 柔', val: scores.gang_yu },
    ];
    const maxAbs = 10; // 대략적 정규화
    const renderMeter = m => {
      // -maxAbs ~ +maxAbs 를 0 ~ 100 으로 매핑
      const pct = Math.min(100, Math.max(0, ((m.val + maxAbs) / (maxAbs * 2)) * 100));
      const signed = m.val >= 0 ? `+${m.val}` : `${m.val}`;
      return `
        <div class="play-result-meter">
          <span class="play-result-meter-key">${m.key}</span>
          <div class="play-result-meter-bar"><span style="width:${pct}%"></span></div>
          <span class="play-result-meter-val">${signed}</span>
        </div>
      `;
    };

    stage.innerHTML = `
      <h3 class="play-result-title">${escapeHtml(type.title)}</h3>
      <p class="play-result-subtitle">${escapeHtml(type.subtitle)}</p>
      <div class="play-result-body">${escapeHtml(type.body)}</div>
      ${meters.map(renderMeter).join('')}
      <div class="play-actions">
        <button type="button" class="play-action play-action-quiet" data-action="retry">다시 풀기</button>
        <button type="button" class="play-action" data-action="done">놀이로</button>
      </div>
    `;

    saveResult({
      kind: 'psychotest',
      type_key: typeKey,
      type_title: type.title,
      scores: { ...scores },
    });

    stage.querySelector('[data-action="retry"]')?.addEventListener('click', () => {
      runPsychotest();
    });
    stage.querySelector('[data-action="done"]')?.addEventListener('click', () => {
      backToMenu();
    });
  }

  renderQuestion();
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
