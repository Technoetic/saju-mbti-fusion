import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
await page.goto('https://saju-mbti-fusion.fly.dev/', { waitUntil: 'load', timeout: 45000 });
await page.waitForTimeout(800);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(300);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(2500);
// 이미지 강제 디코드
await page.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.menu-card-art img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await page.waitForTimeout(500);
await page.screenshot({ path: '_quick_shot.png' });
const r = await page.evaluate(() => {
  const card = document.querySelector('.menu-card-illust');
  const art = card?.querySelector('.menu-card-art');
  const img = art?.querySelector('img');
  return {
    artW: Math.round(art.getBoundingClientRect().width),
    artH: Math.round(art.getBoundingClientRect().height),
    imgComplete: img?.complete, imgNatW: img?.naturalWidth, imgNatH: img?.naturalHeight,
  };
});
console.log(JSON.stringify(r));
await browser.close();
