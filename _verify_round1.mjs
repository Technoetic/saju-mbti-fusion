import { chromium } from 'playwright';
import fs from 'fs';
const log = (...a) => { console.log(...a); fs.appendFileSync('_verify_log.txt', a.join(' ')+'\n'); };
fs.writeFileSync('_verify_log.txt', '');

const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
p.on('console', m => log('[BR]', m.type(), m.text().slice(0, 200)));
p.on('pageerror', e => log('[PE]', String(e).slice(0, 300)));
try {
  log('STEP: goto');
  await p.goto('https://saju-mbti-fusion.fly.dev/?v='+Date.now(), { waitUntil:'domcontentloaded', timeout: 30000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => document.getElementById('swipeHint')?.remove());
  await p.evaluate(() => window.__galleryGoTo?.(0));
  await p.waitForTimeout(500);
  log('STEP: click saju');
  await p.evaluate(() => {
    for (const btn of document.querySelectorAll('.char-card .char-card-enter')) {
      if ((btn.textContent || '').includes('사주')) { btn.click(); return; }
    }
  });
  await p.waitForTimeout(1800);
  log('STEP: click 정통');
  await p.evaluate(() => {
    for (const c of document.querySelectorAll('#menuView .menu-card')) {
      if ((c.textContent || '').includes('정통 사주')) { c.click(); return; }
    }
  });
  await p.waitForTimeout(2200);
  log('STEP: fill form');
  await p.evaluate(() => {
    const set = (id, v) => { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event('change',{bubbles:true})); el.dispatchEvent(new Event('input',{bubbles:true})); } };
    set('fullName', '검증'); set('year', '1995'); set('month', '6'); set('day', '15');
    set('hour', '14'); set('minute', '30'); set('gender', 'F'); set('calendarType', 'solar');
  });
  await p.click('#goResultBtn').catch(()=>{});
  log('STEP: wait webtoon');
  await p.waitForSelector('.webtoon-container', { timeout: 120000 });
  log('STEP: webtoon found');
  // Force-eager-load all webtoon images by removing lazy attr + scroll into view
  await p.evaluate(() => {
    document.querySelectorAll('.webtoon-page-img').forEach(i => { i.loading = 'eager'; });
  });
  // Scroll through webtoon to trigger lazy loads
  await p.evaluate(async () => {
    const pages = document.querySelectorAll('.webtoon-page');
    for (const pg of pages) {
      pg.scrollIntoView({ block: 'start' });
      await new Promise(r => setTimeout(r, 200));
    }
    window.scrollTo(0, 0);
  });
  // Wait up to 180s for all images
  let imgStatus = null;
  for (let t = 0; t < 90; t++) {
    imgStatus = await p.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('.webtoon-page-img'));
      return imgs.map(i => ({ src: i.src.split('/').pop(), complete: i.complete, w: i.naturalWidth }));
    });
    const allOK = imgStatus.length > 0 && imgStatus.every(s => s.complete && s.w > 0);
    if (allOK) break;
    if (t % 10 === 0) log('img status:', JSON.stringify(imgStatus));
    await p.waitForTimeout(2000);
  }
  log('STEP: images final:', JSON.stringify(imgStatus));
  await p.waitForTimeout(1000);
  log('STEP: measure');

  // Per-page measure separately with timeout
  const pageCount = await p.evaluate(() => document.querySelectorAll('.webtoon-page').length);
  log('PAGES:', pageCount);
  const results = [];
  for (let pi = 0; pi < pageCount; pi++) {
    log(`STEP: measure page ${pi+1}`);
    const r = await Promise.race([
      p.evaluate(async (pi) => {
        const pageEl = document.querySelectorAll('.webtoon-page')[pi];
        const pageR = pageEl.getBoundingClientRect();
        const img = pageEl.querySelector('.webtoon-page-img');
        let d = null, W = 0, H = 0;
        try {
          const cv = document.createElement('canvas');
          cv.width = img.naturalWidth; cv.height = img.naturalHeight;
          W = cv.width; H = cv.height;
          const cx = cv.getContext('2d');
          cx.drawImage(img, 0, 0);
          d = cx.getImageData(0,0,W,H).data;
        } catch (e) {
          return { page: pi+1, err: 'canvas: ' + e.message, slots: [] };
        }
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
            cornersRGB: corners.map(c => [c.r, c.g, c.b]),
          };
        });
        return { page: pi+1, slots };
      }, pi),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout-page-' + (pi+1))), 30000)),
    ]).catch(e => ({ page: pi+1, err: e.message, slots: [] }));
    results.push(r);
  }
  log('VERIFY_RESULT:' + JSON.stringify(results));
  fs.writeFileSync('_verify_result.json', JSON.stringify(results, null, 2));
} catch (e) {
  log('ERR:', String(e).slice(0, 500));
}
await b.close().catch(()=>{});
process.exit(0);
