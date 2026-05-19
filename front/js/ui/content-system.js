// ============================================================
// content-system.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// 60 콘텐츠 시스템 (탭·필드·렌더)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
(function setupContentSystem() {
  const menuView = document.getElementById('menuView');
  const menuGrid = document.getElementById('menuGrid');
  const menuName = document.getElementById('menuMasterName');
  const menuSub = document.getElementById('menuMasterSub');
  const contentView = document.getElementById('contentView');
  const contentBody = document.getElementById('contentBody');
  if (!menuView || !contentView) return;

  // 현재 진입한 도사 키 (menu-mode 일 때 의미 있음)
  let currentMaster = null;

  function setMode(mode) {
  // 'gallery' | 'menu' | 'content' | null (in-app default)
  document.body.classList.remove('gallery-mode', 'menu-mode', 'content-mode');
  if (mode === 'gallery') document.body.classList.add('gallery-mode');
  else if (mode === 'menu') document.body.classList.add('menu-mode');
  else if (mode === 'content') document.body.classList.add('content-mode');
  }

  function badgeHtml(item) {
  const out = [];
  if (item.tier === 'free') out.push(`<span class="badge badge-free">무료</span>`);
  if (item.tier === 'premium') out.push(`<span class="badge badge-premium">프리미엄</span>`);
  if (item.tier === 'season') out.push(`<span class="badge badge-season">시즌</span>`);
  (item.badges || []).forEach(b => {
  if (b === 'hot') out.push(`<span class="badge badge-hot">인기</span>`);
  if (b === 'new') out.push(`<span class="badge badge-new">NEW</span>`);
  });
  return out.join('');
  }

  function renderMenu(masterKey) {
  const data = window.WHM_CONTENTS[masterKey];
  if (!data) return;
  currentMaster = masterKey;
  menuName.textContent = data.master;
  menuSub.textContent = data.masterSub;

  // body에 캐릭터 클래스 적용 (배경 문양 + 메뉴 톤 분기)
  ['saju','dream','hwapae','star','face','palm','name'].forEach(k => document.body.classList.remove(`char-${k}`));
  document.body.classList.add(`char-${data.charKey}`);

  // Phase 1에서는 만월 외 다른 도사는 items가 비어있을 수 있음 → 안내
  if (!data.items || data.items.length === 0) {
  menuGrid.innerHTML = `
  <div class="menu-card" style="grid-column:1/-1;text-align:center;cursor:default;min-height:120px;justify-content:center" onmouseover="this.style.transform='none'">
  <div class="menu-card-name" style="text-align:center">콘텐츠 준비 중</div>
  <p class="menu-card-desc" style="text-align:center">곧 다양한 풀이가 펼쳐집니다. 잠시만 기다려주세요.</p>
  </div>`;
  return;
  }

  menuGrid.innerHTML = data.items.map(item => `
  <button class="menu-card" type="button" data-content-key="${item.key}">
  <div class="menu-card-badges">${badgeHtml(item)}</div>
  <div class="menu-card-glyph">${item.glyph || ''}</div>
  <div class="menu-card-name">${item.name}</div>
  <p class="menu-card-desc">${item.desc || ''}</p>
  <div class="menu-card-meta">
  <span class="menu-card-time">⏱ ${item.est || '몇 분'}</span>
  <span>${item.tier === 'premium' ? '💎' : item.tier === 'season' ? '🌸 시즌' : '☆ 무료'}</span>
  </div>
  </button>
  `).join('');
  }

  function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' })[c]);
  }

  // 이름 input 옆 한자 셀렉터 자동 렌더 (사주 정통 풀이의 updateHanjaSelectors 와 동일 로직 미니버전)
  // 슬롯 안의 현재 선택을 기준으로 총 획수·불용한자 표시 갱신
  function updateContentHanjaTotal(slot) {
  const target = slot.querySelector('.content-hanja-total');
  if (!target) return;
  const strokes = window.SAJU?.한자획수 || {};
  const meanings = window.SAJU?.한자_뜻 || {};
  const bad = window.SAJU?.불용한자;
  const cells = slot.querySelectorAll('.content-hanja-cell');
  if (cells.length === 0) {
  target.innerHTML = '<span class="content-hanja-hint">이름을 적어주세요</span>';
  return;
  }
  let total = 0;
  let picked = 0;
  let unusable = [];
  const rows = [];
  cells.forEach(cell => {
  const ch = cell.querySelector('.content-hanja-han b')?.textContent || '';
  const sel = cell.querySelector('.content-hanja-select');
  const han = sel ? sel.value : '';
  if (!han) {
  rows.push(`<span class="cht-row cht-empty">${ch} → 한자 없음</span>`);
  return;
  }
  picked++;
  const stroke = strokes[han] || 0;
  const meaning = meanings[han] || '';
  if (stroke) total += stroke;
  const isBad = bad && typeof bad.has === 'function' && bad.has(han);
  if (isBad) unusable.push(`${ch}(${han})`);
  rows.push(`<span class="cht-row ${isBad ? 'cht-bad' : ''}"><b>${ch}</b> → <b>${han}</b> ${meaning} <span class="cht-num">${stroke || '?'}획</span>${isBad ? '<span class="cht-badge">[불용]</span>' : ''}</span>`);
  });
  let summary;
  if (picked === 0) {
  summary = '<div class="cht-sum-empty">한자를 골라야 총 획수가 계산됩니다</div>';
  } else {
  summary = `<div class="cht-sum">총 획수 <b>${total}</b>획</div>`;
  }
  let warning = '';
  if (unusable.length) {
  warning = `<div class="cht-warning">⚠ 불용한자 포함: <b>${unusable.join(', ')}</b> · 의미가 어둡거나 흉운으로 분류되어 작명에서 잘 쓰지 않습니다</div>`;
  }
  target.innerHTML = `<div class="cht-rows">${rows.join('')}</div>${summary}${warning}`;
  }

  function renderHanjaForInput(input, slot) {
  const name = (input.value || '').trim();
  if (!name) {
  slot.innerHTML = '<span class="content-hanja-hint">이름을 적으면 글자마다 쓸 수 있는 한자가 나옵니다 (모르면 그냥 두셔도 됩니다)</span>';
  return;
  }
  const splitFn = window.SAJU?.splitName;
  const map = window.SAJU?.한글음_한자;
  const strokes = window.SAJU?.한자획수;
  const meanings = window.SAJU?.한자_뜻;
  const bad = window.SAJU?.불용한자;
  if (!splitFn || !map || !strokes || !meanings) {
  slot.innerHTML = '<span class="content-hanja-hint">한자 데이터 로딩 중…</span>';
  return;
  }
  const { surname, givenName } = splitFn(name);
  const surnameChars = Array.from(surname || '');
  const nameChars = Array.from(givenName || '');
  const allChars = [...surnameChars, ...nameChars];
  // 기존 선택 보존
  const previous = {};
  slot.querySelectorAll('.content-hanja-select').forEach(sel => {
  if (sel.value) previous[sel.dataset.char + ':' + sel.dataset.idx] = sel.value;
  });
  let html = '<div class="content-hanja-title">한자 고르기 <span>(모르면 그냥 두세요)</span></div><div class="content-hanja-cells">';
  for (let i = 0; i < allChars.length; i++) {
  const ch = allChars[i];
  const isSurname = i < surnameChars.length;
  const candidates = (map[ch] || []).filter(h => strokes[h] && meanings[h]);
  const key = ch + ':' + i;
  const prevSel = previous[key] || '';
  const opts = ['<option value="">— 한자 안 씀 —</option>'].concat(
  candidates.map(h => {
  const stroke = strokes[h];
  const meaning = meanings[h] || '';
  const isBad = bad && typeof bad.has === 'function' && bad.has(h);
  const selected = (h === prevSel) ? ' selected' : '';
  return `<option value="${h}"${selected}>${h} ${meaning} (${stroke}획)${isBad ? ' · [불용]' : ''}</option>`;
  })
  ).join('');
  html += `<span class="content-hanja-cell">
  <div class="content-hanja-han"><b>${ch}</b><small>${isSurname ? '성' : '이름'}</small></div>
  <select class="content-hanja-select" data-char="${ch}" data-idx="${i}">${opts}</select>
  </span>`;
  }
  html += '</div>';
  // 총 획수·불용 표시 영역 (셀렉트 변경 시 갱신)
  html += '<div class="content-hanja-total"></div>';
  slot.innerHTML = html;
  // 셀렉트 변경 시 총 획수 갱신 (이벤트 위임)
  if (!slot.dataset.totalBound) {
  slot.addEventListener('change', (e) => {
  if (e.target.classList.contains('content-hanja-select')) updateContentHanjaTotal(slot);
  });
  slot.dataset.totalBound = '1';
  }
  updateContentHanjaTotal(slot);
  }

  function fieldHtml(field) {
  const id = `cf_${field.key}`;
  const sess = (window.WHM && window.WHM.load) ? window.WHM.load() : null;
  // 공유 데이터에서 prefill
  let prefill = '';
  if (field.share === 'name' && sess?.profile?.name) prefill = sess.profile.name;
  switch (field.type) {
  case 'text': {
  // share === 'name' 이면 한자 셀렉터 자리도 함께 둠 (renderContent 후 채워짐)
  const hanjaSlot = field.share === 'name'
  ? `<div id="${id}_hanja" class="content-hanja" data-hanja-for="${id}"></div>`
  : '';
  return `<div class="row"><label for="${id}">${field.label}</label>
  <input id="${id}" type="text" placeholder="${field.placeholder || ''}" value="${escapeHtml(prefill)}"${field.share === 'name' ? ' data-name-input="1"' : ''}>${hanjaSlot}</div>`;
  }
  case 'textarea':
  return `<div class="row"><label for="${id}">${field.label}</label>
  <textarea id="${id}" rows="${field.rows || 3}" placeholder="${field.placeholder || ''}"></textarea></div>`;
  case 'number':
  return `<div class="row"><label for="${id}">${field.label}</label>
  <input id="${id}" type="number" min="${field.min ?? ''}" max="${field.max ?? ''}" value="${field.default ?? ''}"></div>`;
  case 'select':
  return `<div class="row"><label for="${id}">${field.label}</label>
  <select id="${id}">
  <option value="">— 선택 —</option>
  ${(field.options || []).map(o => `<option value="${escapeHtml(o.value)}">${escapeHtml(o.label)}</option>`).join('')}
  </select></div>`;
  case 'ymd': {
  const y = sess?.profile?.birth?.year || 1990;
  const m = sess?.profile?.birth?.month || 5;
  const d = sess?.profile?.birth?.day || 15;
  return `<div class="row"><label for="${id}_y">${field.label}</label>
  <div class="row-group">
  <select id="${id}_y" data-ymd="year"></select>
  <select id="${id}_m" data-ymd="month"></select>
  <select id="${id}_d" data-ymd="day"></select>
  </div></div>`;
  }
  case 'hour-branch':
  return `<div class="row"><label for="${id}">${field.label}</label>
  <select id="${id}">
  <option value="子">자시 (子) · 23 ~ 01시</option>
  <option value="丑">축시 (丑) · 01 ~ 03시</option>
  <option value="寅">인시 (寅) · 03 ~ 05시</option>
  <option value="卯">묘시 (卯) · 05 ~ 07시</option>
  <option value="辰">진시 (辰) · 07 ~ 09시</option>
  <option value="巳">사시 (巳) · 09 ~ 11시</option>
  <option value="午">오시 (午) · 11 ~ 13시</option>
  <option value="未" selected>미시 (未) · 13 ~ 15시</option>
  <option value="申">신시 (申) · 15 ~ 17시</option>
  <option value="酉">유시 (酉) · 17 ~ 19시</option>
  <option value="戌">술시 (戌) · 19 ~ 21시</option>
  <option value="亥">해시 (亥) · 21 ~ 23시</option>
  <option value="unknown">시각 모름</option>
  </select></div>`;
  case 'gender':
  return `<div class="row"><label for="${id}">${field.label}</label>
  <select id="${id}">
  <option value="">— 선택 —</option>
  <option value="M">남자</option>
  <option value="F">여자</option>
  </select></div>`;
  default:
  return '';
  }
  }

  function renderContent(item, masterKey) {
  const master = window.WHM_CONTENTS[masterKey];
  // tab 속성이 있으면 기존 탭 화면으로 위임
  if (item.tab) {
  const tabBtn = document.querySelector(`.tab-btn[data-tab="${item.tab}"]`);
  if (tabBtn) { tabBtn.click(); }
  setMode(null); // 탭 콘텐츠가 표시되도록 menu/content 모드 모두 해제
  return;
  }
  // body에 캐릭터 클래스 유지
  ['saju','dream','hwapae','star','face','palm','name'].forEach(k => document.body.classList.remove(`char-${k}`));
  document.body.classList.add(`char-${master.charKey}`);
  // 추천 (이 도사의 다른 메뉴 3개 — 현재 항목 제외)
  const recItems = (master.items || []).filter(x => x.key !== item.key).slice(0, 3);
  const fieldsHtml = (item.fields || []).map(fieldHtml).join('');
  const isPremium = item.tier === 'premium';

  contentBody.innerHTML = `
  <article class="content-card">
  <button class="content-back" type="button" id="contentBackBtn">← ${master.master} 메뉴로</button>
  <div class="content-glyph">${item.glyph || ''}</div>
  <h2 class="content-title">${item.name}</h2>
  <p class="content-master-quote">${item.quote || ''}</p>

  ${fieldsHtml ? `<div class="content-section">
  <div class="content-section-title">― 입력 ―</div>
  <div class="content-form">${fieldsHtml}</div>
  </div>` : ''}

  ${item.sample ? `<div class="content-section">
  <div class="content-section-title">― 풀이 미리보기 ―</div>
  ${item.sample.split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('')}
  </div>` : ''}

  <div class="content-cta-wrap">
  <button class="content-cta" type="button" id="contentCtaBtn">${item.cta || '풀이 받기'}</button>
  <div class="content-cta-hint">
  ${isPremium ? '<span class="premium-mark">💎 프리미엄 콘텐츠</span> — 결제 후 정식 풀이가 펼쳐집니다.' : '백엔드 연결 후 정식 풀이가 펼쳐집니다.'}
  </div>
  </div>

  ${recItems.length ? `<div class="content-recommend">
  <h3 class="content-recommend-title">${master.master}의 다른 풀이</h3>
  <div class="content-recommend-grid">
  ${recItems.map(r => `
  <button class="content-recommend-card" type="button" data-recommend-key="${r.key}">
  <div class="content-recommend-glyph">${r.glyph || ''}</div>
  <div class="content-recommend-name">${r.name}</div>
  </button>`).join('')}
  </div>
  </div>` : ''}
  </article>
  `;

  setMode('content');
  // ymd 셀렉트들 채우기 (populateYmdSelects 모듈이 [data-ymd]에 자동 주입)
  if (window.requestAnimationFrame) {
  requestAnimationFrame(() => {
  contentBody.querySelectorAll('select[data-ymd]').forEach(sel => {
  // populateYmdSelects 와 동일 로직 재사용 — 빈 셀렉트만 채움
  if (sel.options.length === 0) {
  const kind = sel.dataset.ymd;
  const CURRENT_YEAR = new Date().getFullYear();
  let s, e;
  if (kind === 'year')  { s = CURRENT_YEAR; e = 1920; }
  else if (kind === 'month') { s = 1; e = 12; }
  else if (kind === 'day') { s = 1; e = 31; }
  else return;
  const step = s <= e ? 1 : -1;
  const def = { year: 1990, month: 5, day: 15 }[kind];
  for (let v = s; step > 0 ? v <= e : v >= e; v += step) {
  const opt = document.createElement('option');
  opt.value = String(v);
  opt.textContent = String(v);
  if (v === def) opt.selected = true;
  sel.appendChild(opt);
  }
  }
  });
  // 이름 입력(공유) 옆 한자 셀렉터 자동 생성·바인딩
  contentBody.querySelectorAll('input[data-name-input="1"]').forEach(input => {
  const slotId = input.id + '_hanja';
  const slot = document.getElementById(slotId);
  if (!slot) return;
  const refresh = () => renderHanjaForInput(input, slot);
  // 중복 바인딩 방지
  if (!input.dataset.hanjaBound) {
  input.addEventListener('input', refresh);
  input.dataset.hanjaBound = '1';
  }
  // 초기 1회 (prefill 된 이름이 있으면 바로 렌더)
  refresh();
  });
  });
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // 외부 노출 — 카드 갤러리에서 호출
  window.__menuOpen = (masterKey) => {
  renderMenu(masterKey);
  setMode('menu');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  window.__contentOpen = (masterKey, contentKey) => {
  const data = window.WHM_CONTENTS[masterKey];
  if (!data) return;
  const item = (data.items || []).find(x => x.key === contentKey);
  if (!item) return;
  renderContent(item, masterKey);
  };

  // 메뉴 그리드 클릭 → 콘텐츠 진입
  menuGrid.addEventListener('click', (e) => {
  const btn = e.target.closest('.menu-card[data-content-key]');
  if (!btn) return;
  const key = btn.dataset.contentKey;
  if (currentMaster) window.__contentOpen(currentMaster, key);
  });

  // 메뉴 헤더 뒤로가기 → 카드 갤러리로 (다른 점술가 고르기)
  const menuBackBtn = document.getElementById('menuBackToGalleryBtn');
  if (menuBackBtn) {
  menuBackBtn.addEventListener('click', () => {
  setMode('gallery');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  }

  // 콘텐츠 뷰: 뒤로가기 + 추천 카드 클릭
  contentBody.addEventListener('click', (e) => {
  if (e.target.closest('#contentBackBtn')) {
  if (currentMaster) window.__menuOpen(currentMaster);
  return;
  }
  const rec = e.target.closest('.content-recommend-card[data-recommend-key]');
  if (rec && currentMaster) {
  window.__contentOpen(currentMaster, rec.dataset.recommendKey);
  return;
  }
  });
})();

// ═══════════════════════════════════════════════════════════
// 醉仙樓 (취선루) 진입·인증·전환·라우팅 시스템
// 진입: chwiseonGate 클릭 → 인증 게이트 → (인증 OK) → 공간 전환 → 메인
// 본관 시스템과 완전히 분리. localStorage 로 인증 상태 영속화 (프론트만).
// ═══════════════════════════════════════════════════════════
