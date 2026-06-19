// 콘텐츠 메뉴 카드(오늘의 운세)까지 들어가서 분홍 글자 원인 분석
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/';

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 430, height: 932 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1500);

// 스와이프 힌트 닫기 (있으면)
try {
  await page.evaluate(() => {
    const h = document.getElementById('swipeHint');
    if (h) h.remove();
  });
} catch (_) {}

// 만월 아씨 카드 클릭
try {
  await page.click('.char-card:has-text("만월 아씨")', { timeout: 5000 });
  await page.waitForTimeout(800);
} catch (e) {
  console.log('만월 카드 클릭 실패:', e.message);
}

// 오늘의 운세 메뉴 클릭 시도
try {
  await page.click('text=오늘의 운세', { timeout: 5000 });
  await page.waitForTimeout(1200);
} catch (e) {
  console.log('오늘의 운세 클릭 실패:', e.message);
}

await page.screenshot({ path: '_live_content.png', fullPage: false });

// 화면에 보이는 모든 분홍 계열 텍스트와 그 원인 분석
const pinks = await page.evaluate(() => {
  const out = [];
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const rect = el.getBoundingClientRect();
    if (rect.top < 0 || rect.top > 932 || rect.width === 0 || rect.height === 0) continue;
    const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
      ? el.textContent.trim() : '';
    if (!text || text.length > 40) continue;
    const cs = getComputedStyle(el);
    const m = cs.color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) continue;
    const [r, g, b] = [+m[1], +m[2], +m[3]];
    // 분홍/연한핑크 계열만
    if (r > g + 15 && r > b + 15 && r > 150) {
      out.push({
        tag: el.tagName,
        cls: el.className?.toString().slice(0, 60) || '',
        id: el.id || '',
        color: cs.color,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        text: text.slice(0, 30),
        top: Math.round(rect.top),
        inlineStyle: el.getAttribute('style')?.slice(0, 80) || '',
      });
    }
  }
  return out;
});

console.log('=== 분홍 계열 텍스트 (콘텐츠 카드 화면) ===');
for (const p of pinks) {
  console.log(`[${p.tag}.${p.cls}${p.id ? '#'+p.id : ''}] ${p.color} ${p.fontSize}/w${p.fontWeight} top=${p.top}  "${p.text}"`);
  if (p.inlineStyle) console.log(`   inline: ${p.inlineStyle}`);
}

await browser.close();
console.log('\nSaved: _live_content.png');
