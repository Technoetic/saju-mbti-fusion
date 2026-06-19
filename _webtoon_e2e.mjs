// 정통 사주 결과를 실제로 받아 웹툰 변환되는지 직접 확인
import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto('https://saju-mbti-fusion.fly.dev/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2200);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());
await page.evaluate(() => window.__galleryGoTo?.(0));
await page.waitForTimeout(400);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('사주')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  for (const c of document.querySelectorAll('#menuView .menu-card')) {
    if ((c.textContent || '').includes('정통 사주')) { c.click(); return; }
  }
});
await page.waitForTimeout(2000);

// 사주 입력 폼에 이름·생년월일·시각·성별 채우기
await page.evaluate(() => {
  const set = (id, v) => { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('input', {bubbles:true})); } };
  set('fullName', '박지수'); set('year', '1995'); set('month', '6'); set('day', '15');
  set('hour', '14'); set('minute', '30'); set('gender', 'F');
  set('calendarType', 'solar');
});
await page.waitForTimeout(500);

// [풀이 보기] 클릭
await page.click('#goResultBtn').catch(() => {});
console.log('Clicked goResultBtn');
await page.waitForTimeout(4000);
await page.screenshot({ path: '_webtoon_loading.png' });

// LLM 응답 대기 — webtoon-container가 나타날 때까지
let appeared = false;
for (let i = 0; i < 60; i++) {
  appeared = await page.evaluate(() => !!document.querySelector('.webtoon-container'));
  if (appeared) break;
  await page.waitForTimeout(2000);
}
console.log('webtoon-container appeared:', appeared);

const info = await page.evaluate(() => {
  const c = document.querySelector('.webtoon-container');
  if (!c) return null;
  const pages = c.querySelectorAll('.webtoon-page');
  const slots = c.querySelectorAll('.webtoon-slot');
  return {
    pages: pages.length,
    slots: slots.length,
    slotTextSamples: Array.from(slots).slice(0, 6).map(s => (s.textContent || '').slice(0, 35)),
    title: c.querySelector('.webtoon-title')?.textContent,
  };
});
console.log(JSON.stringify(info, null, 2));

await page.screenshot({ path: '_webtoon_result_top.png' });
// 페이지 끝까지 스크롤하면서 한 컷씩 캡쳐
// 이미지 디코드 끝까지 대기
await page.evaluate(async () => {
  const imgs = Array.from(document.querySelectorAll('.webtoon-page-img'));
  await Promise.all(imgs.map(i => i.decode().catch(()=>null)));
});
await page.waitForTimeout(800);
// 페이지별 캡쳐
for (let i = 0; i < 5; i++) {
  await page.evaluate((idx) => {
    document.querySelectorAll('.webtoon-page')[idx]?.scrollIntoView({ behavior: 'instant', block: 'start' });
  }, i);
  await page.waitForTimeout(500);
  await page.screenshot({ path: `_webtoon_p${i+1}.png` });
}

await browser.close();
console.log('Saved screenshots.');
