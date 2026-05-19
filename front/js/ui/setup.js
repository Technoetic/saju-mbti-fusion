// ============================================================
// setup.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// UI setup IIFE 8개 (BgAudio·UxSound·Intro·BgVideo·NonNumeric·Fullscreen·Star·Ymd)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================

// 사주 UI (Section 9): js/core/saju-ui.js (ADR-045)
// fmtPillar·performCalculation·triggerAICall·renderResult + window.SAJU 외부 .js로 이동.

// 배경 음악 + 음소거 토글
(function setupBgAudio() {
  const a = document.getElementById('bgAudio');
  const btn = document.getElementById('muteBtn');
  if (!a) return;
  a.volume = 0.28;  // BGM은 잔잔히 (UX 효과음이 도드라지도록)
  a.loop = true;
  // 브라우저 자동재생 정책 우회 — muted로 시작해서 일단 재생 (소리는 안 남)
  a.muted = true;

  const ICON_ON  = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>';
  const ICON_OFF = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>';
  function refresh() {
  if (!btn) return;
  btn.innerHTML = a.muted ? ICON_OFF : ICON_ON;
  btn.classList.toggle('muted', a.muted);
  btn.title = a.muted ? '소리 켜기' : '소리 끄기';
  }

  const tryPlay = () => a.play().catch(() => {});

  // 1) 즉시 시도 (muted이라 통과)
  tryPlay();
  // 2) 로드되자마자 다시 시도
  a.addEventListener('canplay', tryPlay, { once: true });

  // 3) 사용자 첫 인터랙션 발생 → 자동으로 음소거 해제 + 재생
  let unmuteDone = false;
  function autoUnmute() {
  if (unmuteDone) return;
  unmuteDone = true;
  a.muted = false;
  refresh();
  tryPlay();
  if (window.__uxSetMuted) window.__uxSetMuted(false);
  }
  // 클릭/탭/키/포인터/스크롤 어떤 인터랙션이라도 발생하면 한 번만 실행
  const once = { once: true };
  ['click', 'touchstart', 'touchend', 'keydown', 'pointerdown', 'scroll'].forEach(ev => {
  document.addEventListener(ev, autoUnmute, once);
  });

  // 탭 전환 후 복귀 시 재개
  document.addEventListener('visibilitychange', () => {
  if (!document.hidden && a.paused) tryPlay();
  });

  refresh();
  // UX 사운드 초기 상태도 BGM과 맞춤
  if (window.__uxSetMuted) window.__uxSetMuted(a.muted);

  // 음소거 버튼 수동 토글
  if (!btn) return;
  btn.addEventListener('click', () => {
  a.muted = !a.muted;
  if (!a.muted) unmuteDone = true; // 수동으로 켰으니 자동 unmute 비활성
  refresh();
  if (!a.muted) tryPlay();
  if (window.__uxSetMuted) window.__uxSetMuted(a.muted);
  });
})();

// UX 효과음 (타이핑·클릭) — CC0 라이선스 실제 사운드 파일 사용
(function setupUxSound() {
  // BGM 음소거와 별도 변수. 음소거 버튼 토글하면 같이 따라감.
  let uxMuted = false;
  window.__uxSetMuted = (v) => { uxMuted = !!v; };
  function isMuted() { return uxMuted; }

  // Audio 풀 — 빠르게 연속 재생되어도 겹침 가능
  function makePool(src, size, vol) {
  const arr = [];
  for (let i = 0; i < size; i++) {
  const a = new Audio(src);
  a.preload = 'auto';
  a.volume = vol;
  arr.push(a);
  }
  let idx = 0;
  return {
  play(volOverride) {
  if (isMuted()) return;
  const a = arr[idx];
  try {
  a.currentTime = 0;
  if (volOverride != null) a.volume = volOverride;
  a.play().catch(() => {});
  } catch (_) {}
  idx = (idx + 1) % arr.length;
  }
  };
  }

  const pencilPool  = makePool('./media/sounds/pencil_write.ogg', 6, 0.85);
  const eraserPool  = makePool('./media/sounds/pencil_erase.ogg', 3, 0.8);
  const paperOpen  = makePool('./media/sounds/paper_open.wav',  3, 0.7);
  const tapPools  = [
  makePool('./media/sounds/tap1.ogg', 2, 0.55),
  makePool('./media/sounds/tap2.ogg', 2, 0.55),
  makePool('./media/sounds/tap3.ogg', 2, 0.55),
  makePool('./media/sounds/tap4.ogg', 2, 0.55),
  ];
  function tapRandom() {
  tapPools[Math.floor(Math.random() * tapPools.length)].play();
  }
  // 0~1 범위 랜덤 (min~max)
  function randRange(min, max) {
  return min + Math.random() * (max - min);
  }

  // ── 이벤트 위임 ──
  // 타이핑 (input/textarea 안에서 키 누를 때) — 한글 IME 포함
  const SKIP_KEYS = new Set([
  'Shift','Control','Alt','Meta','CapsLock','Escape',
  'ArrowUp','ArrowDown','ArrowLeft','ArrowRight',
  'PageUp','PageDown','Home','End',
  'NumLock','ScrollLock','Pause','Insert','PrintScreen','ContextMenu',
  'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'
  ]);
  document.addEventListener('keydown', (e) => {
  const t = e.target;
  if (!t || (t.tagName !== 'INPUT' && t.tagName !== 'TEXTAREA')) return;
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (SKIP_KEYS.has(e.key)) return;
  // 지우기 → 지우개 소리, 그 외 → 연필 쓰기 소리 (둘 다 매번 볼륨 변동)
  if (e.key === 'Backspace' || e.key === 'Delete') {
  eraserPool.play(randRange(0.55, 1.0));
  } else {
  pencilPool.play(randRange(0.45, 1.05));
  }
  });

  // 버튼/탭 클릭 → 종이 펼침, select 클릭 → 가벼운 탭
  document.addEventListener('click', (e) => {
  const t = e.target;
  if (!t) return;
  const isBtn = t.closest('button, .tab-btn');
  const isSelect = t.tagName === 'SELECT';
  if (isBtn) paperOpen.play();
  else if (isSelect) tapRandom();
  });

  // select 값 변경
  document.addEventListener('change', (e) => {
  if (e.target && e.target.tagName === 'SELECT') {
  tapRandom();
  }
  });
})();

