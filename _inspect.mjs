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
await p.waitForTimeout(800);
const m = await p.evaluate(() => {
  const r = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      w: Math.round(b.width), h: Math.round(b.height),
      display: cs.display,
      padding: cs.padding, margin: cs.margin,
      border: cs.borderWidth,
      maxWidth: cs.maxWidth, width: cs.width,
      aspectRatio: cs.aspectRatio,
    };
  };
  const claude = document.querySelector('.claude-output');
  const cont = document.querySelector('.webtoon-container');
  const page = document.querySelector('.webtoon-page');
  const parents = [];
  let cur = claude;
  while (cur && cur !== document.body) { parents.push({ tag: cur.tagName, id: cur.id, cls: cur.className, ...r(cur) }); cur = cur.parentElement; }
  return {
    claude: r(claude),
    container: r(cont),
    page: r(page),
    parentChain: parents,
  };
});
console.log(JSON.stringify(m, null, 2));
await b.close();
