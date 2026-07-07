/* ============================================================
   manwol-renderer.js — 만월아씨 통합 서사 렌더러
   ============================================================
   /api/manwol/reading 스트리밍 응답을 심야 방송실 톤 텍스트 카드로 렌더.
   결정론 데이터 시각화(오행 %바 · 대운 타임라인 · 격국) 를 카드 상단에 함께 배치.
   ============================================================ */

/**
 * 만월아씨 통합 서사를 지정 컨테이너에 렌더한다.
 *
 * @param {HTMLElement} targetEl   결과가 삽입될 컨테이너 (.claude-output 권장)
 * @param {object}      payload    /api/manwol/reading 요청 페이로드
 * @param {object}      [opts]
 * @param {string}      [opts.title]   상단 표제 (기본: "만월아씨 사연 풀이")
 */
export async function renderManwolReading(targetEl, payload, opts = {}) {
  if (!targetEl) return;
  const title = opts.title || '만월아씨 · 심야 사연 풀이';

  targetEl.innerHTML = `
    <div class="manwol-card" role="article" aria-label="만월아씨 풀이">
      <div class="manwol-frame">
        <div class="manwol-header">
          <div class="manwol-sign">ON AIR</div>
          <div class="manwol-title">${escapeHtml(title)}</div>
          <div class="manwol-sub">만월아씨가 마이크를 잡는다.</div>
        </div>
        <div class="manwol-viz" data-manwol-viz></div>
        <div class="manwol-body" data-manwol-body>
          <div class="manwol-cursor" aria-hidden="true"></div>
        </div>
        <div class="manwol-foot" data-manwol-foot></div>
      </div>
    </div>
  `;

  const viz = targetEl.querySelector('[data-manwol-viz]');
  const body = targetEl.querySelector('[data-manwol-body]');
  const foot = targetEl.querySelector('[data-manwol-foot]');
  const cursor = body.querySelector('.manwol-cursor');

  // 시각화 즉시 렌더 (LLM 응답 기다리지 않음)
  try {
    renderVisualizations(viz, payload);
  } catch (e) {
    console.warn('[manwol] 시각화 렌더 실패:', e);
  }

  let acc = '';
  try {
    const res = await fetch('/api/manwol/reading', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, stream: true }),
    });
    if (!res.ok) throw new Error(`서버 ${res.status}`);
    if (!res.body) throw new Error('스트림 미지원');

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (!chunk) continue;
      acc += chunk;
      renderParagraphs(body, acc, cursor);
    }
    if (cursor && cursor.isConnected) cursor.remove();
    if (!acc.trim()) {
      body.innerHTML = '<p class="manwol-empty">사연 풀이 응답이 비었다. 다시 시도해봐.</p>';
      return;
    }
    foot.innerHTML = '<div class="manwol-signoff">— 만월아씨</div>';
  } catch (err) {
    if (cursor && cursor.isConnected) cursor.remove();
    body.insertAdjacentHTML(
      'beforeend',
      `<p class="manwol-error">사연 풀이 도중 신호가 끊겼어. (${escapeHtml(String(err.message || err))})</p>`,
    );
  }
}

/* ────────────────────────────────────────────────────────────
   시각화 · 결정론 데이터만으로 즉시 렌더
   ──────────────────────────────────────────────────────────── */

function renderVisualizations(container, payload) {
  if (!container) return;
  const parts = [];

  // 1. 사주 pillar 배지 (년/월/일/시)
  const pillars = payload?.saju?.pillars;
  if (pillars) parts.push(renderPillarBadges(pillars, payload?.saju?.day_master));

  // 2. 오행 분포 %바 (게이지 애니메이션)
  const wuxing = payload?.saju?.wuxing_dist;
  if (wuxing && Object.keys(wuxing).length) {
    parts.push(renderWuxingBars(wuxing, payload?.saju?.day_master));
  }

  // 3. 대운 타임라인
  const cycle = payload?.saju?.luck_cycle;
  if (Array.isArray(cycle) && cycle.length) {
    parts.push(renderLuckCycle(cycle, payload?.age));
  }

  // 4. 격국 · 신강 카드
  const gyeokguk = payload?.saju?.gyeokguk;
  const strength = payload?.saju?.strength;
  if ((gyeokguk && gyeokguk.name) || (strength && strength.grade)) {
    parts.push(renderMetaChips(gyeokguk, strength));
  }

  // 5. 관상 · 얼굴 오버레이 이미지 + 12궁 %바 + 삼정
  const face = payload?.face_reading;
  if (face && (face.visualization || face.palace_scores)) {
    parts.push(renderFaceBlock(face));
  }

  container.innerHTML = parts.join('');

  // 6. 오행 게이지 애니메이션 · initial 0% → target %
  //    innerHTML 세팅 직후 next-frame 에 타겟 width 세팅해서 CSS transition 유발
  requestAnimationFrame(() => {
    const fills = container.querySelectorAll('.viz-bar-fill[data-target-width]');
    fills.forEach((el, i) => {
      const target = el.getAttribute('data-target-width');
      // stagger (원소별 90ms 간격) — 게이지가 순차적으로 주욱 올라감
      setTimeout(() => { el.style.width = target; }, 120 + i * 90);
    });
    // 12궁 palace 바도 동일 애니메이션
    const palaceFills = container.querySelectorAll('.viz-palace-fill[data-target-width]');
    palaceFills.forEach((el, i) => {
      const target = el.getAttribute('data-target-width');
      setTimeout(() => { el.style.width = target; }, 300 + i * 60);
    });
  });
}

