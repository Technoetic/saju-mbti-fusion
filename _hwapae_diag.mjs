// 사용자 화면 재현 — critic PASS인데 stub 나오는 이유 추적
// safety_gate_verdict + failures를 응답 전체에서 캡쳐, 캐시 여부도 확인
import { chromium } from 'playwright';

async function callOnce(question, label) {
  const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 430, height: 932 } });
  const page = await ctx.newPage();
  let apiResp = null;
  page.on('response', async r => {
    if (r.url().includes('/api/hwapae/reading')) {
      apiResp = { status: r.status(), body: await r.text().catch(()=>'') };
    }
  });
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
  page.on('dialog', d => d.accept());
  await page.fill('#hwapaeQuestion', question);
  await page.click('#hwapaeGoToDrawBtn');
  await page.waitForTimeout(3500);
  await page.evaluate(() => {
    const deck = document.getElementById('hwapaeDeck');
    const cards = Array.from(deck.children);
    if (cards.length >= 3) {
      cards[3].click();
      setTimeout(() => cards[12].click(), 250);
      setTimeout(() => cards[22].click(), 500);
    }
  });
  await page.waitForTimeout(20000);
  await browser.close();
  console.log(`\n=== ${label} ===`);
  if (!apiResp) { console.log('NO API CALL'); return; }
  console.log('status:', apiResp.status);
  try {
    const j = JSON.parse(apiResp.body);
    console.log('cached:', j.cached);
    console.log('critic_passed/total:', j.critic_passed, '/', j.critic_total);
    console.log('safety_gate_verdict:', j.safety_gate_verdict);
    console.log('safety_gate_failures:', j.safety_gate_failures);
    console.log('safety_gate_fallback_used:', j.safety_gate_fallback_used);
    console.log('safety_gate_retry_used:', j.safety_gate_retry_used);
    console.log('text(앞 90):', (j.text || '').slice(0, 90));
    console.log('text len:', (j.text || '').length);
  } catch (e) { console.log('parse fail', e.message); console.log(apiResp.body.slice(0,400)); }
}

// 같은 질문은 cache hit 가능 — 다른 질문으로 2회 호출
await callOnce('오늘 그 일이 잘 풀릴까요? ' + Date.now(), 'CASE 1 (unique)');
await callOnce('이번 주 마음 흐름은? ' + Date.now(), 'CASE 2 (unique)');
