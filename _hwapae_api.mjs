// Playwright로 실제 hwapae API 응답·payload 캡쳐
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 } });
const page = await ctx.newPage();

let apiCall = null;
page.on('request', req => {
  if (req.url().includes('/api/hwapae/reading')) {
    apiCall = { url: req.url(), method: req.method(), body: req.postData() };
  }
});
page.on('response', async resp => {
  if (resp.url().includes('/api/hwapae/reading')) {
    apiCall.status = resp.status();
    try { apiCall.responseBody = await resp.text(); } catch (_) {}
  }
});

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(900);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

await page.evaluate(() => window.__galleryGoTo?.(2));
await page.waitForTimeout(500);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('꽃패')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);
page.on('dialog', d => d.accept());
await page.fill('#hwapaeQuestion', '오늘 이 일이 잘 풀릴까요?');
await page.waitForTimeout(300);
await page.click('#hwapaeGoToDrawBtn');
await page.waitForTimeout(3500);

// 카드 3장 클릭
await page.evaluate(() => {
  const deck = document.getElementById('hwapaeDeck');
  const cards = Array.from(deck.children);
  if (cards.length >= 3) {
    cards[5].click();
    setTimeout(() => cards[15].click(), 200);
    setTimeout(() => cards[25].click(), 400);
  }
});
await page.waitForTimeout(2000);

// API 호출이 끝날 때까지 대기
await page.waitForTimeout(15000);

console.log('=== API call ===');
console.log('URL:', apiCall?.url);
console.log('Status:', apiCall?.status);
console.log('\n--- request body ---');
console.log(apiCall?.body?.slice(0, 600));
console.log('\n--- response body (first 1200) ---');
console.log(apiCall?.responseBody?.slice(0, 1200));

await page.screenshot({ path: '_hwapae_result_final.png' });
await browser.close();
