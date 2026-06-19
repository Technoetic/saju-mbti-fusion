// 두 가지 동시 검증:
// (A) 화선 낭자 → 꽃패 풀이 들어가기 → 카드 뽑기 화면(#tab-hwapae) 진입
// (B) 한자 '유'에 瑜(아름다운 옥) 노출

import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1000);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// ── (B-1) window 사전에 瑜 등록 ──
const yuRegistered = await page.evaluate(() => {
  const map = window['한글음_한자'];
  const strokes = window['한자획수'];
  const meaning = window['한자_뜻'];
  return {
    candidateHas瑜: (map?.['유'] || []).includes('瑜'),
    strokes瑜: strokes?.['瑜'] ?? null,
    meaning瑜: meaning?.['瑜'] ?? null,
  };
});
console.log('=== (B) 한자 사전 ===');
console.log(JSON.stringify(yuRegistered, null, 2));

// ── (A) 화선 낭자(idx=2) → 꽃패 풀이 들어가기 ──
await page.evaluate(() => window.__galleryGoTo?.(2));
await page.waitForTimeout(600);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('꽃패')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);
await page.screenshot({ path: '_verify_hwapae.png' });

const hwapaeState = await page.evaluate(() => {
  return {
    tabHwapaeActive: !!document.getElementById('tab-hwapae')?.classList.contains('active'),
    hwapaeStepInputActive: !!document.getElementById('hwapae-step-input')?.classList.contains('active'),
    drawBtnExists: !!document.getElementById('hwapaeGoToDrawBtn'),
    legendText: document.querySelector('#tab-hwapae fieldset legend')?.textContent?.trim(),
  };
});
console.log('\n=== (A) 화패 진입 상태 ===');
console.log(JSON.stringify(hwapaeState, null, 2));

await browser.close();
console.log('\nSaved: _verify_hwapae.png');
