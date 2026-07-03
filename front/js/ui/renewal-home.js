/* ============================================================
   renewal-home.js — 리뉴얼 홈 렌더링 (2026-07)
   ============================================================
   - WHM_CONTENTS 순회 → 상품 카드 그리드
   - 카테고리 필터
   - 카드 클릭 → 기존 tab-bar 라우팅 재사용 (결정론 엔진 손대지 않음)
   ============================================================ */
(function () {
  'use strict';

  const CATS = [
    { key: 'all',    label: '전체' },
    { key: 'saju',   label: '사주' },
    { key: 'dream',  label: '꿈' },
    { key: 'hwapae', label: '꽃패' },
    { key: 'face',   label: '관상' },
  ];
  const ACTIVE = new Set(['saju', 'dream', 'hwapae', 'face']);

  const TIER = {
    free:    { text: '무료' },
    season:  { text: '시즌' },
    premium: { text: '깊이' },
  };
  const FLAG = { hot: 'HOT', new: 'NEW' };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function flatten(contents) {
    const list = [];
    Object.keys(contents || {}).forEach(domain => {
      if (!ACTIVE.has(domain)) return;
      const d = contents[domain] || {};
      (d.items || []).forEach(item => list.push({ domain, master: d.master, ...item }));
    });
    return list;
  }

  function renderCats(container) {
    container.innerHTML = CATS.map((c, i) => `
      <button type="button" class="home-cat" role="tab"
              data-cat="${c.key}" aria-selected="${i === 0 ? 'true' : 'false'}">
        ${esc(c.label)}
      </button>
    `).join('');
  }

  function renderBadges(item) {
    const parts = [];
    const t = TIER[item.tier];
    if (t) parts.push(`<span class="p-badge" data-tier="${esc(item.tier)}">${esc(t.text)}</span>`);
    (item.badges || []).forEach(f => {
      const label = FLAG[f];
      if (label) parts.push(`<span class="p-badge" data-flag="${esc(f)}">${esc(label)}</span>`);
    });
    return parts.join('');
  }

  function renderCard(item) {
    const hasIllust = !!item.illust;
    const poster = hasIllust
      ? `<img class="p-card-poster" src="${esc(item.illust)}" alt="${esc(item.name)}" loading="lazy">`
      : '';
    const glyph = !hasIllust && item.glyph
      ? `<span class="p-card-glyph-big" aria-hidden="true">${esc(item.glyph)}</span>`
      : '';
    // 목업 할인율 (프로덕션 후기에 실제 데이터 연결)
    const mockDiscount = item.tier === 'season' ? 54 : item.tier === 'premium' ? 41 : 0;
    const discountBadge = mockDiscount > 0
      ? `<span class="p-card-discount">${mockDiscount}% 할인중</span>` : '';

    return `
      <button type="button" class="p-card ${hasIllust ? 'has-illust' : 'no-illust'}"
              data-domain="${esc(item.domain)}" data-key="${esc(item.key)}"
              aria-label="${esc(item.name)}">
        <div class="p-card-media">
          ${poster}${glyph}
          <div class="p-card-badges">${renderBadges(item)}</div>
          ${discountBadge}
        </div>
        <div class="p-card-body">
          <p class="p-card-eyebrow">${esc(item.master || '')}</p>
          <h3 class="p-card-name">${esc(item.name)}</h3>
          <p class="p-card-desc">${esc(item.desc || '')}</p>
          <div class="p-card-meta">
            ${item.est ? `<span class="p-card-est">${esc(item.est)}</span>` : ''}
            <span class="p-card-star">★ 4.${8 - (item.key?.length || 0) % 3}</span>
          </div>
        </div>
      </button>
    `;
  }

  function renderCards(container, items, cat) {
    const filtered = cat === 'all' ? items : items.filter(it => it.domain === cat);
    if (!filtered.length) {
      container.innerHTML = `<div class="home-empty">아직 준비 중이야</div>`;
      return;
    }
    container.innerHTML = filtered.map(renderCard).join('');
  }

  function routeToDomain(domain) {
    const tab = document.querySelector(`.tab-btn[data-tab="${domain}"]`);
    if (tab) {
      tab.click();
      requestAnimationFrame(() => {
        const target = document.getElementById(`tab-${domain}`);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      return true;
    }
    return false;
  }

  function attach(section) {
    const catsEl = section.querySelector('.home-cats');
    const cardsEl = section.querySelector('.home-cards');

    catsEl.addEventListener('click', (e) => {
      const btn = e.target.closest('.home-cat');
      if (!btn) return;
      catsEl.querySelectorAll('.home-cat').forEach(b => b.setAttribute('aria-selected', b === btn ? 'true' : 'false'));
      renderCards(cardsEl, section.__items || [], btn.dataset.cat);
    });

    cardsEl.addEventListener('click', (e) => {
      const card = e.target.closest('.p-card');
      if (!card) return;
      const domain = card.dataset.domain;
      if (domain) routeToDomain(domain);
    });
  }

  function build() {
    const section = document.getElementById('homeMain');
    const contents = window.WHM_CONTENTS;
    if (!section || !contents) return false;
    const catsEl = section.querySelector('.home-cats');
    const cardsEl = section.querySelector('.home-cards');
    if (!catsEl || !cardsEl) return false;

    const items = flatten(contents);
    section.__items = items;
    renderCats(catsEl);
    renderCards(cardsEl, items, 'all');
    attach(section);
    return true;
  }

  function waitAndBuild(retries = 40) {
    if (build()) return;
    if (retries <= 0) return;
    setTimeout(() => waitAndBuild(retries - 1), 100);
  }

  // 히어로 CTA 클릭 → 2026 신년운세로 (사주 탭 전환)
  document.addEventListener('click', (e) => {
    const cta = e.target.closest('.hero-cta');
    if (cta) routeToDomain('saju');
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => waitAndBuild());
  } else {
    waitAndBuild();
  }

  window.RenewalHome = { build, routeToDomain };
})();
