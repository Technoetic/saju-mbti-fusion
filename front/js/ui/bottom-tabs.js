// 하단 탭 바 — 5개 탭 전환 (홈/일지/놀이/친구/프로필)
//
// body.tab-{key} 클래스로 탭별 화면 토글:
//   tab-home    → 카드 갤러리 (app-container)
//   tab-journal → 일지 화면
//   tab-play    → 놀이 화면
//   tab-friends → 친구 화면
//   tab-profile → 프로필 화면

const TAB_CLASSES = ['tab-home', 'tab-journal', 'tab-play', 'tab-friends', 'tab-profile'];

function activateTab(key) {
  const body = document.body;
  console.log('[tabs] activateTab:', key);
  // 기존 탭 클래스 모두 제거 + 새 탭 부여
  TAB_CLASSES.forEach(c => body.classList.remove(c));
  body.classList.add(`tab-${key}`);

  // 탭 버튼 active 토글
  document.querySelectorAll('.bottom-tab').forEach(btn => {
    const isActive = btn.dataset.tab === key;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });

  // pane 토글 (CSS class + 직접 style — 이중 보장)
  document.querySelectorAll('.tab-pane').forEach(pane => {
    const isActive = pane.dataset.tabPane === key;
    pane.classList.toggle('active', isActive);
    pane.style.display = isActive ? 'block' : 'none';
  });

  // 메인 콘텐츠/탭 view 직접 토글 (CSS cascade 충돌 우회)
  const appMain = document.getElementById('appMain');
  const tabView = document.getElementById('tabView');
  const isHome = (key === 'home');

  if (appMain) {
    appMain.style.setProperty('display', isHome ? 'block' : 'none', 'important');
  }
  if (tabView) {
    tabView.style.setProperty('display', isHome ? 'none' : 'block', 'important');
  }

  // appMain 형제로 있는 풀이 view들(취선루 등)도 강제 숨김
  document.querySelectorAll(
    '#chwiseonView, #chwiseonMenu, #chwiseonContent, #menuView, #contentView, #cardGallery'
  ).forEach(el => {
    if (!isHome) {
      el.dataset._prevDisplay = el.style.display || '';
      el.style.setProperty('display', 'none', 'important');
    } else {
      el.style.removeProperty('display');
      if (el.dataset._prevDisplay !== undefined) {
        delete el.dataset._prevDisplay;
      }
    }
  });

  // 취선루 게이트도 홈 외엔 숨김
  const chwiseonGate = document.getElementById('chwiseonGate');
  if (chwiseonGate) {
    chwiseonGate.style.setProperty('display', isHome ? '' : 'none', 'important');
  }

  // 좌상단 '← 점술가 고르러' fixed 버튼도 홈 외엔 숨김
  const toGalleryBtn = document.getElementById('toGalleryBtn');
  if (toGalleryBtn) {
    toGalleryBtn.style.setProperty('display', isHome ? '' : 'none', 'important');
  }

  // 코너 버튼(전체화면·음소거)은 어디서나 노출 유지

  // 홈 탭 진입 시 갤러리 모드도 유지
  if (isHome) {
    document.body.classList.add('gallery-mode');
    document.body.classList.remove('menu-mode', 'content-mode');
    if (typeof window.__galleryEnter === 'function') {
      window.__galleryEnter();
    }
  } else {
    document.body.classList.remove('gallery-mode');
  }

  // 프로필 탭이면 정보 새로고침
  if (key === 'profile') {
    refreshProfileView();
  }

  // 스크롤 위로
  window.scrollTo({ top: 0, behavior: 'instant' });
}

// 프로필 탭 표시 갱신 (로그인 상태에 따라 빈/카드 토글)
function refreshProfileView() {
  let account = null;
  try {
    const raw = localStorage.getItem('whm.account');
    if (raw) account = JSON.parse(raw);
  } catch (_) {}

  const empty = document.getElementById('profileEmpty');
  const card = document.getElementById('profileCard');
  if (!empty || !card) return;

  if (!account) {
    empty.style.display = 'block';
    card.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  card.style.display = 'flex';

  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val || '—';
  };

  setText('profileNickname', account.nickname);
  setText('profileEmail', account.email);
  setText('profileNameKo', account.name_ko);

  if (account.birth_year && account.birth_month && account.birth_day) {
    const lunar = account.is_lunar ? '음력' : '양력';
    setText('profileBirth', `${account.birth_year}.${String(account.birth_month).padStart(2,'0')}.${String(account.birth_day).padStart(2,'0')} (${lunar})`);
  } else {
    setText('profileBirth', null);
  }

  const hourLabels = {
    '子': '자시 (子) 23~01시', '丑': '축시 (丑) 01~03시', '寅': '인시 (寅) 03~05시',
    '卯': '묘시 (卯) 05~07시', '辰': '진시 (辰) 07~09시', '巳': '사시 (巳) 09~11시',
    '午': '오시 (午) 11~13시', '未': '미시 (未) 13~15시', '申': '신시 (申) 15~17시',
    '酉': '유시 (酉) 17~19시', '戌': '술시 (戌) 19~21시', '亥': '해시 (亥) 21~23시',
    'unknown': '시간 모름',
  };
  setText('profileHour', hourLabels[account.birth_hour_branch] || null);

  const placeLabels = {
    seoul: '서울', busan: '부산', incheon: '인천', daegu: '대구', gwangju: '광주',
    daejeon: '대전', ulsan: '울산', sejong: '세종', gyeonggi: '경기', gangwon: '강원',
    chungbuk: '충북', chungnam: '충남', jeonbuk: '전북', jeonnam: '전남',
    gyeongbuk: '경북', gyeongnam: '경남', jeju: '제주', tokyo: '도쿄', beijing: '베이징',
    custom: '기타',
  };
  setText('profileBirthplace', placeLabels[account.birthplace] || null);
  setText('profileMbti', account.mbti);
}

function init() {
  // 탭 버튼 클릭 이벤트
  document.querySelectorAll('.bottom-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.tab;
      if (key) activateTab(key);
    });
  });

  // 프로필 탭 안의 로그인/로그아웃 버튼
  const loginBtn = document.getElementById('profileLoginBtn');
  if (loginBtn) {
    loginBtn.addEventListener('click', () => {
      if (window.WHM_AUTH && typeof window.WHM_AUTH.showLogin === 'function') {
        window.WHM_AUTH.showLogin();
      }
    });
  }
  const logoutBtn = document.getElementById('profileLogoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      if (window.WHM_AUTH && typeof window.WHM_AUTH.logout === 'function') {
        window.WHM_AUTH.logout();
      }
      refreshProfileView();
    });
  }

  // 페이지 로드 시 기본 탭 = 홈
  activateTab('home');

  // 카드 갤러리 안의 캐릭터 카드 클릭으로 풀이 화면 진입 시
  // 자동으로 홈 탭 active 유지 (메뉴/콘텐츠/풀이 모드는 home 탭 안의 흐름)
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

window.WHM_TABS = { activate: activateTab };
