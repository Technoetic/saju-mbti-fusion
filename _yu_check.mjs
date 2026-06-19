// 한자 "유" 셀렉터에 瑜가 뜨는지 라이브 직접 검증
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1000);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 빠른 검증: window.한글음_한자/한자획수/한자_뜻에 瑜 등록 여부
const tokens = await page.evaluate(() => {
  const map = window['한글음_한자'] || window.SAJU?.['한글음_한자'];
  const strokes = window['한자획수'] || window.SAJU?.['한자획수'];
  const meaning = window['한자_뜻'] || window.SAJU?.['한자_뜻'];
  return {
    mapHasYu: !!map?.['유'],
    yuList: map?.['유'] || [],
    yuHas瑜: (map?.['유'] || []).includes('瑜'),
    stroke瑜: strokes?.['瑜'] ?? null,
    meaning瑜: meaning?.['瑜'] ?? null,
  };
});
console.log(JSON.stringify(tokens, null, 2));

// 만월 → 메뉴 → "정통 사주" 등 이름 한자 셀이 있는 폼 진입 시도
await page.evaluate(() => {
  const btns = document.querySelectorAll('button, a');
  for (const b of btns) {
    const t = (b.textContent || '').trim();
    if (t === '사주 풀이 들어가기') { b.click(); return; }
  }
});
await page.waitForTimeout(1000);
await page.evaluate(() => {
  for (const e of document.querySelectorAll('.menu-card-name')) {
    if (e.textContent.includes('정통 사주') || e.textContent.includes('오늘의 운세')) {
      e.closest('.menu-card')?.click();
      return;
    }
  }
});
await page.waitForTimeout(1500);

// 이름 input에 "유" 포함 이름 입력 + 한자 셀렉터 옵션 점검
const inputResult = await page.evaluate(() => {
  const nameInput = document.querySelector('input[id*="name" i], input[placeholder*="이름"]');
  if (!nameInput) return { found: false, reason: 'no name input' };
  nameInput.value = '박유진';
  nameInput.dispatchEvent(new Event('input', { bubbles: true }));
  nameInput.dispatchEvent(new Event('change', { bubbles: true }));
  return { found: true };
});
console.log('Name input:', inputResult);
await page.waitForTimeout(1200);

// 한자 셀렉터(select)들에서 옵션 중 '瑜' 포함 여부
const selectorContent = await page.evaluate(() => {
  const selects = Array.from(document.querySelectorAll('select'));
  const out = [];
  for (const s of selects) {
    const opts = Array.from(s.options).map(o => o.textContent.trim());
    const has瑜 = opts.some(o => o.includes('瑜'));
    if (has瑜 || opts.some(o => o.includes('유') || o.match(/[一-龥]/))) {
      out.push({
        id: s.id || s.name || '',
        optionsSample: opts.slice(0, 10),
        has瑜,
      });
    }
  }
  return out;
});
console.log('\nSelectors snapshot:');
console.log(JSON.stringify(selectorContent, null, 2));

await page.screenshot({ path: '_yu_check.png' });
await browser.close();
