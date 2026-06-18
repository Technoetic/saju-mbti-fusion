// webtoon-renderer.js — 만월 아씨 정통 사주 결과 웹툰 모드
//
// 사용:
//   import { renderWebtoonReading } from './webtoon-renderer.js';
//   renderWebtoonReading(targetEl, markdownText, { title, name });
//
// 5장(p6~p10.jpg)에 14개 슬롯. 풀이를 단락→문장으로 쪼개 슬롯에 균등 배분.
// 각 슬롯은 짧고 또렷한 한 마디. 긴 단락은 핵심 문장만 골라 압축.

// ────────────────────────────────────────────────────────
// 페이지 메타 — 슬롯 좌표는 페이지 가로/세로 비율(0~1).
// type: 'oval' (흰 타원 말풍선 — 대사) | 'box' (갈색 박스 — 나레이션)
// ────────────────────────────────────────────────────────
const PAGES = [
  // 픽셀 분석(_full_calib.mjs) + 사용자 첨부 화면 시각 측정 종합 좌표.
  {
    src: 'media/saju_webtoon/p6.jpg',
    slots: [
      // p6 갈색 박스1 — 픽셀 측정: top 0.204 left 0.193 w 0.589 h 0.054
      { type: 'box',  top: 0.204, left: 0.193, width: 0.589, height: 0.054, color: 'narration' },
      // p6 흰 타원 — 컷2 끝. 픽셀 흰 영역 0.498~0.600 + 가로 시각 측정
      { type: 'oval', top: 0.510, left: 0.150, width: 0.750, height: 0.085 },
      // p6 갈색 박스2 — 픽셀 측정: top 0.845 w 0.848 h 0.114
      { type: 'box',  top: 0.845, left: 0.075, width: 0.848, height: 0.114, color: 'narration' },
    ],
  },
  {
    src: 'media/saju_webtoon/p7.jpg',
    slots: [
      // p7 컷1 흰 타원 — 책상 컷 끝
      { type: 'oval', top: 0.200, left: 0.075, width: 0.610, height: 0.100 },
      // p7 컷2 흰 타원 — 가운데 종이 (큰), 픽셀 측정 484~507 헤더 + 509~688 본체
      { type: 'oval', top: 0.500, left: 0.060, width: 0.870, height: 0.180 },
      // p7 컷3 작은 흰 타원 (꼬리)
      { type: 'oval', top: 0.910, left: 0.060, width: 0.345, height: 0.085 },
    ],
  },
  {
    src: 'media/saju_webtoon/p8.jpg',
    slots: [
      // p8 컷1 — 책상 컷 끝 흰 타원 + 뿔
      { type: 'oval', top: 0.260, left: 0.260, width: 0.680, height: 0.105 },
      // p8 컷2 — 만월 + 보름달 컷 끝 큰 흰 타원 + 꼬리
      { type: 'oval', top: 0.625, left: 0.080, width: 0.820, height: 0.095 },
      // p8 컷3 — 등 컷 끝 흰 타원 + 꼬리
      { type: 'oval', top: 0.915, left: 0.110, width: 0.800, height: 0.080 },
    ],
  },
  {
    src: 'media/saju_webtoon/p9.jpg',
    slots: [
      // p9 컷1 — 종이 든 만월. 픽셀 측정: top 0.121 left 0.252 w 0.747 h 0.062
      { type: 'oval', top: 0.121, left: 0.252, width: 0.747, height: 0.062 },
      // p9 컷2 — 가운데 큰 컷 흰 타원
      { type: 'oval', top: 0.560, left: 0.060, width: 0.840, height: 0.130 },
      // p9 컷3 — 책상 컷 흰 타원 꼬리. 측정: top 0.840 left 0.203 w 0.720
      { type: 'oval', top: 0.860, left: 0.060, width: 0.720, height: 0.110 },
    ],
  },
  {
    src: 'media/saju_webtoon/p10.jpg',
    slots: [
      // p10 컷1 — 큰 흰 타원, 위치 0.344~0.498 흰 영역
      { type: 'oval', top: 0.380, left: 0.060, width: 0.820, height: 0.110 },
      // p10 컷2 — 흰 타원 + 뿔, 위치 0.784~끝 흰 영역 안에서
      { type: 'oval', top: 0.840, left: 0.080, width: 0.780, height: 0.130 },
    ],
  },
];

// ────────────────────────────────────────────────────────
// 텍스트 정제 + 핵심 추출
// ────────────────────────────────────────────────────────
function stripMarkdown(md) {
  if (!md) return '';
  return String(md)
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^>\s+/gm, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .trim();
}

function splitSentences(text) {
  return String(text)
    .split(/(?<=[.!?。…!?])\s+|(?<=[다요죠네야오])\.\s*|\n+/)
    .map(s => s.replace(/\s+/g, ' ').trim())
    .filter(s => s.length >= 6);
}

// 한 슬롯에 들어갈 한 문장 압축: maxLen 넘으면 자연스러운 자리에서 자름
function compressForSlot(s, maxLen) {
  s = (s || '').trim();
  if (s.length <= maxLen) return s;
  // 자연스러운 끝맺음(쉼표·접속어)에서 자름
  const cut = s.slice(0, maxLen);
  const lastPunct = Math.max(cut.lastIndexOf(','), cut.lastIndexOf('·'), cut.lastIndexOf(' '));
  return (lastPunct > maxLen * 0.6 ? cut.slice(0, lastPunct) : cut).trim() + '…';
}

