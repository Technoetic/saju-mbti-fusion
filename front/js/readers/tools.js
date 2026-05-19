// ============================================================
// tools.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// TOOL_RENDERERS + 11 async tool renderer (diary·clinical 등)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
// ─── 다국어 라우터 (?lang=en|ja|zh|ar) ───
const USER_LOCALE = (() => {
  const q = new URLSearchParams(location.search).get('lang');
  if (q && ['en', 'ja', 'zh', 'ar', 'es', 'id', 'ms', 'ko'].includes(q)) return q;
  const nav = (navigator.language || 'ko').split('-')[0];
  return ['en', 'ja', 'zh', 'ar', 'es', 'id', 'ms', 'ko'].includes(nav) ? nav : 'ko';
})();
console.log('[locale] active:', USER_LOCALE);

// ADR-042: 외부 모듈 (dream-reader.js 등) 접근용 글로벌 노출
window.USER_LOCALE = USER_LOCALE;
// simpleMarkdown은 saju-engine.js Object.assign(window, {...})에 이미 노출됨
// lastSajuResult는 saju-ui.js에서 직접 window 노출 (ADR-045)

// Dream 외부 모듈: js/readers/dream-reader.js (ADR-042 Phase G)
// 본 위치 인라인 정의는 외부 .js로 이동.


// ─────────────────────────── 부가 도구 6종 ───────────────────────────
const TOOL_RENDERERS = {
  diary: renderDiaryTool,
  clinical: renderClinicalTool,
  trend: renderTrendTool,
  irt: renderIRTWorkflowTool,
  mood: renderMoodTool,
  myoe: renderMyoeTool,
  hill: renderHillTool,
  dormio: renderDormioTool,
  ullman: renderUllmanTool,
  lucid: renderLucidTool,
  incubation: renderIncubationTool,
};

document.querySelectorAll('.tool-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
  document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const tool = btn.dataset.tool;
  const panel = document.getElementById('toolPanel');
  panel.innerHTML = `<div class="tool-panel-inner">로딩 ⋯</div>`;
  try {
  await TOOL_RENDERERS[tool](panel);
  } catch (e) {
  panel.innerHTML = `<div class="tool-panel-inner"><pre style="color:#e9b3a8;font-family:'Nanum Myeongjo',serif;font-size:13px;line-height:1.6">${(e.message||e).toString().replace(/</g,'&lt;')}</pre></div>`;
  }
  });
});

// ─── ⓪ 일기 저장 (Schredl + 묘에 통합) ───
async function renderDiaryTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> 꿈 일기 저장 (Schredl 표준 + 묘에 자기관찰)</h4>
  <p style="opacity:0.8;font-size:0.88em">매일 기록하시면 Cartwright 7일 정서 곡선·묘에 14일 모티프·디지털 바이오마커가 활성화됩니다.</p>

  <label>꿈 본문 *</label>
  <textarea id="diaryText" rows="5" placeholder="기억나는 내용을 자유롭게 적어주세요."></textarea>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:10px">
  <div>
  <label>회상 명료도 (1~5)</label>
  <input type="number" id="diaryRecall" min="1" max="5" value="3">
  </div>
  <div>
  <label>생생함 (1~5)</label>
  <input type="number" id="diaryVividness" min="1" max="5" value="3">
  </div>
  <div>
  <label>정서가 (-3~+3)</label>
  <input type="number" id="diaryValence" min="-3" max="3" value="0">
  </div>
  <div>
  <label>자각도 (0~5)</label>
  <input type="number" id="diaryLucidity" min="0" max="5" value="0">
  </div>
  </div>

  <label style="margin-top:14px">묘에 — 핵심 도해 (1단어)</label>
  <input type="text" id="diaryCoreImage" placeholder="예: 산, 용, 거울">

  <label>묘에 — 느낌의 의미 (1줄)</label>
  <input type="text" id="diaryFeltMeaning" placeholder="해석이 아닌 첫 인상">

  <label style="margin-top:10px">
  <input type="checkbox" id="diaryAnalyze"> 저장 + 즉시 v2 분석 (느려짐)
  </label>

  <button type="button" class="tool-action" id="diarySubmit">저장</button>
  <div id="diaryResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('diarySubmit').addEventListener('click', async () => {
  const txt = document.getElementById('diaryText').value.trim();
  if (!txt) { alert('꿈 본문을 적어주세요.'); return; }
  const uid = await ensureAnonId();
  const body = {
  user_id: uid,
  narrative_text: txt,
  recall_quality: parseInt(document.getElementById('diaryRecall').value) || 3,
  vividness: parseInt(document.getElementById('diaryVividness').value) || 3,
  valence: parseInt(document.getElementById('diaryValence').value) || 0,
  lucidity: parseInt(document.getElementById('diaryLucidity').value) || 0,
  core_image: document.getElementById('diaryCoreImage').value.trim() || null,
  felt_meaning: document.getElementById('diaryFeltMeaning').value.trim() || null,
  analyze: document.getElementById('diaryAnalyze').checked,
  };
  const out = document.getElementById('diaryResult');
  out.innerHTML = '저장 중 ⋯';
  const r = await fetch('/api/diary/add', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(body),
  });
  const d = await r.json();
  if (d.crisis_alert) {
  out.innerHTML = `
  <div style="padding:16px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.7;white-space:pre-line">${(d.text||'').replace(/</g,'&lt;')}</div>
  <div style="margin-top:8px"><a href="tel:1393" style="background:rgba(80,30,30,0.65);color:#e9b3a8;padding:8px 16px;border:1px solid rgba(176,79,79,0.5);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">자살예방 1393</a></div>
  `;
  return;
  }
  if (d.saved) {
  out.innerHTML = `
  <div style="padding:12px;background:rgba(80,160,80,0.3);border-radius:8px">
  저장됨 (diary_id: <code>${d.diary_id.slice(0,8)}</code>)
  ${d.analysis_summary ? `<div style="margin-top:8px;font-size:0.9em">분석 요약: ${JSON.stringify(d.analysis_summary).slice(0,200)}</div>` : ''}
  </div>
  `;
  } else {
  out.innerHTML = `<pre>${JSON.stringify(d, null, 2)}</pre>`;
  }
  });
}

