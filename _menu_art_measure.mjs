import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?v=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(900);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(400);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(2500);
// 이미지 로드 대기
// 모든 이미지 decode 끝날 때까지 대기
await page.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.menu-card-art img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await page.waitForTimeout(800);

const m = await page.evaluate(() => {
  const arts = Array.from(document.querySelectorAll('.menu-card-art')).slice(0, 3);
  return arts.map(a => {
    const r = a.getBoundingClientRect();
    const img = a.querySelector('img');
    const ir = img?.getBoundingClientRect();
    return {
      artW: Math.round(r.width), artH: Math.round(r.height),
      imgW: img ? Math.round(ir.width) : 0,
      imgH: img ? Math.round(ir.height) : 0,
      imgComplete: img?.complete,
      imgNatW: img?.naturalWidth, imgNatH: img?.naturalHeight,
      objFit: img ? getComputedStyle(img).objectFit : null,
    };
  });
});
console.log(JSON.stringify(m, null, 2));

await page.screenshot({ path: '_menu_art_measure.png' });
await browser.close();
