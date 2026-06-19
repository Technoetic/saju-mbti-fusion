// 모바일 폭에서 카드 3장 슬롯이 폭을 넘는지 측정
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
page.on('dialog', d => d.accept());

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(800);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());
await page.evaluate(() => window.__galleryGoTo?.(2));
await page.waitForTimeout(400);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('꽃패')) { b.click(); return; }
  }
});
await page.waitForTimeout(1200);
await page.fill('#hwapaeQuestion', '오늘 일이 잘 풀릴까요?');
await page.click('#hwapaeGoToDrawBtn');
await page.waitForTimeout(3500);
// 순차 클릭 — drawn 슬롯이 3개 채워질 때까지
for (let i = 0; i < 3; i++) {
  await page.evaluate((seed) => {
    const deck = document.getElementById('hwapaeDeck');
    const cards = Array.from(deck.querySelectorAll('.hw-deck-card:not(.drawn)'));
    if (cards.length) cards[seed % cards.length].click();
  }, i * 7 + 3);
  await page.waitForTimeout(700);
}
// 결과 단계로 전환되길 + 카드 펼침 애니메이션 완료
await page.waitForTimeout(2500);

// 어떤 step에 있는지 + overflow 주범 찾기
const overflowCulprits = await page.evaluate(() => {
  const vw = window.innerWidth;
  const out = [];
  for (const el of document.querySelectorAll('#tab-hwapae *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.right > vw + 1) {
      out.push({
        tag: el.tagName,
        cls: (el.className || '').toString().slice(0, 60),
        id: el.id || '',
        w: Math.round(r.width),
        x: Math.round(r.left),
        right: Math.round(r.right),
        overflow: r.right - vw,
      });
    }
  }
  return out.slice(0, 15);
});
console.log('=== overflow culprits ===');
console.log(JSON.stringify(overflowCulprits, null, 2));

const activeStep = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('#tab-hwapae .hw-step')).map(s => ({
    id: s.id, active: s.classList.contains('active'), display: getComputedStyle(s).display,
  }));
});
console.log('\nsteps:', JSON.stringify(activeStep, null, 2));

// 결과 슬롯 측정
const m = await page.evaluate(() => {
  const slots = document.getElementById('hwapaeSlots');
  if (!slots) return null;
  const sr = slots.getBoundingClientRect();
  const tab = document.getElementById('tab-hwapae')?.getBoundingClientRect();
  const ps = slots.parentElement?.getBoundingClientRect();
  const children = Array.from(slots.children).map(c => {
    const r = c.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.left) };
  });
  const hw = document.querySelector('.hw-deck-wrap')?.getBoundingClientRect();
  return {
    viewportW: window.innerWidth,
    slotsLeft: Math.round(sr.left),
    slotsRight: Math.round(sr.right),
    slotsW: Math.round(sr.width),
    parentW: ps ? Math.round(ps.width) : null,
    tabW: tab ? Math.round(tab.width) : null,
    children,
    bodyScrollWidth: document.body.scrollWidth,
    htmlScrollWidth: document.documentElement.scrollWidth,
    overflowX: getComputedStyle(slots).overflowX,
  };
});
console.log(JSON.stringify(m, null, 2));

await page.screenshot({ path: '_hwapae_slot_measure.png', fullPage: true });
await browser.close();