// ─── ① 임상 자가검사 (CES-D 빠른 검사) ───
async function renderClinicalTool(panel) {
  // 척도 문항 불러오기
  const res = await fetch('/api/clinical/instruments');
  const inst = await res.json();
  const cesd = inst.ces_d;

  const html = `
  <div class="tool-panel-inner">
  <h4> CES-D 한국판 — 우울 자가검사 (전겸구·이민규 1992)</h4>
  <p style="opacity:0.8;font-size:0.88em">지난 일주일 동안 다음 항목들을 얼마나 자주 느꼈는지 선택하세요. (cutoff 16점)</p>
  <form id="cesdForm">
  ${cesd.items.map((item, i) => `
  <div class="scale-item">
  <div><b>${item.no}.</b> ${item.text}</div>
  <div class="opts" data-item="${i}">
  ${Object.entries(cesd.response_options).map(([v, label]) =>
  `<button type="button" data-val="${v}">${v}: ${label}</button>`
  ).join('')}
  </div>
  </div>
  `).join('')}
  <button type="button" class="tool-action" id="cesdSubmit">채점 + 저장</button>
  </form>
  <div id="cesdResult" style="margin-top:14px"></div>
  </div>
  `;
  panel.innerHTML = html;

  // 응답 저장 객체
  const responses = new Array(cesd.items.length).fill(null);
  panel.querySelectorAll('.opts').forEach(opt => {
  opt.querySelectorAll('button').forEach(b => {
  b.addEventListener('click', () => {
  opt.querySelectorAll('button').forEach(x => x.classList.remove('selected'));
  b.classList.add('selected');
  responses[parseInt(opt.dataset.item)] = parseInt(b.dataset.val);
  });
  });
  });

  document.getElementById('cesdSubmit').addEventListener('click', async () => {
  if (responses.some(v => v === null)) {
  alert(`아직 답하지 않은 항목이 ${responses.filter(v=>v===null).length}개 있습니다.`);
  return;
  }
  const uid = await ensureAnonId();
  const out = document.getElementById('cesdResult');
  out.innerHTML = '채점 중 ⋯';
  const r = await fetch('/api/clinical/log', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: uid, instrument: 'ces_d', responses}),
  });
  const d = await r.json();
  const isCrisis = d.result.suicide_alert;
  out.innerHTML = `
  <div style="padding:16px;background:${isCrisis ? 'rgba(80,30,30,0.55)' : 'rgba(10,15,30,0.55)'};border:1px solid ${isCrisis ? 'rgba(176,79,79,0.45)' : 'var(--gold-dp)'};border-radius:3px;font-family:'Nanum Myeongjo',serif;color:${isCrisis ? '#e9b3a8' : 'var(--text-main)'};line-height:1.7">
  <div style="font-size:1.4em"><b>총점 ${d.result.total_score}</b> / cutoff ${d.result.cutoff}</div>
  <div style="margin-top:6px"><b>판정:</b> ${d.result.severity}</div>
  <div style="margin-top:6px;opacity:0.85">${d.result.interpretive_note}</div>
  ${d.result.referral_recommended ? '<div style="margin-top:10px;color:#fa8"> 전문가 상담을 권합니다.</div>' : ''}
  ${isCrisis ? '<div style="margin-top:10px"><a href="tel:1393" style="background:rgba(80,30,30,0.65);color:#e9b3a8;padding:8px 16px;border:1px solid rgba(176,79,79,0.5);border-radius:3px;text-decoration:none;font-family:\'Nanum Myeongjo\',serif;letter-spacing:2px">자살예방 1393</a></div>' : ''}
  </div>
  <div style="margin-top:8px;opacity:0.6;font-size:0.8em">${d.result.instrument} · 결과 저장됨 (DB)</div>
  `;
  });
}

