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

const result = await p.evaluate(async () => {
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
      const topN = (sr.top - pageR.top) / pageR.height;
      const leftN = (sr.left - pageR.left) / pageR.width;
      const widthN = sr.width / pageR.width;
      const heightN = sr.height / pageR.height;
      const isOval = s.classList.contains('webtoon-slot-oval');
      const isBox = s.classList.contains('webtoon-slot-box') || s.classList.contains('webtoon-slot-narration');
      const targetType = isOval ? 'white' : 'brown';

      const sample = (fx, fy) => {
        const px = Math.floor((leftN + widthN * fx) * W);
        const py = Math.floor((topN + heightN * fy) * H);
        const i = (py * W + px) * 4;
        const r = d[i], g = d[i+1], bl = d[i+2];
        return { r, g, b: bl,
          isWhite: r > 235 && g > 235 && bl > 230,
          isBrown: r > 50 && r < 100 && g > 40 && g < 80 && bl > 30 && bl < 70,
        };
      };
      const grid = [];
      for (let yy = 0; yy < 8; yy++) {
        for (let xx = 0; xx < 8; xx++) {
          grid.push(sample((xx+0.5)/8, (yy+0.5)/8));
        }
      }
      const whiteRatio = grid.filter(c => c.isWhite).length / grid.length;
      const brownRatio = grid.filter(c => c.isBrown).length / grid.length;
      const fitsTarget = targetType === 'white' ? whiteRatio >= 0.75 : brownRatio >= 0.75;

      const sampleBox = (dxN, dyN) => {
        let whiteN = 0, brownN = 0, total = 0;
        for (let yy = 0; yy < 6; yy++) {
          for (let xx = 0; xx < 6; xx++) {
            const fx = leftN + dxN + widthN * (xx+0.5)/6;
            const fy = topN + dyN + heightN * (yy+0.5)/6;
            if (fx < 0 || fx > 1 || fy < 0 || fy > 1) continue;
            const px = Math.floor(fx * W);
            const py = Math.floor(fy * H);
            const i = (py * W + px) * 4;
            const r = d[i], g = d[i+1], bl = d[i+2];
            if (r > 235 && g > 235 && bl > 230) whiteN++;
            else if (r > 50 && r < 100 && g > 40 && g < 80 && bl > 30 && bl < 70) brownN++;
            total++;
          }
        }
        return total > 0 ? (targetType === 'white' ? whiteN/total : brownN/total) : 0;
      };
      const dirs = {
        up:    sampleBox(0, -0.04),
        down:  sampleBox(0,  0.04),
        left:  sampleBox(-0.04, 0),
        right: sampleBox( 0.04, 0),
        bigger: sampleBox(-0.02, -0.02),
        smaller: sampleBox(0.02, 0.02),
      };

      const currentFit = targetType === 'white' ? whiteRatio : brownRatio;
      const suggestions = [];
      for (const [dir, fit] of Object.entries(dirs)) {
        if (fit > currentFit + 0.05) suggestions.push({dir, fit: +fit.toFixed(2), improvement: +(fit - currentFit).toFixed(2)});
      }
      suggestions.sort((a,b) => b.fit - a.fit);

      return {
        type: targetType,
        currentCoord: { top: +topN.toFixed(4), left: +leftN.toFixed(4), width: +widthN.toFixed(4), height: +heightN.toFixed(4) },
        whiteRatio: +whiteRatio.toFixed(2),
        brownRatio: +brownRatio.toFixed(2),
        fitsTarget,
        suggestions: suggestions.slice(0, 2),
      };
    });
    out.push({ pageIdx: pi, slots });
  }
  return out;
});
console.log('GLYPH_RESULT:' + JSON.stringify(result));
await b.close();
