/* ============================================================
   manwol-renderer.js — 만월아씨 통합 서사 렌더러
   ============================================================
   /api/manwol/reading 스트리밍 응답을 심야 방송실 톤 텍스트 카드로 렌더.
   웹툰 렌더러(webtoon-renderer.js) 대체.
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
        <div class="manwol-body" data-manwol-body>
          <div class="manwol-cursor" aria-hidden="true"></div>
        </div>
        <div class="manwol-foot" data-manwol-foot></div>
      </div>
    </div>
  `;

  const body = targetEl.querySelector('[data-manwol-body]');
  const foot = targetEl.querySelector('[data-manwol-foot]');
  const cursor = body.querySelector('.manwol-cursor');

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
    // 마무리 · cursor 제거
    if (cursor && cursor.isConnected) cursor.remove();
    if (!acc.trim()) {
      body.innerHTML = '<p class="manwol-empty">사연 풀이 응답이 비었다. 다시 시도해봐.</p>';
      return;
    }
    // 하단 사인 (사인 오프)
    foot.innerHTML = '<div class="manwol-signoff">— 만월아씨</div>';
  } catch (err) {
    if (cursor && cursor.isConnected) cursor.remove();
    body.insertAdjacentHTML(
      'beforeend',
      `<p class="manwol-error">사연 풀이 도중 신호가 끊겼어. (${escapeHtml(String(err.message || err))})</p>`,
    );
  }
}

function renderParagraphs(body, text, cursor) {
  const paragraphs = text
    .replace(/\r\n/g, '\n')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
  const html = paragraphs
    .map((p) => `<p>${escapeHtml(p).replace(/\n/g, '<br>')}</p>`)
    .join('');
  // cursor를 유지하면서 본문만 갱신
  if (cursor && cursor.isConnected) cursor.remove();
  body.innerHTML = html;
  // 커서 재부착 (스트리밍 중임을 표시)
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
