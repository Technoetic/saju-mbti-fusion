import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
p.on('pageerror', e => console.log('PAGEERR:' + e.message));
p.on('crash', () => console.log('STEP: page crash'));
p.on('close', () => console.log('STEP: page close'));
ctx.on('close', () => console.log('STEP: ctx close'));
b.on('disconnected', () => console.log('STEP: browser disconnect'));
p.on('console', m => {
  const t = m.text();
  if (/GLYPH|STEP|ERR/i.test(t)) console.log('[BR] ' + t);
});
console.log('STEP: node start');

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
  const set = (id, v) => {
    const el = document.getElementById(id);
    if (el) {
      el.value = v;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
  };
  set('fullName', '검증'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
});
await p.click('#goResultBtn').catch(() => {});
let ready = false;
for (let i = 0; i < 60; i++) {
  ready = await p.evaluate(() => !!document.querySelector('.webtoon-container'));
  if (ready) break;
  await p.waitForTimeout(2000);
}
console.log('STEP: webtoon ready=' + ready);
if (!ready) {
  await b.close();
  process.exit(0);
}

// Skip Promise.all decode — let browser handle natural decoding
console.log('STEP: pre-wait');
await p.waitForTimeout(3000);

// Per-page measurement to keep work bounded
let totalPages = 0;
try {
  totalPages = await p.evaluate(() => document.querySelectorAll('.webtoon-page').length);
} catch (e) { console.log('STEP: count err=' + e.message); }
console.log('STEP: pages=' + totalPages);

const allResults = [];
for (let pi = 0; pi < totalPages; pi++) {
  // Scroll page into view so lazy-loaded imgs decode
  await p.evaluate((pageIdx) => {
    const pages = document.querySelectorAll('.webtoon-page');
    pages[pageIdx]?.scrollIntoView({ block: 'center' });
  }, pi).catch(() => {});
  await p.waitForTimeout(1500);
  // Wait for image to load
  await p.evaluate(async (pageIdx) => {
    const pages = document.querySelectorAll('.webtoon-page');
    const img = pages[pageIdx]?.querySelector('.webtoon-page-img');
    if (img && !img.complete) {
      await new Promise(res => {
        img.addEventListener('load', res, { once: true });
        img.addEventListener('error', res, { once: true });
        setTimeout(res, 5000);
      });
    }
    if (img) { try { await img.decode(); } catch {} }
  }, pi).catch(() => {});
  await p.waitForTimeout(500);

  const pageResult = await p.evaluate(async (pageIdx) => {
    try {
      const pages = Array.from(document.querySelectorAll('.webtoon-page'));
      const pageEl = pages[pageIdx];
      if (!pageEl) return { error: 'no page', pageIdx };
      const pageR = pageEl.getBoundingClientRect();
      const img = pageEl.querySelector('.webtoon-page-img');
      if (!img || !img.naturalWidth) return { error: 'no img', pageIdx };

      // Wait for image natural dims (decoded by now since img has been visible)
      if (!img.naturalWidth) {
        try { await img.decode(); } catch (e) { return { error: 'decode:' + e.message, pageIdx }; }
      }
      // Use a small analysis canvas (downscale) to avoid OOM
      const TARGET_W = 240;
      const scale = TARGET_W / img.naturalWidth;
      const W = TARGET_W;
      const H = Math.round(img.naturalHeight * scale);
      const cv = document.createElement('canvas');
      cv.width = W; cv.height = H;
      const cx = cv.getContext('2d', { willReadFrequently: true });
      cx.drawImage(img, 0, 0, W, H);
      let d;
      try {
        d = cx.getImageData(0, 0, W, H).data;
      } catch (e) {
        return { error: 'getImageData:' + e.message, pageIdx };
      }

      const slots = Array.from(pageEl.querySelectorAll('.webtoon-slot')).map((s, slotIdx) => {
        const sr = s.getBoundingClientRect();
        const topN = (sr.top - pageR.top) / pageR.height;
        const leftN = (sr.left - pageR.left) / pageR.width;
        const widthN = sr.width / pageR.width;
        const heightN = sr.height / pageR.height;
        const isOval = s.classList.contains('webtoon-slot-oval');
        const targetType = isOval ? 'white' : 'brown';

        const sample = (fx, fy) => {
          const px = Math.max(0, Math.min(W - 1, Math.floor(fx * W)));
          const py = Math.max(0, Math.min(H - 1, Math.floor(fy * H)));
          const i = (py * W + px) * 4;
          const r = d[i], g = d[i + 1], bl = d[i + 2];
          return {
            isWhite: r > 230 && g > 230 && bl > 225,
            isBrown: r > 45 && r < 110 && g > 35 && g < 85 && bl > 25 && bl < 75,
          };
        };
        const gridFit = (l, t, w, h) => {
          let whiteN = 0, brownN = 0, total = 0;
          for (let yy = 0; yy < 8; yy++) {
            for (let xx = 0; xx < 8; xx++) {
              const fx = l + w * (xx + 0.5) / 8;
              const fy = t + h * (yy + 0.5) / 8;
              if (fx < 0 || fx > 1 || fy < 0 || fy > 1) continue;
              const r = sample(fx, fy);
              if (r.isWhite) whiteN++;
              else if (r.isBrown) brownN++;
              total++;
            }
          }
          return total > 0 ? { white: whiteN / total, brown: brownN / total } : { white: 0, brown: 0 };
        };
        const fitNow = gridFit(leftN, topN, widthN, heightN);
        const whiteRatio = +fitNow.white.toFixed(2);
        const brownRatio = +fitNow.brown.toFixed(2);
        const currentFit = targetType === 'white' ? fitNow.white : fitNow.brown;
        const fitsTarget = currentFit >= 0.75;

        // Direction suggestions
        const dirs = {
          up:      gridFit(leftN, topN - 0.04, widthN, heightN),
          down:    gridFit(leftN, topN + 0.04, widthN, heightN),
          left:    gridFit(leftN - 0.04, topN, widthN, heightN),
          right:   gridFit(leftN + 0.04, topN, widthN, heightN),
          bigger:  gridFit(leftN - 0.02, topN - 0.02, widthN + 0.04, heightN + 0.04),
          smaller: gridFit(leftN + 0.02, topN + 0.02, widthN - 0.04, heightN - 0.04),
        };
        const suggestions = [];
        for (const [dir, f] of Object.entries(dirs)) {
          const v = targetType === 'white' ? f.white : f.brown;
          if (v > currentFit + 0.05) {
            suggestions.push({ dir, fit: +v.toFixed(2), improvement: +(v - currentFit).toFixed(2) });
          }
        }
        suggestions.sort((a, b) => b.fit - a.fit);

        return {
          slotIdx,
          type: targetType,
          currentCoord: {
            top: +topN.toFixed(4), left: +leftN.toFixed(4),
            width: +widthN.toFixed(4), height: +heightN.toFixed(4),
          },
          whiteRatio, brownRatio, currentFit: +currentFit.toFixed(2),
          fitsTarget,
          suggestions: suggestions.slice(0, 2),
        };
      });
      // Free canvas after use to reduce memory
      cv.width = 0; cv.height = 0;
      return { pageIdx, slots };
    } catch (e) {
      return { error: e.message, pageIdx };
    }
  }, pi);
  console.log('GLYPH_PAGE:' + JSON.stringify(pageResult));
  allResults.push(pageResult);
}

console.log('GLYPH_RESULT:' + JSON.stringify(allResults));
await b.close();
