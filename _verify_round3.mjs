import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/?v='+Date.now(), { waitUntil:'domcontentloaded' });
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
  set('fullName', '검증'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
});
await p.click('#goResultBtn').catch(()=>{});
for (let i=0; i<60; i++) {
  if (await p.evaluate(() => !!document.querySelector('.webtoon-container'))) break;
  await p.waitForTimeout(2000);
}
await p.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.webtoon-page-img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await p.waitForTimeout(1500);

const results = await p.evaluate(async () => {
  const pages = Array.from(document.querySelectorAll('.webtoon-page'));
  const out = [];
  for (let pi = 0; pi < pages.length; pi++) {
    const pageEl = pages[pi];
    const pageR = pageEl.getBoundingClientRect();
    const img = pageEl.querySelector('.webtoon-page-img');
    const cv = document.createElement('canvas');
    cv.width = img.naturalWidth; cv.height = img.naturalHeight;
    const cx = cv.getContext('2d');
    cx.drawImage(img, 0, 0);
    const d = cx.getImageData(0,0,cv.width,cv.height).data;
    const W = cv.width, H = cv.height;

    const slots = Array.from(pageEl.querySelectorAll('.webtoon-slot')).map(s => {
      const sr = s.getBoundingClientRect();
      const topNorm = (sr.top - pageR.top) / pageR.height;
      const leftNorm = (sr.left - pageR.left) / pageR.width;
      const widthNorm = sr.width / pageR.width;
      const heightNorm = sr.height / pageR.height;

      const slotCy = Math.floor((topNorm + heightNorm/2) * H);
      const slotCx = Math.floor((leftNorm + widthNorm/2) * W);

      const idx = (slotCy * W + slotCx) * 4;
      const r = d[idx], g = d[idx+1], bl = d[idx+2];
      const centerIsWhite = (r > 235 && g > 235 && bl > 230);
      const centerIsBrown = (r > 50 && r < 100 && g > 40 && g < 80 && bl > 30 && bl < 70);

      const corners = [];
      for (const [fx, fy] of [[0.1, 0.1], [0.9, 0.1], [0.1, 0.9], [0.9, 0.9], [0.5, 0.5]]) {
        const cx2 = Math.floor((leftNorm + widthNorm * fx) * W);
        const cy2 = Math.floor((topNorm + heightNorm * fy) * H);
        const ci = (cy2 * W + cx2) * 4;
        const cr = d[ci], cg = d[ci+1], cb = d[ci+2];
        corners.push({white: cr>235 && cg>235 && cb>230, brown: cr>50 && cr<100 && cg>40 && cg<80 && cb>30 && cb<70, r:cr, g:cg, b:cb});
      }
      const whiteCount = corners.filter(c => c.white).length;
      const brownCount = corners.filter(c => c.brown).length;
      const isOval = s.classList.contains('webtoon-slot-oval');
      const isBox = s.classList.contains('webtoon-slot-box') || s.classList.contains('webtoon-slot-narration');
      const fitsCorrectly = (isOval && whiteCount >= 4) || (isBox && brownCount >= 4);

      return {
        type: isOval ? 'oval' : 'box',
        top: +topNorm.toFixed(4),
        left: +leftNorm.toFixed(4),
        width: +widthNorm.toFixed(4),
        height: +heightNorm.toFixed(4),
        centerIsWhite,
        centerIsBrown,
        whiteCount,
        brownCount,
        fitsCorrectly,
      };
    });
    out.push({ page: pi+1, slots });
  }
  return out;
});
console.log('VERIFY_RESULT:' + JSON.stringify(results));
await b.close();
