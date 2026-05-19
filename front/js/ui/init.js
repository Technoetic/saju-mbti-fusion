// ============================================================
// init.js — ADR-054 Phase Y2 그룹 분리
// ============================================================
// autoInit·initTabCharacterScene·initBirthplaceSearch·initHourBranch
// 본 파일은 <script type="module"> 로드 — top-level identifier 자동 글로벌 X.
// IIFE 내부는 그대로, window 노출은 명시 (script type=module + Object.assign(window) 패턴).
// ============================================================
// ============================================================
// SECTION: 탭 캐릭터 영상 + 종이 펼침 애니메이션
// ============================================================
(function initTabCharacterScene() {
  const AUTO_UNROLL_MS = 1200;
  let autoUnrollTimer = null;

  // 영상을 body 직접 자식으로 이동 — .app-container(z-index 3) stacking context 밖으로
  // vignette(::after, z-index 2)가 영상 위로 깔리도록.
  function detachVideosToBody() {
    document.querySelectorAll('.tab-bg-video').forEach(v => {
      if (v.parentElement !== document.body) {
        document.body.appendChild(v);
      }
    });
  }

  function getTabVideo(tabId) {
    return document.querySelector('.tab-bg-video[data-character="' + tabId + '"]');
  }
  function getTabPaper(tabId) {
    const tab = document.getElementById('tab-' + tabId);
    return tab ? tab.querySelector('.paper-scroll') : null;
  }

  function activateTabScene(tabId) {
    if (autoUnrollTimer) { clearTimeout(autoUnrollTimer); autoUnrollTimer = null; }
    document.querySelectorAll('.tab-bg-video').forEach(v => {
      v.pause();
      v.classList.remove('show', 'dim');
    });
    document.querySelectorAll('.paper-scroll').forEach(p => p.classList.remove('unrolled'));

    // body의 탭별 상태 클래스 갱신 (CSS에서 탭별 배경 처리에 활용)
    document.body.classList.remove('star-active');

    const video = getTabVideo(tabId);
    if (video) {
      // 영상 없는 탭에서 적용된 inline 숨김/transition 차단 해제 (모든 영상)
      document.querySelectorAll('.tab-bg-video').forEach(v => {
        v.style.transition = '';
        v.style.opacity = '';
        v.style.visibility = '';
      });
      try { video.currentTime = 0; } catch(_) {}
      const p = video.play();
      if (p && p.catch) p.catch(() => {});
      requestAnimationFrame(() => video.classList.add('show'));

      // 히어로 모드 — 영상이 있을 때만 풀스크린 인트로 연출
      document.body.classList.add('hero-mode');
      autoUnrollTimer = setTimeout(() => {
        const paper = getTabPaper(tabId);
        if (paper) paper.classList.add('unrolled');
        video.classList.remove('show');
        video.classList.add('dim');
        document.body.classList.remove('hero-mode');
      }, AUTO_UNROLL_MS);
    } else {
      // 영상 없는 탭(성하 공자 등) — 헤더/탭바 유지, paper 즉시 펼침
      // 이전 탭 영상의 1.2s opacity transition 잔상을 막기 위해 transition도 즉시 끔
      document.querySelectorAll('.tab-bg-video').forEach(v => {
        v.style.transition = 'none';
        v.style.opacity = '0';
        v.style.visibility = 'hidden';
      });
      document.body.classList.remove('hero-mode');
      // 성하 공자 탭 — body에 표식 (CSS에서 인트로 bg-video를 더 어둡게 덮음)
      if (tabId === 'star') document.body.classList.add('star-active');
      requestAnimationFrame(() => {
        const paper = getTabPaper(tabId);
        if (paper) paper.classList.add('unrolled');
      });
    }
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

  function bindEnterButton() {
    const enterBtn = document.getElementById('enterBtn');
    if (!enterBtn) return;
    enterBtn.addEventListener('click', () => {
      setTimeout(() => activateTabScene('saju'), 600);
    });
  }

  function init() {
    detachVideosToBody();
    bindTabSwitch();
    bindEnterButton();
    if (document.body.classList.contains('in-app')) {
      activateTabScene('saju');
    }
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

