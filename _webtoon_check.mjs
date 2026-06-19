// 정통 사주 결과 → 웹툰 모드 적용 확인
import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

page.on('console', m => { if (m.type() === 'error') console.log('[console error]', m.text()); });

await page.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2200);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 만월 아씨 → "사주 풀이 들어가기" → 메뉴 카드 첫번째('정통 사주') 클릭
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(400);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);

// 메뉴 그리드에서 '정통 사주' 카드 클릭
const order = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('#menuView .menu-card .menu-card-name')).map(e => e.textContent?.trim());
});
console.log('menu order:', order);

await page.evaluate(() => {
  for (const c of document.querySelectorAll('#menuView .menu-card')) {
    if ((c.textContent || '').includes('정통 사주')) { c.click(); return; }
  }
});
await page.waitForTimeout(1800);

// 정통 사주 입력 폼 → 사주 풀이 보기 버튼까지 자동
// 폼 ID = goResultBtn (saju-ui.js의 핸들러)
const formInfo = await page.evaluate(() => {
  return {
    hasGoBtn: !!document.getElementById('goResultBtn'),
    tabSajuActive: !!document.getElementById('tab-saju')?.classList.contains('active'),
    bodyClasses: document.body.className,
  };
});
console.log('form state:', formInfo);

await page.screenshot({ path: '_webtoon_check_form.png' });
await browser.close();
