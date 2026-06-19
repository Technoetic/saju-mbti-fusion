// _gt_measure2.mjs — 더 관대한 임계값 + 가까운 fragment 병합
import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext();
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/', { waitUntil:'domcontentloaded' });
await p.waitForTimeout(1200);

async function analyze(src) {
  return await p.evaluate(async (src) => {
    const img = new Image(); img.crossOrigin='anonymous'; img.src=src;
    await new Promise(r=>{img.onload=r;});
    const cv = document.createElement('canvas');
    cv.width = img.naturalWidth; cv.height = img.naturalHeight;
    const cx = cv.getContext('2d'); cx.drawImage(img, 0, 0);
    const d = cx.getImageData(0,0,cv.width,cv.height).data;
    const W = cv.width, H = cv.height;

    const rowData = [];
    for (let y = 0; y < H; y += 2) {
      let whiteCount=0, brownCount=0, total=0;
      let wL=-1, wR=-1, bL=-1, bR=-1;
      for (let x = 0; x < W; x += 2) {
        const i = (y*W + x)*4;
        const r = d[i], g = d[i+1], bl = d[i+2];
        total++;
        if (r>235 && g>235 && bl>230) {
          whiteCount++;
          if (wL<0) wL=x; wR=x;
        } else if (r>50 && r<100 && g>35 && g<82 && bl>25 && bl<72) {
          brownCount++;
          if (bL<0) bL=x; bR=x;
        }
      }
      rowData.push({y, wRatio: whiteCount/total, bRatio: brownCount/total, wL, wR, bL, bR});
    }

    // 흰 row 후보 (좀 더 관대)
    const whiteRows = rowData.map(r => ({
      ...r,
      isW: r.wRatio >= 0.15 && r.wL >= 0 && (r.wL/W) > 0.03 && (r.wR/W) < 0.97
    }));
    const brownRows = rowData.map(r => ({
      ...r,
      isB: r.bRatio >= 0.20 && r.bL >= 0 && (r.bL/W) > 0.03 && (r.bR/W) < 0.97
    }));

    // run-length grouping with gap tolerance
    function groupRuns(rows, key, lkey, rkey, gapPx, minH, minW) {
      const groups = [];
      let cur = null;
      let gapCount = 0;
      for (const r of rows) {
        if (r[key]) {
          if (!cur) cur = { y0:r.y, y1:r.y, xL:r[lkey], xR:r[rkey] };
          else { cur.y1=r.y; cur.xL=Math.min(cur.xL,r[lkey]); cur.xR=Math.max(cur.xR,r[rkey]); }
          gapCount = 0;
        } else {
          if (cur) {
            gapCount += 2;
            if (gapCount > gapPx) {
              if (cur.y1-cur.y0 >= minH && cur.xR-cur.xL >= minW) groups.push(cur);
              cur = null;
              gapCount = 0;
            }
          }
        }
      }
      if (cur && cur.y1-cur.y0 >= minH && cur.xR-cur.xL >= minW) groups.push(cur);
      return groups;
    }

    const ovals = groupRuns(whiteRows, 'isW', 'wL', 'wR', 30, 80, 200)
      .map(g => ({ type:'oval', ...g }));
    const boxes = groupRuns(brownRows, 'isB', 'bL', 'bR', 30, 80, 200)
      .map(g => ({ type:'box', ...g }));

    const balloons = [...ovals, ...boxes].sort((a,b) => a.y0-b.y0);
    return balloons.map(g => ({
      type: g.type,
      top: +(g.y0/H).toFixed(4),
      left: +(g.xL/W).toFixed(4),
      width: +((g.xR-g.xL)/W).toFixed(4),
      height: +((g.y1-g.y0)/H).toFixed(4),
    }));
  }, src);
}

const out = {pages:[]};
for (let i=6; i<=10; i++) {
  const src = '/media/saju_webtoon/p'+i+'.jpg';
  const balloons = await analyze(src);
  out.pages.push({src: 'media/saju_webtoon/p'+i+'.jpg', balloons});
}
console.log(JSON.stringify(out, null, 2));
await b.close();
