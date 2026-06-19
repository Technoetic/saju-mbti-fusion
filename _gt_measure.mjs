// _gt_measure.mjs — 각 페이지에서 흰 타원/갈색 박스 bounding box 정밀 측정
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

    // 각 row에서 흰색·갈색 픽셀 + leftmost/rightmost 위치
    const rowData = [];
    for (let y = 0; y < H; y += 2) {
      let whiteCount=0, brownCount=0, total=0;
      let wL=-1, wR=-1, bL=-1, bR=-1;
      for (let x = 0; x < W; x += 2) {
        const i = (y*W + x)*4;
        const r = d[i], g = d[i+1], bl = d[i+2];
        total++;
        if (r>240 && g>240 && bl>235) {
          whiteCount++;
          if (wL<0) wL=x; wR=x;
        } else if (r>55 && r<95 && g>40 && g<78 && bl>30 && bl<68) {
          brownCount++;
          if (bL<0) bL=x; bR=x;
        }
      }
      rowData.push({y, wRatio: whiteCount/total, bRatio: brownCount/total, wL, wR, bL, bR});
    }

    // 진짜 말풍선/박스 = 좌우 가장자리 닿지 않음 (left>0.04 && right<0.96)
    // + 일정 크기 이상 (h>=40 px, w>=200 px)
    const balloons = [];
    let cur = null;
    for (const r of rowData) {
      const isBalloonRow = r.wRatio >= 0.25 && r.wL >= 0 &&
                         (r.wL/W) > 0.04 && (r.wR/W) < 0.96;
      if (isBalloonRow) {
        if (!cur) cur = { type:'oval', y0:r.y, y1:r.y, xL:r.wL, xR:r.wR };
        else { cur.y1=r.y; cur.xL=Math.min(cur.xL, r.wL); cur.xR=Math.max(cur.xR, r.wR); }
      } else {
        if (cur && cur.y1-cur.y0 >= 40 && cur.xR-cur.xL >= 200) balloons.push(cur);
        cur = null;
      }
    }
    if (cur && cur.y1-cur.y0 >= 40 && cur.xR-cur.xL >= 200) balloons.push(cur);

    // 갈색 박스
    let bcur = null;
    for (const r of rowData) {
      const isBoxRow = r.bRatio >= 0.30 && r.bL >= 0 &&
                       (r.bL/W) > 0.04 && (r.bR/W) < 0.96;
      if (isBoxRow) {
        if (!bcur) bcur = { type:'box', y0:r.y, y1:r.y, xL:r.bL, xR:r.bR };
        else { bcur.y1=r.y; bcur.xL=Math.min(bcur.xL, r.bL); bcur.xR=Math.max(bcur.xR, r.bR); }
      } else {
        if (bcur && bcur.y1-bcur.y0 >= 40 && bcur.xR-bcur.xL >= 200) balloons.push(bcur);
        bcur = null;
      }
    }
    if (bcur && bcur.y1-bcur.y0 >= 40 && bcur.xR-bcur.xL >= 200) balloons.push(bcur);

    balloons.sort((a,b) => a.y0-b.y0);
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
