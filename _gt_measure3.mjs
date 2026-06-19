// _gt_measure3.mjs — 큰 gap 허용 + 인접 그룹 cluster 병합
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

    function detect(rows, ratioKey, lkey, rkey, ratioMin) {
      // 1단계: row를 hit/miss로 표시
      const hits = rows.map(r => ({
        y: r.y,
        ok: r[ratioKey] >= ratioMin && r[lkey] >= 0 && (r[lkey]/W) > 0.03 && (r[rkey]/W) < 0.97,
        l: r[lkey], rr: r[rkey]
      }));
      // 2단계: 작은 run 추출 (gap ≤ 4 px)
      const miniRuns = [];
      let cur = null; let gap=0;
      for (const h of hits) {
        if (h.ok) {
          if (!cur) cur = { y0:h.y, y1:h.y, xL:h.l, xR:h.rr };
          else { cur.y1=h.y; cur.xL=Math.min(cur.xL,h.l); cur.xR=Math.max(cur.xR,h.rr); }
          gap=0;
        } else {
          if (cur) {
            gap+=2;
            if (gap > 6) { miniRuns.push(cur); cur=null; gap=0; }
          }
        }
      }
      if (cur) miniRuns.push(cur);

      // 3단계: cluster — y 거리 ≤ H*0.04 이면 같은 balloon
      const yMerge = H * 0.045;
      const clusters = [];
      for (const r of miniRuns) {
        let merged = false;
        for (const c of clusters) {
          // overlap horizontal AND vertical proximity
          const hOverlap = Math.min(c.xR, r.xR) - Math.max(c.xL, r.xL);
          const vGap = r.y0 - c.y1;
          if (vGap <= yMerge && hOverlap > 50) {
            c.y1 = Math.max(c.y1, r.y1);
            c.xL = Math.min(c.xL, r.xL);
            c.xR = Math.max(c.xR, r.xR);
            merged = true;
            break;
          }
        }
        if (!merged) clusters.push({...r});
      }
      // 두번째 패스로 한번 더
      const merged2 = [];
      for (const c of clusters) {
        let did = false;
        for (const m of merged2) {
          const hOverlap = Math.min(m.xR, c.xR) - Math.max(m.xL, c.xL);
          const vGap = Math.max(0, c.y0 - m.y1);
          if (vGap <= yMerge && hOverlap > 50) {
            m.y1 = Math.max(m.y1, c.y1);
            m.y0 = Math.min(m.y0, c.y0);
            m.xL = Math.min(m.xL, c.xL);
            m.xR = Math.max(m.xR, c.xR);
            did = true; break;
          }
        }
        if (!did) merged2.push({...c});
      }
      // 최소 크기
      return merged2.filter(g => (g.y1-g.y0) >= 80 && (g.xR-g.xL) >= 200);
    }

    const ovals = detect(rowData, 'wRatio', 'wL', 'wR', 0.15).map(g => ({type:'oval', ...g}));
    const boxes = detect(rowData, 'bRatio', 'bL', 'bR', 0.20).map(g => ({type:'box', ...g}));
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
