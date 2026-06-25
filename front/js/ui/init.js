// ============================================================
// init.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// autoInit·initTabCharacterScene·initBirthplaceSearch·initHourBranch
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
// ============================================================
// SECTION: 탭 종이 펼침 애니메이션
// (배경 영상은 사용자 요청으로 제거됨 — paper-scroll만 유지)
// ============================================================
(function initTabCharacterScene() {
  function detachVideosToBody() {
    // 배경 영상 제거됨 — 호환 위해 함수만 유지
  }

  function getTabPaper(tabId) {
    const tab = document.getElementById('tab-' + tabId);
    return tab ? tab.querySelector('.paper-scroll') : null;
  }

  function activateTabScene(tabId) {
    document.querySelectorAll('.paper-scroll').forEach(p => p.classList.remove('unrolled'));
    document.body.classList.remove('star-active', 'hero-mode');

    // 성하 공자 탭 — body에 표식 (별빛 테마 적용용)
    if (tabId === 'star') document.body.classList.add('star-active');

    // paper 즉시 펼침
    requestAnimationFrame(() => {
      const paper = getTabPaper(tabId);
      if (paper) paper.classList.add('unrolled');
    });
  }

  function bindTabSwitch() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        if (!target) return;
        requestAnimationFrame(() => activateTabScene(target));
      });
    });
  }

  function init() {
    detachVideosToBody();
    bindTabSwitch();
    // 인트로 제거: 항상 사주 탭으로 진입
    activateTabScene('saju');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


// ============================================================
// FaceReader 외부 모듈: js/readers/face-reader.js (ADR-038 Phase 2 확장)
// 본 위치 인라인 정의는 외부 .js로 이동.


// ============================================================
// SECTION: 주소 검색 (Daum Postcode) → 시·도 → birthplace 자동 매핑
// ============================================================
(function initBirthplaceSearch() {
  // 시·도 첫 글자(부분 일치) → birthplace select option value
  const SIDO_MAP = [
    { match: /^서울/, key: 'seoul' },
    { match: /^부산/, key: 'busan' },
    { match: /^인천/, key: 'incheon' },
    { match: /^대구/, key: 'daegu' },
    { match: /^광주/, key: 'gwangju' },
    { match: /^대전/, key: 'daejeon' },
    { match: /^울산/, key: 'ulsan' },
    { match: /^세종/, key: 'sejong' },
    { match: /^경기/, key: 'gyeonggi' },
    { match: /^강원/, key: 'gangwon' },
    { match: /^충청북도|^충북/, key: 'chungbuk' },
    { match: /^충청남도|^충남/, key: 'chungnam' },
    { match: /^전라북도|^전북/, key: 'jeonbuk' },
    { match: /^전라남도|^전남/, key: 'jeonnam' },
    { match: /^경상북도|^경북/, key: 'gyeongbuk' },
    { match: /^경상남도|^경남/, key: 'gyeongnam' },
    { match: /^제주/, key: 'jeju' },
  ];

  function closeModal() {
    const modal = document.getElementById('postcodeModal');
    if (modal) modal.style.display = 'none';
    // 주의: container.innerHTML 즉시 비우지 않음 — iframe을 너무 빨리 제거하면
    // postcode의 message 전달이 끊겨 oncomplete가 호출되지 않을 수 있음.
    // 다음 open()에서 새로 채워줌.
  }

  // 마지막으로 어떤 input을 위해 모달을 열었는지 (personal vs partner)
  let activeTargets = { queryId: 'birthplaceQuery', selectId: 'birthplace' };

  function openPostcode(queryId, selectId) {
    if (typeof daum === 'undefined' || !daum.Postcode) {
      alert('주소 검색 스크립트가 아직 로딩되지 않았습니다. 잠시 후 다시 시도하세요.');
      return;
    }
    activeTargets = {
      queryId: queryId || 'birthplaceQuery',
      selectId: selectId || 'birthplace',
    };
    const modal = document.getElementById('postcodeModal');
    const container = document.getElementById('postcodeContainer');
    if (!modal || !container) {
      new daum.Postcode({ oncomplete: handleComplete }).open();
      return;
    }
    container.innerHTML = '';
    modal.style.display = 'flex';

    new daum.Postcode({
      oncomplete: function (data) {
        handleComplete(data);
        setTimeout(closeModal, 80);
      },
      width: '100%',
      height: '100%',
      theme: {
        bgColor: '#0a0f1e',
        searchBgColor: '#1d2540',
        contentBgColor: '#131a2e',
        pageBgColor: '#0a0f1e',
        textColor: '#e8d9b0',
        queryTextColor: '#f4d35e',
        emphTextColor: '#d4af37',
        outlineColor: '#6d5a3a',
      },
    }).embed(container, { autoClose: true });
  }

  function handleComplete(data) {
    const address = data.roadAddress || data.address || data.jibunAddress || '';
    const buildingName = data.buildingName ? ' (' + data.buildingName + ')' : '';
    const display = address + buildingName;
    const input = document.getElementById(activeTargets.queryId);
    if (input) input.value = display;

    const sido = (data.sido || '').trim();
    const mapped = SIDO_MAP.find(s => s.match.test(sido));
    const birthSel = document.getElementById(activeTargets.selectId);
    if (mapped && birthSel) {
      birthSel.value = mapped.key;
      birthSel.dispatchEvent(new Event('change'));
    }
  }

  function init() {
    const input = document.getElementById('birthplaceQuery');
    if (input) input.addEventListener('click', () => openPostcode('birthplaceQuery', 'birthplace'));

    // 상대방(궁합) 주소 검색
    const pInput = document.getElementById('pBirthplaceQuery');
    if (pInput) pInput.addEventListener('click', () => openPostcode('pBirthplaceQuery', 'pBirthplace'));

    const closeBtn = document.getElementById('postcodeModalClose');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    const modal = document.getElementById('postcodeModal');
    if (modal) modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();  // 외곽 클릭 시 닫기
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

// ============================================================
// SECTION: 12지시 드롭다운 ↔ hour/minute hidden 동기화
// ============================================================
(function initHourBranch() {
  function sync(branchId, hourId, minuteId, manualRowId, hourManualId, minuteManualId) {
    const branch = document.getElementById(branchId);
    const hour = document.getElementById(hourId);
    const minute = document.getElementById(minuteId);
    const manualRow = document.getElementById(manualRowId);
    const hourManual = document.getElementById(hourManualId);
    const minuteManual = document.getElementById(minuteManualId);
    if (!branch || !hour || !minute) return;

    function applyFromBranch() {
      const opt = branch.options[branch.selectedIndex];
      const dataHour = opt && opt.dataset.hour;
      const val = branch.value;
      if (val === 'manual') {
        if (manualRow) manualRow.style.display = '';
        hour.value = String(parseInt(hourManual?.value || '12', 10) || 12);
        minute.value = String(parseInt(minuteManual?.value || '0', 10) || 0);
      } else {
        if (manualRow) manualRow.style.display = 'none';
        hour.value = dataHour ? String(parseInt(dataHour, 10)) : '12';
        minute.value = '0';
      }
    }
    branch.addEventListener('change', applyFromBranch);
    if (hourManual) hourManual.addEventListener('input', () => {
      if (branch.value === 'manual') {
        hour.value = String(parseInt(hourManual.value || '0', 10) || 0);
      }
    });
    if (minuteManual) minuteManual.addEventListener('input', () => {
      if (branch.value === 'manual') {
        minute.value = String(parseInt(minuteManual.value || '0', 10) || 0);
      }
    });
    // 초기 동기화
    applyFromBranch();
  }

  function init() {
    sync('hourBranch', 'hour', 'minute', 'hourManualRow', 'hourManual', 'minuteManual');
    sync('pHourBranch', 'pHour', 'pMinute', 'pHourManualRow', 'pHourManual', 'pMinuteManual');
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

// PalmReader 외부 모듈: js/readers/palm-reader.js (ADR-038 Phase 2 확장)
// 본 위치 인라인 정의는 외부 .js로 이동.


// NameReader 외부 모듈: js/readers/name-reader.js (ADR-038 Phase 2 확장)
// 본 위치 인라인 정의는 외부 .js로 이동.


// ============================================================
// SECTION: 한자 후보 보강 — Unihan 9,932자 전체를 한글음_한자에 merge
// 사용자 보고: 한글음→한자 드롭다운에 한자 누락 다수 (예: '민' 9개만 표시, 실제 42개)
// 해결: 페이지 로드 시 front/assets/hangul_to_hanja.json fetch하여 window.한글음_한자에 merge
// 기존 큐레이션 한자는 앞에 (자주 쓰는 거 우선), Unihan 누락 한자는 뒤에 추가
// ============================================================
(async function supplementHanjaCandidates() {
  try {
    // 1) 한글음→한자 후보 보강 (Unihan 9,932자)
    const [rSupp, rMeta] = await Promise.all([
      fetch('assets/hangul_to_hanja.json'),
      fetch('assets/hanja_meta.json'),
    ]);
    if (!rSupp.ok || !rMeta.ok) throw new Error('HTTP ' + rSupp.status + '/' + rMeta.status);
    const supp = await rSupp.json();
    const meta = await rMeta.json();

    // 한글음_한자 merge
    if (!window.한글음_한자) window.한글음_한자 = {};
    const target = window.한글음_한자;
    let added = 0;
    for (const g of Object.keys(supp)) {
      const existing = target[g] || [];
      const seen = new Set(existing);
      const out = [...existing];
      for (const ch of supp[g]) {
        if (!seen.has(ch)) { seen.add(ch); out.push(ch); added++; }
      }
      target[g] = out;
    }

    // 2) 한자획수 + 한자_뜻 보강 (saju-ui filter 통과 위해 필수)
    if (!window.한자획수) window.한자획수 = {};
    if (!window.한자_뜻) window.한자_뜻 = {};
    let metaAdded = 0;
    for (const ch of Object.keys(meta)) {
      if (!window.한자획수[ch] && meta[ch].s) { window.한자획수[ch] = meta[ch].s; metaAdded++; }
      if (!window.한자_뜻[ch]) window.한자_뜻[ch] = meta[ch].m || '';
    }

    // 보강 후 현재 입력된 이름이 있으면 한자 셀 재생성
    if (typeof window.updateHanjaSelectors === 'function') window.updateHanjaSelectors();

    window.__hanjaSuppLoaded = {
      added, metaAdded,
      totalCandidates: Object.values(target).reduce((s, a) => s + a.length, 0),
      totalStrokes: Object.keys(window.한자획수).length,
      totalMeanings: Object.keys(window.한자_뜻).filter(k => window.한자_뜻[k]).length,
    };
  } catch (e) {
    console.warn('한자 보강 로드 실패 (기존 큐레이션만 사용):', e);
  }
})();


// ============================================================
// SECTION: 태어난 곳 — 시도→시군구→읍면동 cascade 드롭다운 + 모드 토글
// 데이터: assets/korea_regions.json (행정안전부 표준 KOSTAT 2013, 동 ~3,482)
// 모드: search (Daum Postcode) / select (3단 cascade) / unknown (서울 종로 디폴트)
// ============================================================
(function initBirthplaceRegions() {
  let _regions = null;
  let _loadingPromise = null;

  function loadRegions() {
    if (_regions) return Promise.resolve(_regions);
    if (_loadingPromise) return _loadingPromise;
    _loadingPromise = fetch('assets/korea_regions.json')
      .then(r => r.json())
      .then(j => { _regions = j; return j; });
    return _loadingPromise;
  }

  function fillSelect(sel, items, placeholder) {
    sel.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = ''; ph.textContent = placeholder;
    sel.appendChild(ph);
    for (const it of items) {
      const opt = document.createElement('option');
      opt.value = it.code; opt.textContent = it.name;
      opt.dataset.lon = it.lon; opt.dataset.lat = it.lat;
      sel.appendChild(opt);
    }
  }

  function applyCoords(lon, sidoKey) {
    const lonInput = document.getElementById('longitude');
    if (lonInput) lonInput.value = (+lon).toFixed(3);
    const tzInput = document.getElementById('timezone');
    if (tzInput) tzInput.value = 9;
    const bp = document.getElementById('birthplace');
    if (bp) {
      const targetKey = sidoKey || 'custom';
      const opt = bp.querySelector(`option[value="${targetKey}"]`);
      if (opt) { bp.value = targetKey; bp.dispatchEvent(new Event('change')); }
      else { bp.value = 'custom'; bp.dispatchEvent(new Event('change')); }
    }
  }

  // 시도 한글명 → 기존 #birthplace 옵션 key 매핑
  const SIDO_NAME_KEY = {
    '서울특별시': 'seoul', '부산광역시': 'busan', '대구광역시': 'daegu',
    '인천광역시': 'incheon', '광주광역시': 'gwangju', '대전광역시': 'daejeon',
    '울산광역시': 'ulsan', '세종특별자치시': 'sejong', '경기도': 'gyeonggi',
    '강원도': 'gangwon', '강원특별자치도': 'gangwon',
    '충청북도': 'chungbuk', '충청남도': 'chungnam',
    '전라북도': 'jeonbuk', '전북특별자치도': 'jeonbuk', '전라남도': 'jeonnam',
    '경상북도': 'gyeongbuk', '경상남도': 'gyeongnam',
    '제주특별자치도': 'jeju',
  };

  async function initRegionCascade() {
    const sidoSel = document.getElementById('bpSidoSel');
    const sggSel = document.getElementById('bpSggSel');
    const dongSel = document.getElementById('bpDongSel');
    if (!sidoSel || !sggSel || !dongSel) return;

    const regs = await loadRegions();
    fillSelect(sidoSel, regs.sido, '— 도/시 —');

    sidoSel.addEventListener('change', () => {
      const code = sidoSel.value;
      if (!code) {
        fillSelect(sggSel, [], '— 시·군·구 —'); sggSel.disabled = true;
        fillSelect(dongSel, [], '— 읍·면·동 —'); dongSel.disabled = true;
        return;
      }
      const list = regs.sgg[code] || [];
      fillSelect(sggSel, list, '— 시·군·구 —');
      sggSel.disabled = !list.length;
      fillSelect(dongSel, [], '— 읍·면·동 —'); dongSel.disabled = true;
    });

    sggSel.addEventListener('change', () => {
      const code = sggSel.value;
      if (!code) { fillSelect(dongSel, [], '— 읍·면·동 —'); dongSel.disabled = true; return; }
      const list = regs.dong[code] || [];
      fillSelect(dongSel, list, list.length ? '— 읍·면·동 —' : '— 동 데이터 없음 —');
      dongSel.disabled = !list.length;
    });

    dongSel.addEventListener('change', () => {
      const opt = dongSel.selectedOptions[0];
      if (!opt || !opt.dataset.lon) return;
      const sidoOpt = sidoSel.selectedOptions[0];
      const sidoKey = sidoOpt ? SIDO_NAME_KEY[sidoOpt.textContent] : null;
      applyCoords(opt.dataset.lon, sidoKey);
    });
  }

  function initModeRadios() {
    const radios = document.querySelectorAll('input[name="bpMode"]');
    if (!radios.length) return;
    radios.forEach(r => r.addEventListener('change', () => {
      const mode = document.querySelector('input[name="bpMode"]:checked').value;
      document.querySelectorAll('.bp-panel').forEach(p => {
        p.style.display = (p.dataset.bpMode === mode) ? '' : 'none';
      });
      if (mode === 'unknown') applyCoords(126.978, 'seoul'); // 서울 종로 디폴트
      if (mode === 'select') loadRegions(); // prefetch
    }));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { initRegionCascade(); initModeRadios(); });
  } else {
    initRegionCascade(); initModeRadios();
  }
})();

