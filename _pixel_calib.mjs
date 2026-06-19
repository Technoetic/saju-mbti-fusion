// p6 컷2 흰 타원 픽셀 위치를 정확히 측정 + 슬롯 좌표와 비교
// 페이지 이미지를 캔버스로 그려 흰색 픽셀 군집 bounding box 잡기
import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 1 });
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/', { waitUntil: 'domcontentloaded' });
await p.waitForTimeout(1500);

// p6 이미지를 캔버스로 분석 → 흰 영역(타원·박스) bounding box 추출
const analysis = await p.evaluate(async () => {
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.src = '/media/saju_webtoon/p6.jpg';
  await new Promise((r, j) => { img.onload = r; img.onerror = j; });
  const cv = document.createElement('canvas');
  cv.width = img.naturalWidth; cv.height = img.naturalHeight;
  const cx = cv.getContext('2d');
  cx.drawImage(img, 0, 0);
  const data = cx.getImageData(0, 0, cv.width, cv.height).data;
  const W = cv.width, H = cv.height;

  // 각 y행에서 "흰색 픽셀(R>240,G>240,B>240)" + "갈색 박스(R≈70,G≈55,B≈45)" 비율
  const whiteRows = []; const brownRows = [];
  for (let y = 0; y < H; y += 2) {
    let white = 0, brown = 0, total = 0;
    for (let x = 0; x < W; x += 4) {
      const i = (y * W + x) * 4;
      const r = data[i], g = data[i+1], bl = data[i+2];
      total++;
      if (r > 240 && g > 240 && bl > 235) white++;
      else if (r > 50 && r < 100 && g > 40 && g < 80 && bl > 30 && bl < 70) brown++;
    }
    whiteRows.push({y, w: white/total});
    brownRows.push({y, b: brown/total});
  }

  // 흰색 비율 ≥0.6인 row들을 군집화 → 흰 타원/공백
  const findRanges = (rows, key, thresh) => {
    const ranges = [];
    let start = null;
    for (const r of rows) {
      if (r[key] >= thresh) {
        if (start == null) start = r.y;
      } else {
        if (start != null) { ranges.push([start, r.y - 2]); start = null; }
      }
    }
    if (start != null) ranges.push([start, rows[rows.length-1].y]);
    return ranges;
  };
  const whiteRanges = findRanges(whiteRows, 'w', 0.6).filter(r => r[1]-r[0] >= 50);
  const brownRanges = findRanges(brownRows, 'b', 0.35).filter(r => r[1]-r[0] >= 30);

  // 정규화
  return {
    H, W,
    white: whiteRanges.map(r => ({y0: r[0], y1: r[1], t0: (r[0]/H).toFixed(3), t1: (r[1]/H).toFixed(3)})),
    brown: brownRanges.map(r => ({y0: r[0], y1: r[1], t0: (r[0]/H).toFixed(3), t1: (r[1]/H).toFixed(3)})),
  };
});
console.log('p6.jpg 분석:');
console.log('  흰 영역(타원·여백):', JSON.stringify(analysis.white));
console.log('  갈색 영역(박스·라인):', JSON.stringify(analysis.brown));

// 추가: 흰 타원 가로 위치 (각 흰 row의 x 범위 평균)
const oval = await p.evaluate(async () => {
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.src = '/media/saju_webtoon/p6.jpg';
  await new Promise((r) => { img.onload = r; });
  const cv = document.createElement('canvas');
  cv.width = img.naturalWidth; cv.height = img.naturalHeight;
  const cx = cv.getContext('2d');
  cx.drawImage(img, 0, 0);
  const data = cx.getImageData(0, 0, cv.width, cv.height).data;
  const W = cv.width, H = cv.height;
  // 흰 타원 영역(자체 측정에서 0.49~0.59 즈음에 있을 것) — y 0.51 row에서 흰색이 어디부터 어디까지?
  // 흰 타원만 (빈 종이 영역 아님) 잡기 위해 타원 윗부분 약 0.510에서 측정.
  // 그 위치는 컷2 그림이 끝나는 자리라 좌우는 그림(짙은 색), 가운데만 흰 타원.
  const probeY = Math.floor(H * 0.510);
  let xStart = -1, xEnd = -1;
  for (let x = 0; x < W; x++) {
    const i = (probeY * W + x) * 4;
    const r = data[i], g = data[i+1], bl = data[i+2];
    if (r > 240 && g > 240 && bl > 235) {
      if (xStart < 0) xStart = x;
      xEnd = x;
    }
  }
  return { probeY, ratioY: (probeY/H).toFixed(3), xStart, xEnd, lStart: (xStart/W).toFixed(3), lEnd: (xEnd/W).toFixed(3), wRatio: ((xEnd-xStart)/W).toFixed(3) };
});
console.log('  흰 타원 가로 측정 (y≈0.535):', JSON.stringify(oval));

await b.close();
