// ============================================================
// card-gallery.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// 카드 갤러리 (60 콘텐츠 스와이프·터치)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
// ─────────────────────────────────────────────────────────
(function setupCardGallery() {
  const deck = document.getElementById('cardDeck');
  const dots = document.getElementById('galleryDots');
  const prevArrow = document.querySelector('.gallery-arrow-prev');
  const nextArrow = document.querySelector('.gallery-arrow-next');
  const gallery = document.getElementById('cardGallery');
  const toGalleryBtn = document.getElementById('toGalleryBtn');
  if (!deck || !gallery) return;

  const cards = Array.from(deck.querySelectorAll('.char-card'));
  const N = cards.length;
  let idx = 0;
  let drag = null;

  // 점 인디케이터 생성
  cards.forEach((c, i) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.setAttribute('role', 'tab');
  b.setAttribute('aria-label', `${c.querySelector('.char-card-name')?.innerText || '카드'} ${i + 1}`);
  b.addEventListener('click', () => goTo(i));
  dots.appendChild(b);
  });
  const dotBtns = Array.from(dots.children);

  // body에 카드별 클래스 부여 (배경 문양 분기용)
  const CHAR_KEYS = ['saju', 'dream', 'hwapae', 'star', 'face', 'palm', 'name'];
  function syncBodyCharClass() {
  CHAR_KEYS.forEach(k => document.body.classList.remove(`char-${k}`));
  const active = cards[idx];
  const key = active?.dataset?.character;
  if (key) document.body.classList.add(`char-${key}`);
  }

  function render() {
  deck.style.transform = `translateX(${-idx * 100}%)`;
  cards.forEach((c, i) => c.classList.toggle('is-active', i === idx));
  dotBtns.forEach((b, i) => b.classList.toggle('is-active', i === idx));
  if (prevArrow) prevArrow.disabled = idx === 0;
  if (nextArrow) nextArrow.disabled = idx === N - 1;
  // 활성 카드 영상만 재생
  cards.forEach((c, i) => {
  const v = c.querySelector('.char-card-video');
  if (!v) return;
  if (i === idx) {
  try { v.currentTime = 0; } catch (_) {}
  v.play().catch(() => {});
  } else {
  v.pause();
  }
  });
  syncBodyCharClass();
  }
  function goTo(i) {
  idx = Math.max(0, Math.min(N - 1, i));
  render();
  }
  function next() { goTo(idx + 1); }
  function prev() { goTo(idx - 1); }

  // 화살표
  if (prevArrow) prevArrow.addEventListener('click', prev);
  if (nextArrow) nextArrow.addEventListener('click', next);

  // 키보드 (갤러리 모드일 때만)
  document.addEventListener('keydown', (e) => {
  if (!document.body.classList.contains('gallery-mode')) return;
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
  });

  // 드래그/터치 스와이프
  function getPoint(e) {
  if (e.touches && e.touches[0]) return { x: e.touches[0].clientX, y: e.touches[0].clientY };
  return { x: e.clientX, y: e.clientY };
  }
  function onDown(e) {
  const p = getPoint(e);
  drag = { startX: p.x, startY: p.y, deltaX: 0, deltaY: 0, locked: null, width: gallery.clientWidth };
  deck.classList.add('is-dragging');
  }
  function onMove(e) {
  if (!drag) return;
  const p = getPoint(e);
  drag.deltaX = p.x - drag.startX;
  drag.deltaY = p.y - drag.startY;
  if (drag.locked === null) {
  if (Math.abs(drag.deltaX) > 8 || Math.abs(drag.deltaY) > 8) {
  drag.locked = Math.abs(drag.deltaX) > Math.abs(drag.deltaY) ? 'x' : 'y';
  }
  }
  if (drag.locked === 'x') {
  e.preventDefault();
  // 끝단에서는 저항 (idx 0에서 오른쪽 드래그, idx N-1에서 왼쪽 드래그)
  let dx = drag.deltaX;
  if ((idx === 0 && dx > 0) || (idx === N - 1 && dx < 0)) dx *= 0.35;
  const pct = (dx / drag.width) * 100;
  deck.style.transform = `translateX(calc(${-idx * 100}% + ${pct}%))`;
  }
  }
  function onUp() {
  if (!drag) return;
  deck.classList.remove('is-dragging');
  if (drag.locked === 'x') {
  const threshold = drag.width * 0.18;
  if (drag.deltaX < -threshold) next();
  else if (drag.deltaX > threshold) prev();
  else render();
  }
  drag = null;
  }
  // 마우스
  deck.addEventListener('mousedown', (e) => {
  // 버튼 클릭은 드래그로 가로채지 않음
  if (e.target.closest('.char-card-enter')) return;
  e.preventDefault();
  onDown(e);
  });
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
  // 터치
  deck.addEventListener('touchstart', onDown, { passive: true });
  deck.addEventListener('touchmove', onMove, { passive: false });
  deck.addEventListener('touchend', onUp);
  deck.addEventListener('touchcancel', onUp);

  // 카드 클릭 → 해당 풀이 진입 (들어가기 버튼 또는 카드 본체)
  function enterCard(card) {
  const target = card.dataset.go;
  const charKey = card.dataset.character;
  if (!target) return;
  exitGalleryMode();
  // 콘텐츠 메뉴가 정의된 도사면 메뉴 그리드로, 아니면 기존 탭(레거시)
  const data = window.WHM_CONTENTS && window.WHM_CONTENTS[charKey];
  if (data && window.__menuOpen) {
  window.__menuOpen(charKey);
  } else {
  const tabBtn = document.querySelector(`.tab-btn[data-tab="${target}"]`);
  if (tabBtn) tabBtn.click();
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  deck.addEventListener('click', (e) => {
  // 드래그 직후 우발 클릭 방지: 드래그가 일정 거리 이상이면 클릭 무시
  // (mouseup → click 흐름에서 drag 객체는 이미 null 이지만, lastMoveX 변수 활용은 생략하고
  //  데드존을 onUp 시점에 처리하는 게 단순함. 여기선 단순 처리)
  const enterBtn = e.target.closest('.char-card-enter');
  if (enterBtn) {
  const card = enterBtn.closest('.char-card');
  if (card) enterCard(card);
  return;
  }
  // 카드 본체 클릭은 들어가기 버튼이 있으니 굳이 진입시키지 않음 (스와이프 우선)
  });

  // 갤러리 모드 전환
  function enterGalleryMode() {
  document.body.classList.add('gallery-mode');
  goTo(idx);
  }
  function exitGalleryMode() {
  document.body.classList.remove('gallery-mode');
  }
  window.__galleryEnter = enterGalleryMode;
  window.__galleryExit = exitGalleryMode;
  window.__galleryGoTo = goTo;

  // ← 점술가 고르러 버튼
  if (toGalleryBtn) {
  toGalleryBtn.addEventListener('click', () => {
  // menu/content 모드 모두 종료 → 갤러리 모드
  document.body.classList.remove('menu-mode', 'content-mode');
  enterGalleryMode();
  window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  }

  // 인트로 → 메인 진입 시 자동으로 갤러리 모드 진입
  // (질문하러 가기 버튼 클릭 시점에 setupIntro가 in-app 클래스 부여)
  const introBtn = document.getElementById('enterBtn');
  if (introBtn) {
  introBtn.addEventListener('click', () => {
  // body.in-app 부여 직후 갤러리 모드도 같이
  setTimeout(enterGalleryMode, 50);
  });
  } else {
  // 이미 in-app인 경우(개발/리로드)
  if (document.body.classList.contains('in-app')) enterGalleryMode();
  }

  // 페이지가 in-app 상태로 로드된 경우 (새로고침 후)
  if (document.readyState !== 'loading' && document.body.classList.contains('in-app')) {
  enterGalleryMode();
  }

  // 초기 렌더
  render();
})();

// ─────────────────────────────────────────────────────────
// 月下夢 콘텐츠 라인업 시스템 (60개 — 7명 점술가 × 7~12 콘텐츠)
// 카드 갤러리 → 도사 카드 클릭 → 메뉴 그리드 → 콘텐츠 진입
//
// 각 콘텐츠 스키마:
//   key:    고유 ID (URL hash 등에 사용)
//   name:   표시 이름
//   glyph:  한자 엠블럼 (2자)
//   desc:   한 줄 설명
//   tier:   'free' | 'premium' | 'season'
//   badges: ['hot', 'new', ...] (선택)
//   est:    예상 소요 시간 ("5분", "30~60초" 등)
//   quote:  캐릭터 말투 인용 (결과 화면 상단)
//   fields: [{ key, label, type:'text|number|select|textarea|year-month-day|hour-branch', ...options }]
//   tab:    기존 탭 활용 시 ID (예: 'saju' — 정통 사주는 기존 화면 사용)
//   sample: 결과 화면 더미 예시 (1~2 단락, 캐릭터 말투)
