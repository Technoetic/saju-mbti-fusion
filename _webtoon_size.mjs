// 웹툰 페이지 폭·슬롯 측정 — 비율 깨진 원인 추적
import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
await page.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2500);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(500);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(1800);
await page.evaluate(() => {
  for (const c of document.querySelectorAll('#menuView .menu-card')) {
    if ((c.textContent || '').includes('정통 사주')) { c.click(); return; }
  }
});
await page.waitForTimeout(2200);
await page.evaluate(() => {
  const set = (id, v) => { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('input', {bubbles:true})); } };
  set('fullName', '김유진'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
});
await page.click('#goResultBtn').catch(() => {});
for (let i = 0; i < 60; i++) {
  if (await page.evaluate(() => !!document.querySelector('.webtoon-container'))) break;
  await page.waitForTimeout(2000);
}
await page.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.webtoon-page-img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await page.waitForTimeout(800);

const m = await page.evaluate(() => {
  const cont = document.querySelector('.webtoon-container');
  const page1 = document.querySelectorAll('.webtoon-page')[0];
  const claudeOut = page1?.closest('.claude-output');
  const rContainer = cont.getBoundingClientRect();
  const rPage = page1.getBoundingClientRect();
  const rClaude = claudeOut?.getBoundingClientRect();
  // 그리고 첫 페이지 슬롯의 위치
  const slots = Array.from(page1.querySelectorAll('.webtoon-slot')).map(s => {
    const r = s.getBoundingClientRect();
    return {
      cls: s.className.replace('webtoon-slot ', ''),
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.left - rPage.left), y: Math.round(r.top - rPage.top),
      text: s.textContent.slice(0, 30),
    };
  });
  return {
    viewportW: window.innerWidth,
    containerW: Math.round(rContainer.width),
    claudeW: rClaude ? Math.round(rClaude.width) : null,
    pageW: Math.round(rPage.width),
    pageH: Math.round(rPage.height),
    pageRatio: (rPage.height / rPage.width).toFixed(2),
    slots,
  };
});
console.log(JSON.stringify(m, null, 2));
await page.screenshot({ path: '_webtoon_size.png' });
await browser.close();