// ───  임상 척도 추세 ───
async function renderTrendTool(panel) {
  const uid = await ensureAnonId();
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> 임상 척도 시계열 추세</h4>
  <p style="opacity:0.85;font-size:0.88em">2회 이상 측정하면 점수 변화 곡선이 표시됩니다.</p>
  <label>척도 선택</label>
  <select id="trendInst" style="padding:6px;background:rgba(0,0,0,0.3);color:#fff;border:1px solid rgba(255,255,255,0.2);border-radius:4px">
  <option value="ces_d">CES-D (우울)</option>
  <option value="bdi_k">BDI-K (우울)</option>
  <option value="stai_k_state">STAI-K (불안)</option>
  <option value="psqi">PSQI (수면 질)</option>
  <option value="isi">ISI (불면)</option>
  </select>
  <button type="button" class="tool-action" id="trendSubmit">조회</button>
  <div id="trendResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('trendSubmit').addEventListener('click', async () => {
  const inst = document.getElementById('trendInst').value;
  const out = document.getElementById('trendResult');
  out.innerHTML = '조회 중 ⋯';
  const r = await fetch('/api/clinical/trend', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: uid, instrument: inst, responses: []}),
  });
  const d = await r.json();
  if ((d.count ?? 0) < 2) {
  out.innerHTML = `<div style="padding:12px;opacity:0.85">측정 횟수 ${d.count || 0}회 — 2회 이상 누적되면 추세 분석.</div>`;
  return;
  }
  const scores = d.all_scores || [];
  const maxScore = Math.max(...scores.map(s => s[1])) || 1;
  out.innerHTML = `
  <div style="padding:12px;background:rgba(60,80,120,0.3);border-radius:8px">
  <div>측정 횟수: <b>${d.count}</b></div>
  <div>첫 측정: ${d.first_score} (${d.first_date.slice(0,10)})</div>
  <div>최근 측정: ${d.latest_score} (${d.latest_date.slice(0,10)})</div>
  <div>Δ: <b style="color:${d.delta < 0 ? '#a8d8a0' : (d.delta > 0 ? '#e9b3a8' : 'var(--text-soft)')}">${d.delta > 0 ? '+' : ''}${d.delta}</b> (<b>${d.trend}</b>)</div>
  <svg viewBox="0 0 ${scores.length * 40} 100" style="width:100%;max-width:600px;margin-top:10px;background:rgba(0,0,0,0.2);border-radius:6px">
  <polyline fill="none" stroke="var(--gold)" stroke-width="2"
  points="${scores.map((s, i) => `${i*40+20},${100 - (s[1]/maxScore*80)}`).join(' ')}" />
  ${scores.map((s, i) => `<circle cx="${i*40+20}" cy="${100 - (s[1]/maxScore*80)}" r="4" fill="#fff"><title>${s[1]}점 @ ${s[0].slice(0,10)}</title></circle>`).join('')}
  </svg>
  </div>
  `;
  });
}

// ─── ② IRT 6단계 워크플로 (재각본은 그 안의 Step 4) ───
async function renderIRTWorkflowTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> IRT 악몽 재각본 6단계 워크플로 (Krakow·Zadra 2010, AASM 2018)</h4>
  <p style="opacity:0.85;font-size:0.88em">만성 악몽(주 1회+ × 6개월+) 사용자용. 8주차에 악몽 빈도 -50% 목표.</p>

  <details open>
  <summary><b>Step 1 — 심리교육 (5분, 1회)</b></summary>
  <div style="padding:10px;background:rgba(0,0,0,0.2);margin:8px 0;border-radius:6px;white-space:pre-line;font-size:0.9em">
악몽은 운명도 신호도 아닙니다. 학습된 행동에 가깝습니다.
같은 결말로 반복된 꿈은 그 결말을 더 잘 학습하게 되고, 결국 자주 떠오릅니다.

좋은 소식: 같은 학습 원리로 결말을 의식적으로 다시 짤 수 있습니다.

