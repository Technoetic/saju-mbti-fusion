// 만월 아씨 메뉴 카드 일러스트 적용 검증
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

const networkFails = [];
page.on('requestfailed', r => {
  if (r.url().includes('/media/')) networkFails.push(r.url() + ' ' + r.failure()?.errorText);
});

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(900);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 만월 아씨 카드(idx 0) → 사주 풀이 들어가기
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(400);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);

// 메뉴 카드 일러스트 상태 점검
const state = await page.evaluate(() => {
  const cards = Array.from(document.querySelectorAll('#menuView .menu-card'));
  return cards.map(c => {
    const img = c.querySelector('.menu-card-art img');
    const name = c.querySelector('.menu-card-name')?.textContent?.trim();
    const hasIllust = c.classList.contains('menu-card-illust');
    return {
      name,
      hasIllust,
      imgSrc: img?.getAttribute('src') || null,
      imgComplete: img ? img.complete && img.naturalWidth > 0 : null,
      imgW: img?.naturalWidth || 0,
      imgH: img?.naturalHeight || 0,
      cardW: Math.round(c.getBoundingClientRect().width),
      cardH: Math.round(c.getBoundingClientRect().height),
    };
  });
});
console.log('=== Menu cards ===');
for (const s of state) console.log(JSON.stringify(s));
console.log('\nMedia fails:', networkFails.length);
for (const f of networkFails.slice(0, 10)) console.log('  ', f);

// 스크린샷 — 전체 페이지
await page.screenshot({ path: '_menu_illust_full.png', fullPage: true });
// 첫 화면만
await page.screenshot({ path: '_menu_illust_view.png' });
await browser.close();
console.log('\nSaved: _menu_illust_view.png, _menu_illust_full.png');
