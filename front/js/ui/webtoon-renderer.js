// webtoon-renderer.js — 만월 아씨 정통 사주 결과 웹툰 모드
//
// 사용:
//   import { renderWebtoonReading } from './webtoon-renderer.js';
//   renderWebtoonReading(targetEl, markdownText);
//
// 페이지 5장(p6~p10.jpg)에 미리 정의된 말풍선 슬롯(15개)에
// 풀이 본문을 단락 단위로 균등 배분해 채운다.

// ────────────────────────────────────────────────────────
// 페이지 메타 — 슬롯 좌표는 페이지 가로/세로 비율(0~1) 기준.
// type: 'oval' (흰 타원 말풍선) | 'box' (갈색 나레이션 박스)
// ────────────────────────────────────────────────────────
const PAGES = [
  {
    src: 'media/saju_webtoon/p6.jpg',
    slots: [
      { type: 'box',  top: 0.182, left: 0.20, width: 0.60, height: 0.045, color: 'narration' },
      { type: 'oval', top: 0.495, left: 0.16, width: 0.70, height: 0.090 },
      { type: 'box',  top: 0.925, left: 0.20, width: 0.60, height: 0.060, color: 'narration' },
    ],
  },
  {
    src: 'media/saju_webtoon/p7.jpg',
    slots: [
      { type: 'oval', top: 0.225, left: 0.10, width: 0.60, height: 0.070 },
      { type: 'oval', top: 0.495, left: 0.08, width: 0.78, height: 0.180 },
      { type: 'oval', top: 0.840, left: 0.05, width: 0.55, height: 0.085 },
    ],
  },
  {
    src: 'media/saju_webtoon/p8.jpg',
    slots: [
      { type: 'oval', top: 0.190, left: 0.22, width: 0.70, height: 0.075 },
      { type: 'oval', top: 0.470, left: 0.12, width: 0.78, height: 0.075 },
      { type: 'oval', top: 0.840, left: 0.10, width: 0.75, height: 0.070 },
    ],
  },
  {
    src: 'media/saju_webtoon/p9.jpg',
    slots: [
      { type: 'oval', top: 0.200, left: 0.12, width: 0.72, height: 0.080 },
      { type: 'oval', top: 0.490, left: 0.10, width: 0.78, height: 0.090 },
      { type: 'oval', top: 0.835, left: 0.10, width: 0.72, height: 0.075 },
    ],
  },
  {
    src: 'media/saju_webtoon/p10.jpg',
    slots: [
      { type: 'oval', top: 0.200, left: 0.12, width: 0.72, height: 0.080 },
      { type: 'oval', top: 0.490, left: 0.10, width: 0.78, height: 0.090 },
      { type: 'oval', top: 0.840, left: 0.10, width: 0.72, height: 0.075 },
    ],
  },
];

// ────────────────────────────────────────────────────────
// 텍스트 정제·단락 분할
// ────────────────────────────────────────────────────────
function stripMarkdown(md) {
  if (!md) return '';
  return String(md)
    // 코드블록·인용·헤더 prefix 제거
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^>\s+/gm, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    // 강조 마크업만 제거(내용 유지)
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    // 링크 [text](url) → text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // 리스트 마커
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .trim();
}

function splitParagraphs(text) {
  return stripMarkdown(text)
    .split(/\n{2,}|\r\n{2,}/)
    .map(s => s.replace(/\s+/g, ' ').trim())
    .filter(Boolean);
}

