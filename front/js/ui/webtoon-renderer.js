// webtoon-renderer.js — 만월 아씨 정통 사주 결과 웹툰 모드 (Nano Banana Pro)
//
// 사용:
//   import { renderWebtoonReading } from './webtoon-renderer.js';
//   await renderWebtoonReading(targetEl, markdownText, { title });
//
// 백엔드 /api/saju/webtoon 호출 → 생성된 이미지 5장(base64 PNG)을 그대로 표시.

export async function renderWebtoonReading(targetEl, markdownText, opts = {}) {
  if (!targetEl) return;
  const title = opts.title || '만월 아씨의 사주 이야기';

  // 로딩 상태 클래스 제거
  targetEl.classList.remove('claude-loading', 'webtoon-loading');

  const container = document.createElement('div');
  container.className = 'webtoon-container';
  const header = document.createElement('h2');
  header.className = 'webtoon-title';
  header.textContent = title;
  container.appendChild(header);

  // 로딩 인디케이터
  const loading = document.createElement('div');
  loading.className = 'webtoon-banana-loading';
  loading.innerHTML = `
    <div class="webtoon-loading-emblem">月</div>
    <div class="webtoon-loading-title">${title}</div>
    <div class="webtoon-loading-sub">만월 아씨가 그대의 사주를 웹툰으로 그리고 있어요 ⋯</div>
    <div class="webtoon-loading-progress">5장 동시 생성 중 (Nano Banana Pro · ~60초)</div>
  `;
  container.appendChild(loading);

  targetEl.innerHTML = '';
  targetEl.appendChild(container);

  try {
    const resp = await fetch('/api/saju/webtoon', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ reading: markdownText }),
    });
    if (!resp.ok) throw new Error('웹툰 생성 실패: HTTP ' + resp.status);
    const data = await resp.json();
    const images = data.images || [];
    if (images.length === 0) throw new Error('생성된 이미지가 없습니다');

    // 로딩 제거 + 이미지 5장 렌더
    loading.remove();
    images.forEach((b64, idx) => {
      const page = document.createElement('div');
      page.className = 'webtoon-page webtoon-page-banana';
      const img = document.createElement('img');
      img.className = 'webtoon-page-img';
      img.src = 'data:image/png;base64,' + b64;
      img.alt = `풀이 ${idx+1}장`;
      img.loading = idx < 2 ? 'eager' : 'lazy';
      page.appendChild(img);
      container.appendChild(page);
    });

    // 본문 그대로 보기
    const raw = document.createElement('details');
    raw.className = 'webtoon-raw';
    const summary = document.createElement('summary');
    summary.textContent = '본문 그대로 보기';
    raw.appendChild(summary);
    const body = document.createElement('div');
    body.className = 'webtoon-raw-body';
    const paragraphs = String(markdownText || '').split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
    body.innerHTML = paragraphs.map(p => '<p>' + p.replace(/</g, '&lt;') + '</p>').join('');
    raw.appendChild(body);
    container.appendChild(raw);
  } catch (e) {
    loading.innerHTML = `
      <div class="webtoon-loading-emblem">!</div>
      <div class="webtoon-loading-title">웹툰 생성에 실패했어요</div>
      <div class="webtoon-loading-sub">${e.message}</div>
      <div class="webtoon-loading-progress">잠시 후 다시 시도해주세요.</div>
    `;
  }
}

export const __WEBTOON_RENDERER_VERSION__ = '3.0.0-nano-banana';
