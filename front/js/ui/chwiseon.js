// ============================================================
// chwiseon.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// 취선루 19+ 영역 (인증·잠금·콘텐츠)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
(function setupChwiseon() {
  const STORAGE_KEY = 'whm.chwiseon.adultVerified.v1';
  const gate = document.getElementById('chwiseonGate');
  const auth = document.getElementById('chwiseonAuth');
  const trans = document.getElementById('chwiseonTransition');
  const main = document.getElementById('chwiseonMain');
  const exitBtn = document.getElementById('chwiseonExit');
  const verifyBtn = document.getElementById('cauthVerifyBtn');
  const cancelBtn = document.getElementById('cauthBackBtn');
  if (!gate || !auth || !main) return;

  function isVerified() {
  try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch (_) { return false; }
  }
  function setVerified(v) {
  try { v ? localStorage.setItem(STORAGE_KEY, '1') : localStorage.removeItem(STORAGE_KEY); } catch (_) {}
  }

  function openAuth() {
  auth.hidden = false;
  requestAnimationFrame(() => auth.classList.add('is-open'));
  }
  function closeAuth() {
  auth.classList.remove('is-open');
  setTimeout(() => { auth.hidden = true; }, 350);
  }

  function playTransition(onDone) {
  trans.hidden = false;
  requestAnimationFrame(() => trans.classList.add('is-active'));
  setTimeout(() => {
  onDone();
  }, 2400);
  setTimeout(() => {
  trans.classList.remove('is-active');
  setTimeout(() => { trans.hidden = true; }, 300);
  }, 3000);
  }

  function enterChwiseon() {
  // 본관 모든 모드 해제 + 취선루 켜기
  document.body.classList.remove('gallery-mode', 'menu-mode', 'content-mode');
  document.body.classList.add('chwiseon-on');
  // 갤러리·메뉴·콘텐츠 서브 모드 초기화
  document.body.classList.remove('chwiseon-menu-mode', 'chwiseon-content-mode');
  // 첫 카드(야선)로 갤러리 리셋
  setChwiseonIdx(0);
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function exitChwiseon() {
  document.body.classList.remove('chwiseon-on', 'chwiseon-menu-mode', 'chwiseon-content-mode');
  // 본관 갤러리 모드로 복귀
  if (typeof window.__galleryEnter === 'function') window.__galleryEnter();
  else document.body.classList.add('gallery-mode');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // 퇴장 전환 애니메이션 (월하몽 톤 — 달·금색·꽃잎·장막)
  const exitTrans = document.getElementById('chwiseonExitTransition');
  function playExitTransition(onDone) {
  if (!exitTrans) { onDone(); return; }
  exitTrans.hidden = false;
  requestAnimationFrame(() => exitTrans.classList.add('is-active'));
  // 본관 전환 시점: 2.2초 (장막 거의 다 닫힘 + 달 자리잡음 + 작별 인사 시작)
  setTimeout(() => { onDone(); }, 2200);
  // 애니 종료 + 정리: 3.0초
  setTimeout(() => {
  exitTrans.classList.remove('is-active');
  setTimeout(() => { exitTrans.hidden = true; }, 350);
  }, 2900);
  }

  // 진입 문 클릭
  gate.addEventListener('click', () => {
  if (isVerified()) {
  playTransition(enterChwiseon);
  } else {
  openAuth();
  }
  });

  // 인증 버튼 (백엔드 미연결 — 프론트 데모용)
  verifyBtn.addEventListener('click', () => {
  // TODO: 백엔드 본인·성인 인증 연결. 지금은 클라이언트 확인만.
  const confirmed = confirm('본인 인증 시스템은 곧 연결됩니다 (백엔드 영역).\n\n프론트 데모로 만 19세 이상이심을 확인하시겠습니까?');
  if (!confirmed) return;
  setVerified(true);
  closeAuth();
  setTimeout(() => playTransition(enterChwiseon), 200);
  });
  cancelBtn.addEventListener('click', closeAuth);
  auth.querySelector('.cauth-backdrop').addEventListener('click', closeAuth);

  // 본관으로 돌아가기
  exitBtn.addEventListener('click', () => playExitTransition(exitChwiseon));

  // ───────────── 취선루 카드 갤러리 (5인) ─────────────
  const deck = document.getElementById('chwiseonDeck');
  const dotsHost = document.getElementById('chwiseonDots');
  const cards = Array.from(deck.querySelectorAll('.char-card'));
  const N = cards.length;
  let idx = 0;

  // 점 인디케이터 생성
  cards.forEach((c, i) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.addEventListener('click', () => setChwiseonIdx(i));
  dotsHost.appendChild(b);
  });
  const dotBtns = Array.from(dotsHost.children);

  function renderChwiseon() {
  deck.style.transform = `translateX(${-idx * 100}%)`;
  cards.forEach((c, i) => c.classList.toggle('is-active', i === idx));
  dotBtns.forEach((b, i) => b.classList.toggle('is-active', i === idx));
  }
  function setChwiseonIdx(i) {
  idx = Math.max(0, Math.min(N - 1, i));
  renderChwiseon();
  }
  function csNext() { setChwiseonIdx(idx + 1); }
  function csPrev() { setChwiseonIdx(idx - 1); }
  document.querySelector('[data-chwiseon-prev]').addEventListener('click', csPrev);
  document.querySelector('[data-chwiseon-next]').addEventListener('click', csNext);

  // 카드 들어가기 → 메뉴 모드
  deck.addEventListener('click', (e) => {
  const enterBtn = e.target.closest('.char-card-enter');
  if (!enterBtn) return;
  const card = enterBtn.closest('.char-card');
  const charKey = card?.dataset?.character;
  if (charKey) openChwiseonMenu(charKey);
  });

  // ─── 드래그·스와이프 (본관과 동일 패턴) ───
  const csGallery = deck.closest('.card-gallery');
  let csDrag = null;
  const DRAG_DEAD_PX = 8;
  function csGetPoint(e) {
  if (e.touches && e.touches[0]) return { x: e.touches[0].clientX, y: e.touches[0].clientY };
  return { x: e.clientX, y: e.clientY };
  }
  function csOnDown(e) {
  const p = csGetPoint(e);
  csDrag = { startX: p.x, startY: p.y, deltaX: 0, deltaY: 0, locked: null, width: csGallery?.clientWidth || deck.clientWidth };
  deck.classList.add('is-dragging');
  }
  function csOnMove(e) {
  if (!csDrag) return;
  const p = csGetPoint(e);
  csDrag.deltaX = p.x - csDrag.startX;
  csDrag.deltaY = p.y - csDrag.startY;
  if (csDrag.locked === null) {
  if (Math.abs(csDrag.deltaX) > DRAG_DEAD_PX || Math.abs(csDrag.deltaY) > DRAG_DEAD_PX) {
  csDrag.locked = Math.abs(csDrag.deltaX) > Math.abs(csDrag.deltaY) ? 'x' : 'y';
  }
  }
  if (csDrag.locked === 'x') {
  if (e.cancelable) e.preventDefault();
  let dx = csDrag.deltaX;
  if ((idx === 0 && dx > 0) || (idx === N - 1 && dx < 0)) dx *= 0.35;
  const pct = (dx / csDrag.width) * 100;
  deck.style.transform = `translateX(calc(${-idx * 100}% + ${pct}%))`;
  }
  }
  function csOnUp() {
  if (!csDrag) return;
  deck.classList.remove('is-dragging');
  if (csDrag.locked === 'x') {
  const threshold = csDrag.width * 0.18;
  if (csDrag.deltaX < -threshold) csNext();
  else if (csDrag.deltaX > threshold) csPrev();
  else renderChwiseon();
  }
  csDrag = null;
  }
  // 마우스
  deck.addEventListener('mousedown', (e) => {
  if (e.target.closest('.char-card-enter')) return; // 들어가기 버튼 클릭은 패스
  e.preventDefault();
  csOnDown(e);
  });
  window.addEventListener('mousemove', csOnMove);
  window.addEventListener('mouseup', csOnUp);
  // 터치
  deck.addEventListener('touchstart', csOnDown, { passive: true });
  deck.addEventListener('touchmove', csOnMove, { passive: false });
  deck.addEventListener('touchend', csOnUp);
  deck.addEventListener('touchcancel', csOnUp);

  // 키보드 (취선루 갤러리 모드일 때만)
  document.addEventListener('keydown', (e) => {
  if (!document.body.classList.contains('chwiseon-on')) return;
  if (document.body.classList.contains('chwiseon-menu-mode')) return;
  if (document.body.classList.contains('chwiseon-content-mode')) return;
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.key === 'ArrowRight') { e.preventDefault(); csNext(); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); csPrev(); }
  });

  // ───────────── 취선루 메뉴/콘텐츠 라우팅 ─────────────
  const menuView = document.getElementById('chwiseonMenu');
  const menuGrid = document.getElementById('chwiseonMenuGrid');
  const menuName = document.getElementById('chwiseonMasterName');
  const menuSub = document.getElementById('chwiseonMasterSub');
  const contentView = document.getElementById('chwiseonContent');
  const contentBody = document.getElementById('chwiseonContentBody');
  let currentMaster = null;

  function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' })[c]);
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

  function fieldHtml(field) {
  const id = `cs_cf_${field.key}`;
  const sess = (window.WHM && window.WHM.load) ? window.WHM.load() : null;
  let prefill = '';
  if (field.share === 'name' && sess?.profile?.name) prefill = sess.profile.name;
  switch (field.type) {
  case 'text':
  return `<div class="row"><label for="${id}">${escapeHtml(field.label)}</label>
  <input id="${id}" type="text" placeholder="${escapeHtml(field.placeholder || '')}" value="${escapeHtml(prefill)}"></div>`;
  case 'textarea':
  return `<div class="row"><label for="${id}">${escapeHtml(field.label)}</label>
  <textarea id="${id}" rows="${field.rows || 3}" placeholder="${escapeHtml(field.placeholder || '')}"></textarea></div>`;
  case 'select':
  return `<div class="row"><label for="${id}">${escapeHtml(field.label)}</label>
  <select id="${id}">
  <option value="">— 선택 —</option>
  ${(field.options || []).map(o => `<option value="${escapeHtml(o.value)}">${escapeHtml(o.label)}</option>`).join('')}
  </select></div>`;
  case 'ymd':
  return `<div class="row"><label>${escapeHtml(field.label)}</label>
  <div class="row-group">
  <select id="${id}_y" data-ymd="year"></select>
  <select id="${id}_m" data-ymd="month"></select>
  <select id="${id}_d" data-ymd="day"></select>
  </div></div>`;
  case 'hour-branch':
  return `<div class="row"><label for="${id}">${escapeHtml(field.label)}</label>
  <select id="${id}">
  <option value="子">자시 (子) · 23 ~ 01시</option><option value="丑">축시 (丑)</option>
  <option value="寅">인시 (寅)</option><option value="卯">묘시 (卯)</option>
  <option value="辰">진시 (辰)</option><option value="巳">사시 (巳)</option>
  <option value="午">오시 (午)</option><option value="未" selected>미시 (未)</option>
  <option value="申">신시 (申)</option><option value="酉">유시 (酉)</option>
  <option value="戌">술시 (戌)</option><option value="亥">해시 (亥)</option>
  <option value="unknown">시각 모름</option>
  </select></div>`;
  case 'gender':
  return `<div class="row"><label for="${id}">${escapeHtml(field.label)}</label>
  <select id="${id}"><option value="">— 선택 —</option><option value="M">남자</option><option value="F">여자</option></select></div>`;
  default: return '';
  }
  }

  function openChwiseonMenu(charKey) {
  const data = window.CHWISEON_CONTENTS?.[charKey];
  if (!data) return;
  currentMaster = charKey;
  menuName.textContent = data.master;
  menuSub.textContent = data.masterSub;
  menuGrid.innerHTML = (data.items || []).map(item => `
  <button class="menu-card" type="button" data-content-key="${item.key}">
  <div class="menu-card-badges">${badgeHtml(item)}</div>
  <div class="menu-card-glyph">${item.glyph || ''}</div>
  <div class="menu-card-name">${escapeHtml(item.name)}</div>
  <p class="menu-card-desc">${escapeHtml(item.desc || '')}</p>
  <div class="menu-card-meta">
  <span class="menu-card-time">⏱ ${escapeHtml(item.est || '')}</span>
  <span>${item.price ? `💎 ${escapeHtml(item.price)}` : '💎 프리미엄'}</span>
  </div>
  </button>`).join('');
  document.body.classList.add('chwiseon-menu-mode');
  document.body.classList.remove('chwiseon-content-mode');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openChwiseonContent(charKey, contentKey) {
  const data = window.CHWISEON_CONTENTS?.[charKey];
  if (!data) return;
  const item = (data.items || []).find(x => x.key === contentKey);
  if (!item) return;
  const recItems = data.items.filter(x => x.key !== contentKey).slice(0, 3);
  const fieldsHtml = (item.fields || []).map(fieldHtml).join('');
  contentBody.innerHTML = `
  <article class="content-card">
  <button class="content-back" type="button" id="csContentBack">← ${escapeHtml(data.master)} 메뉴로</button>
  <div class="content-glyph">${item.glyph || ''}</div>
  <h2 class="content-title">${escapeHtml(item.name)}</h2>
  <p class="content-master-quote">${escapeHtml(item.quote || '')}</p>

  ${fieldsHtml ? `<div class="content-section">
  <div class="content-section-title">― 입력 ―</div>
  <div class="content-form">${fieldsHtml}</div>
  </div>` : ''}

  ${item.sample ? `<div class="content-section">
  <div class="content-section-title">― 풀이 미리보기 ―</div>
  ${item.sample.split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('')}
  </div>` : ''}

  <div class="content-cta-wrap">
  <button class="content-cta" type="button" id="csContentCta">${escapeHtml(item.cta || '풀이 받기')}</button>
  <div class="content-cta-hint">
  <span class="premium-mark">💎 ${escapeHtml(item.price || '프리미엄')} · 19금 콘텐츠</span><br>
  결제 후 정식 풀이가 펼쳐집니다.
  </div>
  </div>

  ${recItems.length ? `<div class="content-recommend">
  <h3 class="content-recommend-title">${escapeHtml(data.master)}의 다른 풀이</h3>
  <div class="content-recommend-grid">
  ${recItems.map(r => `
  <button class="content-recommend-card" type="button" data-recommend-key="${r.key}">
  <div class="content-recommend-glyph">${r.glyph || ''}</div>
  <div class="content-recommend-name">${escapeHtml(r.name)}</div>
  </button>`).join('')}
  </div>
  </div>` : ''}
  </article>
  `;
  document.body.classList.remove('chwiseon-menu-mode');
  document.body.classList.add('chwiseon-content-mode');
  // ymd 셀렉트 채움
  requestAnimationFrame(() => {
  contentBody.querySelectorAll('select[data-ymd]').forEach(sel => {
  if (sel.options.length > 0) return;
  const kind = sel.dataset.ymd;
  const CY = new Date().getFullYear();
  let s, e;
  if (kind === 'year') { s = CY; e = 1920; }
  else if (kind === 'month') { s = 1; e = 12; }
  else if (kind === 'day') { s = 1; e = 31; }
  else return;
  const step = s <= e ? 1 : -1;
  const def = { year: 1990, month: 5, day: 15 }[kind];
  for (let v = s; step > 0 ? v <= e : v >= e; v += step) {
  const opt = document.createElement('option');
  opt.value = String(v); opt.textContent = String(v);
  if (v === def) opt.selected = true;
  sel.appendChild(opt);
  }
  });
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // 메뉴 카드 / 콘텐츠 뒤로가기 / 추천 라우팅
  menuGrid.addEventListener('click', (e) => {
  const card = e.target.closest('.menu-card[data-content-key]');
  if (!card) return;
  if (currentMaster) openChwiseonContent(currentMaster, card.dataset.contentKey);
  });

  // 취선루 메뉴 헤더 뒤로가기 → 카드 갤러리로 (다른 점술가 고르기)
  const csMenuBackBtn = document.getElementById('chwiseonMenuBackBtn');
  if (csMenuBackBtn) {
  csMenuBackBtn.addEventListener('click', () => {
  document.body.classList.remove('chwiseon-menu-mode', 'chwiseon-content-mode');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  }

  contentBody.addEventListener('click', (e) => {
  if (e.target.closest('#csContentBack')) {
  if (currentMaster) openChwiseonMenu(currentMaster);
  return;
  }
  const rec = e.target.closest('.content-recommend-card[data-recommend-key]');
  if (rec && currentMaster) {
  openChwiseonContent(currentMaster, rec.dataset.recommendKey);
  return;
  }
  });

  // 외부 노출 (디버깅·테스트용)
  window.__chwiseonEnter = () => playTransition(enterChwiseon);
  window.__chwiseonExit = () => playExitTransition(exitChwiseon);
  window.__chwiseonExitInstant = exitChwiseon; // 애니 없이 즉시
  window.__chwiseonGoTo = setChwiseonIdx;
  window.__chwiseonOpenMenu = openChwiseonMenu;
  window.__chwiseonResetAuth = () => setVerified(false);

  // 초기 렌더
  renderChwiseon();
})();

// Hwapae 외부 모듈: js/readers/hwapae-reader.js (ADR-042 Phase G)
// 본 위치 인라인 정의는 외부 .js로 이동.