본 워크플로는 자가 도움 도구이며 의료 치료가 아닙니다.
자살·자해 생각이 있다면 즉시 1393으로 연락하십시오.
  </div>
  </details>

  <details>
  <summary><b>Step 2 — 악몽 기록 (7일 베이스라인)</b></summary>
  <div style="padding:10px">
  위의 "꿈 일기 저장" 도구로 7일간 매일 기록하세요. 베이스라인 측정.
  </div>
  </details>

  <details>
  <summary><b>Step 3 — 표적 악몽 선택</b></summary>
  <div style="padding:10px">
  가장 빈번하거나 가장 고통스러운 악몽 <b>1개</b>를 선택 (다중 선택 금지 — Krakow 원칙).
  <textarea id="irtTarget" rows="4" placeholder="표적으로 삼을 악몽 본문" style="margin-top:8px"></textarea>
  </div>
  </details>

  <details>
  <summary><b>Step 4 — 재각본 생성 (AI 3안)</b></summary>
  <div style="padding:10px">
  <button type="button" class="tool-action" id="irtGenerate">AI 재각본 3안 생성</button>
  <div id="irtRescript" style="margin-top:10px"></div>
  </div>
  </details>

  <details>
  <summary><b>Step 5 — 낮 시간 리허설 (2주)</b></summary>
  <div style="padding:10px">
  매일 낮 1회, 5~20분간 위 선택한 재각본을 시각화·내적 낭독.
  기본 알림 시각: <b>14:00</b> (사용자 조정 가능, 브라우저 알림 권한 필요).
  <br><br>
  <button type="button" class="tool-action" id="irtAlarm">알림 켜기</button>
  </div>
  </details>

  <details>
  <summary><b>Step 6 — 8주차 효과 측정</b></summary>
  <div style="padding:10px">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
  <div>
  <label>베이스라인 악몽 빈도 (회/주)</label>
  <input type="number" id="irtBaseline" step="0.1" placeholder="예: 3">
  </div>
  <div>
  <label>8주차 악몽 빈도 (회/주)</label>
  <input type="number" id="irtWeek8" step="0.1" placeholder="예: 1">
  </div>
  </div>
  <button type="button" class="tool-action" id="irtEvaluate">효과 평가</button>
  <div id="irtOutcome" style="margin-top:10px"></div>
  </div>
  </details>
  </div>
  `;

  document.getElementById('irtGenerate').addEventListener('click', async () => {
  const text = document.getElementById('irtTarget').value.trim();
  if (!text) { alert('Step 3 — 표적 악몽 본문을 적어주세요.'); return; }
  const out = document.getElementById('irtRescript');
  out.innerHTML = 'AI가 안전한 결말 3안을 생성 중 ⋯ (30~60초)';
  const r = await fetch('/api/irt/rescript', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({nightmare_text: text}),
  });
  const d = await r.json();
  if (d.blocked) {
  out.innerHTML = `<div style="padding:12px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.7;white-space:pre-line">${(d.text||'').replace(/</g,'&lt;')}</div>`;
  return;
  }
  if (!d.options || !d.options.length) {
  out.innerHTML = `<pre>${(d.text||'(빈)').replace(/</g,'&lt;')}</pre>`;
  return;
  }
  out.innerHTML = d.options.map((opt, i) => `
  <div style="padding:12px;margin:6px 0;background:rgba(60,80,120,0.3);border-radius:8px;white-space:pre-wrap;line-height:1.6">
  <b>안 ${i+1}</b><br>${opt.replace(/</g,'&lt;')}
  <br><button type="button" class="tool-action" onclick="alert('안 ${i+1} 선택됨. 매일 14시 알림으로 시각화하세요.')">이 안 선택</button>
  </div>
  `).join('');
  });

  document.getElementById('irtAlarm').addEventListener('click', async () => {
  if (!('Notification' in window)) { alert('이 브라우저는 알림을 지원하지 않습니다.'); return; }
  const perm = await Notification.requestPermission();
  if (perm === 'granted') {
  alert('알림 권한 OK. 14시에 리허설 알림이 옵니다 (탭이 열려 있어야 작동).');
  // 간단한 1회 alarm — 매일 14시
  const now = new Date();
  const next = new Date();
  next.setHours(14, 0, 0, 0);
  if (next < now) next.setDate(next.getDate() + 1);
  setTimeout(() => {
  new Notification('IRT 리허설 시간 (14:00)', {
  body: '재각본을 5~20분 시각화하세요.',
  });
  }, next - now);
  }
  });

  document.getElementById('irtEvaluate').addEventListener('click', () => {
  const base = parseFloat(document.getElementById('irtBaseline').value);
  const w8 = parseFloat(document.getElementById('irtWeek8').value);
  if (isNaN(base) || isNaN(w8) || base <= 0) {
  alert('두 빈도 모두 입력하세요.'); return;
  }
  const reduction = ((base - w8) / base * 100).toFixed(1);
  const met = reduction >= 50;
  document.getElementById('irtOutcome').innerHTML = `
  <div style="padding:12px;background:${met ? 'rgba(80,160,80,0.3)' : 'rgba(160,80,80,0.3)'};border-radius:8px">
  악몽 빈도 감소: <b>${reduction}%</b>
  ${met ? ' 목표 달성 (-50% 이상)' : ' 미달 — 표적 재선정 권장. CES-D ≥16점 동반 시 정신건강의학과 의뢰.'}
  </div>
  `;
  });
}

// ───  Hill 3단계 ───
async function renderHillTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> Clara Hill 3단계 — 탐색 → 통찰 → 실행</h4>
  <p style="opacity:0.85;font-size:0.88em">해석에서 멈추지 않고 현실 행동으로 이어주는 CBT 기반 모델.</p>

  <label>꿈 본문</label>
  <textarea id="hillDream" rows="4" placeholder="꿈을 적어주세요."></textarea>

  <div style="margin-top:10px">
  <button type="button" class="tool-action" data-step="1">Step 1: 탐색</button>
  <button type="button" class="tool-action" data-step="2">Step 2: 통찰</button>
  <button type="button" class="tool-action" data-step="3">Step 3: 실행 </button>
  </div>

  <label style="margin-top:10px">Step 1 응답 (Step 2 입력)</label>
  <textarea id="hillExploration" rows="2" placeholder="탐색 단계에서 떠올린 느낌·정서·위치"></textarea>

  <label>Step 2 결과 (Step 3 입력)</label>
  <textarea id="hillInsight" rows="2" placeholder="통찰 단계에서 도출된 의미"></textarea>

  <div id="hillResult" style="margin-top:14px"></div>
  </div>
  `;
  panel.querySelectorAll('button.tool-action[data-step]').forEach(btn => {
  btn.addEventListener('click', async () => {
  const step = parseInt(btn.dataset.step);
  const dream = document.getElementById('hillDream').value.trim();
  if (!dream) { alert('꿈 본문 필수'); return; }
  const out = document.getElementById('hillResult');
  out.innerHTML = `Step ${step} 진행 중 ⋯`;
  const r = await fetch('/api/hill/step', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
  dream_text: dream, step,
  exploration_responses: document.getElementById('hillExploration').value.trim()
  ? [document.getElementById('hillExploration').value.trim()] : [],
  insight_text: document.getElementById('hillInsight').value.trim() || null,
  }),
  });
  const d = await r.json();
  if (d.crisis_alert) {
  out.innerHTML = `<div style="padding:12px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.7;white-space:pre-line">${(d.text||'').replace(/</g,'&lt;')}</div>`;
  return;
  }
  out.innerHTML = `
  <div style="padding:14px;background:rgba(60,80,120,0.3);border-radius:8px">
  <b>Step ${step} — ${d.step_name}</b>
  <div style="margin-top:10px;white-space:pre-wrap;line-height:1.6">${(d.text||'').replace(/</g,'&lt;')}</div>
  </div>
  `;
  });
  });
}