// N개 슬롯에 단락을 균등 분배.
// 단락 수 > 슬롯 수: 인접 단락을 자연스럽게 묶어 슬롯 수에 맞춤.
// 단락 수 < 슬롯 수: 긴 단락을 문장 단위로 쪼개 슬롯 수를 채움.
function distributeIntoSlots(paragraphs, slotCount) {
  if (!paragraphs.length) return Array(slotCount).fill('');
  let units = paragraphs.slice();

  // 단락 수 < 슬롯 수: 가장 긴 단락을 문장으로 쪼갬
  while (units.length < slotCount) {
    let idx = 0, longest = 0;
    units.forEach((u, i) => { if (u.length > longest) { longest = u.length; idx = i; } });
    const sentences = units[idx].split(/(?<=[.!?。…ㄻ"'\]\)])\s+/);
    if (sentences.length < 2) break;
    const mid = Math.ceil(sentences.length / 2);
    units.splice(idx, 1, sentences.slice(0, mid).join(' ').trim(), sentences.slice(mid).join(' ').trim());
  }

  // 단락 수 > 슬롯 수: 인접 단락 병합
  while (units.length > slotCount) {
    let idx = 0, shortest = Infinity;
    for (let i = 0; i < units.length - 1; i++) {
      const sum = units[i].length + units[i + 1].length;
      if (sum < shortest) { shortest = sum; idx = i; }
    }
    units.splice(idx, 2, units[idx] + ' ' + units[idx + 1]);
  }

  // 마지막 안전망 — 길이 모자라면 빈 문자열로 채움
  while (units.length < slotCount) units.push('');
  return units.slice(0, slotCount);
}

// ────────────────────────────────────────────────────────
// 페이지·슬롯 DOM 생성
// ────────────────────────────────────────────────────────
function buildPage(pageMeta, slotTexts, pageIdx) {
  const page = document.createElement('div');
  page.className = 'webtoon-page';
  page.style.setProperty('--page-aspect', '1 / 5');  // 2000x10000

  const img = document.createElement('img');
  img.className = 'webtoon-page-img';
  img.src = pageMeta.src;
  img.alt = `풀이 ${pageIdx + 1}장`;
  img.loading = pageIdx < 2 ? 'eager' : 'lazy';
  page.appendChild(img);

  pageMeta.slots.forEach((slot, sIdx) => {
    const el = document.createElement('div');
    el.className = `webtoon-slot webtoon-slot-${slot.type}` + (slot.color === 'narration' ? ' webtoon-slot-narration' : '');
    el.style.top    = (slot.top * 100) + '%';
    el.style.left   = (slot.left * 100) + '%';
    el.style.width  = (slot.width * 100) + '%';
    el.style.height = (slot.height * 100) + '%';
    el.textContent = slotTexts[sIdx] || '';
    page.appendChild(el);
  });

  return page;
}

// ────────────────────────────────────────────────────────
// 공개 API
// ────────────────────────────────────────────────────────
export function renderWebtoonReading(targetEl, markdownText, opts = {}) {
  if (!targetEl) return;

  const title = opts.title || '만월 아씨의 사주 이야기';
  const paragraphs = splitParagraphs(markdownText);
  const totalSlots = PAGES.reduce((n, p) => n + p.slots.length, 0);
  const allSlotTexts = distributeIntoSlots(paragraphs, totalSlots);

  const container = document.createElement('div');
  container.className = 'webtoon-container';

  const header = document.createElement('h2');
  header.className = 'webtoon-title';
  header.textContent = title;
  container.appendChild(header);

  let slotCursor = 0;
  PAGES.forEach((pm, pIdx) => {
    const texts = allSlotTexts.slice(slotCursor, slotCursor + pm.slots.length);
    slotCursor += pm.slots.length;
    container.appendChild(buildPage(pm, texts, pIdx));
  });

  // 원본 본문은 펼침 가능한 details로 보관 (접근성·복사용)
  const raw = document.createElement('details');
  raw.className = 'webtoon-raw';
  const summary = document.createElement('summary');
  summary.textContent = '본문 그대로 보기';
  raw.appendChild(summary);
  const pre = document.createElement('div');
  pre.className = 'webtoon-raw-body';
  pre.innerHTML = paragraphs.map(p => `<p>${p.replace(/</g, '&lt;')}</p>`).join('');
  raw.appendChild(pre);
  container.appendChild(raw);

  targetEl.innerHTML = '';
  targetEl.appendChild(container);
}

// 마지막 풀이 텍스트를 보관해 두면 stream 종료 후 다시 렌더링 가능
export const __WEBTOON_RENDERER_VERSION__ = '1.0.0';
