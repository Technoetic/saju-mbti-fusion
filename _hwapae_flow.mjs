// 화선 낭자 → 카드 뽑기 화면까지 가는 경로 추적
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1000);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 화선 낭자 카드(idx 2) 활성화 후 "꽃패 풀이 들어가기" 클릭
await page.evaluate(() => window.__galleryGoTo?.(2));
await page.waitForTimeout(800);
await page.screenshot({ path: '_flow_1_hwaseon_card.png' });

await page.evaluate(() => {
  const btns = document.querySelectorAll('.char-card .char-card-enter');
  for (const b of btns) {
    if ((b.textContent || '').includes('꽃패')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);
await page.screenshot({ path: '_flow_2_after_enter.png' });

// 어떤 뷰가 떴는지 + #tab-hwapae·#menuView 표시 여부
const state = await page.evaluate(() => {
  return {
    bodyClasses: document.body.className,
    tabHwapaeVisible: !!document.getElementById('tab-hwapae')?.classList.contains('active'),
    menuViewDisplay: getComputedStyle(document.getElementById('menuView')).display,
    contentViewDisplay: getComputedStyle(document.getElementById('contentView')).display,
    hwapaeStepInputDisplay: getComputedStyle(document.getElementById('hwapae-step-input') || document.body).display,
    menuMasterName: document.getElementById('menuMasterName')?.textContent?.trim(),
  };
});
console.log(JSON.stringify(state, null, 2));

await browser.close();
console.log('\nSaved: _flow_1_hwaseon_card.png, _flow_2_after_enter.png');