// ───  Dormio TDI ───
async function renderDormioTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> Dormio TDI — N1 입면환각 표적 부화 (MIT MediaLab)</h4>
  <p style="opacity:0.85;font-size:0.88em">잠들기 직전 N1 단계를 능동 활용해 창의성·정서·기억 통합 발산. 주 2회 제한.</p>

  <label>표적 주제 (한 단어 ~ 한 문장)</label>
  <input type="text" id="dormioTopic" placeholder="예: 새 디자인 아이디어, 풀어야 할 문제">

  <label>카테고리</label>
  <select id="dormioCat" style="padding:6px;background:rgba(0,0,0,0.3);color:#fff;border:1px solid rgba(255,255,255,0.2);border-radius:4px">
  <option value="creative_problem">창의적 문제 해결</option>
  <option value="memory_recall">기억 회상 보조</option>
  <option value="emotional_processing">정서 처리</option>
  <option value="skill_consolidation">기술 통합</option>
  </select>

  <label>반복 횟수</label>
  <input type="number" id="dormioCycles" min="1" max="4" value="2">

  <button type="button" class="tool-action" id="dormioBuild">세션 안내 받기</button>
  <div id="dormioResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('dormioBuild').addEventListener('click', async () => {
  const topic = document.getElementById('dormioTopic').value.trim();
  if (!topic) { alert('표적 주제 필수'); return; }
  const out = document.getElementById('dormioResult');
  out.innerHTML = '안내 생성 ⋯';
  const r = await fetch('/api/dormio/session', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
  target_topic: topic,
  category: document.getElementById('dormioCat').value,
  cycles: parseInt(document.getElementById('dormioCycles').value) || 2,
  }),
  });
  const d = await r.json();
  out.innerHTML = `
  <div style="padding:14px;background:rgba(60,80,120,0.3);border-radius:8px">
  <div>카테고리: <b>${d.category_label}</b> · 기대 결과: ${d.expected_outcome}</div>
  <div style="margin-top:8px"><b>음성 큐 (취침 후 8분에 재생)</b></div>
  <div style="padding:10px;margin:6px 0;background:rgba(255,255,255,0.05);border-radius:4px;font-style:italic">"${d.audio_cue_text}"</div>
  <details style="margin-top:8px"><summary>N1 진입 추정 가이드</summary>
  <pre style="white-space:pre-wrap;font-size:0.85em;background:rgba(0,0,0,0.3);padding:10px;border-radius:4px">${d.n1_entry_guide.replace(/</g,'&lt;')}</pre>
  </details>
  <details style="margin-top:8px"><summary>미세꿈 보고 양식 (깨우면 음성으로 답변)</summary>
  <ul>${(d.microdream_fields || []).map(f => `<li><b>${f.name}:</b> ${f.instruction}</li>`).join('')}</ul>
  </details>
  <div style="margin-top:10px;padding:8px;background:rgba(0,0,0,0.25);border-radius:4px;font-size:0.78em;opacity:0.85">${d.disclaimer}</div>
  </div>
  `;
  });
}

