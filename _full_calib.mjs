// 5장 모든 흰 타원/박스 영역의 픽셀 정확 bounding box 측정
// 모든 행에서 흰색 픽셀이 모인 가로 범위를 추출 → 흰 타원/박스의 정확한 경계

import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext();
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/', { waitUntil: 'domcontentloaded' });
await p.waitForTimeout(1500);

async function analyzePage(src) {
  return await p.evaluate(async (src) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = src;
    await new Promise((r) => { img.onload = r; });
    const cv = document.createElement('canvas');
    cv.width = img.naturalWidth; cv.height = img.naturalHeight;
    const cx = cv.getContext('2d');
    cx.drawImage(img, 0, 0);
    const data = cx.getImageData(0, 0, cv.width, cv.height).data;
    const W = cv.width, H = cv.height;

    // 각 행에서 흰색·갈색 픽셀 비율 + 흰색 영역의 가로 외곽 (leftmost·rightmost)
    const rows = [];
    for (let y = 0; y < H; y += 4) {
      let white = 0, brown = 0, total = 0;
      let xMin = -1, xMax = -1, brownXMin = -1, brownXMax = -1;
      for (let x = 0; x < W; x += 2) {
        const i = (y * W + x) * 4;
        const r = data[i], g = data[i+1], bl = data[i+2];
        total++;
        if (r > 240 && g > 240 && bl > 235) {
          white++;
          if (xMin < 0) xMin = x; xMax = x;
        } else if (r > 50 && r < 100 && g > 40 && g < 80 && bl > 30 && bl < 70) {
          brown++;
          if (brownXMin < 0) brownXMin = x; brownXMax = x;
        }
      }
      rows.push({ y, w: white/total, b: brown/total, xMin, xMax, brownXMin, brownXMax });
    }

    // 흰 영역 그룹화 — 단순히 연속된 흰 비율>0.6 + xMin/xMax 통합
    const groups = [];
    let cur = null;
    for (const r of rows) {
      if (r.w >= 0.4 && r.xMin >= 0) {
        if (!cur) cur = { y0: r.y, y1: r.y, xMin: r.xMin, xMax: r.xMax, color: 'white' };
        else { cur.y1 = r.y; cur.xMin = Math.min(cur.xMin, r.xMin); cur.xMax = Math.max(cur.xMax, r.xMax); }
      } else {
        if (cur && cur.y1 - cur.y0 >= 40) groups.push(cur);
        cur = null;
      }
    }
    if (cur && cur.y1 - cur.y0 >= 40) groups.push(cur);

    // 갈색 박스 그룹화
    const brownGroups = [];
    let bcur = null;
    for (const r of rows) {
      if (r.b >= 0.30 && r.brownXMin >= 0) {
        if (!bcur) bcur = { y0: r.y, y1: r.y, xMin: r.brownXMin, xMax: r.brownXMax, color: 'brown' };
        else { bcur.y1 = r.y; bcur.xMin = Math.min(bcur.xMin, r.brownXMin); bcur.xMax = Math.max(bcur.xMax, r.brownXMax); }
      } else {
        if (bcur && bcur.y1 - bcur.y0 >= 40) brownGroups.push(bcur);
        bcur = null;
      }
    }
    if (bcur && bcur.y1 - bcur.y0 >= 40) brownGroups.push(bcur);

    // 정규화
    const norm = (g) => ({
      color: g.color,
      top: (g.y0/H).toFixed(3),
      bottom: (g.y1/H).toFixed(3),
      left: (g.xMin/W).toFixed(3),
      right: (g.xMax/W).toFixed(3),
      height: ((g.y1-g.y0)/H).toFixed(3),
      width: ((g.xMax-g.xMin)/W).toFixed(3),
    });
    const all = [...groups, ...brownGroups].map(norm).sort((a,b) => parseFloat(a.top) - parseFloat(b.top));
    // 진짜 말풍선/박스만: 좌우 가장자리까지 채우지 않는 = 컷 안에 갇힌 영역
    return all.filter(g => parseFloat(g.left) > 0.04 || parseFloat(g.right) < 0.96);
  }, src);
}

for (let i = 6; i <= 10; i++) {
  const src = `/media/saju_webtoon/p${i}.jpg`;
  const r = await analyzePage(src);
  console.log(`\n=== p${i}.jpg ===`);
  for (const g of r) console.log(`  ${g.color}  top=${g.top} bot=${g.bottom} h=${g.height}  left=${g.left} right=${g.right} w=${g.width}`);
}

await b.close();