// 인트로 → 메인 전환
(function setupIntro() {
  const enterBtn = document.getElementById('enterBtn');
  const intro = document.getElementById('introScreen');
  const main = document.getElementById('appMain');
  if (!enterBtn || !intro || !main) return;
  enterBtn.addEventListener('click', () => {
  // 사용자 인터랙션 시점 — BGM unmute + 강제 재생 (브라우저 자동재생 정책 우회)
  const a = document.getElementById('bgAudio');
  if (a) {
    a.muted = false;                           // 인터랙션이라 안전하게 unmute
    a.volume = a.volume || 0.28;
    if (a.paused) a.play().catch(() => {});
    // muteBtn 아이콘 갱신 (등록되어 있으면)
    const muteBtn = document.getElementById('muteBtn');
    if (muteBtn && typeof muteBtn._refreshIcon === 'function') muteBtn._refreshIcon();
  }
  const v = document.querySelector('.bg-video');
  if (v && v.paused) v.play().catch(() => {});

  intro.classList.add('hiding');
  document.body.classList.add('in-app');
  main.classList.add('visible');
  setTimeout(() => { intro.style.display = 'none'; }, 1200);
  window.scrollTo({ top: 0, behavior: 'instant' });
  });
})();

// 배경 영상 — 단순 loop 재생 + 자동재생 폴백
(function setupBgVideo() {
  const v = document.querySelector('.bg-video');
  if (!v) return;
  v.muted = true;
  v.playsInline = true;
  v.loop = true;
  const tryPlay = () => v.play().catch(() => {});
  tryPlay();
  // 사용자 첫 인터랙션 시 재시도 (autoplay 정책 우회용)
  const once = { once: true };
  ['click', 'touchstart', 'keydown', 'scroll'].forEach(ev => {
  document.addEventListener(ev, tryPlay, once);
  });
  // 탭 전환 후 돌아왔을 때 멈춰 있으면 재개
  document.addEventListener('visibilitychange', () => {
  if (!document.hidden && v.paused) tryPlay();
  });
})();

// 숫자 input에 문자 입력 차단 (IME·붙여넣기 포함)
(function blockNonNumericInputs() {
  const inputs = document.querySelectorAll('input[type="number"]');
  inputs.forEach(input => {
  // 한글 IME 차단을 위해 inputmode 설정
  input.setAttribute('inputmode', 'decimal');
  input.setAttribute('lang', 'en');

  // 입력 직전 차단 (가장 효과적)
  input.addEventListener('beforeinput', (e) => {
  if (e.inputType && e.inputType.startsWith('insert')) {
  const txt = e.data;
  if (txt !== null && txt !== undefined && !/^[0-9.\-]*$/.test(txt)) {
  e.preventDefault();
  }
  }
  });

  // 안전망: 통과한 문자가 있으면 정리
  input.addEventListener('input', () => {
  const cleaned = input.value.replace(/[^0-9.\-]/g, '');
  if (cleaned !== input.value) input.value = cleaned;
  });

  // 키보드로 문자 직접 누를 때
  input.addEventListener('keydown', (e) => {
  // 허용 키: 숫자, 소수점, 마이너스, 화살표·삭제·탭·엔터, 단축키 조합
  const allowed = ['Backspace','Delete','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Tab','Enter','Home','End','.','-'];
  if (allowed.includes(e.key)) return;
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.key.length === 1 && !/[0-9]/.test(e.key)) {
  e.preventDefault();
  }
  });
  });
})();