// ───  Ullman 5인 투사 ───
async function renderUllmanTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> Ullman 그룹 꿈 분석 — "이 꿈이 내 꿈이라면"</h4>
  <p style="opacity:0.85;font-size:0.88em">5명의 가상 페르소나(어머니·예술가·의사·수행자·철학자)가 동시에 투사. 단일 정답 강제 없음.</p>

  <label>꿈 본문</label>
  <textarea id="ullmanDream" rows="4" placeholder="꿈을 적어주세요."></textarea>
  <button type="button" class="tool-action" id="ullmanSubmit">5인 페르소나 투사 생성 (40~60초)</button>
  <div id="ullmanResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('ullmanSubmit').addEventListener('click', async () => {
  const text = document.getElementById('ullmanDream').value.trim();
  if (!text) { alert('꿈 본문 필수'); return; }
  const out = document.getElementById('ullmanResult');
  out.innerHTML = '5인 LLM 병렬 호출 중 ⋯';
  const r = await fetch('/api/ullman/group', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({dream_text: text}),
  });
  const d = await r.json();
  if (d.crisis_alert) {
  out.innerHTML = `<div style="padding:12px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.7;white-space:pre-line">${(d.text||'').replace(/</g,'&lt;')}</div>`;
  return;
  }
  out.innerHTML = (d.projections || []).map(p => `
  <div style="padding:12px;margin:6px 0;background:rgba(60,80,120,0.3);border-radius:8px">
  <b>${p.persona_name}</b>
  <div style="margin-top:6px;white-space:pre-wrap;line-height:1.6">${(p.text||'').replace(/</g,'&lt;')}</div>
  </div>
  `).join('') +
  (d.aggregate && d.aggregate.common_themes && d.aggregate.common_themes.length
  ? `<div style="margin-top:10px;padding:10px;background:rgba(120,80,160,0.3);border-radius:8px"><b>공통 모티프:</b> ${d.aggregate.common_themes.slice(0,5).join(', ')}</div>`
  : '');
  });
}

// ─── ② IRT 악몽 재각본 (구버전 — 호환용, 미사용) ───
async function renderIRTTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> IRT — 악몽 재각본 생성</h4>
  <p style="opacity:0.8;font-size:0.88em">반복되는 악몽이 있다면 그 결말을 의식적으로 다시 써서 매일 시각화하면 빈도가 줄어듭니다 (Krakow·Zadra 2010, AASM 2018 권고).</p>
  <label>표적 악몽 본문</label>
  <textarea id="irtNightmare" rows="5" placeholder="가장 자주·강하게 반복되는 악몽 한 편을 적어주세요."></textarea>
  <button type="button" class="tool-action" id="irtSubmit">재각본 3안 생성</button>
  <div id="irtResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('irtSubmit').addEventListener('click', async () => {
  const text = document.getElementById('irtNightmare').value.trim();
  if (!text) { alert('악몽 본문을 적어주세요.'); return; }
  const out = document.getElementById('irtResult');
  out.innerHTML = 'AI가 안전한 결말 3안을 생성 중 ⋯ (30~60초)';
  const r = await fetch('/api/irt/rescript', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({nightmare_text: text}),
  });
  const d = await r.json();
  if (d.blocked) {
  out.innerHTML = `<div style="padding:12px;background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.7;white-space:pre-line">${(d.text||'').replace(/</g,'&lt;')}</div>`;
  return;
  }
  if (!d.options || !d.options.length) {
  out.innerHTML = `<pre>${(d.text||'(빈 응답)').replace(/</g,'&lt;')}</pre>`;
  return;
  }
  out.innerHTML = d.options.map((opt, i) => `
  <div style="padding:14px;margin:8px 0;background:rgba(60,80,120,0.3);border-radius:8px;white-space:pre-wrap;line-height:1.6"><b>안 ${i+1}</b><br>${opt.replace(/</g,'&lt;')}</div>
  `).join('') +
  `<div style="margin-top:10px;opacity:0.85;font-size:0.88em">${d.instruction || ''}</div>` +
  (d.legal_notice ? `<div style="margin-top:8px;padding:8px;background:rgba(0,0,0,0.25);border-radius:4px;font-size:0.78em;white-space:pre-line">${d.legal_notice.replace(/</g,'&lt;')}</div>` : '');
  });
}

