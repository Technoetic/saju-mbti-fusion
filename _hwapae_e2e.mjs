// 화패 풀이 전 흐름 추적 — 카드 뽑기 화면 + 결과까지
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

const consoleLogs = [];
page.on('console', m => consoleLogs.push(`[${m.type()}] ${m.text()}`));
page.on('pageerror', err => consoleLogs.push(`[pageerror] ${err.message}`));
page.on('requestfailed', req => consoleLogs.push(`[netfail] ${req.url()} ${req.failure()?.errorText}`));

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(900);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 화선 낭자 카드 클릭
await page.evaluate(() => window.__galleryGoTo?.(2));
await page.waitForTimeout(500);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('.char-card .char-card-enter')) {
    if ((b.textContent || '').includes('꽃패')) { b.click(); return; }
  }
});
await page.waitForTimeout(1500);

// alert 자동 처리
page.on('dialog', d => d.accept());

// 질문 입력 (필수)
await page.fill('#hwapaeQuestion', '오늘 이 일이 잘 풀릴까요?');
await page.waitForTimeout(300);

// "화 패 뽑 으 러 가 기" 버튼 클릭
await page.click('#hwapaeGoToDrawBtn');
await page.waitForTimeout(3500);  // 셔플 1.6s + 400ms + 마진

// 셔플 끝나길 기다리고 카드 화면 캡쳐
await page.waitForTimeout(2500);
await page.screenshot({ path: '_hwapae_deck.png', fullPage: false });

// 덱 상태
const deckState = await page.evaluate(() => {
  const shuffleEl = document.getElementById('hwapaeShuffle');
  const deckWrap  = document.getElementById('hwapaeDeckWrap');
  const deck      = document.getElementById('hwapaeDeck');
  return {
    shuffleDisplay: shuffleEl ? getComputedStyle(shuffleEl).display : null,
    deckWrapDisplay: deckWrap ? getComputedStyle(deckWrap).display : null,
    deckCount: deck ? deck.children.length : 0,
    deckChildSizes: deck ? Array.from(deck.children).slice(0,3).map(c => {
      const r = c.getBoundingClientRect();
      return { w: Math.round(r.width), h: Math.round(r.height), tag: c.tagName, cls: c.className };
    }) : [],
  };
});
console.log('=== Deck state after shuffle ===');
console.log(JSON.stringify(deckState, null, 2));

// 카드 3장 클릭 (랜덤 위치)
const drawn = await page.evaluate(() => {
  const deck = document.getElementById('hwapaeDeck');
  if (!deck) return { ok: false, reason: 'no deck' };
  const cards = Array.from(deck.children);
  if (cards.length < 3) return { ok: false, count: cards.length };
  for (let i = 0; i < 3; i++) cards[i * Math.floor(cards.length/3) + 1]?.click();
  return { ok: true };
});
console.log('Draw 3:', drawn);
await page.waitForTimeout(1500);
await page.screenshot({ path: '_hwapae_after_draw.png' });

// 결과 화면 대기 (LLM 호출이라 시간 걸림)
await page.waitForTimeout(8000);
await page.screenshot({ path: '_hwapae_result.png' });

const result = await page.evaluate(() => {
  const out = document.querySelector('#tab-hwapae .claude-output, #tab-hwapae .interp-box, #tab-hwapae .hwapae-result, .hwapae-reading');
  return {
    foundResult: !!out,
    resultText: out?.textContent?.slice(0, 200) || null,
    stepDrawActive: !!document.getElementById('hwapae-step-draw')?.classList.contains('active'),
    stepResultActive: !!document.getElementById('hwapae-step-result')?.classList.contains('active'),
    visibleSteps: Array.from(document.querySelectorAll('#tab-hwapae .hw-step')).map(s => ({
      id: s.id, active: s.classList.contains('active'), display: getComputedStyle(s).display
    })),
  };
});
console.log('\n=== Result state ===');
console.log(JSON.stringify(result, null, 2));

console.log('\n=== Console errors / network ===');
for (const l of consoleLogs.filter(x => /error|warn|fail/i.test(x)).slice(0, 30)) console.log(l);

await browser.close();
console.log('\nSaved: _hwapae_deck.png _hwapae_after_draw.png _hwapae_result.png');