// 전체화면 토글
(function setupFullscreen() {
  const btn = document.getElementById('fullscreenBtn');
  if (!btn) return;
  const ICON_ENTER = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';
  const ICON_EXIT  = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>';
  btn.addEventListener('click', async () => {
  try {
  if (!document.fullscreenElement) {
  await (document.documentElement.requestFullscreen?.() ||
  document.documentElement.webkitRequestFullscreen?.());
  } else {
  await (document.exitFullscreen?.() ||
  document.webkitExitFullscreen?.());
  }
  } catch (e) {
  console.warn('전체화면 전환 실패:', e);
  }
  });
  const refresh = () => {
  const on = !!(document.fullscreenElement || document.webkitFullscreenElement);
  btn.innerHTML = on ? ICON_EXIT : ICON_ENTER;
  btn.title = on ? '전체화면 종료 (Esc)' : '전체화면 (F11)';
  document.body.classList.toggle('is-fullscreen', on);
  };
  document.addEventListener('fullscreenchange', refresh);
  document.addEventListener('webkitfullscreenchange', refresh);
})();

// 탭 전환 (사주 풀이 ↔ 꿈 해몽)
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
  const target = btn.dataset.tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === 'tab-' + target));
  });
});

// 성하 공자 · 별빛 풀이 — step 전환 (백엔드 미연결, 화면 흐름만)
(function setupStar() {
  const readBtn = document.getElementById('starReadBtn');
  const restartBtn = document.getElementById('starRestartBtn');
  const board = document.getElementById('starResultBoard');
  if (!readBtn) return;

  function showStarStep(id) {
  document.querySelectorAll('#tab-star .star-step').forEach(s => {
  s.classList.toggle('active', s.id === id);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  readBtn.addEventListener('click', () => {
  const name = (document.getElementById('starName').value || '').trim();
  const year = document.getElementById('starYear').value;
  const month = document.getElementById('starMonth').value;
  const day = document.getElementById('starDay').value;
  if (!name) {
  document.getElementById('starName').focus();
  document.getElementById('starName').placeholder = '이름을 적어주시지요 (필수)';
  return;
  }
  // 백엔드 연결 전 — 로딩 화면을 잠시 보여준 뒤 placeholder 결과 표시
  showStarStep('star-step-loading');
  setTimeout(() => {
  if (window.WHM) window.WHM.markCompleted('astrology', { name });
  if (board) {
  board.innerHTML = `
  <div class="star-result-card">
  <h3>${escapeHtml(name)}님의 별빛 풀이</h3>
  <p>오시었군요. 이 사람을 성하라 부르지요.<br>
  그대의 별을 한 번 살펴드리리다.</p>
  <p>하늘의 별은 그대 운명의 지도이옵니다.
  천공에 흩뿌려진 빛 하나하나가 그대의 길을 가리키지요.</p>
  <p style="margin-top:18px;color:var(--starh-silver-dp);font-size:13px">
  ※ 별빛 풀이는 곧 깊이 있게 펼쳐집니다. 지금은 화면 흐름만 살펴보실 수 있어요.<br>
  생년월일 ${year}.${month}.${day} 의 천공도를 살핀 풀이를 준비 중이옵니다.
  </p>
  </div>`;
  }
  showStarStep('star-step-result');
  }, 1400);
  });

  if (restartBtn) {
  restartBtn.addEventListener('click', () => {
  if (board) board.innerHTML = '';
  showStarStep('star-step-input');
  });
  }

  function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
  }
})();

// 생년월일 드롭다운 — 모든 [data-ymd] select 에 옵션 자동 주입 (만월·궁합상대·성하 공통)
(function populateYmdSelects() {
  const CURRENT_YEAR = new Date().getFullYear();
  const YEAR_MIN = 1920;
  // 기본값: 기존 input 의 value (1990·5·15) 와 동일하게 맞춰 백엔드 호환 유지
  const DEFAULTS = { year: 1990, month: 5, day: 15 };

  function fillSelect(sel) {
  if (!sel || sel.options.length > 0) return; // 이미 채워졌으면 skip
  const kind = sel.dataset.ymd;
  let start, end;
  if (kind === 'year')  { start = CURRENT_YEAR; end = YEAR_MIN; } // 최신 연도 위로
  else if (kind === 'month') { start = 1; end = 12; }
  else if (kind === 'day') { start = 1; end = 31; }
  else return;

  const step = start <= end ? 1 : -1;
  for (let v = start; step > 0 ? v <= end : v >= end; v += step) {
  const opt = document.createElement('option');
  opt.value = String(v);
  opt.textContent = String(v);
  if (v === DEFAULTS[kind]) opt.selected = true;
  sel.appendChild(opt);
  }
  }

  function init() {
  document.querySelectorAll('select[data-ymd]').forEach(fillSelect);
  }
  if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
  } else {
  init();
  }
})();

// ─────────────────────────────────────────────────────────
// 月下夢 릴레이 풀이 시스템 — 사용자 정보·풀이 결과 공유 모듈
// 기획서 데이터 모델: userProfile + readings
// 모든 캐릭터가 동일한 기본 정보를 공유, 풀이 결과는 다음 캐릭터의 컨텍스트로 활용