// ─── ③ 7일 정서 곡선 (Cartwright) ───
async function renderMoodTool(panel) {
  const uid = await ensureAnonId();
  panel.innerHTML = `<div class="tool-panel-inner"> 최근 일기 정서 분석 중 ⋯</div>`;
  const r = await fetch('/api/cartwright/mood_curve', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: uid, days: 14}),
  });
  const d = await r.json();

  const hasData = (d.samples ?? 0) > 0;
  const html = `
  <div class="tool-panel-inner">
  <h4> Cartwright 7일+ mood-dream 곡선</h4>
  ${!hasData ? `
  <p style="opacity:0.85">아직 누적된 일기가 부족합니다. 매일 꿈을 기록하시면 7일 후 정서 추세 곡선이 표시됩니다.</p>
  <p style="opacity:0.6;font-size:0.85em">${d.note || ''}</p>
  ` : `
  <div>관측 일수: <b>${d.days_observed}</b>일 / 평균 정서가: <b>${d.mean_valence}</b></div>
  <div>전반 평균: ${d.first_half_mean} → 후반 평균: ${d.second_half_mean} (Δ ${d.delta})</div>
  <div style="margin-top:6px">패턴: <b>${d.pattern}</b></div>
  <div style="margin-top:6px;opacity:0.85">${d.interpretive_note}</div>
  <div style="margin-top:12px">
  <svg viewBox="0 0 ${(d.valences||[]).length * 40} 100" style="width:100%;max-width:600px;background:rgba(0,0,0,0.2);border-radius:6px">
  <polyline fill="none" stroke="var(--gold)" stroke-width="2"
  points="${(d.valences||[]).map((v, i) => `${i*40+20},${50-v*12}`).join(' ')}" />
  ${(d.valences||[]).map((v, i) => `<circle cx="${i*40+20}" cy="${50-v*12}" r="4" fill="#fff"/>`).join('')}
  <line x1="0" y1="50" x2="${(d.valences||[]).length*40}" y2="50" stroke="rgba(255,255,255,0.3)" stroke-dasharray="2,2"/>
  </svg>
  <div style="opacity:0.6;font-size:0.75em">Y축: -3(부정) ~ +3(긍정)</div>
  </div>
  <div style="margin-top:10px;opacity:0.8;font-size:0.85em">${d.cartwright_principle || ''}</div>
  `}
  </div>
  `;
  panel.innerHTML = html;
}

// ─── ④ 묘에 14일 장기 일기 ───
async function renderMyoeTool(panel) {
  const uid = await ensureAnonId();
  panel.innerHTML = `<div class="tool-panel-inner"> 묘에 분석 중 ⋯</div>`;
  const r = await fetch('/api/myoe/long_term', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: uid, min_entries: 14, days: 30}),
  });
  const d = await r.json();

  const html = `
  <div class="tool-panel-inner">
  <h4> 묘에 쇼닌『몽기』 — 14일+ 장기 자기관찰</h4>
  ${!d.analysis_available ? `
  <p>${d.note || '데이터 부족'}</p>
  <p style="opacity:0.6;font-size:0.85em">묘에 쇼닌은 40년간 꿈을 기록하며 마음 공부의 자료로 삼았습니다. 14일 이상 누적되면 반복 모티프와 정서 추세가 보입니다.</p>
  ` : `
  <div>관측 기간: <b>${d.entries_observed}</b>일</div>
  <div style="margin-top:8px"><b>반복 모티프 (3회 이상):</b></div>
  <ul>${(d.repeating_motifs||[]).map(m => `<li>${m}</li>`).join('') || '<li style="opacity:0.6">아직 강한 반복 모티프 없음</li>'}</ul>
  <div><b>정서 평균:</b> ${d.valence_mean} (추세 Δ ${d.valence_trend_delta})</div>
  <div style="margin-top:10px;opacity:0.85">${d.myoe_insight || ''}</div>
  <details style="margin-top:10px"><summary>상위 5 모티프 빈도</summary>
  <ul>${(d.top_5_motifs||[]).map(([m, n]) => `<li>${m} — ${n}회</li>`).join('')}</ul>
  </details>
  `}
  </div>
  `;
  panel.innerHTML = html;
}

