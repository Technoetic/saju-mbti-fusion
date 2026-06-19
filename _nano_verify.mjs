import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil:'domcontentloaded' });
await p.waitForTimeout(2500);
await p.evaluate(() => document.getElementById('swipeHint')?.remove());
await p.evaluate(() => window.__galleryGoTo?.(0));
await p.waitForTimeout(500);
await p.evaluate(() => {
  for (const btn of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((btn.textContent || '').includes('사주')) { btn.click(); return; }
  }
});
await p.waitForTimeout(1800);
await p.evaluate(() => {
  for (const c of document.querySelectorAll('#menuView .menu-card')) {
    if ((c.textContent || '').includes('정통 사주')) { c.click(); return; }
  }
});
await p.waitForTimeout(2200);
await p.evaluate(() => {
  const set = (id, v) => { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event('change',{bubbles:true})); el.dispatchEvent(new Event('input',{bubbles:true})); } };
  set('fullName', '나노검증'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
});
await p.click('#goResultBtn').catch(()=>{});
// nano-banana는 60초+ 걸림. 최대 150초 대기.
for (let i=0; i<75; i++) {
  if (await p.evaluate(() => document.querySelectorAll('.webtoon-page-banana').length >= 3)) break;
  await p.waitForTimeout(2000);
}
const count = await p.evaluate(() => document.querySelectorAll('.webtoon-page-banana').length);
console.log('banana pages rendered:', count);
await p.waitForTimeout(2000);
await p.screenshot({ path: '_nano_check.png', fullPage: false });
await b.close();
