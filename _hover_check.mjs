import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
await p.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
await p.waitForTimeout(2200);
await p.evaluate(() => document.getElementById('swipeHint')?.remove());

// 일반 상태 캡쳐
await p.screenshot({ path: '_hover_normal.png' });

// 좌측 hot zone 위에 hover
const leftHot = await p.$('.gallery-swipe-hint-left, .gallery-edge-left');
if (leftHot) {
  const box = await leftHot.boundingBox();
  await p.mouse.move(box.x + box.width/2, box.y + box.height/2);
  await p.waitForTimeout(800);
  await p.screenshot({ path: '_hover_left.png' });
}
const rightHot = await p.$('.gallery-swipe-hint-right, .gallery-edge-right');
if (rightHot) {
  const box = await rightHot.boundingBox();
  await p.mouse.move(box.x + box.width/2, box.y + box.height/2);
  await p.waitForTimeout(800);
  await p.screenshot({ path: '_hover_right.png' });
}
await b.close();
console.log('captured normal/left/right');