// ─── ⑤ 자각몽 7일 프로그램 ───
async function renderLucidTool(panel) {
  panel.innerHTML = `<div class="tool-panel-inner"> 자각몽 프로그램 로드 중 ⋯</div>`;
  const r = await fetch('/api/lucid/program');
  const d = await r.json();
  const prog = d.program;

  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> 자각몽 7일 입문 프로그램 (LaBerge 1980)</h4>
  <ol style="line-height:1.7">
  ${prog.daily_plan.map(p => `<li><b>Day ${p.day}:</b> ${p.task}</li>`).join('')}
  </ol>
  <details style="margin-top:10px">
  <summary>Reality Check 3종 (오늘 시도)</summary>
  <ul>${prog.reality_checks.map(rc => `<li><b>${rc.name}:</b> ${rc.instruction}</li>`).join('')}</ul>
  </details>
  <details style="margin-top:10px">
  <summary>MILD 기법 (기억 유도 자각몽)</summary>
  <pre style="white-space:pre-wrap;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;font-size:0.88em">${prog.mild_protocol.replace(/</g,'&lt;')}</pre>
  </details>
  <details style="margin-top:10px">
  <summary>WBTB 기법 (다시 자기)</summary>
  <pre style="white-space:pre-wrap;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;font-size:0.88em">${prog.wbtb_protocol.replace(/</g,'&lt;')}</pre>
  </details>
  <div style="margin-top:12px;padding:8px;background:rgba(0,0,0,0.25);border-radius:4px;font-size:0.8em;opacity:0.85">${prog.disclaimer}</div>
  </div>
  `;
}

// ─── ⑥ 꿈 부화 ───
async function renderIncubationTool(panel) {
  panel.innerHTML = `
  <div class="tool-panel-inner">
  <h4> 꿈 부화 (Dream Incubation, 고대 아스클레피오스 신전 수면 현대화)</h4>
  <p style="opacity:0.85;font-size:0.88em">취침 약 20분 전, 한 질문에 집중하면 의미 있는 꿈을 꿀 가능성이 높아집니다.</p>
  <label>오늘 밤 꿈에서 답을 구하고 싶은 질문 (한 문장)</label>
  <input type="text" id="incQuestion" placeholder="예: 내가 지금 이직하는 것이 옳은가?">
  <div style="margin-top:10px">
  <label><input type="checkbox" id="incLowRecall"> 평소 꿈을 잘 못 꿈/기억 안 남</label>
  <label><input type="checkbox" id="incDecision"> 중요한 결정을 앞두고 있음</label>
  <label><input type="checkbox" id="incStress"> 정서 회복이 필요</label>
  <label><input type="checkbox" id="incLucid"> 자각몽 훈련 중</label>
  </div>
  <button type="button" class="tool-action" id="incSubmit">5단계 안내 받기</button>
  <div id="incResult" style="margin-top:14px"></div>
  </div>
  `;
  document.getElementById('incSubmit').addEventListener('click', async () => {
  const q = document.getElementById('incQuestion').value;
  const body = {
  question: q,
  low_recall: document.getElementById('incLowRecall').checked,
  upcoming_decision: document.getElementById('incDecision').checked,
  high_stress: document.getElementById('incStress').checked,
  lucid_dream_practice: document.getElementById('incLucid').checked,
  };
  const out = document.getElementById('incResult');
  out.innerHTML = '안내 생성 중 ⋯';
  const r = await fetch('/api/incubation/session', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(body),
  });
  const d = await r.json();
  const sess = d.session;
  out.innerHTML = `
  <div style="padding:14px;background:rgba(10,15,30,0.55);border:1px solid var(--gold-dp);border-radius:3px">
  <div><b>오늘 밤 의도 문장:</b></div>
  <div style="padding:10px;margin:8px 0;background:rgba(255,255,255,0.05);border-radius:4px;font-style:italic">${sess.affirmation}</div>
  <div style="margin-top:8px"><b>총 소요:</b> 약 ${sess.total_duration_min}분</div>
  <ol style="margin-top:8px;line-height:1.7">
  ${sess.steps.map(s => `<li><b>${s.name}</b> (${s.duration_min}분)<br><span style="opacity:0.85">${s.instruction}</span></li>`).join('')}
  </ol>
  <details style="margin-top:8px">
  <summary>깨어난 직후 회상 가이드</summary>
  <pre style="white-space:pre-wrap;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;font-size:0.88em">${sess.recall_instruction.replace(/</g,'&lt;')}</pre>
  </details>
  <div style="margin-top:10px;padding:8px;background:rgba(0,0,0,0.25);border-radius:4px;font-size:0.8em;opacity:0.85">${sess.disclaimer}</div>
  </div>
  `;
  });
}

// 페이지 로드 시 한 번 계산 (기본값) — 안전망 포함
function autoInit() {
  console.log('[사주 엔진] 로드 완료. SAJU 함수들:', Object.keys(window.SAJU || {}));
  try {
  // ADR-052: ES6 module 호환 — window.SAJU prefix 명시 (외부 .js는 module scope 격리)
  window.SAJU.updateHanjaSelectors(); // 빈 이름 칸용 안내 표시
  window.SAJU.performCalculation();   // 기본값으로 백그라운드 계산만 (화면 전환 X)
  console.log('[사주 엔진] 자동 계산 완료');
  } catch (e) {
  console.error('[사주 엔진] 자동 계산 실패:', e);
  document.getElementById('result').innerHTML =
  `<div style="background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.45);border-radius:3px;padding:14px;color:#e9b3a8;font-family:'Nanum Myeongjo',serif;line-height:1.6">
  <b>초기 계산 실패</b><br>
  <code>${(e.message || e).toString().replace(/</g,'&lt;')}</code><br>
  </div>`;
  }
}
// ADR-045: saju-ui.js (defer) 실행 후 autoInit 호출 보장 → 항상 DOMContentLoaded 가드.
// readyState === 'interactive' 즉시 호출은 defer script 미실행 상태라 함수 미정의 위험.
if (document.readyState === 'loading' || document.readyState === 'interactive') {
  document.addEventListener('DOMContentLoaded', autoInit);
} else {
  autoInit();  // complete 상태에서만 즉시
}

