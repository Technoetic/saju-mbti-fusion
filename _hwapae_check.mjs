// 화패 복원 검증 — 카드 4개 확인 + 화선 낭자 카드 + 탭 노출
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1200);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 카드 갤러리에 노출된 캐릭터들
const cards = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('#cardDeck .char-card')).map(c => ({
    go: c.dataset.go,
    char: c.dataset.character,
    name: c.querySelector('.char-card-name')?.textContent?.trim(),
  }));
});
console.log('카드 갤러리:');
for (const c of cards) console.log(`  - ${c.go} (${c.char}): ${c.name}`);

// 탭바
const tabs = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.tab-bar .tab-btn')).map(b => b.dataset.tab);
});
console.log('\n탭바:', tabs);

// 만월 → 갤러리 두 번 스와이프해서 화선 낭자 카드 노출
await page.evaluate(() => window.__galleryGoTo?.(2));   // 0:만월 1:몽이 2:화선 3:운학
await page.waitForTimeout(800);
await page.screenshot({ path: '_hwapae_card.png' });

await browser.close();
console.log('\nSaved: _hwapae_card.png');
