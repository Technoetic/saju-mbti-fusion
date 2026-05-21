// 첫 진입 스와이프 안내 툴팁
//
// 동작:
//   - 홈(카드 갤러리) 첫 진입 시 → 안내 표시
//   - 취선루 첫 진입 시 → 안내 다시 표시 (별도 키)
//   - 닫기 버튼: 이번 세션에만 안 보임 (sessionStorage)
//   - 다시 보지 않기: 영구히 안 보임 (localStorage)

const NEVER_KEY_HOME = 'whm.swipeHint.never.home';
const NEVER_KEY_CHWISEON = 'whm.swipeHint.never.chwiseon';
const SHOWN_SESSION_KEY = 'whm.swipeHint.shownThisSession';

function hasSeenForever(key) {
  try { return localStorage.getItem(key) === '1'; } catch (_) { return false; }
}
function markForever(key) {
  try { localStorage.setItem(key, '1'); } catch (_) {}
}

function getShownSession() {
  try { return JSON.parse(sessionStorage.getItem(SHOWN_SESSION_KEY) || '{}'); }
  catch (_) { return {}; }
}
function markShownSession(context) {
  const s = getShownSession();
  s[context] = true;
  try { sessionStorage.setItem(SHOWN_SESSION_KEY, JSON.stringify(s)); } catch (_) {}
}

function showSwipeHint(context) {
  const hint = document.getElementById('swipeHint');
  if (!hint) return;
  // context: 'home' | 'chwiseon'
  hint.dataset.context = context;
  hint.classList.remove('hiding');
  hint.style.display = 'flex';
  positionOverGallery(context);
}

function positionOverGallery(context) {
  const hint = document.getElementById('swipeHint');
  if (!hint) return;
  // 카드 갤러리 DOM 위치를 잡아 hint를 그 영역에 딱 얹음
  const gallery = context === 'chwiseon'
    ? document.querySelector('#chwiseonMain .card-gallery, #chwiseonDeck')
    : document.getElementById('cardGallery');

  if (!gallery) return;
  const rect = gallery.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  hint.style.top    = Math.max(0, rect.top) + 'px';
  hint.style.left   = rect.left + 'px';
  hint.style.right  = (window.innerWidth - rect.right) + 'px';
  hint.style.bottom = (window.innerHeight - rect.bottom) + 'px';
}

// 스크롤·리사이즈 시 위치 갱신
function repositionIfVisible() {
  const hint = document.getElementById('swipeHint');
  if (!hint || hint.style.display === 'none' || hint.style.display === '') return;
  positionOverGallery(hint.dataset.context || 'home');
}

function hideSwipeHint() {
  const hint = document.getElementById('swipeHint');
  if (!hint) return;
  hint.classList.add('hiding');
  setTimeout(() => {
    hint.style.display = 'none';
    hint.classList.remove('hiding');
  }, 320);
}

function maybeShow(context) {
  const neverKey = context === 'home' ? NEVER_KEY_HOME : NEVER_KEY_CHWISEON;
  if (hasSeenForever(neverKey)) return;
  const session = getShownSession();
  if (session[context]) return;
  showSwipeHint(context);
  markShownSession(context);
}

function init() {
  const hint = document.getElementById('swipeHint');
  if (!hint) return;

  // 버튼 이벤트
  hint.querySelectorAll('[data-swipe-hint]').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.swipeHint;
      if (action === 'never') {
        const ctx = hint.dataset.context || 'home';
        const neverKey = ctx === 'home' ? NEVER_KEY_HOME : NEVER_KEY_CHWISEON;
        markForever(neverKey);
      }
      hideSwipeHint();
    });
  });

  // 사용자가 카드 드래그/스와이프 한 번이라도 했으면 자동 숨김 + 영구 안 보임
  const onUserSwipe = () => {
    if (hint.style.display !== 'none' && hint.style.display !== '') {
      const ctx = hint.dataset.context || 'home';
      const neverKey = ctx === 'home' ? NEVER_KEY_HOME : NEVER_KEY_CHWISEON;
      markForever(neverKey);
      hideSwipeHint();
    }
  };
  ['touchmove', 'mousemove'].forEach(ev => {
    document.addEventListener(ev, (e) => {
      // 카드 갤러리 안에서 드래그 중일 때만
      const target = e.target;
      if (target && (target.closest('.card-deck.is-dragging') || target.closest('#chwiseonDeck.is-dragging'))) {
        onUserSwipe();
      }
    }, { passive: true });
  });

  // 홈 첫 진입 — 페이지 로드 후 살짝 지연 (다른 UI 렌더 후 자연스럽게)
  setTimeout(() => {
    if (document.body.classList.contains('tab-home')) {
      maybeShow('home');
    }
  }, 1500);

  // 스크롤·리사이즈 시 위치 갱신
  window.addEventListener('resize', repositionIfVisible);
  window.addEventListener('scroll', repositionIfVisible, { passive: true });

  // 탭 전환 감지 — body class 변화 관찰
  const observer = new MutationObserver(() => {
    if (document.body.classList.contains('chwiseon-on')) {
      // 취선루 진입
      setTimeout(() => {
        if (document.body.classList.contains('chwiseon-on')) {
          maybeShow('chwiseon');
        }
      }, 600);
    } else if (document.body.classList.contains('tab-home') && hint.style.display !== 'none') {
      // 홈 외 탭으로 이동 시 안내 강제 닫기 (혹시 떠있으면)
    }
  });
  observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

window.WHM_SWIPE_HINT = {
  show: maybeShow,
  hide: hideSwipeHint,
  reset: () => {
    try {
      localStorage.removeItem(NEVER_KEY_HOME);
      localStorage.removeItem(NEVER_KEY_CHWISEON);
      sessionStorage.removeItem(SHOWN_SESSION_KEY);
    } catch (_) {}
  },
};
