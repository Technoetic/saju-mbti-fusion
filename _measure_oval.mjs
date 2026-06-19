// 실제 라이브에서 흰 타원 위치와 슬롯 위치 비교 측정
import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
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
  const set = (id, v) => { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('input', {bubbles:true})); } };
  set('fullName', '테스트'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
});
await p.click('#goResultBtn').catch(() => {});
for (let i = 0; i < 60; i++) {
  if (await p.evaluate(() => !!document.querySelector('.webtoon-container'))) break;
  await p.waitForTimeout(2000);
}
await p.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.webtoon-page-img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await p.waitForTimeout(1500);

// 첫 페이지(p6) 캡쳐 후, 슬롯과 페이지 좌표 출력
const page1 = await p.evaluate(() => {
  const pageEl = document.querySelectorAll('.webtoon-page')[0];
  const pageR = pageEl.getBoundingClientRect();
  const slots = Array.from(pageEl.querySelectorAll('.webtoon-slot')).map(s => {
    const r = s.getBoundingClientRect();
    return {
      cls: s.className,
      // 페이지 기준 정규화 (현재 좌표가 어디로 잡혀있는지)
      topNorm: ((r.top - pageR.top) / pageR.height).toFixed(3),
      leftNorm: ((r.left - pageR.left) / pageR.width).toFixed(3),
      widthNorm: (r.width / pageR.width).toFixed(3),
      heightNorm: (r.height / pageR.height).toFixed(3),
      // pixel 좌표 (페이지 안에서)
      yPx: Math.round(r.top - pageR.top),
      hPx: Math.round(r.height),
    };
  });
  return { pageW: Math.round(pageR.width), pageH: Math.round(pageR.height), slots };
});
console.log('Page 1 (p6):', JSON.stringify(page1, null, 2));

// 페이지 1만 캡쳐 (해상도 높여서 좌표 정확히)
await p.evaluate(() => {
  document.querySelectorAll('.webtoon-page')[0].scrollIntoView({behavior:'instant', block:'start'});
});
await p.waitForTimeout(500);
await p.screenshot({ path: '_oval_check_p1.png', fullPage: false });
await b.close();
