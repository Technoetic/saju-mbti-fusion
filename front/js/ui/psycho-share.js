// psychotest 결과 카드 SNS 공유 도구 (P3-7)
// ─────────────────────────────────────────────
// 3종 공유 액션:
//   1. navigator.share (모바일 OS 공유 시트)
//   2. PNG 다운로드 (canvas → blob → download)
//   3. 텍스트 클립보드 복사 (fallback)
//
// 캔버스 카드 디자인:
//   720×900 (인스타 스토리 9:16 근사)
//   배경 그라데이션 + 글리프 + 캐릭터 타이틀 + 본문 + 면책
//   ADR-006·010·014 정합 — 면책 자동 포함
//
// 외부 의존성: 없음 (브라우저 내장 Canvas + Blob + Clipboard API)

const CARD_W = 720;
const CARD_H = 900;

// ── 폰트 측정 helper (한국어 줄바꿈) ──
function wrapText(ctx, text, maxWidth) {
  const lines = [];
  for (const para of (text || '').split('\n')) {
    if (!para.trim()) { lines.push(''); continue; }
    let line = '';
    for (const ch of para) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = ch;
      } else {
        line = test;
      }
    }
    if (line) lines.push(line);
  }
  return lines;
}

// ── 캔버스 카드 렌더링 ──
export function renderShareCard(card, character) {
  const canvas = document.createElement('canvas');
  canvas.width = CARD_W;
  canvas.height = CARD_H;
  const ctx = canvas.getContext('2d');

  // 배경 그라데이션
  const grad = ctx.createLinearGradient(0, 0, 0, CARD_H);
  grad.addColorStop(0, '#2a2042');
  grad.addColorStop(1, '#1a1530');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, CARD_W, CARD_H);

  // 상단 장식 띠
  ctx.fillStyle = 'rgba(180, 130, 220, 0.25)';
  ctx.fillRect(0, 0, CARD_W, 6);
  ctx.fillRect(0, CARD_H - 6, CARD_W, 6);

  // 글리프 (큰 한자)
  ctx.fillStyle = 'rgba(220, 200, 240, 0.95)';
  ctx.font = 'bold 180px "Noto Serif KR", "Malgun Gothic", serif';
  ctx.textAlign = 'center';
  ctx.fillText(card.glyph || '心', CARD_W / 2, 230);

  // 카드 타이틀 (장면)
  ctx.fillStyle = 'rgba(220, 200, 240, 0.7)';
  ctx.font = '28px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.fillText(card.title || '', CARD_W / 2, 290);

  // 구분선
  ctx.strokeStyle = 'rgba(180, 160, 220, 0.3)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(120, 320);
  ctx.lineTo(CARD_W - 120, 320);
  ctx.stroke();

  // 캐릭터 타이틀 (큰 글씨)
  ctx.fillStyle = '#f0e6f8';
  ctx.font = 'bold 56px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.fillText(character.title || '결의 결', CARD_W / 2, 400);

  // 아키타입
  ctx.fillStyle = 'rgba(220, 180, 240, 0.85)';
  ctx.font = '28px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.fillText(character.archetype || '', CARD_W / 2, 445);

  // 본문 (줄바꿈)
  ctx.fillStyle = 'rgba(232, 224, 240, 0.92)';
  ctx.font = '24px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.textAlign = 'left';
  const bodyLines = wrapText(ctx, character.body || '', CARD_W - 160);
  let y = 510;
  for (const line of bodyLines.slice(0, 8)) {
    ctx.fillText(line, 80, y);
    y += 36;
  }

  // 그림자
  if (character.shadow) {
    ctx.fillStyle = 'rgba(240, 180, 180, 0.78)';
    ctx.font = '20px "Noto Sans KR", "Malgun Gothic", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`그림자 — ${character.shadow}`, CARD_W / 2, CARD_H - 110);
  }

  // 면책 (CLAUDE.md §9)
  ctx.fillStyle = 'rgba(180, 160, 200, 0.5)';
  ctx.font = '16px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('※ 일상 심리 가벼운 캐릭터 진단 (ADR-014).', CARD_W / 2, CARD_H - 60);
  ctx.fillText('참고용이며 의료·법률·금융 단독 근거 X.', CARD_W / 2, CARD_H - 36);

  return canvas;
}

// ── 텍스트 요약 (공유 API + 클립보드 공통) ──
export function buildShareText(card, character) {
  return [
    `${card.glyph || '心'} ${character.title || '결의 결'}`,
    character.archetype ? `[${character.archetype}]` : '',
    '',
    (character.body || '').split('\n')[0],
    '',
    `— ${card.title || ''} (사주·MBTI 융합 SaaS)`,
    'https://saju-mbti-fusion.fly.dev/',
  ].filter(Boolean).join('\n');
}

// ── 액션 1: navigator.share (모바일 OS 공유 시트) ──
export async function shareNative(card, character) {
  if (!navigator.share) return { ok: false, reason: 'unsupported' };
  const text = buildShareText(card, character);
  const canvas = renderShareCard(card, character);
  try {
    // canvas → blob → File (모바일 share 지원)
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    const file = blob ? new File([blob], `${card.key || 'psycho'}.png`, { type: 'image/png' }) : null;
    const payload = { title: character.title || '오늘 그대의 결', text };
    if (file && navigator.canShare && navigator.canShare({ files: [file] })) {
      payload.files = [file];
    }
    await navigator.share(payload);
    return { ok: true };
  } catch (err) {
    return { ok: false, reason: err.name === 'AbortError' ? 'cancelled' : 'failed' };
  }
}

// ── 액션 2: PNG 다운로드 ──
export function downloadShareCard(card, character) {
  const canvas = renderShareCard(card, character);
  canvas.toBlob(blob => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `psycho-${card.key || 'result'}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, 'image/png');
}

// ── 액션 3: 텍스트 클립보드 복사 ──
export async function copyShareText(card, character) {
  const text = buildShareText(card, character);
  try {
    await navigator.clipboard.writeText(text);
    return { ok: true };
  } catch (_) {
    return { ok: false };
  }
}
