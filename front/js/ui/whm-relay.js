// ============================================================
// whm-relay.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// WHM 릴레이 시스템 (탭→탭 이동·완료 표시)
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
// ─────────────────────────────────────────────────────────
window.WHM = window.WHM || {};
(function initRelaySystem() {
  const STORAGE_KEY = 'whm.userSession.v1';
  const CHARACTERS = ['saju', 'astrology', 'tarot', 'naming', 'physiognomy', 'palmistry', 'dream'];
  const CHAR_LABEL = {
  saju: '만월 아씨', astrology: '성하 공자', tarot: '화선 낭자',
  naming: '묵향 선생', physiognomy: '운학 도사', palmistry: '옥선 할미', dream: '몽이 도령',
  };
  const CHAR_TAB = {
  saju: 'saju', astrology: 'star', tarot: 'hwapae',
  naming: 'name', physiognomy: 'face', palmistry: 'palm', dream: 'dream',
  };

  function emptySession() {
  return {
  profile: {
  name: '',
  birth: { year: null, month: null, day: null, hourBranch: null, gender: null, birthplace: null },
  mbti: null,
  concern: null,
  },
  readings: Object.fromEntries(CHARACTERS.map(c => [c, { completed: false, summary: null, completedAt: null }])),
  storyContext: [],
  };
  }
  function load() {
  try {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return emptySession();
  const parsed = JSON.parse(raw);
  // 스키마 호환을 위해 기본 구조와 머지
  const base = emptySession();
  return Object.assign(base, parsed, {
  profile: Object.assign(base.profile, parsed.profile || {}),
  readings: Object.assign(base.readings, parsed.readings || {}),
  storyContext: parsed.storyContext || [],
  });
  } catch (_) { return emptySession(); }
  }
  function save(session) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(session)); } catch (_) {}
  }
  function reset() {
  localStorage.removeItem(STORAGE_KEY);
  }

  // 만월 아씨 입력 폼 → profile 동기화 (실시간)
  function bindProfileSync() {
  const ids = ['fullName', 'year', 'month', 'day', 'hourBranch', 'gender', 'birthplaceQuery', 'mbti', 'userConcern'];
  ids.forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('change', captureProfile);
  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
  el.addEventListener('input', captureProfile);
  }
  });
  // 성하 폼도 동기화
  ['starName', 'starYear', 'starMonth', 'starDay', 'starHourBranch', 'starGender', 'starBirthplace'].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('change', captureProfileFromStar);
  if (el.tagName === 'INPUT') el.addEventListener('input', captureProfileFromStar);
  });
  }
  function captureProfile() {
  const s = load();
  s.profile.name = (document.getElementById('fullName')?.value || '').trim();
  s.profile.birth = {
  year: parseInt(document.getElementById('year')?.value, 10) || null,
  month: parseInt(document.getElementById('month')?.value, 10) || null,
  day: parseInt(document.getElementById('day')?.value, 10) || null,
  hourBranch: document.getElementById('hourBranch')?.value || null,
  gender: document.getElementById('gender')?.value || null,
  birthplace: document.getElementById('birthplaceQuery')?.value || null,
  };
  s.profile.mbti = document.getElementById('mbti')?.value || null;
  s.profile.concern = (document.getElementById('userConcern')?.value || '').trim() || null;
  save(s);
  // 성하 폼에도 같은 정보 자동 반영 (사용자가 한 번 입력 후 다른 도사로 가도 재입력 불필요)
  mirrorToStar(s.profile);
  }
  function captureProfileFromStar() {
  const s = load();
  s.profile.name = (document.getElementById('starName')?.value || '').trim() || s.profile.name;
  const y = parseInt(document.getElementById('starYear')?.value, 10);
  const m = parseInt(document.getElementById('starMonth')?.value, 10);
  const d = parseInt(document.getElementById('starDay')?.value, 10);
  if (y) s.profile.birth.year = y;
  if (m) s.profile.birth.month = m;
  if (d) s.profile.birth.day = d;
  const hb = document.getElementById('starHourBranch')?.value;
  if (hb) s.profile.birth.hourBranch = hb;
  const gn = document.getElementById('starGender')?.value;
  if (gn) s.profile.birth.gender = (gn === '남성' ? 'M' : gn === '여성' ? 'F' : s.profile.birth.gender);
  const bp = document.getElementById('starBirthplace')?.value;
  if (bp) s.profile.birth.birthplace = bp;
  save(s);
  // 만월 폼에도 미러
  mirrorToSaju(s.profile);
  }
  function mirrorToStar(p) {
  const set = (id, v) => { const el = document.getElementById(id); if (el && v != null && el.value !== String(v)) el.value = String(v); };
  if (p.name) set('starName', p.name);
  if (p.birth?.year) set('starYear', p.birth.year);
  if (p.birth?.month) set('starMonth', p.birth.month);
  if (p.birth?.day) set('starDay', p.birth.day);
  if (p.birth?.hourBranch) set('starHourBranch', p.birth.hourBranch);
  if (p.birth?.gender) {
  const gn = p.birth.gender === 'M' ? '남성' : p.birth.gender === 'F' ? '여성' : '';
  if (gn) set('starGender', gn);
  }
  if (p.birth?.birthplace) set('starBirthplace', p.birth.birthplace);
  }
  function mirrorToSaju(p) {
  const set = (id, v) => { const el = document.getElementById(id); if (el && v != null && el.value !== String(v)) el.value = String(v); };
  if (p.name) set('fullName', p.name);
  if (p.birth?.year) set('year', p.birth.year);
  if (p.birth?.month) set('month', p.birth.month);
  if (p.birth?.day) set('day', p.birth.day);
  if (p.birth?.hourBranch) set('hourBranch', p.birth.hourBranch);
  if (p.birth?.gender) set('gender', p.birth.gender);
  if (p.birth?.birthplace) set('birthplaceQuery', p.birth.birthplace);
  }

  // 풀이 완료 표시 (각 캐릭터 결과 화면 진입 시 호출)
  function markCompleted(charKey, summary) {
  const s = load();
  if (!s.readings[charKey]) s.readings[charKey] = {};
  s.readings[charKey].completed = true;
  s.readings[charKey].summary = summary || null;
  s.readings[charKey].completedAt = new Date().toISOString();
  save(s);
  refreshProgressUI();
  }

  // 진행도 UI 새로고침 (E단계에서 추가)
  function refreshProgressUI() {
  const dotsEl = document.getElementById('whmProgressDots');
  if (!dotsEl) return;
  const s = load();
  const order = ['saju', 'astrology', 'tarot', 'naming', 'physiognomy', 'palmistry', 'dream'];
  dotsEl.innerHTML = order.map(k => {
  const done = s.readings[k]?.completed;
  return `<span class="whm-dot ${done ? 'done' : 'pending'}" title="${CHAR_LABEL[k]}: ${done ? '완료' : '미완'}">${done ? '●' : '○'}</span>`;
  }).join('');
  const completedCount = order.filter(k => s.readings[k]?.completed).length;
  const counter = document.getElementById('whmProgressCount');
  if (counter) counter.textContent = `${completedCount} / 7`;
  }

  // 페이지 진입 시 저장된 profile을 폼에 복원
  function restoreToForms() {
  const s = load();
  if (!s.profile?.name) return;
  mirrorToSaju(s.profile);
  mirrorToStar(s.profile);
  }

  // 외부 노출 API
  window.WHM = {
  load, save, reset, emptySession,
  captureProfile, captureProfileFromStar,
  markCompleted, refreshProgressUI, restoreToForms,
  CHARACTERS, CHAR_LABEL, CHAR_TAB,
  };

  // next-btn 클릭 → 해당 탭으로 이동 (탭바의 .tab-btn 클릭과 동일 효과)
  function bindNextButtons() {
  document.addEventListener('click', (e) => {
  const btn = e.target.closest('.next-btn[data-go]');
  if (!btn) return;
  const target = btn.dataset.go;
  if (!target) return;
  const tabBtn = document.querySelector(`.tab-btn[data-tab="${target}"]`);
  if (tabBtn) {
  tabBtn.click();
  window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  });
  }

  function init() {
  bindProfileSync();
  bindNextButtons();
  restoreToForms();
  refreshProgressUI();
  }
  if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
  } else {
  init();
  }
})();

// ─────────────────────────────────────────────────────────
// 月下夢 카드 갤러리 캐러셀 — 7명 점술가 카드 스와이프 UI
// 인트로 진입 시 갤러리 모드 → 카드 클릭/들어가기 → 풀이 화면