// 풀이를 N개 슬롯에 균등 분배
// 1) 마크다운 제거 → 문장 단위로 모두 분해
// 2) 각 슬롯 maxLen에 맞춰 문장 1~2개 묶어 채움
// 3) 슬롯 수보다 문장이 적으면 뒤쪽 슬롯은 비움
function distributeToSlots(fullText, slots) {
  const sentences = splitSentences(stripMarkdown(fullText));
  if (!sentences.length) return slots.map(() => '');

  // 슬롯별 최대 글자수 — 면적 기반. 짧고 또렷한 한 마디 우선.
  const slotCapacities = slots.map(s => {
    const area = s.width * s.height;
    if (s.type === 'box') return Math.round(area * 1100) + 18;
    return Math.round(area * 1200) + 22;
  });

  // 문장 큐
  const queue = sentences.slice();
  const result = [];
  const slotCount = slots.length;

  for (let i = 0; i < slotCount; i++) {
    const cap = slotCapacities[i];
    if (!queue.length) { result.push(''); continue; }

    let chunk = '';
    while (queue.length) {
      const next = queue[0];
      const joiner = chunk ? ' ' : '';
      const tentative = chunk + joiner + next;
      // 남은 슬롯이 충분하면 한 슬롯에 하나만, 빠듯하면 합침
      const remainingSlots = slotCount - i - 1;
      const mustCompress = queue.length > remainingSlots + 1;

      if (tentative.length <= cap) {
        chunk = tentative;
        queue.shift();
        if (!mustCompress) break;  // 여유 있으면 한 문장씩
      } else if (!chunk) {
        // 한 문장이 슬롯보다 큼 — 압축해서 한 슬롯에 담고 다음으로
        chunk = compressForSlot(next, cap);
        queue.shift();
        break;
      } else {
        break;
      }
    }
    result.push(chunk);
  }

  // 마지막 슬롯이 비어있고 남은 문장이 있으면 마지막 슬롯에 합쳐 넣기
  if (queue.length && result.length) {
    let lastIdx = result.length - 1;
    while (lastIdx >= 0 && !result[lastIdx]) lastIdx--;
    if (lastIdx < 0) lastIdx = 0;
    const merge = queue.join(' ');
    const cap = slotCapacities[lastIdx];
    const combined = (result[lastIdx] ? result[lastIdx] + ' ' : '') + merge;
    result[lastIdx] = compressForSlot(combined, cap);
  }

  return result;
}

// ────────────────────────────────────────────────────────
// DOM 생성
// ────────────────────────────────────────────────────────
function buildPage(pageMeta, slotTexts, pageIdx) {
  const page = document.createElement('div');
  page.className = 'webtoon-page';

  const img = document.createElement('img');
  img.className = 'webtoon-page-img';
  img.src = pageMeta.src;
  img.alt = `풀이 ${pageIdx + 1}장`;
  img.loading = pageIdx < 2 ? 'eager' : 'lazy';
  page.appendChild(img);

  pageMeta.slots.forEach((slot, sIdx) => {
    const el = document.createElement('div');
    el.className = `webtoon-slot webtoon-slot-${slot.type}` +
      (slot.color === 'narration' ? ' webtoon-slot-narration' : '');
    el.style.top    = (slot.top * 100) + '%';
    el.style.left   = (slot.left * 100) + '%';
    el.style.width  = (slot.width * 100) + '%';
    el.style.height = (slot.height * 100) + '%';
    const text = slotTexts[sIdx] || '';
    el.textContent = text;
    // 텍스트 길이 기반 클래스 — CSS에서 폰트 자동 축소
    const len = text.length;
    if (len > 80) el.classList.add('len-xl');
    else if (len > 50) el.classList.add('len-l');
    else if (len > 25) el.classList.add('len-m');
    else el.classList.add('len-s');
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

  const allSlots = PAGES.flatMap(p => p.slots);
  const slotTexts = distributeToSlots(markdownText, allSlots);

  const container = document.createElement('div');
  container.className = 'webtoon-container';

  const header = document.createElement('h2');
  header.className = 'webtoon-title';
  header.textContent = title;
  container.appendChild(header);

  let cursor = 0;
  PAGES.forEach((pm, pIdx) => {
    const texts = slotTexts.slice(cursor, cursor + pm.slots.length);
    cursor += pm.slots.length;
    container.appendChild(buildPage(pm, texts, pIdx));
  });

  // 본문 그대로 보기
  const raw = document.createElement('details');
  raw.className = 'webtoon-raw';
  const summary = document.createElement('summary');
  summary.textContent = '본문 그대로 보기';
  raw.appendChild(summary);
  const pre = document.createElement('div');
  pre.className = 'webtoon-raw-body';
  const paragraphs = stripMarkdown(markdownText)
    .split(/\n{2,}/).map(p => p.replace(/\s+/g, ' ').trim()).filter(Boolean);
  pre.innerHTML = paragraphs.map(p => `<p>${p.replace(/</g, '&lt;')}</p>`).join('');
  raw.appendChild(pre);
  container.appendChild(raw);

  // 로딩 상태 클래스 제거 (flex 강제 등 잔존 스타일이 webtoon-container 폭을 깎는 문제 차단)
  targetEl.classList.remove('claude-loading', 'webtoon-loading');
  targetEl.innerHTML = '';
  targetEl.appendChild(container);
}

export const __WEBTOON_RENDERER_VERSION__ = '2.0.0';
