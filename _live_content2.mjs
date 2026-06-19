// 콘텐츠 메뉴 카드 — 인증 우회 + 오늘의 운세 폼까지 직접 확인
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 430, height: 932 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1500);

// 1) 스와이프 힌트 제거
await page.evaluate(() => {
  document.getElementById('swipeHint')?.remove();
});

// 2) 만월 카드 클릭
await page.click('.char-card:has-text("만월 아씨")', { timeout: 5000 }).catch(() => {});
await page.waitForTimeout(800);

// 3) 인증 모달 우회 — '나중에 / 스킵 / 게스트' 버튼 시도, 없으면 직접 닫기
const skipped = await page.evaluate(() => {
  const auth = document.querySelector('.auth-modal, #cauthModal, [class*="cauth"]');
  if (!auth) return 'no_modal';
  // skip 버튼 모음
  const buttons = auth.querySelectorAll('button');
  for (const b of buttons) {
    const t = (b.textContent || '').trim();
    if (/스킵|건너|나중|skip|guest|게스트/i.test(t)) { b.click(); return 'clicked_skip: ' + t; }
  }
  // 그냥 강제 제거
  auth.remove();
  document.body.style.overflow = '';
  return 'force_removed';
});
console.log('Auth bypass:', skipped);
await page.waitForTimeout(600);

// 4) "오늘의 운세" 메뉴 클릭
const clicked = await page.evaluate(() => {
  const cards = document.querySelectorAll('.menu-card, .content-menu-card, .cmenu-card, [class*="menu"][class*="card"]');
  for (const c of cards) {
    if ((c.textContent || '').includes('오늘의 운세')) { c.click(); return c.className; }
  }
  // 백업: 텍스트 노드 검색
  const all = document.querySelectorAll('button, a, div, li');
  for (const el of all) {
    if ((el.textContent || '').trim().startsWith('오늘의 운세') && el.offsetWidth < 400) {
      el.click();
      return 'fallback:' + el.tagName + '.' + el.className;
    }
  }
  return 'not_found';
});
console.log('Today click:', clicked);
await page.waitForTimeout(1500);

await page.screenshot({ path: '_live_content2.png', fullPage: false });

// 5) 분홍 계열 텍스트 + 사용 토큰 추정
const pinks = await page.evaluate(() => {
  const out = [];
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const rect = el.getBoundingClientRect();
    if (rect.top < 0 || rect.top > 932 || rect.width === 0 || rect.height === 0) continue;
    const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
      ? el.textContent.trim() : '';
    if (!text || text.length > 40) continue;
    const cs = getComputedStyle(el);
    const m = cs.color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) continue;
    const [r, g, b] = [+m[1], +m[2], +m[3]];
    if (r > g + 15 && r > b + 15 && r > 120) {
      out.push({
        tag: el.tagName,
        cls: el.className?.toString().slice(0, 60) || '',
        color: cs.color,
        fontSize: cs.fontSize,
        text: text.slice(0, 30),
      });
    }
  }
  return out.slice(0, 25);
});
console.log('\n=== 분홍 계열 텍스트 ===');
for (const p of pinks) {
  console.log(`[${p.tag}.${p.cls}] ${p.color} ${p.fontSize}  "${p.text}"`);
}

await browser.close();
console.log('\nSaved: _live_content2.png');
