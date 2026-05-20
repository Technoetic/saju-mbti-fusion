// 회원가입/로그인 모달 + 사주 폼 자동 prefill
// 세션 유지: localStorage('whm.account')

const STORAGE_KEY = 'whm.account';

function loadAccount() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_) {
    return null;
  }
}

function saveAccount(account) {
  if (!account) {
    localStorage.removeItem(STORAGE_KEY);
  } else {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(account));
  }
}

function setError(text) {
  const el = document.getElementById('authError');
  if (el) el.textContent = text || '';
}

function setMode(modal, mode) {
  modal.dataset.mode = mode;
  // 타이틀/제출 버튼 텍스트
  const title = document.getElementById('authTitle');
  const submit = document.getElementById('authSubmit');
  const tabs = modal.querySelectorAll('.auth-tab');
  if (mode === 'login') {
    if (title) title.textContent = '月 下 夢 · 로그인';
    if (submit) submit.textContent = '로그인';
  } else {
    if (title) title.textContent = '月 下 夢 · 회원가입';
    if (submit) submit.textContent = '회원가입';
  }
  tabs.forEach(t => t.classList.toggle('active', t.dataset.authMode === mode));
  setError('');
}

function showModal(modal, mode = 'signup') {
  setMode(modal, mode);
  modal.style.display = 'flex';
}

function hideModal(modal) {
  modal.style.display = 'none';
}

function updateUserBadge(account) {
  const badge = document.getElementById('userBadge');
  const nameEl = document.getElementById('userBadgeName');
  if (!badge || !nameEl) return;
  if (!account) {
    badge.style.display = 'none';
    return;
  }
  const label = account.nickname || account.name_ko || account.email || '회원';
  nameEl.textContent = label;
  badge.style.display = 'flex';
}

// 사주/이름 풀이 폼에 가입 정보 자동 채움
function prefillSajuForm(account) {
  if (!account) return;

  const trySet = (id, value) => {
    if (value == null || value === '') return;
    const el = document.getElementById(id);
    if (!el) return;
    el.value = String(value);
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
  };

  // 이름
  trySet('fullName', account.name_ko);
  // 성별
  trySet('gender', account.gender);
  // MBTI
  trySet('mbti', account.mbti);
  // 생년월일 (select#year, #month, #day)
  trySet('year', account.birth_year);
  trySet('month', account.birth_month);
  trySet('day', account.birth_day);
  // 태어난 시각
  trySet('hourBranch', account.birth_hour_branch);
  // 태어난 곳 (숨김 select#birthplace + birthplaceQuery 표시)
  if (account.birthplace) {
    const bp = document.getElementById('birthplace');
    if (bp) {
      bp.value = account.birthplace;
      bp.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
}

async function submitAuth(modal) {
  const mode = modal.dataset.mode || 'signup';
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  setError('');

  const submitBtn = document.getElementById('authSubmit');
  if (submitBtn) submitBtn.disabled = true;

  try {
    let body, url;
    if (mode === 'signup') {
      const password2 = document.getElementById('authPassword2').value;
      if (password !== password2) {
        setError('비밀번호 확인이 일치하지 않습니다.');
        return;
      }
      const nickname = document.getElementById('authNickname').value.trim();
      const name_ko = document.getElementById('authNameKo').value.trim();
      const birth_year = parseInt(document.getElementById('authBirthYear').value, 10);
      const birth_month = parseInt(document.getElementById('authBirthMonth').value, 10);
      const birth_day = parseInt(document.getElementById('authBirthDay').value, 10);
      const birth_hour_branch = document.getElementById('authBirthHourBranch').value;
      const birthplace = document.getElementById('authBirthplace').value;
      const is_lunar = document.getElementById('authIsLunar').value === 'true';
      const gender = document.getElementById('authGender').value;
      const mbti = document.getElementById('authMbti').value;

      body = {
        email, password,
        nickname: nickname || null,
        name_ko: name_ko || null,
        birth_year: Number.isFinite(birth_year) ? birth_year : null,
        birth_month: Number.isFinite(birth_month) ? birth_month : null,
        birth_day: Number.isFinite(birth_day) ? birth_day : null,
        birth_hour_branch: birth_hour_branch || null,
        birthplace: birthplace || null,
        is_lunar,
        gender: gender || null,
        mbti: mbti || null,
      };
      url = '/api/auth/signup';
    } else {
      body = { email, password };
      url = '/api/auth/login';
    }

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail;
      let msg = '오류가 발생했습니다. 다시 시도해 주세요.';
      if (detail) {
        if (typeof detail === 'string') msg = detail;
        else if (detail.message) msg = detail.message;
      }
      setError(msg);
      return;
    }
    if (!data?.account) {
      setError('서버 응답 형식 오류입니다.');
      return;
    }
    saveAccount(data.account);
    updateUserBadge(data.account);
    prefillSajuForm(data.account);
    hideModal(modal);
  } catch (err) {
    console.error(err);
    setError('네트워크 오류입니다. 잠시 후 다시 시도해 주세요.');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function init() {
  const modal = document.getElementById('authModal');
  if (!modal) return;

  // 폼 제출
  const form = document.getElementById('authForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      submitAuth(modal);
    });
  }

  // 탭 전환
  modal.querySelectorAll('.auth-tab').forEach(tab => {
    tab.addEventListener('click', () => setMode(modal, tab.dataset.authMode));
  });

  // 닫기 / 둘러보기
  const closeBtn = document.getElementById('authClose');
  if (closeBtn) closeBtn.addEventListener('click', () => hideModal(modal));
  const skipBtn = document.getElementById('authSkipBtn');
  if (skipBtn) skipBtn.addEventListener('click', () => hideModal(modal));

  // 로그아웃
  const logoutBtn = document.getElementById('userBadgeLogout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      saveAccount(null);
      updateUserBadge(null);
      showModal(modal, 'login');
    });
  }

  // 기존 세션 복원 or 첫 방문 시 모달 표시
  const existing = loadAccount();
  if (existing) {
    updateUserBadge(existing);
    prefillSajuForm(existing);
  } else {
    // 페이지가 다 그려진 직후 모달 노출 (배경 페이드인과 자연스럽게 겹치도록)
    setTimeout(() => showModal(modal, 'signup'), 300);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// 외부에서 모달 다시 띄울 수 있도록 글로벌 노출
window.WHM_AUTH = {
  showSignup: () => {
    const m = document.getElementById('authModal');
    if (m) showModal(m, 'signup');
  },
  showLogin: () => {
    const m = document.getElementById('authModal');
    if (m) showModal(m, 'login');
  },
  logout: () => {
    saveAccount(null);
    updateUserBadge(null);
  },
  getAccount: loadAccount,
};