const ELEMENT_META = {
  '木': { ko: '목', color: '#4a8c3f', dayStems: ['甲','乙'] },
  '火': { ko: '화', color: '#c8323e', dayStems: ['丙','丁'] },
  '土': { ko: '토', color: '#c9a45a', dayStems: ['戊','己'] },
  '金': { ko: '금', color: '#a8a8a8', dayStems: ['庚','辛'] },
  '水': { ko: '수', color: '#3f6da8', dayStems: ['壬','癸'] },
};
const ELEMENT_ORDER = ['木','火','土','金','水'];

function stemElement(stem) {
  for (const el of ELEMENT_ORDER) {
    if (ELEMENT_META[el].dayStems.includes(stem)) return el;
  }
  return null;
}

function renderPillarBadges(pillars, dayMaster) {
  const cols = [
    { key: 'year',  label: '년주' },
    { key: 'month', label: '월주' },
    { key: 'day',   label: '일주' },
    { key: 'hour',  label: '시주' },
  ];
  const rows = cols.map(({ key, label }) => {
    const p = pillars[key] || pillars[key === 'hour' ? 'time' : key];
    if (!p) return '';
    const gan = p.gan_han || p.gan || '?';
    const ji  = p.ji_han || p.ji || '?';
    const ganEl = stemElement(gan);
    const jiElBranch = branchElement(ji);
    const isDay = key === 'day';
    return `
      <div class="viz-p-col ${isDay ? 'viz-p-col-day' : ''}">
        <div class="viz-p-label">${label}</div>
        <div class="viz-p-gan" data-el="${ganEl || ''}">${gan}</div>
        <div class="viz-p-ji"  data-el="${jiElBranch || ''}">${ji}</div>
      </div>
    `;
  }).join('');
  return `
    <div class="viz-block viz-pillars">
      <div class="viz-block-head">
        <span class="viz-block-title">四柱 · 사주</span>
        ${dayMaster ? `<span class="viz-block-hint">일간 <b>${dayMaster}</b></span>` : ''}
      </div>
      <div class="viz-p-row">${rows}</div>
    </div>
  `;
}

const BRANCH_ELEMENT = {
  '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
  '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水',
};
function branchElement(ji) {
  return BRANCH_ELEMENT[ji] || null;
}

function renderWuxingBars(dist, dayMaster) {
  const total = ELEMENT_ORDER.reduce((s,el) => s + (+dist[el] || 0), 0) || 1;
  const rows = ELEMENT_ORDER.map(el => {
    const v = +dist[el] || 0;
    const pct = Math.round((v / total) * 1000) / 10; // 0.1 소수
    const targetW = `${Math.min(100, pct)}%`;
    const meta = ELEMENT_META[el];
    const isDayMaster = meta.dayStems.includes(dayMaster);
    return `
      <div class="viz-bar-row ${isDayMaster ? 'viz-bar-me' : ''}">
        <div class="viz-bar-label">
          <span class="viz-bar-hanja" style="color:${meta.color}">${el}</span>
          <span class="viz-bar-ko">${meta.ko}</span>
        </div>
        <div class="viz-bar-track">
          <div class="viz-bar-fill" style="width:0%; background:${meta.color}" data-target-width="${targetW}"></div>
        </div>
        <div class="viz-bar-pct">${pct.toFixed(1)}%</div>
      </div>
    `;
  }).join('');
  return `
    <div class="viz-block viz-wuxing">
      <div class="viz-block-head">
        <span class="viz-block-title">오행 분포</span>
        ${dayMaster ? `<span class="viz-block-hint">(일간 기준 · 짙은 색이 나)</span>` : ''}
      </div>
      <div class="viz-bars">${rows}</div>
    </div>
  `;
}

/* ── 관상 · 얼굴 오버레이 이미지 + 12궁 %바 ──────────────── */
const PALACE_KO = {
  myeong: '명궁', jaebaek: '재백궁', gwanrok: '관록궁', bokdeok: '복덕궁',
  cheocheop: '처첩궁', janyeo: '남녀궁', hyeongje: '형제궁', jeontaek: '전택궁',
  jilek: '질액궁', cheoni: '천이궁', nobok: '노복궁', bumo: '부모궁',
};
const FACE_SHAPE_KO = {
  long: '긴형 (木)', round: '둥근형 (水)', oval: '달걀형 (火/土)', square: '각형 (金)',
};

