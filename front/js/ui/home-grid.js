/* ============================================================
   home-grid.js — 홈 콘텐츠 카드 그리드 + 카테고리 필터
   ============================================================
   - window.WHM_CONTENTS 순회 → 카테고리 탭 + 카드 렌더
   - 카테고리: 전체 · 사주 · 꿈 · 꽃패 · 관상
   - 카드 클릭 → 해당 도메인 캐릭터 카드의 진입 버튼 클릭 위임
     (기존 라우팅 로직 재사용 · 결정론 엔진 손대지 않음)
   - contents.js 로드된 이후 실행 (DOMContentLoaded + 짧은 폴링)
   ============================================================ */
(function () {
  'use strict';

  const CATEGORIES = [
    { key: 'all',    ko: '전체', han: '全' },
    { key: 'saju',   ko: '사주', han: '四柱' },
    { key: 'dream',  ko: '꿈',   han: '夢' },
    { key: 'hwapae', ko: '꽃패', han: '花牌' },
    { key: 'face',   ko: '관상', han: '相' },
  ];

  // MVP 활성 도메인만 그리드 노출 (star/palm/name은 히어로에서도 히든 상태)
  const ACTIVE_DOMAINS = new Set(['saju', 'dream', 'hwapae', 'face']);

  const MASTER_LABEL = {
    saju:   '만월 아씨',
    dream:  '몽이 도령',
    hwapae: '화선 낭자',
    face:   '운학 도사',
  };

  const CHAR_FALLBACK_POSTER = {
    saju:   './media/characters/manweol_assi.jpg',
    dream:  './media/characters/mongi_doryeong.jpg',
    hwapae: './media/characters/hwaseon_nangja.jpg',
    face:   './media/characters/unhak_dosa.jpg',
  };

  const TIER_LABEL = {
    free:    { text: '무료',   flag: 'free' },
    season:  { text: '시즌',   flag: 'season' },
    premium: { text: '깊이',   flag: 'premium' },
  };

  const FLAG_LABEL = {
    hot:  'HOT',
    new:  'NEW',
    beta: 'β',
  };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function flattenContents(contents) {
    const list = [];
    Object.keys(contents || {}).forEach(domainKey => {
      if (!ACTIVE_DOMAINS.has(domainKey)) return; // MVP: 활성 도메인만
      const domain = contents[domainKey] || {};
      const items = Array.isArray(domain.items) ? domain.items : [];
      items.forEach(item => {
        list.push({
          domainKey,
          master: domain.master || MASTER_LABEL[domainKey] || '',
          key: item.key,
          name: item.name,
          glyph: item.glyph,
          illust: item.illust,
          desc: item.desc,
          tier: item.tier,
          badges: Array.isArray(item.badges) ? item.badges : [],
          est: item.est,
          quote: item.quote,
          hasForm: Array.isArray(item.fields) && item.fields.length > 0,
          hasTab: !!item.tab,
        });
      });
    });
    return list;
  }

  function renderTabs(container) {
    container.innerHTML = CATEGORIES.map((c, idx) => `
      <button type="button" class="home-cat-tab" role="tab"
              data-cat="${c.key}" aria-selected="${idx === 0 ? 'true' : 'false'}">
        <span>${esc(c.ko)}</span>
        <span class="home-cat-tab-han">${esc(c.han)}</span>
      </button>
    `).join('');
  }

  function renderBadges(item) {
    const parts = [];
    const tier = TIER_LABEL[item.tier];
    if (tier) parts.push(`<span class="home-card-badge" data-tier="${esc(item.tier)}">${esc(tier.text)}</span>`);
    (item.badges || []).forEach(flag => {
      const label = FLAG_LABEL[flag];
      if (label) parts.push(`<span class="home-card-badge" data-flag="${esc(flag)}">${esc(label)}</span>`);
    });
    return parts.join('');
  }

  const DOMAIN_KO = { saju: '사주', dream: '꿈', hwapae: '꽃패', face: '관상' };

  function renderCard(item) {
    const hasIllust = !!item.illust;
    const poster = item.illust || CHAR_FALLBACK_POSTER[item.domainKey] || '';
    const posterFallback = CHAR_FALLBACK_POSTER[item.domainKey] || '';
    const posterAttr = poster
      ? `<img class="home-card-poster" src="${esc(poster)}" alt="${esc(item.name)}" loading="lazy"
              onerror="this.onerror=null;this.src='${esc(posterFallback)}';">`
      : `<div class="home-card-poster" aria-hidden="true"></div>`;

    // fallback(캐릭터 대표) 이미지는 시각 다양성 확보 위해 큰 글리프 오버레이
    const cornerGlyph = hasIllust && item.glyph
      ? `<span class="home-card-glyph" aria-hidden="true">${esc(item.glyph)}</span>`
      : '';
    const centerGlyph = !hasIllust && item.glyph
      ? `<span class="home-card-glyph-center" aria-hidden="true">${esc(item.glyph)}</span>`
      : '';

    return `
      <button type="button" class="home-card ${hasIllust ? 'has-illust' : 'no-illust'}"
              data-domain="${esc(item.domainKey)}"
              data-key="${esc(item.key)}"
              aria-label="${esc(item.name)} · ${esc(item.master)}">
        <div class="home-card-media">
          ${posterAttr}
          ${cornerGlyph}
          ${centerGlyph}
          <div class="home-card-badges">${renderBadges(item)}</div>
        </div>
        <div class="home-card-body">
          <p class="home-card-eyebrow">${esc(item.master)}</p>
          <h3 class="home-card-name">${esc(item.name)}</h3>
          <p class="home-card-desc">${esc(item.desc || item.quote || '')}</p>
          <div class="home-card-meta">
            ${item.est ? `<span class="home-card-meta-est">${esc(item.est)}</span>` : ''}
            <span class="home-card-meta-master">${esc(DOMAIN_KO[item.domainKey] || '')}</span>
          </div>
        </div>
      </button>
    `;
  }

  function renderGrid(container, items, activeCat) {
    const filtered = activeCat === 'all' ? items : items.filter(it => it.domainKey === activeCat);
    if (filtered.length === 0) {
      container.innerHTML = `<div class="home-grid-empty">아직 준비 중인 풀이입니다.</div>`;
      return;
    }
    container.innerHTML = filtered.map(renderCard).join('');
  }

  function routeToDomain(domainKey) {
    // 기존 캐릭터 카드 진입 로직 재사용:
    // .char-card[data-go="{domainKey}"] 안의 진입 버튼을 클릭
    const enterBtn = document.querySelector(`.char-card[data-go="${domainKey}"] .char-card-enter`);
    if (enterBtn) {
      enterBtn.click();
      return true;
    }
    // fallback: 해당 도메인 탭 버튼 직접 클릭
    const tabBtn = document.querySelector(`.tab-btn[data-tab="${domainKey}"]`);
    if (tabBtn) {
      tabBtn.click();
      // 탭 활성화 후 폼까지 스크롤
      requestAnimationFrame(() => {
        const target = document.getElementById(`tab-${domainKey}`);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      return true;
    }
    return false;
  }

  function attachHandlers(sectionEl) {
    const tabsEl = sectionEl.querySelector('.home-cat-tabs');
    const gridEl = sectionEl.querySelector('.home-grid');

    tabsEl.addEventListener('click', (e) => {
      const btn = e.target.closest('.home-cat-tab');
      if (!btn) return;
      const cat = btn.dataset.cat;
      tabsEl.querySelectorAll('.home-cat-tab').forEach(t => t.setAttribute('aria-selected', t === btn ? 'true' : 'false'));
      const items = sectionEl.__items || [];
      renderGrid(gridEl, items, cat);
    });

    gridEl.addEventListener('click', (e) => {
      const card = e.target.closest('.home-card');
      if (!card) return;
      const domain = card.dataset.domain;
      if (!domain) return;
      routeToDomain(domain);
      // 상단 히어로 위치로 스크롤 (기존 카드 갤러리가 활성화됨)
      const gallery = document.getElementById('cardGallery');
      if (gallery) gallery.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  function build() {
    const contents = window.WHM_CONTENTS;
    if (!contents) return false;
    const sectionEl = document.getElementById('homeGridSection');
    if (!sectionEl) return false;
    const tabsEl = sectionEl.querySelector('.home-cat-tabs');
    const gridEl = sectionEl.querySelector('.home-grid');
    if (!tabsEl || !gridEl) return false;

    const items = flattenContents(contents);
    sectionEl.__items = items;

    renderTabs(tabsEl);
    renderGrid(gridEl, items, 'all');
    attachHandlers(sectionEl);

    // 노출
    sectionEl.hidden = false;
    return true;
  }

  function waitAndBuild(retries = 30) {
    if (build()) return;
    if (retries <= 0) return;
    setTimeout(() => waitAndBuild(retries - 1), 100);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => waitAndBuild());
  } else {
    waitAndBuild();
  }

  window.HomeGrid = { build, routeToDomain };
})();