function renderFaceBlock(face) {
  const parts = [];
  parts.push(`<div class="viz-block-head">
    <span class="viz-block-title">관상 · 12궁 결정론</span>
    <span class="viz-block-hint">(MediaPipe 8메트릭 → 12궁·삼정 점수)</span>
  </div>`);

  // 얼굴 오버레이 이미지
  if (face.visualization?.image_base64) {
    parts.push(`
      <div class="viz-face-overlay">
        <img src="${escapeHtml(face.visualization.image_base64)}" alt="관상 12궁 오버레이" loading="lazy"/>
      </div>
    `);
  }

  // 5형·신·기 배지
  const badges = [];
  const fs = face.face_shape;
  const fsKey = (fs && typeof fs === 'object') ? (fs.shape || fs.type) : fs;
  if (fsKey) badges.push(`<span class="viz-chip viz-chip-shape">5형 · ${escapeHtml(FACE_SHAPE_KO[fsKey] || fsKey)}</span>`);
  if (face.shen_score != null) badges.push(`<span class="viz-chip">신 (神) ${(+face.shen_score).toFixed(2)}</span>`);
  if (face.qi_score != null) badges.push(`<span class="viz-chip">기 (氣) ${(+face.qi_score).toFixed(2)}</span>`);
  if (face.overall_balance != null) badges.push(`<span class="viz-chip">균형 ${(+face.overall_balance).toFixed(2)}</span>`);
  if (badges.length) parts.push(`<div class="viz-face-badges">${badges.join('')}</div>`);

  // 12궁 %바
  const ps = face.palace_scores;
  if (ps && typeof ps === 'object') {
    const rows = Object.entries(ps).map(([key, meta]) => {
      if (!meta || typeof meta !== 'object') return '';
      const label = meta.label_ko || PALACE_KO[key] || key;
      const short = meta.label_short || '';
      const score = typeof meta.score === 'number' ? meta.score : (parseFloat(meta.score) || 0);
      const pct = Math.max(0, Math.min(100, Math.round(score * 100)));
      const isTop = key === face.top_palace;
      const isWeak = key === face.weakest_palace;
      const mark = isTop ? ' ★' : (isWeak ? ' ▼' : '');
      return `
        <div class="viz-palace-row ${isTop ? 'viz-palace-top' : ''} ${isWeak ? 'viz-palace-weak' : ''}">
          <div class="viz-palace-label">${escapeHtml(label)}${mark}</div>
          <div class="viz-palace-track">
            <div class="viz-palace-fill" style="width:0%" data-target-width="${pct}%"></div>
          </div>
          <div class="viz-palace-pct">${pct}${short ? ' · ' + escapeHtml(short) : ''}</div>
        </div>
      `;
    }).filter(Boolean).join('');
    if (rows) parts.push(`<div class="viz-palace-bars">${rows}</div>`);
  }

  return `<div class="viz-block viz-face">${parts.join('')}</div>`;
}

function renderLuckCycle(cycle, currentAge) {
  const shown = cycle.slice(0, 9);
  const items = shown.map(c => {
    const isCurrent = currentAge != null
      && c.age != null
      && c.age <= currentAge
      && (c.age + 10) > currentAge;
    const stemEl = stemElement(c.gan_han);
    const jiEl = branchElement(c.ji_han);
    return `
      <div class="viz-lc-item ${isCurrent ? 'viz-lc-current' : ''}">
        <div class="viz-lc-age">${c.age != null ? c.age + '세' : ''}</div>
        <div class="viz-lc-gz">
          <span data-el="${stemEl || ''}">${c.gan_han || ''}</span>
          <span data-el="${jiEl || ''}">${c.ji_han || ''}</span>
        </div>
      </div>
    `;
  }).join('');
  return `
    <div class="viz-block viz-luck">
      <div class="viz-block-head">
        <span class="viz-block-title">대운 흐름</span>
        <span class="viz-block-hint">(빛나는 칸이 지금 대운)</span>
      </div>
      <div class="viz-lc-track">${items}</div>
    </div>
  `;
}

function renderMetaChips(gyeokguk, strength) {
  const chips = [];
  if (gyeokguk && gyeokguk.name) {
    chips.push(`<span class="viz-chip viz-chip-guk">격국 · ${escapeHtml(gyeokguk.name)}</span>`);
  }
  if (strength && strength.grade) {
    chips.push(`<span class="viz-chip viz-chip-str">${escapeHtml(strength.grade)}</span>`);
  }
  if (!chips.length) return '';
  return `<div class="viz-block viz-meta">${chips.join('')}</div>`;
}

/* ────────────────────────────────────────────────────────────
   서사 스트리밍 렌더
   ──────────────────────────────────────────────────────────── */

function renderParagraphs(body, text, cursor) {
  const paragraphs = text
    .replace(/\r\n/g, '\n')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
  const html = paragraphs
    .map((p) => `<p>${escapeHtml(p).replace(/\n/g, '<br>')}</p>`)
    .join('');
  if (cursor && cursor.isConnected) cursor.remove();
  body.innerHTML = html;
  const cur = document.createElement('span');
  cur.className = 'manwol-cursor';
  cur.setAttribute('aria-hidden', 'true');
  body.appendChild(cur);
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
